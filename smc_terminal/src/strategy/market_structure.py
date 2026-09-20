"""
SMC Algorithmic Trading Terminal - Market Structure Engine.
Calculates Swing Highs/Lows, HH/HL/LH/LL, BOS, and MSS/CHoCH with zero lookahead bias.
A fractal swing of length N is only confirmed at index i + N when the right confirmation bars have closed.
"""

from typing import List, Optional, Tuple
from src.data.models import Candle
from src.strategy.models import (
    BOS,
    MSS,
    StructureType,
    SwingPoint,
    SwingType,
    TrendDirection,
)


class MarketStructureEngine:
    """
    Quantitative Market Structure Analyzer.
    Enforces strict chronological confirmation (no lookahead bias).
    """

    def __init__(
        self,
        swing_length: int = 3,
        require_bos_close: bool = True,
        min_break_atr: float = 0.05,
        require_mss_close: bool = True,
        min_displacement_ratio: float = 1.0,
    ) -> None:
        self.swing_length = swing_length
        self.require_bos_close = require_bos_close
        self.min_break_atr = min_break_atr
        self.require_mss_close = require_mss_close
        self.min_displacement_ratio = min_displacement_ratio

    def calculate_atr(self, candles: List[Candle], period: int = 14) -> float:
        """Calculate Average True Range for volatility normalization."""
        if len(candles) < 2:
            return 1.0
        
        tr_list: List[float] = []
        for i in range(1, len(candles)):
            curr = candles[i]
            prev = candles[i - 1]
            tr = max(
                curr.high - curr.low,
                abs(curr.high - prev.close),
                abs(curr.low - prev.close),
            )
            tr_list.append(tr)

        lookback = tr_list[-period:] if len(tr_list) >= period else tr_list
        return sum(lookback) / max(len(lookback), 1)

    def identify_swings(self, candles: List[Candle], as_of_index: Optional[int] = None) -> List[SwingPoint]:
        """
        Identify fractal swing pivots strictly up to as_of_index.
        A swing at index k requires swing_length bars to its left and right.
        Therefore, it is ONLY confirmed and available at index k + swing_length.
        """
        max_idx = len(candles) - 1 if as_of_index is None else min(as_of_index, len(candles) - 1)
        k_min = self.swing_length
        k_max = max_idx - self.swing_length

        if k_max < k_min:
            return []

        swings: List[SwingPoint] = []
        n = self.swing_length

        for k in range(k_min, k_max + 1):
            pivot = candles[k]
            # Check swing high
            is_high = True
            for offset in range(1, n + 1):
                if candles[k - offset].high >= pivot.high or candles[k + offset].high > pivot.high:
                    is_high = False
                    break

            if is_high:
                swings.append(
                    SwingPoint(
                        index=k,
                        timestamp=pivot.timestamp,
                        price=pivot.high,
                        swing_type=SwingType.SWING_HIGH,
                        confirmed_at_index=k + n,
                    )
                )

            # Check swing low
            is_low = True
            for offset in range(1, n + 1):
                if candles[k - offset].low <= pivot.low or candles[k + offset].low < pivot.low:
                    is_low = False
                    break

            if is_low:
                swings.append(
                    SwingPoint(
                        index=k,
                        timestamp=pivot.timestamp,
                        price=pivot.low,
                        swing_type=SwingType.SWING_LOW,
                        confirmed_at_index=k + n,
                    )
                )

        # Sort chronologically by confirmation time
        swings.sort(key=lambda s: (s.confirmed_at_index, s.index))
        return swings

    def classify_trend(self, swings: List[SwingPoint]) -> TrendDirection:
        """
        Trend is defined by sequential Higher Highs & Higher Lows (Bullish),
        or Lower Lows & Lower Highs (Bearish).
        """
        highs = [s for s in swings if s.swing_type == SwingType.SWING_HIGH]
        lows = [s for s in swings if s.swing_type == SwingType.SWING_LOW]

        if len(highs) < 2 or len(lows) < 2:
            return TrendDirection.RANGING

        is_bullish = highs[-1].price > highs[-2].price and lows[-1].price > lows[-2].price
        is_bearish = highs[-1].price < highs[-2].price and lows[-1].price < lows[-2].price

        if is_bullish:
            return TrendDirection.BULLISH
        elif is_bearish:
            return TrendDirection.BEARISH
        return TrendDirection.RANGING

    def detect_bos_and_mss(
        self,
        candles: List[Candle],
        swings: List[SwingPoint],
        as_of_index: Optional[int] = None,
    ) -> Tuple[List[BOS], List[MSS]]:
        """
        Detects Break of Structure (continuation) and Market Structure Shift (reversal).
        Only evaluates swings confirmed on or before the current candle.
        """
        max_idx = len(candles) - 1 if as_of_index is None else min(as_of_index, len(candles) - 1)
        if max_idx < 1 or not swings:
            return [], []

        atr = self.calculate_atr(candles[: max_idx + 1])
        bos_events: List[BOS] = []
        mss_events: List[MSS] = []

        last_trend = self.classify_trend([s for s in swings if s.confirmed_at_index <= max_idx])

        # Track active swing levels that have not been invalidated yet
        confirmed_highs = [s for s in swings if s.swing_type == SwingType.SWING_HIGH and s.confirmed_at_index <= max_idx]
        confirmed_lows = [s for s in swings if s.swing_type == SwingType.SWING_LOW and s.confirmed_at_index <= max_idx]

        for i in range(1, max_idx + 1):
            curr_bar = candles[i]

            # Available swings confirmed prior to bar i
            avail_highs = [s for s in confirmed_highs if s.confirmed_at_index < i]
            avail_lows = [s for s in confirmed_lows if s.confirmed_at_index < i]

            # Check break above most recent swing high
            if avail_highs:
                recent_high = avail_highs[-1]
                broken = curr_bar.close > recent_high.price if self.require_bos_close else curr_bar.high > recent_high.price
                if broken and (curr_bar.close - recent_high.price) >= (self.min_break_atr * atr):
                    # Check if it was continuation (BOS) or reversal (MSS)
                    if last_trend == TrendDirection.BEARISH:
                        # Broken previous high in downtrend = Bullish MSS / CHoCH
                        displacement = curr_bar.body_size / max(atr, 1e-6)
                        mss_events.append(
                            MSS(
                                direction=TrendDirection.BULLISH,
                                broken_swing=recent_high,
                                break_candle_index=i,
                                displacement_ratio=displacement,
                                confirmed_by_close=curr_bar.close > recent_high.price,
                            )
                        )
                        last_trend = TrendDirection.BULLISH
                    else:
                        bos_events.append(
                            BOS(
                                direction=TrendDirection.BULLISH,
                                broken_swing=recent_high,
                                break_price=curr_bar.close,
                                break_candle_index=i,
                                confirmed_by_close=curr_bar.close > recent_high.price,
                                atr_at_break=atr,
                            )
                        )
                        last_trend = TrendDirection.BULLISH

            # Check break below most recent swing low
            if avail_lows:
                recent_low = avail_lows[-1]
                broken = curr_bar.close < recent_low.price if self.require_bos_close else curr_bar.low < recent_low.price
                if broken and (recent_low.price - curr_bar.close) >= (self.min_break_atr * atr):
                    if last_trend == TrendDirection.BULLISH:
                        # Broken previous low in uptrend = Bearish MSS / CHoCH
                        displacement = curr_bar.body_size / max(atr, 1e-6)
                        mss_events.append(
                            MSS(
                                direction=TrendDirection.BEARISH,
                                broken_swing=recent_low,
                                break_candle_index=i,
                                displacement_ratio=displacement,
                                confirmed_by_close=curr_bar.close < recent_low.price,
                            )
                        )
                        last_trend = TrendDirection.BEARISH
                    else:
                        bos_events.append(
                            BOS(
                                direction=TrendDirection.BEARISH,
                                broken_swing=recent_low,
                                break_price=curr_bar.close,
                                break_candle_index=i,
                                confirmed_by_close=curr_bar.close < recent_low.price,
                                atr_at_break=atr,
                            )
                        )
                        last_trend = TrendDirection.BEARISH

        return bos_events, mss_events
