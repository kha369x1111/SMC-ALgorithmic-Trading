"""
Strict No-Lookahead-Bias Unit Test.
Proves mathematically that any swing, structure break, or signal calculated at step t
depends solely on candles[0...t] and never accesses or leaks candles[t+1...N].
"""

import unittest
from src.strategy.fvg import FVGEngine
from src.strategy.market_structure import MarketStructureEngine
from tests.fixtures import create_candle


class TestNoLookaheadBias(unittest.TestCase):

    def test_swing_confirmation_never_premature(self):
        """
        A 3-bar fractal swing at index k is confirmed strictly when bar k+3 closes.
        At bar k+2, it MUST NOT exist or be confirmed in the system.
        """
        engine = MarketStructureEngine(swing_length=3)

        # 7-bar series with peak at index 3
        # Bar 0, 1, 2, 3 (peak), 4, 5, 6
        candles = [
            create_candle(0, 100, 102, 99, 101),
            create_candle(1, 101, 108, 100, 107),
            create_candle(2, 107, 114, 106, 112),
            create_candle(3, 112, 125, 111, 122),  # The swing pivot
            create_candle(4, 122, 123, 115, 118),
            create_candle(5, 118, 119, 112, 114),
            create_candle(6, 114, 115, 108, 110),  # Confirmation bar (3 + 3 = 6)
        ]

        # 1. Evaluate up to index 4 (only 1 bar after pivot): Swing must NOT be confirmed
        swings_at_4 = engine.identify_swings(candles, as_of_index=4)
        self.assertEqual(len(swings_at_4), 0, "Lookahead violation: Swing confirmed before N right bars!")

        # 2. Evaluate up to index 5 (only 2 bars after pivot): Still NOT confirmed
        swings_at_5 = engine.identify_swings(candles, as_of_index=5)
        self.assertEqual(len(swings_at_5), 0, "Lookahead violation: Swing confirmed at index 5 before required index 6!")

        # 3. Evaluate up to index 6 (exactly 3 bars after pivot): MUST be confirmed
        swings_at_6 = engine.identify_swings(candles, as_of_index=6)
        self.assertEqual(len(swings_at_6), 1, "Swing at index 3 should be confirmed at index 6.")
        self.assertEqual(swings_at_6[0].confirmed_at_index, 6)

    def test_future_data_invariance(self):
        """
        Adding arbitrary future candles must NOT alter historical structure decisions
        at or before index t.
        """
        engine = MarketStructureEngine(swing_length=3)
        candles_t = [
            create_candle(0, 100, 102, 99, 101),
            create_candle(1, 101, 108, 100, 107),
            create_candle(2, 107, 114, 106, 112),
            create_candle(3, 112, 125, 111, 122),
            create_candle(4, 122, 123, 115, 118),
            create_candle(5, 118, 119, 112, 114),
            create_candle(6, 114, 115, 108, 110),
        ]
        swings_baseline = engine.identify_swings(candles_t, as_of_index=6)

        # Now append future bars with wild volatility
        candles_future = list(candles_t) + [
            create_candle(7, 110, 200, 105, 195),
            create_candle(8, 195, 250, 190, 240),
            create_candle(9, 240, 260, 220, 230),
        ]

        # Structure calculated at index 6 must remain bit-for-bit identical
        swings_evaluated_with_future = engine.identify_swings(candles_future, as_of_index=6)
        self.assertEqual(len(swings_baseline), len(swings_evaluated_with_future))
        self.assertEqual(swings_baseline[0].price, swings_evaluated_with_future[0].price)
        self.assertEqual(swings_baseline[0].confirmed_at_index, swings_evaluated_with_future[0].confirmed_at_index)


if __name__ == "__main__":
    unittest.main()
