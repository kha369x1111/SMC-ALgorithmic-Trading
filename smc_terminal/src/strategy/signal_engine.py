"""
SMC Algorithmic Trading Terminal - Multi-Timeframe Signal Engine Orchestrator.
Synthesizes Market Structure (HTF/LTF), Liquidity Sweeps, FVGs (50% CE),
Order Blocks, and Premium/Discount Valuation into an institutional 0-10 composite score.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Dict, List, Optional, Tuple

from src.data.models import Candle
from src.strategy.fvg import FVGEngine
from src.strategy.liquidity import LiquidityEngine
from src.strategy.market_structure import MarketStructureEngine
from src.strategy.models import (
    FVGDirection,
    FVGZone,
    LiquidityPool,
    LiquiditySweepEvent,
    LiquidityType,
    MSS,
    OrderBlockZone,
    PDZone,
    SetupLifecycleState,
    Signal,
    SignalDirection,
    TrendDirection,
)
from src.strategy.order_blocks import OrderBlockEngine
from src.strategy.premium_discount import PremiumDiscountEngine

logger = logging.getLogger("SMC_TERMINAL.SIGNAL_ENGINE")


class SignalEngine:
    """
    Composite Smart Money Concepts (SMC) Signal Generation Engine.
    Enforces multi-timeframe alignment, 8.0+ score gating, and 2.0R floor.
    """

    def __init__(
        self,
        score_threshold: float = 8.0,
        min_reward_risk: float = 2.0,
        allowed_sessions: Optional[List[str]] = None,
    ) -> None:
        self.score_threshold = score_threshold
        self.min_reward_risk = min_reward_risk
        self.allowed_sessions = allowed_sessions or ["london_killzone", "newyork_killzone", "asian_killzone"]

        # Strategy sub-engines
        self.structure_engine = MarketStructureEngine(swing_length=3)
        self.liquidity_engine = LiquidityEngine(equal_tolerance_percent=0.08)
        self.fvg_engine = FVGEngine(min_atr_ratio=0.15)
        self.ob_engine = OrderBlockEngine(min_displacement_atr_ratio=1.0)
        self.pd_engine = PremiumDiscountEngine()

    def check_session(self, timestamp_ms: int) -> Tuple[bool, str]:
        """
        Evaluate if timestamp falls within an ICT Killzone:
        - Asian Session: 00:00 - 06:00 UTC
        - London Killzone: 07:00 - 10:00 UTC
        - New York Killzone: 12:00 - 15:00 UTC
        """
        dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
        hour = dt.hour

        if 0 <= hour < 6:
            session_name = "asian_killzone"
        elif 7 <= hour < 10:
            session_name = "london_killzone"
        elif 12 <= hour < 15:
            session_name = "newyork_killzone"
        else:
            session_name = "off_session"

        is_allowed = session_name in self.allowed_sessions
        return is_allowed, session_name

    def evaluate_setup(
        self,
        symbol: str,
        candles_4h: List[Candle],
        candles_15m: List[Candle],
        candles_5m: List[Candle],
    ) -> Optional[Signal]:
        """
        Execute full Multi-Timeframe (4H -> 15M -> 5M) SMC analysis.
        Returns a qualified Signal if score >= threshold and RR >= 2.0R,
        or an explainable rejected signal if sub-criteria fail.
        """
        if len(candles_4h) < 10 or len(candles_15m) < 15 or len(candles_5m) < 15:
            logger.warning("Insufficient candle count for symbol %s", symbol)
            return None

        current_candle = candles_5m[-1]
        current_price = current_candle.close
        timestamp_ms = current_candle.timestamp

        reasons: List[str] = []
        score_breakdown: Dict[str, float] = {
            "structure": 0.0,
            "liquidity": 0.0,
            "fvg": 0.0,
            "order_block": 0.0,
            "premium_discount": 0.0,
        }

        # 1. Higher Timeframe (4H) Trend Bias
        swings_4h = self.structure_engine.identify_swings(candles_4h)
        htf_bias = self.structure_engine.classify_trend(swings_4h)
        reasons.append(f"4H HTF Bias: {htf_bias.value}")

        # 2. Intermediate Structure (15M) Swings, BOS, and MSS
        swings_15m = self.structure_engine.identify_swings(candles_15m)
        bos_list, mss_list = self.structure_engine.detect_bos_and_mss(candles_15m, swings_15m)
        recent_mss: Optional[MSS] = mss_list[-1] if mss_list else None

        # 3. Liquidity Engine (15M) Pools and Sweeps
        pools_15m = self.liquidity_engine.build_liquidity_pools(candles_15m, swings_15m)
        sweeps = self.liquidity_engine.detect_sweeps(candles_15m, pools_15m)

        # Determine Primary Direction Intent
        # Priority: HTF bias alignment + confirmed MSS or high-conviction liquidity sweep
        if htf_bias == TrendDirection.BULLISH:
            signal_dir = SignalDirection.LONG
        elif htf_bias == TrendDirection.BEARISH:
            signal_dir = SignalDirection.SHORT
        elif recent_mss:
            signal_dir = SignalDirection.LONG if recent_mss.direction == TrendDirection.BULLISH else SignalDirection.SHORT
        elif sweeps:
            latest_reclaimed = next((s for s in reversed(sweeps) if s.reclaimed), sweeps[-1])
            if latest_reclaimed.pool.pool_type in (LiquidityType.SSL, LiquidityType.EQL, LiquidityType.ASIAN_LOW, LiquidityType.PDL):
                signal_dir = SignalDirection.LONG
            else:
                signal_dir = SignalDirection.SHORT
        else:
            signal_dir = SignalDirection.LONG if candles_15m[-1].close >= candles_15m[0].close else SignalDirection.SHORT

        # Select matching sweep aligned with signal direction if available
        reclaimed_sweeps = [s for s in sweeps if s.reclaimed]
        matching_sweep: Optional[LiquiditySweepEvent] = None
        if signal_dir == SignalDirection.LONG:
            matching_sweep = next((s for s in reversed(reclaimed_sweeps) if s.pool.pool_type in (LiquidityType.SSL, LiquidityType.EQL, LiquidityType.ASIAN_LOW, LiquidityType.PDL)), None)
        else:
            matching_sweep = next((s for s in reversed(reclaimed_sweeps) if s.pool.pool_type in (LiquidityType.BSL, LiquidityType.EQH, LiquidityType.ASIAN_HIGH, LiquidityType.PDH)), None)

        recent_sweep: Optional[LiquiditySweepEvent] = matching_sweep or (reclaimed_sweeps[-1] if reclaimed_sweeps else (sweeps[-1] if sweeps else None))

        # Score Structure
        mss_confirmed = False
        if recent_mss:
            if recent_mss.direction == TrendDirection.BULLISH and signal_dir == SignalDirection.LONG:
                mss_confirmed = True
                score_breakdown["structure"] = 2.5
                reasons.append("Bullish MSS confirmed on 15M with displacement")
            elif recent_mss.direction == TrendDirection.BEARISH and signal_dir == SignalDirection.SHORT:
                mss_confirmed = True
                score_breakdown["structure"] = 2.5
                reasons.append("Bearish MSS confirmed on 15M with displacement")
            else:
                score_breakdown["structure"] = 1.0
                reasons.append(f"Counter-trend MSS detected ({recent_mss.direction.value})")
        else:
            if htf_bias != TrendDirection.RANGING:
                score_breakdown["structure"] = 1.5
                reasons.append(f"Trend continuation ({htf_bias.value}) without fresh MSS")
            else:
                score_breakdown["structure"] = 1.0
                reasons.append("Market ranging, waiting for directional MSS")

        # Score Liquidity Sweep
        liquidity_swept = False
        swept_low_price = 0.0
        swept_high_price = 0.0

        if recent_sweep:
            ptype = recent_sweep.pool.pool_type
            if signal_dir == SignalDirection.LONG and ptype in (LiquidityType.SSL, LiquidityType.EQL, LiquidityType.ASIAN_LOW, LiquidityType.PDL):
                liquidity_swept = True
                swept_low_price = recent_sweep.sweep_price
                score_breakdown["liquidity"] = 2.5
                reasons.append(f"SSL/EQL swept and reclaimed at {swept_low_price:.2f}")
            elif signal_dir == SignalDirection.SHORT and ptype in (LiquidityType.BSL, LiquidityType.EQH, LiquidityType.ASIAN_HIGH, LiquidityType.PDH):
                liquidity_swept = True
                swept_high_price = recent_sweep.sweep_price
                score_breakdown["liquidity"] = 2.5
                reasons.append(f"BSL/EQH swept and reclaimed at {swept_high_price:.2f}")
            else:
                score_breakdown["liquidity"] = 1.0
                reasons.append(f"Opposing liquidity swept: {ptype.value}")
        else:
            reasons.append("No confirmed liquidity sweep on current range")

        # 4. Fair Value Gaps (5M)
        fvgs_5m = self.fvg_engine.detect_fvgs(candles_5m, timeframe="5m")
        active_fvg: Optional[FVGZone] = None

        for fvg in reversed(fvgs_5m):
            if not fvg.mitigated:
                if signal_dir == SignalDirection.LONG and fvg.direction == FVGDirection.BULLISH:
                    if fvg.bottom <= current_price <= fvg.top * 1.01:
                        active_fvg = fvg
                        score_breakdown["fvg"] = 2.0
                        reasons.append(f"Bullish 5M FVG open [{fvg.bottom:.2f} - {fvg.top:.2f}], CE: {fvg.midpoint:.2f}")
                        break
                elif signal_dir == SignalDirection.SHORT and fvg.direction == FVGDirection.BEARISH:
                    if fvg.bottom * 0.99 <= current_price <= fvg.top:
                        active_fvg = fvg
                        score_breakdown["fvg"] = 2.0
                        reasons.append(f"Bearish 5M FVG open [{fvg.bottom:.2f} - {fvg.top:.2f}], CE: {fvg.midpoint:.2f}")
                        break

        fvg_present = active_fvg is not None
        if not fvg_present:
            # Partial score if nearby unmitigated FVG exists
            matching_fvgs = [f for f in fvgs_5m if not f.mitigated and f.direction == (FVGDirection.BULLISH if signal_dir == SignalDirection.LONG else FVGDirection.BEARISH)]
            if matching_fvgs:
                score_breakdown["fvg"] = 1.0
                reasons.append(f"Resting unmitigated FVG nearby at {matching_fvgs[-1].midpoint:.2f}")

        # 5. Order Blocks (15M)
        obs_15m = self.ob_engine.detect_order_blocks(candles_15m, bos_list, mss_list, timeframe="15m")
        active_ob: Optional[OrderBlockZone] = None

        for ob in reversed(obs_15m):
            if not ob.mitigated:
                if signal_dir == SignalDirection.LONG and ob.direction == TrendDirection.BULLISH:
                    if ob.bottom <= current_price <= ob.top * 1.01:
                        active_ob = ob
                        score_breakdown["order_block"] = 1.5
                        reasons.append(f"Bullish Demand OB active [{ob.bottom:.2f} - {ob.top:.2f}], Score: {ob.strength_score:.1f}")
                        break
                elif signal_dir == SignalDirection.SHORT and ob.direction == TrendDirection.BEARISH:
                    if ob.bottom * 0.99 <= current_price <= ob.top:
                        active_ob = ob
                        score_breakdown["order_block"] = 1.5
                        reasons.append(f"Bearish Supply OB active [{ob.bottom:.2f} - {ob.top:.2f}], Score: {ob.strength_score:.1f}")
                        break

        ob_present = active_ob is not None

        # 6. Dealing Range & Premium / Discount Valuation (15M)
        pd_state = self.pd_engine.evaluate_range(current_price, swings_15m)
        pd_zone = pd_state.current_zone
        range_high = pd_state.range_high
        range_low = pd_state.range_low

        if signal_dir == SignalDirection.LONG and pd_zone in (PDZone.DISCOUNT, PDZone.EQUILIBRIUM):
            score_breakdown["premium_discount"] = 1.0
            reasons.append(f"Price in {pd_zone.value} ({current_price:.2f} <= {pd_state.equilibrium:.2f})")
        elif signal_dir == SignalDirection.SHORT and pd_zone in (PDZone.PREMIUM, PDZone.EQUILIBRIUM):
            score_breakdown["premium_discount"] = 1.0
            reasons.append(f"Price in {pd_zone.value} ({current_price:.2f} >= {pd_state.equilibrium:.2f})")
        else:
            reasons.append(f"Suboptimal dealing zone: {pd_zone.value} for {signal_dir.value}")

        # 7. Session Validation
        session_allowed, session_name = self.check_session(timestamp_ms)
        reasons.append(f"Session: {session_name} ({'ACTIVE' if session_allowed else 'OFF-PEAK'})")

        # Total Composite Score
        total_score = sum(score_breakdown.values())

        # 8. Entry, Stop Loss, and Take Profit Determination
        if signal_dir == SignalDirection.LONG:
            # Entry: FVG 50% CE or OB top or current price
            if active_fvg:
                entry_price = active_fvg.midpoint
            elif active_ob:
                entry_price = active_ob.top
            else:
                entry_price = current_price

            # Stop loss: below swept low or range low
            base_stop = swept_low_price if swept_low_price > 0 else (active_ob.bottom if active_ob else range_low)
            stop_loss = round(base_stop * 0.9985, 2)  # 0.15% buffer
            stop_distance = entry_price - stop_loss

            if stop_distance <= 0:
                stop_loss = round(entry_price * 0.985, 2)
                stop_distance = entry_price - stop_loss

            tp1 = round(entry_price + (stop_distance * 2.5), 2)
            tp2 = round(range_high, 2) if range_high > tp1 else round(entry_price + (stop_distance * 4.0), 2)
            reward_risk = round((tp1 - entry_price) / max(0.01, stop_distance), 2)

        else:  # SHORT
            if active_fvg:
                entry_price = active_fvg.midpoint
            elif active_ob:
                entry_price = active_ob.bottom
            else:
                entry_price = current_price

            base_stop = swept_high_price if swept_high_price > 0 else (active_ob.top if active_ob else range_high)
            stop_loss = round(base_stop * 1.0015, 2)  # 0.15% buffer
            stop_distance = stop_loss - entry_price

            if stop_distance <= 0:
                stop_loss = round(entry_price * 1.015, 2)
                stop_distance = stop_loss - entry_price

            tp1 = round(entry_price - (stop_distance * 2.5), 2)
            tp2 = round(range_low, 2) if range_low < tp1 else round(entry_price - (stop_distance * 4.0), 2)
            reward_risk = round((entry_price - tp1) / max(0.01, stop_distance), 2)

        # 9. Qualification & Lifecycle State
        rejection_reason = None
        if total_score < self.score_threshold:
            rejection_reason = f"Composite score {total_score:.1f} is below minimum threshold {self.score_threshold:.1f}"
            lifecycle = SetupLifecycleState.WATCHING
        elif reward_risk < self.min_reward_risk:
            rejection_reason = f"Reward:Risk ratio {reward_risk:.2f}R is below hard floor {self.min_reward_risk:.2f}R"
            lifecycle = SetupLifecycleState.REJECTED
        else:
            lifecycle = SetupLifecycleState.SETUP_ARMED

        signal_id = f"SIG-{symbol}-{int(time.time())}"

        return Signal(
            signal_id=signal_id,
            timestamp=timestamp_ms,
            symbol=symbol,
            direction=signal_dir,
            score=round(total_score, 1),
            score_breakdown={k: round(v, 2) for k, v in score_breakdown.items()},
            htf_bias=htf_bias,
            liquidity_swept=liquidity_swept,
            mss_confirmed=mss_confirmed,
            fvg_present=fvg_present,
            ob_present=ob_present,
            pd_zone=pd_zone,
            session_allowed=session_allowed,
            entry_price=round(entry_price, 2),
            stop_loss=round(stop_loss, 2),
            tp1=round(tp1, 2),
            tp2=round(tp2, 2),
            reward_risk=reward_risk,
            lifecycle=lifecycle,
            reasons=reasons,
            rejection_reason=rejection_reason,
        )
