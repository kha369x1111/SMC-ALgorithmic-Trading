"""
SMC Algorithmic Trading Terminal - Abstract Exchange Adapter Interface.
Enables pluggable exchange integrations (Binance, Bybit, OKX, Paper) without strategy changes.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from src.data.models import Candle, OrderBook, Ticker, Timeframe
from src.exchange.models import (
    BalanceModel,
    OrderRequest,
    OrderResponse,
    PositionModel,
    SymbolConstraints,
)


class ExchangeAdapter(ABC):
    """Abstract Interface contract for all execution and market data adapters."""

    @abstractmethod
    def get_name(self) -> str:
        """Name of the exchange adapter (e.g., 'binance_spot', 'paper')."""
        pass

    @abstractmethod
    def connect(self) -> bool:
        """Establish session or API connection."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Tear down connection safely."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Verify active connection state."""
        pass

    @abstractmethod
    def get_symbol_constraints(self, symbol: str) -> SymbolConstraints:
        """Retrieve min quantity, tick size, step size, and precision rules."""
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Ticker:
        """Fetch latest price ticker."""
        pass

    @abstractmethod
    def get_candles(self, symbol: str, timeframe: Timeframe, limit: int = 200) -> List[Candle]:
        """Fetch historical completed OHLCV bars."""
        pass

    @abstractmethod
    def get_order_book(self, symbol: str, depth: int = 20) -> OrderBook:
        """Fetch order book depth."""
        pass

    @abstractmethod
    def create_order(self, request: OrderRequest) -> OrderResponse:
        """Submit a validated order with idempotent client_order_id."""
        pass

    @abstractmethod
    def cancel_order(self, symbol: str, client_order_id: str) -> bool:
        """Cancel an open order."""
        pass

    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderResponse]:
        """Fetch all working orders."""
        pass

    @abstractmethod
    def get_account_balances(self) -> Dict[str, BalanceModel]:
        """Fetch asset balances (USDT, BTC, ETH, etc.)."""
        pass

    @abstractmethod
    def get_positions(self) -> List[PositionModel]:
        """Fetch active positions."""
        pass
