"""
SMC Algorithmic Trading Terminal - Premium vs Discount Valuation Engine.
Maps dealing range from major Swing High to Swing Low.
Determines whether market location favors Longs (Discount) or Shorts (Premium).
"""

from src.strategy.models import PDZone, PremiumDiscountState, SwingPoint, SwingType


class PremiumDiscountEngine:
    """Quantitative Dealing Range Evaluator."""

    def __init__(self, equilibrium_ratio: float = 0.50) -> None:
        self.eq_ratio = equilibrium_ratio

    def evaluate_range(
        self,
        current_price: float,
        swings: list[SwingPoint],
    ) -> PremiumDiscountState:
        """
        Calculates Dealing Range using the most recent confirmed Swing High and Swing Low.
        """
        highs = [s for s in swings if s.swing_type == SwingType.SWING_HIGH]
        lows = [s for s in swings if s.swing_type == SwingType.SWING_LOW]

        if not highs or not lows:
            # Fallback when swings are not yet confirmed
            return PremiumDiscountState(
                range_high=current_price * 1.05,
                range_low=current_price * 0.95,
                equilibrium=current_price,
                current_price=current_price,
                current_zone=PDZone.EQUILIBRIUM,
            )

        range_high = highs[-1].price
        range_low = lows[-1].price

        # Handle inverted ranges safely
        actual_high = max(range_high, range_low)
        actual_low = min(range_high, range_low)

        equilibrium = actual_low + (actual_high - actual_low) * self.eq_ratio

        tolerance = (actual_high - actual_low) * 0.02  # 2% equilibrium neutrality band
        if abs(current_price - equilibrium) <= tolerance:
            zone = PDZone.EQUILIBRIUM
        elif current_price > equilibrium:
            zone = PDZone.PREMIUM
        else:
            zone = PDZone.DISCOUNT

        return PremiumDiscountState(
            range_high=actual_high,
            range_low=actual_low,
            equilibrium=equilibrium,
            current_price=current_price,
            current_zone=zone,
        )

    def validate_entry_location(self, direction_is_long: bool, zone: PDZone) -> tuple[bool, str]:
        """
        Strict SMC rule:
        Long entries are ONLY valid in Discount (or Equilibrium).
        Short entries are ONLY valid in Premium (or Equilibrium).
        """
        if direction_is_long:
            if zone == PDZone.PREMIUM:
                return False, "Long entry rejected: Price is in Premium (expensive)."
            return True, f"Long entry approved in {zone.value} zone."
        else:
            if zone == PDZone.DISCOUNT:
                return False, "Short entry rejected: Price is in Discount (cheap)."
            return True, f"Short entry approved in {zone.value} zone."
