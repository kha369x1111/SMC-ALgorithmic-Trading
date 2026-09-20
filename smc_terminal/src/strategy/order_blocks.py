"""
SMC Algorithmic Trading Terminal - Order Block (OB) Engine.
Identifies institutional footprints: last opposing candle before aggressive displacement and BOS/MSS.
Computes comprehensive quantitative OB Score (0-100).
"""

from typing import List, Optional
from src.data.models import Candle
from src.strategy.models import BOS, MSS, OrderBlockZone, TrendDirection


class OrderBlockEngine:
    """Quantitative Order Block Detector and Scorer."""

    def __init__(
        self,
        min_displacement_atr_ratio: float = 1.0,
        max_invalidation_breach_pct: float = 0.05,
    ) -> None:
        self.min_displacement_atr_ratio = min_displacement_atr_ratio
        self.max_invalidation_breach_pct = max_invalidation_breach_pct

    def calculate_atr(self, candles: List[Candle], period: int = 14) -> float:
        if len(candles) < 2:
            return 1.0
        tr_list = [
            max(
                candles[i].high - candles[i].low,
                abs(candles[i].high - candles[i - 1].close),
                abs(candles[i].low - candles[i - 1].close),
            )
            for i in range(1, len(candles))
        ]
        lookback = tr_list[-period:] if len(tr_list) >= period else tr_list
        return sum(lookback) / max(len(lookback), 1)

    def detect_order_blocks(
        self,
        candles: List[Candle],
        bos_events: List[BOS],
        mss_events: List[MSS],
        timeframe: str = "15m",
    ) -> List[OrderBlockZone]:
        """
        Scans for valid institutional order blocks.
        A Bullish OB is the last bearish down-candle preceding strong displacement and an upside BOS/MSS.
        A Bearish OB is the last bullish up-candle preceding strong displacement and a downside BOS/MSS.
        """
        if len(candles) < 4:
            return []

        atr = self.calculate_atr(candles)
        order_blocks: List[OrderBlockZone] = []
        break_indices = [b.break_candle_index for b in bos_events] + [m.break_candle_index for m in mss_events]

        for i in range(1, len(candles) - 1):
            curr_bar = candles[i]
            next_bar = candles[i + 1]

            # 1. Bullish Order Block candidate:
            # Bearish candle (curr_bar) followed by aggressive bullish expansion (next_bar)
            if curr_bar.is_bearish and next_bar.is_bullish:
                displacement = next_bar.body_size / max(atr, 1e-6)
                if displacement >= self.min_displacement_atr_ratio:
                    # Check structural relevance: was there a BOS/MSS nearby?
                    has_structural_break = any(abs(idx - i) <= 6 for idx in break_indices)
                    
                    # Compute OB Score (0 to 100)
                    score = 40.0  # Base for displacement
                    score += min(displacement * 20.0, 30.0)
                    if has_structural_break:
                        score += 30.0

                    order_blocks.append(
                        OrderBlockZone(
                            direction=TrendDirection.BULLISH,
                            timeframe=timeframe,
                            top=curr_bar.high,
                            bottom=curr_bar.low,
                            candle_index=i,
                            strength_score=min(score, 100.0),
                            freshness=True,
                            touches=0,
                            mitigated=False,
                            invalidated=False,
                            associated_displacement=displacement,
                        )
                    )

            # 2. Bearish Order Block candidate:
            # Bullish candle (curr_bar) followed by aggressive bearish expansion (next_bar)
            elif curr_bar.is_bullish and next_bar.is_bearish:
                displacement = next_bar.body_size / max(atr, 1e-6)
                if displacement >= self.min_displacement_atr_ratio:
                    has_structural_break = any(abs(idx - i) <= 6 for idx in break_indices)
                    score = 40.0
                    score += min(displacement * 20.0, 30.0)
                    if has_structural_break:
                        score += 30.0

                    order_blocks.append(
                        OrderBlockZone(
                            direction=TrendDirection.BEARISH,
                            timeframe=timeframe,
                            top=curr_bar.high,
                            bottom=curr_bar.low,
                            candle_index=i,
                            strength_score=min(score, 100.0),
                            freshness=True,
                            touches=0,
                            mitigated=False,
                            invalidated=False,
                            associated_displacement=displacement,
                        )
                    )

        # Track touches and invalidation over subsequent bars
        for ob in order_blocks:
            for k in range(ob.candle_index + 2, len(candles)):
                bar = candles[k]
                if ob.direction == TrendDirection.BULLISH:
                    # Invalidation: candle closes below OB bottom
                    if bar.close < ob.bottom:
                        ob.invalidated = True
                        ob.freshness = False
                        break
                    # Mitigation / Touch: price trades inside OB range
                    if bar.low <= ob.top and bar.high >= ob.bottom:
                        ob.touches += 1
                        ob.freshness = False
                        ob.mitigated = True
                else:
                    # Bearish OB: candle closes above OB top
                    if bar.close > ob.top:
                        ob.invalidated = True
                        ob.freshness = False
                        break
                    if bar.high >= ob.bottom and bar.low <= ob.top:
                        ob.touches += 1
                        ob.freshness = False
                        ob.mitigated = True

        return [ob for ob in order_blocks if not ob.invalidated]
