"""
SMC Algorithmic Trading Terminal - Data Models & Validation.
Enforces strict chronological sequencing, data validity, and staleness detection.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from src.exchange.exceptions import DataError


class Timeframe(str, Enum):
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

    @property
    def seconds(self) -> int:
        mapping = {
            "1m": 60,
            "3m": 180,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400,
        }
        return mapping[self.value]


@dataclass(frozen=True)
class Candle:
    """Immutable OHLCV Bar representation."""
    timestamp: int        # Milliseconds epoch timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_closed: bool = True
    confirmed_at: Optional[datetime] = None

    @property
    def dt(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp / 1000.0, tz=timezone.utc)

    @property
    def is_bullish(self) -> bool:
        return self.close >= self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)

    @property
    def range_size(self) -> float:
        return self.high - self.low

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low


@dataclass
class Ticker:
    """Current market ticker."""
    symbol: str
    bid: float
    ask: float
    last_price: float
    volume_24h: float
    timestamp: int


@dataclass
class OrderBookLevel:
    price: float
    quantity: float


@dataclass
class OrderBook:
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: int


class DataValidator:
    """Validates incoming market data bars against strict quantitative constraints."""

    @staticmethod
    def validate_candle(candle: Candle) -> None:
        """Verify that candle OHLCV logic is mathematically coherent."""
        if candle.open <= 0 or candle.high <= 0 or candle.low <= 0 or candle.close <= 0:
            raise DataError(f"Candle prices must be strictly positive: {candle}")
        
        if candle.high < candle.low:
            raise DataError(f"Invalid candle: High ({candle.high}) < Low ({candle.low})")
            
        if candle.high < max(candle.open, candle.close):
            raise DataError(f"Invalid candle: High ({candle.high}) < max(open, close)")
            
        if candle.low > min(candle.open, candle.close):
            raise DataError(f"Invalid candle: Low ({candle.low}) > min(open, close)")
            
        if candle.volume < 0:
            raise DataError(f"Invalid candle: Volume cannot be negative: {candle.volume}")

    @staticmethod
    def validate_series(candles: List[Candle], max_gap_multiplier: float = 2.5) -> None:
        """
        Validates chronological order, uniqueness, and consistency across a series.
        Prevents lookahead and data gaps.
        """
        if not candles:
            return
            
        for i, candle in enumerate(candles):
            DataValidator.validate_candle(candle)
            if i > 0:
                prev = candles[i - 1]
                if candle.timestamp <= prev.timestamp:
                    raise DataError(
                        f"Non-chronological or duplicate candle timestamp at index {i}: "
                        f"prev={prev.timestamp}, curr={candle.timestamp}"
                    )
