"""
SMC Algorithmic Trading Terminal - Liquidity Engine.
Discovers BSL, SSL, Equal Highs (EQH), Equal Lows (EQL), Session Extremes, and validates Sweeps.
A valid sweep requires price to penetrate the pool and quickly reclaim back inside within N bars.
"""

from typing import List, Optional
from src.data.models import Candle
from src.strategy.models import (
    LiquidityPool,
    LiquiditySweepEvent,
    LiquidityType,
    SwingPoint,
    SwingType,
)


class LiquidityEngine:
    """Quantitative Liquidity Pool and Sweep Detector."""

    def __init__(
        self,
        equal_tolerance_percent: float = 0.08,  # 0.08% tolerance for EQH/EQL
        require_reclaim: bool = True,
        max_confirmation_bars: int = 5,
    ) -> None:
        self.equal_tolerance_pct = equal_tolerance_percent
        self.require_reclaim = require_reclaim
        self.max_confirmation_bars = max_confirmation_bars

    def build_liquidity_pools(
        self,
        candles: List[Candle],
        swings: List[SwingPoint],
        timeframe: str = "15m",
    ) -> List[LiquidityPool]:
        """
        Extracts BSL, SSL, and clusters equal highs/lows into reinforced liquidity pools.
        """
        pools: List[LiquidityPool] = []
        if not swings:
            return pools

        highs = [s for s in swings if s.swing_type == SwingType.SWING_HIGH]
        lows = [s for s in swings if s.swing_type == SwingType.SWING_LOW]

        # 1. Detect Equal Highs (EQH)
        visited_highs = set()
        for i in range(len(highs)):
            if i in visited_highs:
                continue
            h1 = highs[i]
            eq_cluster = [h1]
            for j in range(i + 1, len(highs)):
                h2 = highs[j]
                pct_diff = abs(h1.price - h2.price) / h1.price * 100.0
                if pct_diff <= self.equal_tolerance_pct:
                    eq_cluster.append(h2)
                    visited_highs.add(j)

            if len(eq_cluster) >= 2:
                avg_price = sum(h.price for h in eq_cluster) / len(eq_cluster)
                pools.append(
                    LiquidityPool(
                        price=avg_price,
                        timeframe=timeframe,
                        pool_type=LiquidityType.EQH,
                        strength=float(len(eq_cluster)),
                        created_at_index=eq_cluster[-1].index,
                        touches=len(eq_cluster),
                    )
                )
            else:
                # Standalone BSL pool
                pools.append(
                    LiquidityPool(
                        price=h1.price,
                        timeframe=timeframe,
                        pool_type=LiquidityType.BSL,
                        strength=1.0,
                        created_at_index=h1.index,
                        touches=1,
                    )
                )

        # 2. Detect Equal Lows (EQL)
        visited_lows = set()
        for i in range(len(lows)):
            if i in visited_lows:
                continue
            l1 = lows[i]
            eq_cluster = [l1]
            for j in range(i + 1, len(lows)):
                l2 = lows[j]
                pct_diff = abs(l1.price - l2.price) / l1.price * 100.0
                if pct_diff <= self.equal_tolerance_pct:
                    eq_cluster.append(l2)
                    visited_lows.add(j)

            if len(eq_cluster) >= 2:
                avg_price = sum(l.price for l in eq_cluster) / len(eq_cluster)
                pools.append(
                    LiquidityPool(
                        price=avg_price,
                        timeframe=timeframe,
                        pool_type=LiquidityType.EQL,
                        strength=float(len(eq_cluster)),
                        created_at_index=eq_cluster[-1].index,
                        touches=len(eq_cluster),
                    )
                )
            else:
                # Standalone SSL pool
                pools.append(
                    LiquidityPool(
                        price=l1.price,
                        timeframe=timeframe,
                        pool_type=LiquidityType.SSL,
                        strength=1.0,
                        created_at_index=l1.index,
                        touches=1,
                    )
                )

        return pools

    def detect_sweeps(
        self,
        candles: List[Candle],
        pools: List[LiquidityPool],
    ) -> List[LiquiditySweepEvent]:
        """
        Validates whether resting liquidity pools have been swept and reclaimed.
        A BSL/EQH sweep occurs when price penetrates pool.price with its high,
        then closes back below the level within max_confirmation_bars.
        An SSL/EQL sweep occurs when price pierces below pool.price with low,
        then closes back above the level within max_confirmation_bars.
        """
        sweeps: List[LiquiditySweepEvent] = []
        if len(candles) < 2:
            return sweeps

        for pool in pools:
            if pool.swept:
                continue

            # Look for breach after pool formation
            start_idx = pool.created_at_index + 1
            if start_idx >= len(candles):
                continue

            is_high_pool = pool.pool_type in (LiquidityType.BSL, LiquidityType.EQH, LiquidityType.PDH, LiquidityType.PWH, LiquidityType.ASIAN_HIGH)

            for i in range(start_idx, len(candles)):
                bar = candles[i]

                if is_high_pool:
                    # Penetration above high
                    if bar.high > pool.price:
                        # Check reclaim within max_confirmation_bars
                        reclaimed = False
                        bars_checked = 0
                        end_check = min(len(candles), i + self.max_confirmation_bars + 1)
                        for k in range(i, end_check):
                            bars_checked += 1
                            if candles[k].close < pool.price:
                                reclaimed = True
                                break

                        if not self.require_reclaim or reclaimed:
                            pool.swept = True
                            pool.reclaimed = reclaimed
                            pool.sweep_time = bar.timestamp
                            sweeps.append(
                                LiquiditySweepEvent(
                                    pool=pool,
                                    sweep_price=bar.high,
                                    sweep_candle_index=i,
                                    reclaimed=reclaimed,
                                    structure_shifted=False,  # Linked by strategy engine
                                    confirmation_bars_used=bars_checked,
                                )
                            )
                        break  # Stop checking this pool once pierced
                else:
                    # Penetration below low (SSL / EQL)
                    if bar.low < pool.price:
                        reclaimed = False
                        bars_checked = 0
                        end_check = min(len(candles), i + self.max_confirmation_bars + 1)
                        for k in range(i, end_check):
                            bars_checked += 1
                            if candles[k].close > pool.price:
                                reclaimed = True
                                break

                        if not self.require_reclaim or reclaimed:
                            pool.swept = True
                            pool.reclaimed = reclaimed
                            pool.sweep_time = bar.timestamp
                            sweeps.append(
                                LiquiditySweepEvent(
                                    pool=pool,
                                    sweep_price=bar.low,
                                    sweep_candle_index=i,
                                    reclaimed=reclaimed,
                                    structure_shifted=False,
                                    confirmation_bars_used=bars_checked,
                                )
                            )
                        break

        return sweeps
