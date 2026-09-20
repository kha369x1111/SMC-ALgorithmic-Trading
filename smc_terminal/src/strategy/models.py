"""
SMC Algorithmic Trading Terminal - Core Strategy Domain Models.
Defines formal entities for Market Structure, Liquidity, FVG, Order Blocks, and Signals.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class TrendDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGING = "RANGING"


class SwingType(str, Enum):
    SWING_HIGH = "SWING_HIGH"
    SWING_LOW = "SWING_LOW"


class StructureType(str, Enum):
    HH = "HH"  # Higher High
    HL = "HL"  # Higher Low
    LH = "LH"  # Lower High
    LL = "LL"  # Lower Low


@dataclass(frozen=True)
class SwingPoint:
    """Represents an identified structural pivot."""
    index: int
    timestamp: int
    price: float
    swing_type: SwingType
    confirmed_at_index: int  # Prevents lookahead: confirmed when right bars close


@dataclass
class BOS:
    """Break of Structure (trend continuation)."""
    direction: TrendDirection
    broken_swing: SwingPoint
    break_price: float
    break_candle_index: int
    confirmed_by_close: bool
    atr_at_break: float = 0.0


@dataclass
class MSS:
    """Market Structure Shift / CHoCH (trend change)."""
    direction: TrendDirection
    broken_swing: SwingPoint
    break_candle_index: int
    displacement_ratio: float
    confirmed_by_close: bool


class LiquidityType(str, Enum):
    BSL = "BSL"             # Buy Side Liquidity (Above Highs)
    SSL = "SSL"             # Sell Side Liquidity (Below Lows)
    EQH = "EQH"             # Equal Highs
    EQL = "EQL"             # Equal Lows
    PDH = "PDH"             # Previous Day High
    PDL = "PDL"             # Previous Day Low
    PWH = "PWH"             # Previous Week High
    PWL = "PWL"             # Previous Week Low
    ASIAN_HIGH = "ASIAN_H"   # Asian Session High
    ASIAN_LOW = "ASIAN_L"    # Asian Session Low


@dataclass
class LiquidityPool:
    """Identified resting liquidity resting above or below market price."""
    price: float
    timeframe: str
    pool_type: LiquidityType
    strength: float = 1.0
    created_at_index: int = 0
    swept: bool = False
    sweep_time: Optional[int] = None
    touches: int = 1
    reclaimed: bool = False


@dataclass
class LiquiditySweepEvent:
    """Occurs when price violates a liquidity pool and confirms reclaim/MSS."""
    pool: LiquidityPool
    sweep_price: float
    sweep_candle_index: int
    reclaimed: bool
    structure_shifted: bool
    confirmation_bars_used: int


class FVGDirection(str, Enum):
    BULLISH = "BULLISH"  # Low of bar 3 > High of bar 1
    BEARISH = "BEARISH"  # High of bar 3 < Low of bar 1


@dataclass
class FVGZone:
    """Fair Value Gap / Price Imbalance."""
    direction: FVGDirection
    top: float
    bottom: float
    timeframe: str
    candle_index: int  # Middle candle index
    atr_ratio: float
    mitigated: bool = False
    mitigated_at_index: Optional[int] = None

    @property
    def midpoint(self) -> float:
        """50% Consequent Encroachment (CE) entry level."""
        return (self.top + self.bottom) / 2.0

    @property
    def size(self) -> float:
        return self.top - self.bottom


@dataclass
class OrderBlockZone:
    """High-probability Order Block preceding displacement and structural break."""
    direction: TrendDirection  # Bullish OB (demand) or Bearish OB (supply)
    timeframe: str
    top: float
    bottom: float
    candle_index: int
    strength_score: float      # 0.0 to 100.0
    freshness: bool = True
    touches: int = 0
    mitigated: bool = False
    invalidated: bool = False
    associated_displacement: float = 0.0

    @property
    def midpoint(self) -> float:
        return (self.top + self.bottom) / 2.0


class PDZone(str, Enum):
    PREMIUM = "PREMIUM"
    DISCOUNT = "DISCOUNT"
    EQUILIBRIUM = "EQUILIBRIUM"


@dataclass
class PremiumDiscountState:
    """Dealing Range Valuation."""
    range_high: float
    range_low: float
    equilibrium: float  # 50%
    current_price: float
    current_zone: PDZone


class SetupLifecycleState(str, Enum):
    """Rigorous state tracking for SMC trade setups."""
    WATCHING = "WATCHING"
    LIQUIDITY_SWEPT = "LIQUIDITY_SWEPT"
    STRUCTURE_CONFIRMED = "STRUCTURE_CONFIRMED"
    SETUP_ARMED = "SETUP_ARMED"
    ENTRY_VALIDATED = "ENTRY_VALIDATED"
    RISK_VALIDATED = "RISK_VALIDATED"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    ORDER_FILLED = "ORDER_FILLED"
    POSITION_ACTIVE = "POSITION_ACTIVE"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class SignalDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Signal:
    """Complete, fully-explainable SMC Trading Signal."""
    signal_id: str
    timestamp: int
    symbol: str
    direction: SignalDirection
    score: float
    score_breakdown: Dict[str, float]
    htf_bias: TrendDirection
    liquidity_swept: bool
    mss_confirmed: bool
    fvg_present: bool
    ob_present: bool
    pd_zone: PDZone
    session_allowed: bool
    entry_price: float
    stop_loss: float
    tp1: float
    tp2: float
    reward_risk: float
    lifecycle: SetupLifecycleState
    reasons: List[str]
    rejection_reason: Optional[str] = None
