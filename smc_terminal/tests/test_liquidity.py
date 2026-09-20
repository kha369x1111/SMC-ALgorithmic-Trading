"""
Unit tests for Liquidity Engine (EQH, EQL, BSL, SSL, Sweeps).
"""

import unittest
from src.strategy.liquidity import LiquidityEngine
from src.strategy.market_structure import MarketStructureEngine
from src.strategy.models import LiquidityType
from tests.fixtures import generate_equal_highs_and_sweep_series


class TestLiquidity(unittest.TestCase):

    def setUp(self):
        self.struct_engine = MarketStructureEngine(swing_length=3)
        self.liq_engine = LiquidityEngine(
            equal_tolerance_percent=0.10,
            require_reclaim=True,
            max_confirmation_bars=5,
        )

    def test_eqh_detection_and_sweep(self):
        candles = generate_equal_highs_and_sweep_series()
        swings = self.struct_engine.identify_swings(candles)
        pools = self.liq_engine.build_liquidity_pools(candles, swings, timeframe="15m")

        # Verify Equal High pool formed
        eqh_pools = [p for p in pools if p.pool_type == LiquidityType.EQH]
        self.assertGreaterEqual(len(eqh_pools), 1)
        self.assertAlmostEqual(eqh_pools[0].price, 150.025, places=2)

        # Detect sweep by bar 13 (piercing to 151.20 and closing at 147.50)
        sweeps = self.liq_engine.detect_sweeps(candles, pools)
        self.assertGreaterEqual(len(sweeps), 1)
        sweep_event = sweeps[0]
        self.assertTrue(sweep_event.reclaimed)
        self.assertEqual(sweep_event.sweep_price, 151.20)
        self.assertEqual(sweep_event.sweep_candle_index, 13)


if __name__ == "__main__":
    unittest.main()
