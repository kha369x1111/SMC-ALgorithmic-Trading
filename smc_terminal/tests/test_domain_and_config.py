"""
Unit tests for Domain Models, Configuration, and System State.
"""

import unittest
from src.app.state import Environment, SystemStatus, TerminalState, TradingMode
from src.data.models import Candle, DataValidator
from src.exchange.exceptions import DataError
from tests.fixtures import create_candle


class TestDomainAndConfig(unittest.TestCase):

    def test_default_state_safety(self):
        """Live trading must be disabled and demo/paper by default."""
        state = TerminalState()
        self.assertEqual(state.environment, Environment.DEMO)
        self.assertEqual(state.trading_mode, TradingMode.PAPER)
        self.assertFalse(state.is_live_confirmed)

        # Attempt to open orders under live environment without user confirmation
        state.environment = Environment.LIVE
        can_trade, reason = state.can_open_orders()
        self.assertFalse(can_trade)
        self.assertIn("unconfirmed", reason.lower())

    def test_kill_switch_blocks_orders(self):
        state = TerminalState()
        state.kill_switch_engaged = True
        can_trade, reason = state.can_open_orders()
        self.assertFalse(can_trade)
        self.assertIn("kill switch", reason.lower())

    def test_candle_math_validation(self):
        valid = create_candle(0, 100, 110, 95, 105, 500)
        DataValidator.validate_candle(valid)

        # High lower than low should raise DataError
        invalid_high = Candle(timestamp=1000, open=100, high=90, low=95, close=100, volume=10)
        with self.assertRaises(DataError):
            DataValidator.validate_candle(invalid_high)

        # Negative volume
        invalid_vol = Candle(timestamp=1000, open=100, high=110, low=90, close=100, volume=-5)
        with self.assertRaises(DataError):
            DataValidator.validate_candle(invalid_vol)

    def test_series_chronological_order(self):
        c1 = create_candle(0, 100, 105, 95, 102)
        c2 = create_candle(1, 102, 108, 100, 105)
        DataValidator.validate_series([c1, c2])

        # Out-of-order timestamp raises DataError
        c_bad = Candle(timestamp=c1.timestamp - 1000, open=105, high=110, low=100, close=107, volume=10)
        with self.assertRaises(DataError):
            DataValidator.validate_series([c1, c_bad])


if __name__ == "__main__":
    unittest.main()
