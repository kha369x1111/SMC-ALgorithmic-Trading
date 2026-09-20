"""
Unit tests for Market Structure Engine (Swings, HH/HL, BOS, MSS).
"""

import unittest
from src.strategy.market_structure import MarketStructureEngine
from src.strategy.models import SwingType, TrendDirection
from tests.fixtures import generate_fractal_high_series


class TestMarketStructure(unittest.TestCase):

    def setUp(self):
        self.engine = MarketStructureEngine(
            swing_length=3,
            require_bos_close=True,
            min_break_atr=0.01,
            require_mss_close=True,
            min_displacement_ratio=0.8,
        )

    def test_fractal_swing_high_detection(self):
        candles = generate_fractal_high_series()
        swings = self.engine.identify_swings(candles)

        high_swings = [s for s in swings if s.swing_type == SwingType.SWING_HIGH]
        self.assertEqual(len(high_swings), 1)
        pivot = high_swings[0]
        self.assertEqual(pivot.index, 3)
        self.assertEqual(pivot.price, 125.0)
        # 3-bar fractal must only be confirmed at index 3 + 3 = 6
        self.assertEqual(pivot.confirmed_at_index, 6)

    def test_trend_classification(self):
        candles = generate_fractal_high_series()
        swings = self.engine.identify_swings(candles)
        trend = self.engine.classify_trend(swings)
        # Single swing high is insufficient for trend -> RANGING
        self.assertEqual(trend, TrendDirection.RANGING)

    def test_bos_confirmed_by_close(self):
        candles = generate_fractal_high_series()
        swings = self.engine.identify_swings(candles)
        # Initially no BOS since prices declined after the swing high
        bos_events, mss_events = self.engine.detect_bos_and_mss(candles, swings)
        self.assertEqual(len(bos_events), 0)


if __name__ == "__main__":
    unittest.main()
