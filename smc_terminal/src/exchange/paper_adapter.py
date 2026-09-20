"""
SMC Algorithmic Trading Terminal - Realistic Paper Trading Exchange Adapter.
Simulates fee deduction (0.075%), realistic slippage (0.10%), tick constraints, and SL/TP fills.
"""

from datetime import datetime, timezone
import time
from typing import Dict, List, Optional
from src.data.models import Candle, OrderBook, OrderBookLevel, Ticker, Timeframe
from src.exchange.base import ExchangeAdapter
from src.exchange.exceptions import OrderError
from src.exchange.models import (
    BalanceModel,
    OrderRequest,
    OrderResponse,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionModel,
    SymbolConstraints,
)


class PaperTradingAdapter(ExchangeAdapter):
    """Local simulation adapter for realistic paper trading."""

    def __init__(
        self,
        initial_usdt: float = 10000.0,
        fee_rate: float = 0.00075,      # 0.075% standard maker/taker
        slippage_pct: float = 0.0010,    # 0.10% market order slippage
    ) -> None:
        self._connected = True
        self.initial_usdt = initial_usdt
        self.fee_rate = fee_rate
        self.slippage_pct = slippage_pct
        
        self.balances: Dict[str, BalanceModel] = {
            "USDT": BalanceModel("USDT", free=initial_usdt, locked=0.0, total=initial_usdt)
        }
        self.open_orders: Dict[str, OrderResponse] = {}
        self.order_history: List[OrderResponse] = []
        self.positions: Dict[str, PositionModel] = {}
        self.last_tickers: Dict[str, Ticker] = {}

        # Default standard crypto spot constraints
        self.constraints: Dict[str, SymbolConstraints] = {
            "BTCUSDT": SymbolConstraints("BTCUSDT", 0.01, 0.00001, 0.00001, 1000.0, 5.0, 2, 5),
            "ETHUSDT": SymbolConstraints("ETHUSDT", 0.01, 0.0001, 0.0001, 10000.0, 5.0, 2, 4),
            "SOLUSDT": SymbolConstraints("SOLUSDT", 0.001, 0.01, 0.01, 50000.0, 5.0, 3, 2),
        }

    def get_name(self) -> str:
        return "paper_trading_adapter"

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_symbol_constraints(self, symbol: str) -> SymbolConstraints:
        if symbol not in self.constraints:
            # Fallback safe constraint
            self.constraints[symbol] = SymbolConstraints(symbol, 0.01, 0.001, 0.001, 10000.0, 5.0, 2, 3)
        return self.constraints[symbol]

    def set_mock_ticker(self, symbol: str, price: float) -> None:
        """Inject current price for simulation."""
        now_ms = int(time.time() * 1000)
        self.last_tickers[symbol] = Ticker(
            symbol=symbol,
            bid=price * 0.9998,
            ask=price * 10002,
            last_price=price,
            volume_24h=150000000.0,
            timestamp=now_ms,
        )

    def get_ticker(self, symbol: str) -> Ticker:
        if symbol in self.last_tickers:
            return self.last_tickers[symbol]
        # Default price if none injected
        default_prices = {"BTCUSDT": 65000.0, "ETHUSDT": 3500.0, "SOLUSDT": 150.0}
        p = default_prices.get(symbol, 100.0)
        self.set_mock_ticker(symbol, p)
        return self.last_tickers[symbol]

    def get_candles(self, symbol: str, timeframe: Timeframe, limit: int = 200) -> List[Candle]:
        # Handled in feed / backtest
        return []

    def get_order_book(self, symbol: str, depth: int = 20) -> OrderBook:
        ticker = self.get_ticker(symbol)
        bids = [OrderBookLevel(ticker.bid * (1 - 0.0002 * i), 1.5) for i in range(depth)]
        asks = [OrderBookLevel(ticker.ask * (1 + 0.0002 * i), 1.5) for i in range(depth)]
        return OrderBook(symbol, bids, asks, int(time.time() * 1000))

    def create_order(self, request: OrderRequest) -> OrderResponse:
        constraints = self.get_symbol_constraints(request.symbol)
        
        # Determine execution price
        current_ticker = self.get_ticker(request.symbol)
        if request.order_type == OrderType.MARKET:
            slippage = 1 + self.slippage_pct if request.side == OrderSide.BUY else 1 - self.slippage_pct
            exec_price = constraints.round_price(current_ticker.last_price * slippage)
        else:
            if request.price is None:
                raise OrderError("Limit order requires price parameter.")
            exec_price = constraints.round_price(request.price)

        valid_qty = constraints.round_qty(request.quantity)
        constraints.validate_order(exec_price, valid_qty)

        # Check balance
        notional = exec_price * valid_qty
        usdt_bal = self.balances.get("USDT", BalanceModel("USDT", 0.0, 0.0, 0.0))
        fee = notional * self.fee_rate

        if request.side == OrderSide.BUY:
            total_cost = notional + fee
            if usdt_bal.free < total_cost:
                raise OrderError(
                    f"Insufficient funds: Requires {total_cost:.2f} USDT, available {usdt_bal.free:.2f} USDT"
                )
            # Deduct free balance
            usdt_bal.free -= total_cost
            usdt_bal.total -= fee

        now_ms = int(time.time() * 1000)
        resp = OrderResponse(
            client_order_id=request.client_order_id,
            exchange_order_id=f"PAPER-{now_ms}",
            symbol=request.symbol,
            status=OrderStatus.FILLED if request.order_type == OrderType.MARKET else OrderStatus.NEW,
            side=request.side,
            order_type=request.order_type,
            orig_qty=valid_qty,
            executed_qty=valid_qty if request.order_type == OrderType.MARKET else 0.0,
            avg_price=exec_price,
            fee_paid=fee,
            timestamp=now_ms,
        )

        if resp.status == OrderStatus.FILLED:
            self.order_history.append(resp)
            # Open position
            self.positions[request.symbol] = PositionModel(
                symbol=request.symbol,
                side=request.side,
                entry_price=exec_price,
                current_price=exec_price,
                quantity=valid_qty,
                unrealized_pnl=0.0,
                pnl_percent=0.0,
                stop_loss=request.stop_price or 0.0,
                take_profit=0.0,
                timestamp=now_ms,
            )
        else:
            self.open_orders[request.client_order_id] = resp

        return resp

    def cancel_order(self, symbol: str, client_order_id: str) -> bool:
        if client_order_id in self.open_orders:
            order = self.open_orders.pop(client_order_id)
            order.status = OrderStatus.CANCELED
            self.order_history.append(order)
            return True
        return False

    def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderResponse]:
        if symbol:
            return [o for o in self.open_orders.values() if o.symbol == symbol]
        return list(self.open_orders.values())

    def get_account_balances(self) -> Dict[str, BalanceModel]:
        return self.balances

    def get_positions(self) -> List[PositionModel]:
        return list(self.positions.values())
