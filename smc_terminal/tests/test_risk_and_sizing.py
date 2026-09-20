"""
Unit tests for Risk Management Engine and Position Sizing.
"""

import unittest
from src.exchange.models import SymbolConstraints
from src.risk.position_sizing import PositionSizingEngine
from src.risk.risk_manager import RiskManager
from src.strategy.models import (
    PDZone,
    SetupLifecycleState,
    Signal,
    SignalDirection,
    TrendDirection,
)


class TestRiskAndSizing(unittest.TestCase):

    def setUp(self):
        self.sizing_engine = PositionSizingEngine(default_risk_percent=0.25, max_risk_percent=1.0)
        self.risk_mgr = RiskManager(
            max_daily_loss_percent=2.0,
            max_consecutive_losses=3,
            max_open_positions=2,
            minimum_reward_risk=2.0,
        )
        self.eth_constraints = SymbolConstraints(
            symbol="ETHUSDT",
            tick_size=0.01,
            step_size=0.0001,
            min_qty=0.0001,
            max_qty=10000.0,
            min_notional=5.0,
            price_precision=2,
            qty_precision=4,
        )

    def test_position_sizing_formula(self):
        # Equity: 10,000 USD, Risk: 0.25% = 25 USD
        # Entry: 3,000 USD, Stop: 2,950 USD -> Stop distance = 50 USD
        # Expected quantity = 25 / (50 * 1.05 slippage buffer) ~ 0.4761 ETH
        res = self.sizing_engine.calculate_size(
            equity=10000.0,
            entry_price=3000.0,
            stop_price=2950.0,
            constraints=self.eth_constraints,
            risk_percent=0.25,
        )
        self.assertTrue(res.is_valid)
        self.assertEqual(res.risk_amount_usd, 25.0)
        self.assertAlmostEqual(res.rounded_quantity, 0.4761, places=3)
        self.assertGreater(res.notional_usd, 5.0)

    def test_consecutive_loss_circuit_breaker(self):
        # 3 consecutive losses must trigger circuit breaker
        self.risk_mgr.record_trade_outcome(-50.0)
        self.risk_mgr.record_trade_outcome(-50.0)
        self.assertFalse(self.risk_mgr.circuit_breaker_active)

        self.risk_mgr.record_trade_outcome(-50.0)
        self.assertTrue(self.risk_mgr.circuit_breaker_active)
        self.assertIn("Consecutive Loss Limit", self.risk_mgr.circuit_breaker_reason)

    def test_daily_loss_guard(self):
        # Daily loss limit = 2% of 10,000 = 200 USD
        self.risk_mgr.record_trade_outcome(-210.0)
        self.assertTrue(self.risk_mgr.circuit_breaker_active)
        self.assertIn("Daily Loss Limit hit", self.risk_mgr.circuit_breaker_reason)

    def test_signal_rr_rejection(self):
        signal_low_rr = Signal(
            signal_id="SIG-001",
            timestamp=1000,
            symbol="ETHUSDT",
            direction=SignalDirection.LONG,
            score=9.0,
            score_breakdown={},
            htf_bias=TrendDirection.BULLISH,
            liquidity_swept=True,
            mss_confirmed=True,
            fvg_present=True,
            ob_present=True,
            pd_zone=PDZone.DISCOUNT,
            session_allowed=True,
            entry_price=3000.0,
            stop_loss=2950.0,
            tp1=3070.0,
            tp2=3100.0,
            reward_risk=1.4,  # Below minimum 2.0R!
            lifecycle=SetupLifecycleState.SETUP_ARMED,
            reasons=["High quality setup"],
        )
        verdict = self.risk_mgr.evaluate_signal(signal_low_rr)
        self.assertFalse(verdict.approved)
        self.assertIn("below minimum threshold", verdict.reason)


if __name__ == "__main__":
    unittest.main()
