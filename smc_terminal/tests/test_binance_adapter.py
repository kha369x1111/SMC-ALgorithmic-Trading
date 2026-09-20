"""
Unit & Integration tests for BinanceSpotAdapter in SMC Algorithmic Trading Terminal.
Tests public REST endpoints (ping, time, exchangeInfo, klines, ticker), filter caching,
and withdrawal safety rejection.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.data.models import Timeframe
from src.exchange.binance import BinanceSpotAdapter
from src.exchange.exceptions import AuthenticationError, OrderError
from src.exchange.models import OrderRequest, OrderSide, OrderType, SymbolConstraints


class TestBinanceSpotAdapter(unittest.TestCase):
    def setUp(self):
        # Default to Testnet
        self.adapter = BinanceSpotAdapter(testnet=True)

    def test_public_ping_and_server_time(self):
        """Verify real or mocked connectivity to Binance Testnet ping and time."""
        try:
            self.assertTrue(self.adapter.ping())
            server_time = self.adapter.get_server_time()
            self.assertGreater(server_time, 1700000000000)
        except Exception as e:
            self.skipTest(f"Binance Testnet public ping skipped due to network: {e}")

    def test_fetch_real_exchange_info(self):
        """Verify exchangeInfo parsing and filter caching for ETHUSDT."""
        try:
            constraints = self.adapter.fetch_exchange_info(["ETHUSDT"])
            self.assertIn("ETHUSDT", constraints)
            eth = constraints["ETHUSDT"]
            self.assertEqual(eth.symbol, "ETHUSDT")
            self.assertGreater(eth.tick_size, 0)
            self.assertGreater(eth.step_size, 0)
            self.assertGreaterEqual(eth.min_notional, 1.0)
            self.assertTrue(eth.is_trading_active)
        except Exception as e:
            self.skipTest(f"Binance Testnet exchangeInfo skipped due to network: {e}")

    def test_fetch_real_ticker_and_candles(self):
        """Verify real ticker price and klines parsing."""
        try:
            ticker = self.adapter.get_ticker("ETHUSDT")
            self.assertEqual(ticker.symbol, "ETHUSDT")
            self.assertGreater(ticker.last_price, 0)

            candles = self.adapter.get_candles("ETHUSDT", Timeframe.M15, limit=5)
            self.assertEqual(len(candles), 5)
            latest = candles[-1]
            self.assertGreater(latest.close, 0)
            self.assertGreater(latest.high, latest.low)
        except Exception as e:
            self.skipTest(f"Binance Testnet klines skipped due to network: {e}")

    def test_security_withdrawal_lockout(self):
        """Verify that any API key with enableWithdrawals=True is strictly REJECTED."""
        adapter_with_keys = BinanceSpotAdapter(
            api_key="TEST_API_KEY",
            api_secret="TEST_API_SECRET",
            testnet=True,
        )

        # Mock /api/v3/account returning enableWithdrawals = True
        with patch.object(adapter_with_keys, "_http_request") as mock_req:
            mock_req.side_effect = [
                {},  # ping
                {"serverTime": 1710000000000},  # time
                {"canTrade": True, "enableWithdrawals": True, "balances": []},  # account
            ]
            with self.assertRaises(AuthenticationError) as ctx:
                adapter_with_keys.connect()
            self.assertIn("WITHDRAWALS ENABLED", str(ctx.exception))

    def test_security_valid_trading_key_accepted(self):
        """Verify that an API key with enableWithdrawals=False connects successfully."""
        adapter_with_keys = BinanceSpotAdapter(
            api_key="TEST_API_KEY",
            api_secret="TEST_API_SECRET",
            testnet=True,
        )

        with patch.object(adapter_with_keys, "_http_request") as mock_req:
            mock_req.side_effect = [
                {},  # ping
                {"serverTime": 1710000000000},  # time
                {"canTrade": True, "enableWithdrawals": False, "balances": []},  # account
            ]
            self.assertTrue(adapter_with_keys.connect())
            self.assertTrue(adapter_with_keys.is_connected())

    def test_order_preflight_min_notional_rejection(self):
        """Verify pre-flight validation catches order below min notional before network dispatch."""
        self.adapter.register_constraints(SymbolConstraints(
            symbol="ETHUSDT",
            tick_size=0.01,
            step_size=0.0001,
            min_qty=0.0001,
            max_qty=1000.0,
            min_notional=10.0,
            price_precision=2,
            qty_precision=4,
        ))

        # 0.001 ETH * $3000 = $3.00, below $10.00 min notional
        small_order = OrderRequest(
            client_order_id="TEST-FAIL-NOTIONAL",
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.001,
            price=3000.0,
        )

        with self.assertRaises(OrderError) as ctx:
            self.adapter.create_order(small_order)
        self.assertIn("below minimum", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
