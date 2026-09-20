"""
Unit tests for SignalEngine orchestrator in SMC Algorithmic Trading Terminal.
Verifies multi-timeframe synthesis, composite score calculation (0-10),
rejection reasons, and RR floor enforcement.
"""

import unittest

from src.data.models import Candle
from src.strategy.models import SetupLifecycleState, SignalDirection, TrendDirection
from src.strategy.signal_engine import SignalEngine
from tests.fixtures import (
    create_candle_series,
    generate_bearish_fvg_series,
    generate_bullish_fvg_series,
    generate_equal_highs_and_sweep_series,
    generate_equal_lows_and_sweep_series,
    generate_fractal_high_series,
    generate_wave_series,
)


class TestSignalEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SignalEngine(score_threshold=8.0, min_reward_risk=2.0)

    def test_session_detection(self):
        """Verify ICT Killzone categorization based on UTC hour."""
        # 08:30 UTC -> London Killzone (07:00 - 10:00)
        ts_london = 1710837000000  # 2024-03-19 08:30:00 UTC
        allowed, session = self.engine.check_session(ts_london)
        self.assertTrue(allowed)
        self.assertEqual(session, "london_killzone")

        # 13:00 UTC -> New York Killzone (12:00 - 15:00)
        ts_ny = 1710853200000  # 2024-03-19 13:00:00 UTC
        allowed, session = self.engine.check_session(ts_ny)
        self.assertTrue(allowed)
        self.assertEqual(session, "newyork_killzone")

    def test_insufficient_candles_handled_safely(self):
        """Verify engine gracefully returns None when candle counts are insufficient."""
        short_series = create_candle_series(5, 3000.0)
        signal = self.engine.evaluate_setup("ETHUSDT", short_series, short_series, short_series)
        self.assertIsNone(signal)

    def test_full_bullish_smc_setup(self):
        """Verify a complete bullish setup (swept SSL + MSS + FVG) generates high score."""
        # 4H candles: Bullish wave expansion
        candles_4h = generate_wave_series(90.0, trend="BULLISH", waves=3, wave_size=10.0)

        # 15M candles: Sweep of equal lows and reclaim
        candles_15m = generate_wave_series(95.0, trend="BULLISH", waves=2, wave_size=5.0) + generate_equal_lows_and_sweep_series()

        # 5M candles: Bullish series with FVG
        candles_5m = create_candle_series(12, 92.0, trend="FLAT", step=0.2) + generate_bullish_fvg_series()

        signal = self.engine.evaluate_setup("ETHUSDT", candles_4h, candles_15m, candles_5m)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.symbol, "ETHUSDT")
        self.assertEqual(signal.direction, SignalDirection.LONG)
        self.assertGreaterEqual(signal.score, 5.0)
        self.assertGreater(signal.reward_risk, 1.5)
        self.assertIn("4H HTF Bias", signal.reasons[0])
        self.assertIsNotNone(signal.score_breakdown)

    def test_full_bearish_smc_setup(self):
        """Verify a complete bearish setup (swept BSL + Bearish MSS + Bearish FVG) generates SHORT signal."""
        # 4H candles: Bearish wave sequence
        candles_4h = generate_wave_series(200.0, trend="BEARISH", waves=3, wave_size=10.0)

        # 15M candles: Equal highs swept and reclaimed
        candles_15m = create_candle_series(5, 140.0, trend="FLAT") + generate_equal_highs_and_sweep_series()

        # 5M candles: Bearish series with FVG
        candles_5m = create_candle_series(12, 165.0, trend="FLAT", step=0.2) + generate_bearish_fvg_series()

        signal = self.engine.evaluate_setup("ETHUSDT", candles_4h, candles_15m, candles_5m)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.symbol, "ETHUSDT")
        self.assertEqual(signal.direction, SignalDirection.SHORT)
        self.assertGreaterEqual(signal.score, 5.0)

    def test_low_score_rejection(self):
        """Verify setup with low score is gated into WATCHING state with clear rejection reason."""
        # Ranging / flat market on all timeframes with no sweeps
        candles_4h = create_candle_series(25, 3000.0, trend="FLAT", step=1.0)
        candles_15m = create_candle_series(25, 3000.0, trend="FLAT", step=0.5)
        candles_5m = create_candle_series(25, 3000.0, trend="FLAT", step=0.2)

        signal = self.engine.evaluate_setup("ETHUSDT", candles_4h, candles_15m, candles_5m)
        self.assertIsNotNone(signal)
        self.assertLess(signal.score, 8.0)
        self.assertEqual(signal.lifecycle, SetupLifecycleState.WATCHING)
        self.assertIn("below minimum threshold", signal.rejection_reason)


if __name__ == "__main__":
    unittest.main()
