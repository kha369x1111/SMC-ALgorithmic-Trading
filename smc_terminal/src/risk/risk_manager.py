"""
SMC Algorithmic Trading Terminal - Risk Management Engine.
Acts as the final, immutable decision authority on all proposed trades.
Enforces Daily Loss Guard (2%), Consecutive Loss Protection (3), Max Concurrent Positions (2),
Minimum Reward:Risk ratio (2.0), Kill Switch, and Circuit Breaker gating.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from src.strategy.models import Signal


@dataclass
class RiskVerdict:
    approved: bool
    reason: str
    equity: float
    current_daily_loss_pct: float
    consecutive_losses: int
    open_positions_count: int


class RiskManager:
    """Quantitative Risk Guardian and Circuit Breaker."""

    def __init__(
        self,
        max_daily_loss_percent: float = 2.0,
        max_consecutive_losses: int = 3,
        max_open_positions: int = 2,
        minimum_reward_risk: float = 2.0,
    ) -> None:
        self.max_daily_loss_pct = max_daily_loss_percent
        self.max_consecutive_losses = max_consecutive_losses
        self.max_open_positions = max_open_positions
        self.minimum_rr = minimum_reward_risk

        # Dynamic runtime risk metrics
        self.daily_pnl_usd: float = 0.0
        self.start_of_day_equity: float = 10000.0
        self.current_equity: float = 10000.0
        self.consecutive_losses: int = 0
        self.open_positions: int = 0
        self.kill_switch_active: bool = False
        self.circuit_breaker_active: bool = False
        self.circuit_breaker_reason: str = ""

    def engage_kill_switch(self) -> None:
        """Emergency Kill Switch - immediately terminates order routing."""
        self.kill_switch_active = True

    def disengage_kill_switch(self) -> None:
        self.kill_switch_active = False

    def trigger_circuit_breaker(self, reason: str) -> None:
        """Trigger automated circuit breaker."""
        self.circuit_breaker_active = True
        self.circuit_breaker_reason = reason

    def reset_circuit_breaker(self) -> None:
        self.circuit_breaker_active = False
        self.circuit_breaker_reason = ""

    def record_trade_outcome(self, pnl_usd: float) -> None:
        """Update consecutive loss counter and daily PnL."""
        self.daily_pnl_usd += pnl_usd
        self.current_equity += pnl_usd

        if pnl_usd < 0:
            self.consecutive_losses += 1
        elif pnl_usd > 0:
            self.consecutive_losses = 0

        # Check automated circuit breaker conditions
        daily_loss_pct = (abs(self.daily_pnl_usd) / max(self.start_of_day_equity, 1e-6)) * 100.0
        if self.daily_pnl_usd < 0 and daily_loss_pct >= self.max_daily_loss_pct:
            self.trigger_circuit_breaker(
                f"Daily Loss Limit hit: -{daily_loss_pct:.2f}% >= -{self.max_daily_loss_pct:.2f}%"
            )

        if self.consecutive_losses >= self.max_consecutive_losses:
            self.trigger_circuit_breaker(
                f"Consecutive Loss Limit reached: {self.consecutive_losses} losses in a row."
            )

    def evaluate_signal(self, signal: Signal) -> RiskVerdict:
        """
        Final safety gate. Checks if proposed signal conforms to all risk boundaries.
        Returns RiskVerdict (approved: bool, reason: str).
        """
        # 1. Kill switch
        if self.kill_switch_active:
            return RiskVerdict(
                approved=False,
                reason="REJECTED: Emergency Kill Switch is ACTIVE.",
                equity=self.current_equity,
                current_daily_loss_pct=self._calc_daily_loss_pct(),
                consecutive_losses=self.consecutive_losses,
                open_positions_count=self.open_positions,
            )

        # 2. Circuit breaker
        if self.circuit_breaker_active:
            return RiskVerdict(
                approved=False,
                reason=f"REJECTED: Circuit Breaker ACTIVE: {self.circuit_breaker_reason}",
                equity=self.current_equity,
                current_daily_loss_pct=self._calc_daily_loss_pct(),
                consecutive_losses=self.consecutive_losses,
                open_positions_count=self.open_positions,
            )

        # 3. Daily loss guard
        daily_loss_pct = self._calc_daily_loss_pct()
        if self.daily_pnl_usd < 0 and daily_loss_pct >= self.max_daily_loss_pct:
            return RiskVerdict(
                approved=False,
                reason=f"REJECTED: Daily Loss Guard ({daily_loss_pct:.2f}% >= {self.max_daily_loss_pct:.2f}%).",
                equity=self.current_equity,
                current_daily_loss_pct=daily_loss_pct,
                consecutive_losses=self.consecutive_losses,
                open_positions_count=self.open_positions,
            )

        # 4. Consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            return RiskVerdict(
                approved=False,
                reason=f"REJECTED: Max Consecutive Losses reached ({self.consecutive_losses}/{self.max_consecutive_losses}).",
                equity=self.current_equity,
                current_daily_loss_pct=daily_loss_pct,
                consecutive_losses=self.consecutive_losses,
                open_positions_count=self.open_positions,
            )

        # 5. Open positions cap
        if self.open_positions >= self.max_open_positions:
            return RiskVerdict(
                approved=False,
                reason=f"REJECTED: Max Open Positions reached ({self.open_positions}/{self.max_open_positions}).",
                equity=self.current_equity,
                current_daily_loss_pct=daily_loss_pct,
                consecutive_losses=self.consecutive_losses,
                open_positions_count=self.open_positions,
            )

        # 6. Minimum Reward to Risk ratio
        if signal.reward_risk < self.minimum_rr:
            return RiskVerdict(
                approved=False,
                reason=f"REJECTED: Signal R:R ({signal.reward_risk:.2f}R) is below minimum threshold ({self.minimum_rr:.2f}R).",
                equity=self.current_equity,
                current_daily_loss_pct=daily_loss_pct,
                consecutive_losses=self.consecutive_losses,
                open_positions_count=self.open_positions,
            )

        return RiskVerdict(
            approved=True,
            reason="APPROVED: All quantitative risk and portfolio constraints passed.",
            equity=self.current_equity,
            current_daily_loss_pct=daily_loss_pct,
            consecutive_losses=self.consecutive_losses,
            open_positions_count=self.open_positions,
        )

    def _calc_daily_loss_pct(self) -> float:
        if self.daily_pnl_usd >= 0:
            return 0.0
        return (abs(self.daily_pnl_usd) / max(self.start_of_day_equity, 1e-6)) * 100.0
