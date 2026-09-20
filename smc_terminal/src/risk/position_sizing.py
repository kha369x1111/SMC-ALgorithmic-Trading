"""
SMC Algorithmic Trading Terminal - Position Sizing Engine.
Calculates position size strictly as:
  Risk Amount = Equity * Risk_Percent
  Position Size = Risk Amount / Stop_Distance
Adjusts for exchange step size, tick size, minimum notional, and estimated slippage/fees.
Strictly prohibits fixed-dollar allocations or Martingale progressions.
"""

from dataclasses import dataclass
from typing import Tuple
from src.exchange.exceptions import RiskError
from src.exchange.models import SymbolConstraints


@dataclass
class SizingResult:
    equity: float
    risk_percent: float
    risk_amount_usd: float
    entry_price: float
    stop_price: float
    stop_distance_usd: float
    raw_quantity: float
    rounded_quantity: float
    notional_usd: float
    estimated_fee_usd: float
    is_valid: bool
    rejection_reason: str = ""


class PositionSizingEngine:
    """Quantitative Risk-Weighted Position Sizer."""

    def __init__(
        self,
        default_risk_percent: float = 0.25,  # 0.25% of equity
        max_risk_percent: float = 1.00,      # 1.00% hard limit
        fee_rate_est: float = 0.00075,       # 0.075% fee estimate
        slippage_buffer_pct: float = 0.05,   # 5% buffer on stop distance for slippage
    ) -> None:
        self.default_risk_pct = default_risk_percent
        self.max_risk_pct = max_risk_percent
        self.fee_rate_est = fee_rate_est
        self.slippage_buffer_pct = slippage_buffer_pct

    def calculate_size(
        self,
        equity: float,
        entry_price: float,
        stop_price: float,
        constraints: SymbolConstraints,
        risk_percent: float = 0.25,
    ) -> SizingResult:
        """
        Calculate compliant position size based on capital at risk.
        """
        if equity <= 0:
            raise RiskError("Account equity must be positive.")

        # Cap risk percent at hard safety ceiling
        effective_risk_pct = min(risk_percent, self.max_risk_pct)
        risk_amount_usd = equity * (effective_risk_pct / 100.0)

        stop_distance = abs(entry_price - stop_price)
        if stop_distance <= 0:
            return SizingResult(
                equity=equity,
                risk_percent=effective_risk_pct,
                risk_amount_usd=risk_amount_usd,
                entry_price=entry_price,
                stop_price=stop_price,
                stop_distance_usd=0.0,
                raw_quantity=0.0,
                rounded_quantity=0.0,
                notional_usd=0.0,
                estimated_fee_usd=0.0,
                is_valid=False,
                rejection_reason="Stop price cannot equal entry price.",
            )

        # Incorporate slippage buffer into stop distance
        effective_stop_distance = stop_distance * (1.0 + self.slippage_buffer_pct)

        raw_qty = risk_amount_usd / effective_stop_distance
        rounded_qty = constraints.round_qty(raw_qty)
        notional = entry_price * rounded_qty
        est_fee = notional * self.fee_rate_est

        # Pre-flight constraint validation
        if rounded_qty < constraints.min_qty:
            return SizingResult(
                equity=equity,
                risk_percent=effective_risk_pct,
                risk_amount_usd=risk_amount_usd,
                entry_price=entry_price,
                stop_price=stop_price,
                stop_distance_usd=stop_distance,
                raw_quantity=raw_qty,
                rounded_quantity=rounded_qty,
                notional_usd=notional,
                estimated_fee_usd=est_fee,
                is_valid=False,
                rejection_reason=f"Position size {rounded_qty} is below min quantity {constraints.min_qty}",
            )

        if notional < constraints.min_notional:
            return SizingResult(
                equity=equity,
                risk_percent=effective_risk_pct,
                risk_amount_usd=risk_amount_usd,
                entry_price=entry_price,
                stop_price=stop_price,
                stop_distance_usd=stop_distance,
                raw_quantity=raw_qty,
                rounded_quantity=rounded_qty,
                notional_usd=notional,
                estimated_fee_usd=est_fee,
                is_valid=False,
                rejection_reason=f"Order notional {notional:.2f} USD is below exchange minimum {constraints.min_notional:.2f} USD",
            )

        if notional > equity:
            return SizingResult(
                equity=equity,
                risk_percent=effective_risk_pct,
                risk_amount_usd=risk_amount_usd,
                entry_price=entry_price,
                stop_price=stop_price,
                stop_distance_usd=stop_distance,
                raw_quantity=raw_qty,
                rounded_quantity=rounded_qty,
                notional_usd=notional,
                estimated_fee_usd=est_fee,
                is_valid=False,
                rejection_reason=f"Spot order notional {notional:.2f} USD exceeds total cash equity {equity:.2f} USD",
            )

        return SizingResult(
            equity=equity,
            risk_percent=effective_risk_pct,
            risk_amount_usd=risk_amount_usd,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_usd=stop_distance,
            raw_quantity=raw_qty,
            rounded_quantity=rounded_qty,
            notional_usd=notional,
            estimated_fee_usd=est_fee,
            is_valid=True,
            rejection_reason="",
        )
