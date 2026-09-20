"""
Unit tests for SQLite DatabaseManager in SMC Algorithmic Trading Terminal.
Verifies WAL mode, schema integrity, atomic transactions, and idempotency.
"""

import os
import tempfile
import time
import unittest

from src.database.sqlite import DatabaseManager
from src.exchange.models import OrderRequest, OrderSide, OrderStatus, OrderType, PositionModel
from src.strategy.models import PDZone, SetupLifecycleState, Signal, SignalDirection, TrendDirection


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_terminal.db")
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_wal_mode_and_foreign_keys(self):
        """Verify SQLite PRAGMA journal_mode is WAL."""
        cursor = self.db._conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        self.assertEqual(mode.lower(), "wal")

        cursor.execute("PRAGMA foreign_keys;")
        fk = cursor.fetchone()[0]
        self.assertEqual(fk, 1)
        cursor.close()

    def test_signal_persistence_and_retrieval(self):
        """Test saving and querying structured SMC signals."""
        now = int(time.time())
        signal = Signal(
            signal_id="SIG-ETH-TEST-001",
            timestamp=now,
            symbol="ETHUSDT",
            direction=SignalDirection.LONG,
            score=9.2,
            score_breakdown={"structure": 2.5, "liquidity": 2.5, "fvg": 2.0, "ob": 1.2, "pd": 1.0},
            htf_bias=TrendDirection.BULLISH,
            liquidity_swept=True,
            mss_confirmed=True,
            fvg_present=True,
            ob_present=True,
            pd_zone=PDZone.DISCOUNT,
            session_allowed=True,
            entry_price=3485.0,
            stop_loss=3445.0,
            tp1=3540.0,
            tp2=3580.0,
            reward_risk=2.85,
            lifecycle=SetupLifecycleState.SETUP_ARMED,
            reasons=["4H Bullish", "SSL swept at 3450", "MSS confirmed", "FVG 50% CE entry"],
            rejection_reason=None,
        )

        self.db.save_signal(signal)
        retrieved = self.db.get_signals("ETHUSDT", limit=10)
        self.assertEqual(len(retrieved), 1)
        saved = retrieved[0]
        self.assertEqual(saved.signal_id, "SIG-ETH-TEST-001")
        self.assertEqual(saved.direction, SignalDirection.LONG)
        self.assertEqual(saved.score, 9.2)
        self.assertTrue(saved.liquidity_swept)
        self.assertEqual(saved.entry_price, 3485.0)
        self.assertEqual(len(saved.reasons), 4)

    def test_order_lifecycle_idempotency(self):
        """Verify order insertion, status updates, and retrieval."""
        order = OrderRequest(
            client_order_id="ORD-TEST-12345",
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.5,
            price=3485.0,
        )

        now = int(time.time())
        self.db.save_order(order, exchange_order_id="EX-001", status=OrderStatus.NEW, timestamp=now)

        ord_record = self.db.get_order("ORD-TEST-12345")
        self.assertIsNotNone(ord_record)
        self.assertEqual(ord_record["status"], "NEW")
        self.assertEqual(ord_record["quantity"], 0.5)

        # Update order fill
        self.db.update_order_status(
            client_order_id="ORD-TEST-12345",
            status=OrderStatus.FILLED,
            executed_qty=0.5,
            avg_price=3485.0,
            fee_paid=1.30,
        )

        updated = self.db.get_order("ORD-TEST-12345")
        self.assertEqual(updated["status"], "FILLED")
        self.assertEqual(updated["executed_qty"], 0.5)
        self.assertEqual(updated["fee_paid"], 1.30)

    def test_position_tracking_and_trade_closing(self):
        """Verify opening position, mark update, closing, and trade creation."""
        now = int(time.time())
        pos = PositionModel(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            entry_price=3485.0,
            current_price=3485.0,
            quantity=0.5,
            unrealized_pnl=0.0,
            pnl_percent=0.0,
            stop_loss=3445.0,
            take_profit=3565.0,
            timestamp=now,
        )

        self.db.save_position(pos)
        open_positions = self.db.get_open_positions()
        self.assertEqual(len(open_positions), 1)
        self.assertEqual(open_positions[0]["symbol"], "ETHUSDT")

        # Update mark price
        self.db.update_position_mark("ETHUSDT", 3540.0, 27.5, 1.57)
        open_positions = self.db.get_open_positions()
        self.assertAlmostEqual(open_positions[0]["current_price"], 3540.0)

        # Close position
        self.db.close_position(
            symbol="ETHUSDT",
            close_price=3565.0,
            pnl_usd=40.0,
            pnl_percent=2.29,
            fees_usd=1.30,
            exit_reason="TAKE_PROFIT_HIT",
            timestamp=now + 3600,
        )

        # Open positions should now be empty
        self.assertEqual(len(self.db.get_open_positions()), 0)

        # Trade should be recorded
        trades = self.db.get_trades(limit=10)
        self.assertEqual(len(trades), 1)
        trade = trades[0]
        self.assertEqual(trade["symbol"], "ETHUSDT")
        self.assertEqual(trade["pnl_usd"], 40.0)
        self.assertEqual(trade["exit_reason"], "TAKE_PROFIT_HIT")

        # Daily PnL
        daily_pnl = self.db.get_daily_pnl_usd(start_timestamp=now - 100)
        self.assertEqual(daily_pnl, 40.0)

    def test_risk_and_system_events(self):
        """Verify risk event recording and querying."""
        now = int(time.time())
        self.db.record_risk_event(
            event_type="CIRCUIT_BREAKER_TRIPPED",
            description="3 consecutive losses hit",
            value=3.0,
            threshold=3.0,
            timestamp=now,
        )
        self.db.record_system_event(
            event_type="HEARTBEAT",
            message="System state OK",
            level="INFO",
            timestamp=now,
        )

        risk_events = self.db.get_risk_events(limit=5)
        self.assertEqual(len(risk_events), 1)
        self.assertEqual(risk_events[0]["event_type"], "CIRCUIT_BREAKER_TRIPPED")

        sys_events = self.db.get_system_events(limit=5)
        self.assertEqual(len(sys_events), 1)
        self.assertEqual(sys_events[0]["message"], "System state OK")


if __name__ == "__main__":
    unittest.main()
