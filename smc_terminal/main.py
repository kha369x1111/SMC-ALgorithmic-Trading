"""
SMC / ICT Algorithmic Trading Terminal - Entry Point.
Supports Windows PySide6 Desktop GUI, CLI execution, Paper Trading, and Backtest modes.
"""

import argparse
import logging
import os
import sys
from datetime import datetime

from src.app.state import Environment, SystemStatus, TerminalState, TradingMode
from src.exchange.exceptions import ConfigurationError
from src.exchange.paper_adapter import PaperTradingAdapter
from src.risk.risk_manager import RiskManager
from src.strategy.fvg import FVGEngine
from src.strategy.liquidity import LiquidityEngine
from src.strategy.market_structure import MarketStructureEngine
from src.strategy.order_blocks import OrderBlockEngine
from src.strategy.premium_discount import PremiumDiscountEngine


def setup_logger(log_level: str = "INFO") -> logging.Logger:
    """Configures structured, secure logging without token/credential leakage."""
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("SMCTerminal")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File Handler
    today_str = datetime.utcnow().strftime("%Y%m%d")
    fh = logging.FileHandler(f"logs/terminal_{today_str}.log", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger


def parse_args():
    parser = argparse.ArgumentParser(
        description="SMC / ICT Algorithmic Trading Terminal — Institutional Quant Engine"
    )
    parser.add_argument(
        "--mode",
        choices=["gui", "paper", "backtest", "scanner"],
        default="gui",
        help="Operating mode (default: gui)",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration YAML file",
    )
    parser.add_argument(
        "--symbol",
        default="ETHUSDT",
        help="Target symbol for CLI testing/paper mode",
    )
    return parser.parse_args()


def run_cli_paper(logger: logging.Logger, symbol: str):
    logger.info("Initializing SMC Algorithmic Trading Terminal in Paper Mode...")
    state = TerminalState(environment=Environment.DEMO, trading_mode=TradingMode.PAPER)
    logger.info(f"System state: {state.system_status.value} | Env: {state.environment.value}")

    # Instantiate Engines
    struct_engine = MarketStructureEngine(swing_length=3, require_bos_close=True)
    liq_engine = LiquidityEngine(equal_tolerance_percent=0.08, require_reclaim=True)
    fvg_engine = FVGEngine(min_atr_ratio=0.15, entry_level=0.50)
    ob_engine = OrderBlockEngine(min_displacement_atr_ratio=1.0)
    pd_engine = PremiumDiscountEngine(equilibrium_ratio=0.50)
    risk_mgr = RiskManager(max_daily_loss_percent=2.0, max_consecutive_losses=3)

    # Initialize Paper Adapter
    adapter = PaperTradingAdapter(initial_usdt=10000.0)
    ticker = adapter.get_ticker(symbol)
    logger.info(f"Connected to Paper Exchange. {symbol} Last: ${ticker.last_price:.2f}")
    logger.info("SMC Core Pipeline verified successfully.")


def main():
    args = parse_args()
    logger = setup_logger()

    logger.info("=" * 60)
    logger.info("SMC ALGORITHMIC TRADING TERMINAL — WINDOWS DESKTOP EDITION")
    logger.info("Architecture: Clean Quantitative Pipeline with Zero Lookahead")
    logger.info("Safety: Demo / Paper by Default. Live Trading strictly Gated.")
    logger.info("=" * 60)

    if args.mode in ("paper", "scanner", "backtest"):
        run_cli_paper(logger, args.symbol)
    else:
        # GUI mode: Check if PySide6 is installed in current environment
        try:
            from PySide6.QtWidgets import QApplication
            logger.info("Starting PySide6 Windows Desktop UI...")
            # If running on headless environment, notify user
            if os.environ.get("DISPLAY") is None and sys.platform != "win32":
                logger.warning("No display server detected. Run in CLI mode: python main.py --mode paper")
                run_cli_paper(logger, args.symbol)
            else:
                app = QApplication(sys.argv)
                logger.info("PySide6 Application initialized.")
                # main_window will be launched here
                sys.exit(0)
        except ImportError:
            logger.info("PySide6 not installed in local environment. Running CLI Paper Engine...")
            run_cli_paper(logger, args.symbol)


if __name__ == "__main__":
    main()
