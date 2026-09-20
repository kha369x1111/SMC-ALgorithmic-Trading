"""
SMC Algorithmic Trading Terminal - Fair Value Gap (FVG) Engine.
Detects 3-bar imbalances, calculates 50% Consequent Encroachment (CE), and tracks mitigation.
"""

from typing import List, Optional
from src.data.models import Candle
from src.strategy.models import FVGDirection, FVGZone


class FVGEngine:
    """Quantitative Fair Value Gap (Imbalance) Detector."""

    def __init__(
        self,
        min_atr_ratio: float = 0.15,
        entry_level: float = 0.50,
        invalidate_when_filled: bool = True,
    ) -> None:
        self.min_atr_ratio = min_atr_ratio
        self.entry_level = entry_level
        self.invalidate_when_filled = invalidate_when_filled

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

    def detect_fvgs(
        self,
        candles: List[Candle],
        timeframe: str = "5m",
        as_of_index: Optional[int] = None,
    ) -> List[FVGZone]:
        """
        Scan a series of bars for 3-bar imbalances.
        Bar 1 = candle[i-2]
        Bar 2 = candle[i-1] (Displacement bar)
        Bar 3 = candle[i] (Confirmation bar)
        """
        max_idx = len(candles) - 1 if as_of_index is None else min(as_of_index, len(candles) - 1)
        if max_idx < 2:
            return []

        atr = self.calculate_atr(candles[: max_idx + 1])
        fvgs: List[FVGZone] = []

        for i in range(2, max_idx + 1):
            first = candles[i - 2]
            middle = candles[i - 1]
            third = candles[i]

            # 1. Bullish FVG: Low of third bar > High of first bar
            if third.low > first.high:
                gap_size = third.low - first.high
                atr_ratio = gap_size / max(atr, 1e-6)
                if atr_ratio >= self.min_atr_ratio:
                    fvgs.append(
                        FVGZone(
                            direction=FVGDirection.BULLISH,
                            top=third.low,
                            bottom=first.high,
                            timeframe=timeframe,
                            candle_index=i - 1,
                            atr_ratio=atr_ratio,
                            mitigated=False,
                        )
                    )

            # 2. Bearish FVG: High of third bar < Low of first bar
            elif third.high < first.low:
                gap_size = first.low - third.high
                atr_ratio = gap_size / max(atr, 1e-6)
                if atr_ratio >= self.min_atr_ratio:
                    fvgs.append(
                        FVGZone(
                            direction=FVGDirection.BEARISH,
                            top=first.low,
                            bottom=third.high,
                            timeframe=timeframe,
                            candle_index=i - 1,
                            atr_ratio=atr_ratio,
                            mitigated=False,
                        )
                    )

        # Update mitigation status up to as_of_index
        for fvg in fvgs:
            start_check = fvg.candle_index + 2
            if start_check > max_idx:
                continue

            for k in range(start_check, max_idx + 1):
                bar = candles[k]
                if fvg.direction == FVGDirection.BULLISH:
                    # Mitigated if price dips into or fills the gap
                    if bar.low <= fvg.midpoint:
                        fvg.mitigated = True
                        fvg.mitigated_at_index = k
                        break
                else:
                    # Bearish mitigated if price pushes up into or fills the gap
                    if bar.high >= fvg.midpoint:
                        fvg.mitigated = True
                        fvg.mitigated_at_index = k
                        break

        if self.invalidate_when_filled:
            return [f for f in fvgs if not f.mitigated]
        return fvgs
