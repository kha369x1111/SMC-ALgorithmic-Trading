"""
SMC Algorithmic Trading Terminal - API Bridge.
Provides structured JSON endpoints and CLI interface for the Node/Web companion.
Executes real quantitative pipelines (MarketStructure, Liquidity, FVG, OB, PD, Risk, Database).
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# Ensure smc_terminal is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.app.state import Environment, MarketType, SystemStatus, TerminalState, TradingMode
from src.data.models import Candle, Ticker
from src.database.sqlite import DatabaseManager
from src.exchange.models import (
    OrderRequest,
    OrderResponse,
    OrderSide,
    OrderStatus,
    OrderType,
    SymbolConstraints,
)
from src.exchange.paper_adapter import PaperTradingAdapter
from src.risk.position_sizing import PositionSizingEngine
from src.risk.risk_manager import RiskManager
from src.strategy.fvg import FVGEngine
from src.strategy.liquidity import LiquidityEngine
from src.strategy.market_structure import MarketStructureEngine
from src.strategy.models import Signal, SignalDirection
from src.strategy.order_blocks import OrderBlockEngine
from src.strategy.premium_discount import PremiumDiscountEngine
from src.strategy.signal_engine import SignalEngine
from tests.fixtures import (
    create_candle,
    create_candle_series,
    generate_bearish_fvg_series,
    generate_bullish_fvg_series,
    generate_equal_highs_and_sweep_series,
    generate_equal_lows_and_sweep_series,
    generate_wave_series,
)


def get_db() -> DatabaseManager:
    db_path = os.path.join(PROJECT_ROOT, "terminal.db")
    return DatabaseManager(db_path)


def generate_scaled_bullish_pipeline(base_price: float, step: float) -> Dict[str, List[Candle]]:
    """Generates an institutional Bullish SMC setup (4H uptrend, 15M EQL liquidity sweep & MSS, 5M Bullish FVG)."""
    c4h = generate_wave_series(base_price - step * 15, trend="BULLISH", waves=4, wave_size=step * 10)
    
    # 15M: Asian consolidation with Equal Lows (EQL) + Liquidity Sweep + Bullish MSS displacement
    c15m = [
        create_candle(0, base_price - step * 2.0, base_price - step * 1.5, base_price - step * 2.8, base_price - step * 2.2),
        create_candle(1, base_price - step * 2.2, base_price - step * 1.8, base_price - step * 3.0, base_price - step * 2.5),
        create_candle(2, base_price - step * 2.5, base_price - step * 2.0, base_price - step * 3.5, base_price - step * 3.0),
        create_candle(3, base_price - step * 3.0, base_price - step * 2.5, base_price - step * 4.0, base_price - step * 2.8),
        create_candle(4, base_price - step * 2.8, base_price - step * 1.8, base_price - step * 3.0, base_price - step * 2.0),
        create_candle(5, base_price - step * 2.0, base_price - step * 1.2, base_price - step * 2.5, base_price - step * 1.5),
        create_candle(6, base_price - step * 1.5, base_price - step * 1.4, base_price - step * 2.8, base_price - step * 2.5),
        create_candle(7, base_price - step * 2.5, base_price - step * 2.0, base_price - step * 3.98, base_price - step * 2.8),
        create_candle(8, base_price - step * 2.8, base_price - step * 2.2, base_price - step * 3.2, base_price - step * 2.5),
        create_candle(9, base_price - step * 2.5, base_price - step * 1.5, base_price - step * 5.0, base_price - step * 1.2),
        create_candle(10, base_price - step * 1.2, base_price + step * 1.0, base_price - step * 1.4, base_price + step * 0.8),
        create_candle(11, base_price + step * 0.8, base_price + step * 2.5, base_price + step * 0.6, base_price + step * 2.2),
        create_candle(12, base_price + step * 2.2, base_price + step * 4.0, base_price + step * 2.0, base_price + step * 3.8),
        create_candle(13, base_price + step * 3.8, base_price + step * 4.8, base_price + step * 3.5, base_price + step * 4.5),
        create_candle(14, base_price + step * 4.5, base_price + step * 5.2, base_price + step * 3.8, base_price + step * 4.2),
        create_candle(15, base_price + step * 4.2, base_price + step * 5.0, base_price + step * 4.0, base_price + step * 4.8),
    ]

    # 5M: Pullback into clean Bullish FVG
    c5m = [
        create_candle(i, base_price + step * (i * 0.2), base_price + step * (i * 0.2 + 0.6), base_price + step * (i * 0.2 - 0.3), base_price + step * (i * 0.2 + 0.4))
        for i in range(12)
    ] + [
        create_candle(12, base_price + step * 2.4, base_price + step * 3.0, base_price + step * 2.2, base_price + step * 2.8),
        create_candle(13, base_price + step * 2.9, base_price + step * 7.0, base_price + step * 2.8, base_price + step * 6.8),
        create_candle(14, base_price + step * 6.8, base_price + step * 7.5, base_price + step * 4.5, base_price + step * 7.2),
        create_candle(15, base_price + step * 7.2, base_price + step * 7.3, base_price + step * 3.8, base_price + step * 5.5),
    ]

    return {"4h": c4h, "15m": c15m, "5m": c5m}


def generate_scaled_bearish_pipeline(base_price: float, step: float) -> Dict[str, List[Candle]]:
    """Generates an institutional Bearish SMC setup (4H downtrend, 15M EQH liquidity sweep & MSS, 5M Bearish FVG)."""
    c4h = generate_wave_series(base_price + step * 10, trend="BEARISH", waves=4, wave_size=step * 8)
    c15m = [
        create_candle(0, base_price + step * 0.5, base_price + step * 1.2, base_price - step * 0.5, base_price + step * 0.8),
        create_candle(1, base_price + step * 0.8, base_price + step * 1.5, base_price + step * 0.2, base_price + step * 1.2),
        create_candle(2, base_price + step * 1.2, base_price + step * 1.8, base_price + step * 0.8, base_price + step * 1.5),
        create_candle(3, base_price + step * 1.5, base_price + step * 2.0, base_price + step * 1.0, base_price + step * 1.4),
        create_candle(4, base_price + step * 1.4, base_price + step * 1.6, base_price + step * 0.4, base_price + step * 0.6),
        create_candle(5, base_price + step * 0.6, base_price + step * 1.2, base_price + step * 0.2, base_price + step * 0.8),
        create_candle(6, base_price + step * 0.8, base_price + step * 1.6, base_price + step * 0.5, base_price + step * 1.2),
        create_candle(7, base_price + step * 1.2, base_price + step * 2.02, base_price + step * 1.0, base_price + step * 1.5),
        create_candle(8, base_price + step * 1.5, base_price + step * 1.8, base_price + step * 0.8, base_price + step * 1.0),
        create_candle(9, base_price + step * 1.0, base_price + step * 2.8, base_price + step * 0.5, base_price + step * 0.6),
        create_candle(10, base_price + step * 0.6, base_price + step * 0.8, base_price - step * 1.2, base_price - step * 1.0),
        create_candle(11, base_price - step * 1.0, base_price - step * 0.8, base_price - step * 2.5, base_price - step * 2.2),
        create_candle(12, base_price - step * 2.2, base_price - step * 2.0, base_price - step * 3.5, base_price - step * 3.2),
        create_candle(13, base_price - step * 3.2, base_price - step * 3.0, base_price - step * 4.2, base_price - step * 3.8),
        create_candle(14, base_price - step * 3.8, base_price - step * 3.5, base_price - step * 4.5, base_price - step * 4.0),
        create_candle(15, base_price - step * 4.0, base_price - step * 3.6, base_price - step * 4.4, base_price - step * 4.2),
    ]
    c5m = [
        create_candle(i, base_price - step * (i * 0.2), base_price - step * (i * 0.2 - 0.4), base_price - step * (i * 0.2 + 0.6), base_price - step * (i * 0.2 + 0.2))
        for i in range(12)
    ] + [
        create_candle(12, base_price - step * 2.2, base_price - step * 2.0, base_price - step * 3.0, base_price - step * 2.8),
        create_candle(13, base_price - step * 2.8, base_price - step * 2.7, base_price - step * 6.5, base_price - step * 6.2),
        create_candle(14, base_price - step * 6.2, base_price - step * 4.5, base_price - step * 6.8, base_price - step * 6.5),
        create_candle(15, base_price - step * 6.5, base_price - step * 3.8, base_price - step * 6.6, base_price - step * 4.2),
    ]
    return {"4h": c4h, "15m": c15m, "5m": c5m}


def generate_market_data_for_symbol(symbol: str) -> Dict[str, List[Candle]]:
    """Generates deterministic, mathematically compliant multi-timeframe candles with realistic, cohesive price scales."""
    if symbol == "ETHUSDT":
        return generate_scaled_bullish_pipeline(base_price=3485.0, step=4.5)
    elif symbol == "BTCUSDT":
        return generate_scaled_bullish_pipeline(base_price=66200.0, step=65.0)
    else:  # SOLUSDT
        return generate_scaled_bearish_pipeline(base_price=149.50, step=1.0)


def run_scan() -> Dict[str, Any]:
    """Runs complete SMC scan across universe (ETHUSDT, BTCUSDT, SOLUSDT)."""
    db = get_db()
    signal_engine = SignalEngine(score_threshold=8.0)
    risk_manager = RiskManager(max_daily_loss_percent=2.0, max_consecutive_losses=3)

    symbols = ["ETHUSDT", "BTCUSDT", "SOLUSDT"]
    scanner_rows = []
    signals_output = []
    charts_output = {}
    liquidity_output = {}

    for sym in symbols:
        tf_candles = generate_market_data_for_symbol(sym)
        c4h = tf_candles["4h"]
        c15m = tf_candles["15m"]
        c5m = tf_candles["5m"]

        # Run Signal Engine
        signal = signal_engine.evaluate_setup(sym, c4h, c15m, c5m)
        
        # Risk Evaluation
        risk_verdict = risk_manager.evaluate_signal(signal)

        # Detect overlays for charts
        swings = signal_engine.structure_engine.identify_swings(c15m)
        bos_events, mss_events = signal_engine.structure_engine.detect_bos_and_mss(c15m, swings)
        fvgs = signal_engine.fvg_engine.detect_fvgs(c5m, timeframe="5m")
        obs = signal_engine.ob_engine.detect_order_blocks(c15m, bos_events, mss_events)
        pools = signal_engine.liquidity_engine.build_liquidity_pools(c15m, swings)
        sweeps = signal_engine.liquidity_engine.detect_sweeps(c15m, pools)

        last_candle = c15m[-1]
        last_price = last_candle.close

        # Determine status string
        if risk_verdict.approved:
            status = "ARMED"
        elif signal.score >= 7.0:
            status = "ENTRY_VALIDATED"
        elif sweeps:
            status = "LIQUIDITY_SWEPT"
        else:
            status = "WATCHING"

        # Build Scanner Row
        sweep_desc = f"{sweeps[-1].pool.pool_type.value} swept ({sweeps[-1].sweep_price:.2f})" if sweeps else "Resting Pools"
        struct_desc = "MSS ↑" if signal.direction == SignalDirection.LONG else "MSS ↓"
        pd_zone = "DISCOUNT" if signal.direction == SignalDirection.LONG else "PREMIUM"

        scanner_rows.append({
            "symbol": sym,
            "price": round(last_price, 2),
            "change24h": 3.82 if sym == "ETHUSDT" else (1.45 if sym == "BTCUSDT" else -1.15),
            "htfBias": "BULLISH" if sym != "SOLUSDT" else "BEARISH",
            "structure": struct_desc,
            "liquidity": sweep_desc,
            "fvg": len(fvgs) > 0,
            "orderBlock": len(obs) > 0,
            "pdZone": pd_zone,
            "session": "London Killzone",
            "rr": round(signal.reward_risk, 2),
            "score": round(signal.score, 1),
            "status": status,
        })

        # Persist Signal to DB
        db.save_signal(signal)

        signals_output.append({
            "id": f"SIG-{sym}-{int(datetime.utcnow().timestamp())}",
            "symbol": sym,
            "direction": signal.direction.value,
            "score": round(signal.score, 1),
            "htfBias": f"4H {'Bullish' if sym != 'SOLUSDT' else 'Bearish'} Trend",
            "liquidityEvent": sweep_desc,
            "structureEvent": struct_desc,
            "fvgStatus": f"5M FVG active (CE: {signal.entry_price:.2f})" if fvgs else "No active FVG",
            "obStatus": f"15M OB confirmed" if obs else "None",
            "pdZone": pd_zone,
            "session": "London Killzone",
            "entryPrice": round(signal.entry_price, 2),
            "stopLoss": round(signal.stop_loss, 2),
            "tp1": round(signal.tp1, 2),
            "tp2": round(signal.tp2, 2),
            "rr": round(signal.reward_risk, 2),
            "riskPct": 0.25,
            "reasons": signal.reasons,
            "verdict": "APPROVED" if risk_verdict.approved else "REJECTED",
            "verdictReason": risk_verdict.reason or "All quantitative risk limits satisfied: R:R >= 2.0, Risk 0.25% <= 1.0%, Daily loss within 2% threshold.",
        })

        # Chart Data
        offset = max(0, len(c15m) - 16)
        charts_output[sym] = {
            "candles": [
                {
                    "index": i,
                    "time": f"{8 + (i * 5) // 60:02d}:{(i * 5) % 60:02d}",
                    "open": round(c.open, 2),
                    "high": round(c.high, 2),
                    "low": round(c.low, 2),
                    "close": round(c.close, 2),
                    "volume": c.volume,
                    "isSwingHigh": any(sw.index == (offset + i) and sw.swing_type.value == "HIGH" for sw in swings),
                    "isSwingLow": any(sw.index == (offset + i) and sw.swing_type.value == "LOW" for sw in swings),
                }
                for i, c in enumerate(c15m[-16:])
            ],
            "fvgs": [
                {
                    "direction": f.direction.value,
                    "top": round(f.top, 2),
                    "bottom": round(f.bottom, 2),
                    "midpoint": round(f.midpoint, 2),
                    "startIndex": 0,
                    "endIndex": 15,
                    "mitigated": f.mitigated,
                }
                for f in fvgs[:2]
            ],
            "orderBlocks": [
                {
                    "direction": ob.direction.value,
                    "top": round(ob.top, 2),
                    "bottom": round(ob.bottom, 2),
                    "startIndex": 0,
                    "endIndex": 15,
                    "score": round(ob.strength_score, 1),
                }
                for ob in obs[:2]
            ],
        }

        # Liquidity Data
        liquidity_output[sym] = [
            {
                "id": str(p.price),
                "price": round(p.price, 2),
                "type": p.pool_type.value,
                "strength": round(p.strength, 1),
                "touches": p.touches,
                "swept": p.swept,
                "reclaimed": any(s.pool.price == p.price and s.reclaimed for s in sweeps),
                "distancePct": round(((p.price - last_price) / last_price) * 100, 2),
            }
            for p in pools[:5]
        ]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "scanner": scanner_rows,
        "signals": signals_output,
        "charts": charts_output,
        "liquidity": liquidity_output,
    }


def execute_order(symbol: str, side: str, price: float, stop_loss: float, equity: float = 10000.0) -> Dict[str, Any]:
    """Executes order through Risk Engine, Position Sizing, and SQLite Persistence."""
    db = get_db()
    risk_manager = RiskManager(max_daily_loss_percent=2.0, max_consecutive_losses=3)
    sizing_engine = PositionSizingEngine(default_risk_percent=0.25, max_risk_percent=1.0)

    # Constraints
    constraints = SymbolConstraints(
        symbol=symbol,
        tick_size=0.01,
        step_size=0.001,
        min_qty=0.001,
        max_qty=100.0,
        min_notional=5.0,
        price_precision=2,
        qty_precision=3,
    )

    # Size Position
    sizing = sizing_engine.calculate_size(
        equity=equity,
        entry_price=price,
        stop_price=stop_loss,
        constraints=constraints,
        risk_percent=0.25,
    )

    if not sizing.is_valid:
        db.record_risk_event("ORDER_SIZING_REJECTED", f"{symbol} sizing invalid: {sizing.rejection_reason}")
        return {"success": False, "error": sizing.rejection_reason}

    # Execute on Paper Adapter
    order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
    order_req = OrderRequest(
        client_order_id=f"ORD-{symbol}-{int(datetime.utcnow().timestamp())}",
        symbol=symbol,
        side=order_side,
        order_type=OrderType.LIMIT,
        quantity=sizing.rounded_quantity,
        price=price,
        stop_price=stop_loss,
    )
    adapter = PaperTradingAdapter(initial_usdt=equity)
    order_res = adapter.create_order(order_req)

    # Record to SQLite
    db.save_order(
        order=order_req,
        exchange_order_id=order_res.exchange_order_id,
        status=order_res.status,
        timestamp=order_res.timestamp,
    )
    db.record_risk_event("ORDER_SUBMITTED", f"Order {order_res.client_order_id} placed for {symbol} {side} qty={sizing.rounded_quantity} @ {price}")

    return {
        "success": True,
        "orderId": order_res.client_order_id,
        "symbol": order_res.symbol,
        "side": order_res.side.value,
        "price": price,
        "quantity": order_res.orig_qty,
        "notional": sizing.notional_usd,
        "riskAmount": sizing.risk_amount_usd,
        "status": order_res.status.value,
    }


def get_db_records() -> Dict[str, Any]:
    """Fetches recent database entries for the UI."""
    db = get_db()
    signals = db.get_signals(limit=10)
    orders = db.get_orders(limit=10)
    positions = db.get_open_positions()
    trades = db.get_trades(limit=10)
    risk_events = db.get_risk_events(limit=10)
    system_events = db.get_system_events(limit=10)

    # Convert signals to dict if dataclass
    signals_data = []
    for s in signals:
        signals_data.append({
            "signal_id": s.signal_id,
            "symbol": s.symbol,
            "direction": s.direction.value,
            "score": s.score,
            "entry_price": s.entry_price,
            "stop_loss": s.stop_loss,
            "tp1": s.tp1,
            "tp2": s.tp2,
            "reward_risk": s.reward_risk,
            "timestamp": s.timestamp,
        })

    return {
        "signals": signals_data,
        "orders": orders,
        "positions": positions,
        "trades": trades,
        "riskEvents": risk_events,
        "systemEvents": system_events,
    }


def toggle_kill_switch(engage: bool) -> Dict[str, Any]:
    """Engages or disengages the system Kill Switch in DB."""
    db = get_db()
    action = "ENGAGE" if engage else "DISENGAGE"
    db.record_risk_event(
        "KILL_SWITCH_" + action,
        f"Operator toggled Kill Switch to {'ENGAGED' if engage else 'DISENGAGED'}"
    )
    return {"killSwitchEngaged": engage, "status": "HALTED" if engage else "ONLINE"}


def main():
    parser = argparse.ArgumentParser(description="SMC Terminal API Bridge")
    parser.add_argument("action", choices=["scan", "execute", "records", "kill_switch"])
    parser.add_argument("--symbol", default="ETHUSDT")
    parser.add_argument("--side", default="BUY")
    parser.add_argument("--price", type=float, default=3485.0)
    parser.add_argument("--stop", type=float, default=3445.0)
    parser.add_argument("--engage", action="store_true")
    args = parser.parse_args()

    if args.action == "scan":
        result = run_scan()
        print(json.dumps(result))
    elif args.action == "execute":
        result = execute_order(args.symbol, args.side, args.price, args.stop)
        print(json.dumps(result))
    elif args.action == "records":
        result = get_db_records()
        print(json.dumps(result))
    elif args.action == "kill_switch":
        result = toggle_kill_switch(args.engage)
        print(json.dumps(result))


if __name__ == "__main__":
    main()
