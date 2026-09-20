"""
SMC Algorithmic Trading Terminal - SQLite Persistence Engine.
Enforces WAL mode, foreign key integrity, atomic transactions, and clean indexing.
"""

import json
import logging
import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional

from src.exchange.models import OrderRequest, OrderResponse, OrderSide, OrderStatus, OrderType, PositionModel
from src.strategy.models import PDZone, SetupLifecycleState, Signal, SignalDirection, TrendDirection

logger = logging.getLogger("SMC_TERMINAL.DATABASE")


class DatabaseManager:
    """Institutional SQLite database manager with WAL mode and thread safety."""

    def __init__(self, db_path: str = "smc_terminal/data/terminal.db"):
        self.db_path = db_path
        self._lock = threading.RLock()

        # Ensure target directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self._conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._init_schema()

    def _connect(self) -> None:
        """Establish SQLite connection with WAL journal mode and PRAGMA settings."""
        with self._lock:
            self._conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0,
                isolation_level=None,  # Autocommit mode, manual transaction blocks
            )
            self._conn.row_factory = sqlite3.Row
            cursor = self._conn.cursor()
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA synchronous = NORMAL;")
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("PRAGMA busy_timeout = 5000;")
            cursor.close()
            logger.info("SQLite database connected with WAL mode at %s", self.db_path)

    def _init_schema(self) -> None:
        """Initialize database schema with tables and indexes."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")
            try:
                # 1. Signals Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS signals (
                        signal_id TEXT PRIMARY KEY,
                        timestamp INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        score REAL NOT NULL,
                        score_breakdown TEXT NOT NULL,
                        htf_bias TEXT NOT NULL,
                        liquidity_swept INTEGER NOT NULL,
                        mss_confirmed INTEGER NOT NULL,
                        fvg_present INTEGER NOT NULL,
                        ob_present INTEGER NOT NULL,
                        pd_zone TEXT NOT NULL,
                        session_allowed INTEGER NOT NULL,
                        entry_price REAL NOT NULL,
                        stop_loss REAL NOT NULL,
                        tp1 REAL NOT NULL,
                        tp2 REAL NOT NULL,
                        reward_risk REAL NOT NULL,
                        lifecycle TEXT NOT NULL,
                        reasons TEXT NOT NULL,
                        rejection_reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 2. Orders Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        client_order_id TEXT PRIMARY KEY,
                        exchange_order_id TEXT,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        order_type TEXT NOT NULL,
                        quantity REAL NOT NULL,
                        price REAL,
                        stop_price REAL,
                        status TEXT NOT NULL,
                        executed_qty REAL DEFAULT 0.0,
                        avg_price REAL DEFAULT 0.0,
                        fee_paid REAL DEFAULT 0.0,
                        timestamp INTEGER NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 3. Positions Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        current_price REAL NOT NULL,
                        quantity REAL NOT NULL,
                        stop_loss REAL NOT NULL,
                        take_profit REAL NOT NULL,
                        unrealized_pnl REAL DEFAULT 0.0,
                        pnl_percent REAL DEFAULT 0.0,
                        status TEXT NOT NULL DEFAULT 'OPEN',
                        opened_at INTEGER NOT NULL,
                        closed_at INTEGER,
                        close_price REAL
                    );
                """)

                # 4. Closed Trades Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        trade_id TEXT PRIMARY KEY,
                        client_order_id TEXT,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        exit_price REAL NOT NULL,
                        quantity REAL NOT NULL,
                        pnl_usd REAL NOT NULL,
                        pnl_percent REAL NOT NULL,
                        fees_usd REAL DEFAULT 0.0,
                        exit_reason TEXT,
                        opened_at INTEGER NOT NULL,
                        closed_at INTEGER NOT NULL
                    );
                """)

                # 5. Risk Events Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS risk_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        value REAL,
                        threshold REAL,
                        timestamp INTEGER NOT NULL
                    );
                """)

                # 6. System Events Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        level TEXT NOT NULL DEFAULT 'INFO',
                        timestamp INTEGER NOT NULL
                    );
                """)

                # 7. Market Structure & SMC Events Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS market_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        price REAL NOT NULL,
                        details TEXT,
                        timestamp INTEGER NOT NULL
                    );
                """)

                # Indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_sym_time ON signals(symbol, timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_lifecycle ON signals(lifecycle);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_sym_status ON orders(symbol, status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_sym_status ON positions(symbol, status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_sym_closed ON trades(symbol, closed_at);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_events_sym_time ON market_events(symbol, timestamp);")

                cursor.execute("COMMIT;")
            except Exception as e:
                cursor.execute("ROLLBACK;")
                logger.error("Schema initialization failed: %s", str(e))
                raise
            finally:
                cursor.close()

    # --- Signal Operations ---

    def save_signal(self, signal: Signal) -> None:
        """Persist or update an institutional SMC signal."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO signals (
                    signal_id, timestamp, symbol, direction, score, score_breakdown,
                    htf_bias, liquidity_swept, mss_confirmed, fvg_present, ob_present,
                    pd_zone, session_allowed, entry_price, stop_loss, tp1, tp2,
                    reward_risk, lifecycle, reasons, rejection_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                signal.signal_id,
                signal.timestamp,
                signal.symbol,
                signal.direction.value,
                signal.score,
                json.dumps(signal.score_breakdown),
                signal.htf_bias.value,
                1 if signal.liquidity_swept else 0,
                1 if signal.mss_confirmed else 0,
                1 if signal.fvg_present else 0,
                1 if signal.ob_present else 0,
                signal.pd_zone.value,
                1 if signal.session_allowed else 0,
                signal.entry_price,
                signal.stop_loss,
                signal.tp1,
                signal.tp2,
                signal.reward_risk,
                signal.lifecycle.value,
                json.dumps(signal.reasons),
                signal.rejection_reason,
            ))
            cursor.close()

    def get_signals(self, symbol: Optional[str] = None, limit: int = 50) -> List[Signal]:
        """Fetch historical signals ordered by timestamp descending."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            if symbol:
                cursor.execute(
                    "SELECT * FROM signals WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?",
                    (symbol, limit),
                )
            else:
                cursor.execute(
                    "SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            cursor.close()

            signals = []
            for r in rows:
                signals.append(Signal(
                    signal_id=r["signal_id"],
                    timestamp=r["timestamp"],
                    symbol=r["symbol"],
                    direction=SignalDirection(r["direction"]),
                    score=r["score"],
                    score_breakdown=json.loads(r["score_breakdown"]),
                    htf_bias=TrendDirection(r["htf_bias"]),
                    liquidity_swept=bool(r["liquidity_swept"]),
                    mss_confirmed=bool(r["mss_confirmed"]),
                    fvg_present=bool(r["fvg_present"]),
                    ob_present=bool(r["ob_present"]),
                    pd_zone=PDZone(r["pd_zone"]),
                    session_allowed=bool(r["session_allowed"]),
                    entry_price=r["entry_price"],
                    stop_loss=r["stop_loss"],
                    tp1=r["tp1"],
                    tp2=r["tp2"],
                    reward_risk=r["reward_risk"],
                    lifecycle=SetupLifecycleState(r["lifecycle"]),
                    reasons=json.loads(r["reasons"]),
                    rejection_reason=r["rejection_reason"],
                ))
            return signals

    # --- Order Operations ---

    def save_order(
        self,
        order: OrderRequest,
        exchange_order_id: Optional[str] = None,
        status: OrderStatus = OrderStatus.NEW,
        timestamp: int = 0,
    ) -> None:
        """Record an order request idempotently."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO orders (
                    client_order_id, exchange_order_id, symbol, side, order_type,
                    quantity, price, stop_price, status, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                order.client_order_id,
                exchange_order_id,
                order.symbol,
                order.side.value,
                order.order_type.value,
                order.quantity,
                order.price,
                order.stop_price,
                status.value,
                timestamp,
            ))
            cursor.close()

    def update_order_status(
        self,
        client_order_id: str,
        status: OrderStatus,
        executed_qty: float = 0.0,
        avg_price: float = 0.0,
        fee_paid: float = 0.0,
        exchange_order_id: Optional[str] = None,
    ) -> None:
        """Update status and fill details for an order."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            if exchange_order_id:
                cursor.execute("""
                    UPDATE orders
                    SET status = ?, executed_qty = ?, avg_price = ?, fee_paid = ?,
                        exchange_order_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE client_order_id = ?;
                """, (status.value, executed_qty, avg_price, fee_paid, exchange_order_id, client_order_id))
            else:
                cursor.execute("""
                    UPDATE orders
                    SET status = ?, executed_qty = ?, avg_price = ?, fee_paid = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE client_order_id = ?;
                """, (status.value, executed_qty, avg_price, fee_paid, client_order_id))
            cursor.close()

    def get_order(self, client_order_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single order by client_order_id."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE client_order_id = ?;", (client_order_id,))
            row = cursor.fetchone()
            cursor.close()
            return dict(row) if row else None

    def get_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent orders."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM orders ORDER BY timestamp DESC LIMIT ?;", (limit,))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

    # --- Position Operations ---

    def save_position(self, pos: PositionModel) -> int:
        """Open or update active position."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO positions (
                    symbol, side, entry_price, current_price, quantity,
                    stop_loss, take_profit, unrealized_pnl, pnl_percent, status, opened_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?);
            """, (
                pos.symbol,
                pos.side.value,
                pos.entry_price,
                pos.current_price,
                pos.quantity,
                pos.stop_loss,
                pos.take_profit,
                pos.unrealized_pnl,
                pos.pnl_percent,
                pos.timestamp,
            ))
            pos_id = cursor.lastrowid or 0
            cursor.close()
            return pos_id

    def update_position_mark(self, symbol: str, current_price: float, unrealized_pnl: float, pnl_percent: float) -> None:
        """Update mark price and unrealized PnL for active positions."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("""
                UPDATE positions
                SET current_price = ?, unrealized_pnl = ?, pnl_percent = ?
                WHERE symbol = ? AND status = 'OPEN';
            """, (current_price, unrealized_pnl, pnl_percent, symbol))
            cursor.close()

    def close_position(
        self,
        symbol: str,
        close_price: float,
        pnl_usd: float,
        pnl_percent: float,
        fees_usd: float = 0.0,
        exit_reason: str = "TAKE_PROFIT",
        timestamp: int = 0,
    ) -> None:
        """Close open position and record corresponding trade."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")
            try:
                # Find open position
                cursor.execute("SELECT * FROM positions WHERE symbol = ? AND status = 'OPEN' LIMIT 1;", (symbol,))
                row = cursor.fetchone()
                if row:
                    pos_id = row["id"]
                    cursor.execute("""
                        UPDATE positions
                        SET status = 'CLOSED', closed_at = ?, close_price = ?
                        WHERE id = ?;
                    """, (timestamp, close_price, pos_id))

                    trade_id = f"TRD-{symbol}-{timestamp}"
                    cursor.execute("""
                        INSERT INTO trades (
                            trade_id, client_order_id, symbol, side, entry_price,
                            exit_price, quantity, pnl_usd, pnl_percent, fees_usd,
                            exit_reason, opened_at, closed_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        trade_id,
                        f"POS-{pos_id}",
                        symbol,
                        row["side"],
                        row["entry_price"],
                        close_price,
                        row["quantity"],
                        pnl_usd,
                        pnl_percent,
                        fees_usd,
                        exit_reason,
                        row["opened_at"],
                        timestamp,
                    ))
                cursor.execute("COMMIT;")
            except Exception as e:
                cursor.execute("ROLLBACK;")
                logger.error("Failed to close position: %s", str(e))
                raise
            finally:
                cursor.close()

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Return all open positions."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE status = 'OPEN' ORDER BY opened_at DESC;")
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

    def get_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return historical closed trades."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY closed_at DESC LIMIT ?;", (limit,))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

    def get_daily_pnl_usd(self, start_timestamp: int) -> float:
        """Calculate realized PnL since start of day timestamp."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(pnl_usd), 0.0) as daily_pnl FROM trades WHERE closed_at >= ?;",
                (start_timestamp,),
            )
            row = cursor.fetchone()
            cursor.close()
            return float(row["daily_pnl"]) if row else 0.0

    # --- Risk & System Events ---

    def record_risk_event(
        self,
        event_type: str,
        description: str,
        value: Optional[float] = None,
        threshold: Optional[float] = None,
        timestamp: int = 0,
    ) -> None:
        """Record risk event (kill switch, circuit breaker, daily loss)."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO risk_events (event_type, description, value, threshold, timestamp)
                VALUES (?, ?, ?, ?, ?);
            """, (event_type, description, value, threshold, timestamp))
            cursor.close()

    def get_risk_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch latest risk events."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM risk_events ORDER BY timestamp DESC LIMIT ?;", (limit,))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

    def record_system_event(self, event_type: str, message: str, level: str = "INFO", timestamp: int = 0) -> None:
        """Record system log event."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO system_events (event_type, message, level, timestamp)
                VALUES (?, ?, ?, ?);
            """, (event_type, message, level, timestamp))
            cursor.close()

    def get_system_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch latest system events."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM system_events ORDER BY timestamp DESC LIMIT ?;", (limit,))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

    def record_market_event(
        self,
        symbol: str,
        timeframe: str,
        event_type: str,
        price: float,
        details: Optional[str] = None,
        timestamp: int = 0,
    ) -> None:
        """Record SMC market event (BOS, MSS, Sweep, FVG, OB)."""
        with self._lock:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO market_events (symbol, timeframe, event_type, price, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (symbol, timeframe, event_type, price, details, timestamp))
            cursor.close()

    def close(self) -> None:
        """Gracefully close database connection."""
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None
                logger.info("SQLite database connection closed.")
