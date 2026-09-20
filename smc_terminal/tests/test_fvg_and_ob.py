"""
Unit tests for FVG Engine, Order Blocks, and Premium/Discount.
"""

import unittest
from src.strategy.fvg import FVGEngine
from src.strategy.models import FVGDirection, PDZone, SwingPoint, SwingType
from src.strategy.order_blocks import OrderBlockEngine
from src.strategy.premium_discount import PremiumDiscountEngine
from tests.fixtures import generate_bearish_fvg_series, generate_bullish_fvg_series


class TestFVGAndOB(unittest.TestCase):

    def test_bullish_fvg_and_mitigation(self):
        engine = FVGEngine(min_atr_ratio=0.05, invalidate_when_filled=False)
        candles = generate_bullish_fvg_series()
        # Bar 0: High = 100, Bar 2: Low = 108 -> Gap top=108, bottom=100, midpoint=104
        fvgs = engine.detect_fvgs(candles, timeframe="5m")
        self.assertGreaterEqual(len(fvgs), 1)

        bull_fvg = fvgs[0]
        self.assertEqual(bull_fvg.direction, FVGDirection.BULLISH)
        self.assertEqual(bull_fvg.top, 108.0)
        self.assertEqual(bull_fvg.bottom, 100.0)
        self.assertEqual(bull_fvg.midpoint, 104.0)

        # Bar 3 dipped to low=104, reaching 50% CE midpoint
        self.assertTrue(bull_fvg.mitigated)

    def test_bearish_fvg_detection(self):
        engine = FVGEngine(min_atr_ratio=0.05, invalidate_when_filled=True)
        candles = generate_bearish_fvg_series()
        # Bar 0: Low = 120, Bar 2: High = 112 -> Gap top=120, bottom=112, midpoint=116
        fvgs = engine.detect_fvgs(candles, timeframe="5m")
        self.assertEqual(len(fvgs), 1)
        bear_fvg = fvgs[0]
        self.assertEqual(bear_fvg.direction, FVGDirection.BEARISH)
        self.assertEqual(bear_fvg.top, 120.0)
        self.assertEqual(bear_fvg.bottom, 112.0)
        self.assertEqual(bear_fvg.midpoint, 116.0)

    def test_premium_discount_gating(self):
        pd_engine = PremiumDiscountEngine(equilibrium_ratio=0.50)
        swings = [
            SwingPoint(index=0, timestamp=1000, price=100.0, swing_type=SwingType.SWING_LOW, confirmed_at_index=3),
            SwingPoint(index=5, timestamp=2000, price=200.0, swing_type=SwingType.SWING_HIGH, confirmed_at_index=8),
        ]
        # Range: 100 to 200, Equilibrium: 150
        # Price at 120 is in Discount
        state_discount = pd_engine.evaluate_range(current_price=120.0, swings=swings)
        self.assertEqual(state_discount.current_zone, PDZone.DISCOUNT)
        can_buy, _ = pd_engine.validate_entry_location(direction_is_long=True, zone=state_discount.current_zone)
        self.assertTrue(can_buy)

        can_short, reason = pd_engine.validate_entry_location(direction_is_long=False, zone=state_discount.current_zone)
        self.assertFalse(can_short)
        self.assertIn("cheap", reason.lower())

        # Price at 180 is in Premium
        state_prem = pd_engine.evaluate_range(current_price=180.0, swings=swings)
        self.assertEqual(state_prem.current_zone, PDZone.PREMIUM)
        can_buy_prem, reason_prem = pd_engine.validate_entry_location(direction_is_long=True, zone=state_prem.current_zone)
        self.assertFalse(can_buy_prem)
        self.assertIn("expensive", reason_prem.lower())


if __name__ == "__main__":
    unittest.main()
