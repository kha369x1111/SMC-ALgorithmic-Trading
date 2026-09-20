"""
SMC Algorithmic Trading Terminal - Exchange Data Models & Symbol Constraints.
Enforces precision, tick size, step size, min notional, and idempotency.
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Optional
from src.exchange.exceptions import OrderError


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"


class OrderStatus(str, Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class SymbolConstraints:
    """Binance Spot / Exchange Trading Rules for specific pair."""
    symbol: str
    tick_size: float
    step_size: float
    min_qty: float
    max_qty: float
    min_notional: float
    price_precision: int
    qty_precision: int
    is_trading_active: bool = True

    def round_price(self, price: float) -> float:
        """Round price down to nearest valid tick size."""
        if self.tick_size <= 0:
            return round(price, self.price_precision)
        precision = max(0, int(round(-math.log10(self.tick_size))))
        ticks = math.floor(price / self.tick_size + 1e-8)
        return round(ticks * self.tick_size, precision)

    def round_qty(self, qty: float) -> float:
        """Round quantity down to nearest valid step size."""
        if self.step_size <= 0:
            return round(qty, self.qty_precision)
        precision = max(0, int(round(-math.log10(self.step_size))))
        steps = math.floor(qty / self.step_size + 1e-8)
        return round(steps * self.step_size, precision)

    def validate_order(self, price: float, qty: float) -> None:
        """Strict pre-flight check before order dispatch."""
        if not self.is_trading_active:
            raise OrderError(f"Trading halted for symbol {self.symbol}")

        if qty < self.min_qty:
            raise OrderError(
                f"Quantity {qty} is below min quantity {self.min_qty} for {self.symbol}"
            )
        if qty > self.max_qty:
            raise OrderError(
                f"Quantity {qty} exceeds max quantity {self.max_qty} for {self.symbol}"
            )

        notional = price * qty
        if notional < self.min_notional:
            raise OrderError(
                f"Order notional value {notional:.2f} USDT is below minimum {self.min_notional} USDT"
            )


@dataclass
class OrderRequest:
    client_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    reduce_only: bool = False


@dataclass
class OrderResponse:
    client_order_id: str
    exchange_order_id: str
    symbol: str
    status: OrderStatus
    side: OrderSide
    order_type: OrderType
    orig_qty: float
    executed_qty: float
    avg_price: float
    fee_paid: float
    timestamp: int


@dataclass
class PositionModel:
    symbol: str
    side: OrderSide
    entry_price: float
    current_price: float
    quantity: float
    unrealized_pnl: float
    pnl_percent: float
    stop_loss: float
    take_profit: float
    timestamp: int


@dataclass
class BalanceModel:
    asset: str
    free: float
    locked: float
    total: float
