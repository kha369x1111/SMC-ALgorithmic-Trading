"""
SMC Algorithmic Trading Terminal - System State & Safety Enums.
Defines execution modes, environment gating, and safety states.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class Environment(str, Enum):
    """Trading environments. Live trading is strictly isolated."""
    DEMO = "demo"
    TESTNET = "testnet"
    LIVE = "live"


class TradingMode(str, Enum):
    """Trading execution mode."""
    PAPER = "paper"
    EXECUTION = "execution"


class SystemStatus(str, Enum):
    """Overall operational health of the trading system."""
    ONLINE = "ONLINE"
    HALTED = "HALTED"
    CIRCUIT_BROKEN = "CIRCUIT_BROKEN"
    DATA_STALE = "DATA_STALE"
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"


class MarketType(str, Enum):
    """Supported market segments."""
    SPOT = "spot"
    FUTURES = "futures"


@dataclass
class TerminalState:
    """Current dynamic state of the SMC Terminal runtime."""
    environment: Environment = Environment.DEMO
    trading_mode: TradingMode = TradingMode.PAPER
    system_status: SystemStatus = SystemStatus.ONLINE
    market_type: MarketType = MarketType.SPOT
    is_live_confirmed: bool = False
    kill_switch_engaged: bool = False
    circuit_breaker_reason: Optional[str] = None
    daily_pnl_usd: float = 0.0
    daily_pnl_percent: float = 0.0
    consecutive_losses: int = 0
    open_positions_count: int = 0
    total_equity_usd: float = 10000.0
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)

    def can_open_orders(self) -> tuple[bool, str]:
        """Verify whether new orders can be initiated under current safety state."""
        if self.kill_switch_engaged:
            return False, "Emergency Kill Switch is engaged."
        if self.system_status == SystemStatus.HALTED:
            return False, "System is manually halted."
        if self.system_status == SystemStatus.CIRCUIT_BROKEN:
            return False, f"Circuit Breaker active: {self.circuit_breaker_reason}"
        if self.system_status == SystemStatus.DATA_STALE:
            return False, "Market data is stale. Order generation blocked."
        if self.environment == Environment.LIVE and not self.is_live_confirmed:
            return False, "Live environment selected but unconfirmed by user."
        return True, "Trading allowed."
