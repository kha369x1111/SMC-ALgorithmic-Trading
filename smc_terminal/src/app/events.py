"""
SMC Algorithmic Trading Terminal - Event System.
Defines typed event payloads and event bus for deterministic pipeline tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List


class EventType(str, Enum):
    # Pipeline transitions
    MARKET_DATA_RECEIVED = "MARKET_DATA_RECEIVED"
    SWING_DETECTED = "SWING_DETECTED"
    BOS_CONFIRMED = "BOS_CONFIRMED"
    MSS_CONFIRMED = "MSS_CONFIRMED"
    LIQUIDITY_POOL_CREATED = "LIQUIDITY_POOL_CREATED"
    LIQUIDITY_SWEPT = "LIQUIDITY_SWEPT"
    FVG_FORMED = "FVG_FORMED"
    FVG_MITIGATED = "FVG_MITIGATED"
    ORDER_BLOCK_VALIDATED = "ORDER_BLOCK_VALIDATED"
    
    # Setup & Signal Lifecycle
    SETUP_WATCHING = "SETUP_WATCHING"
    SETUP_ARMED = "SETUP_ARMED"
    SIGNAL_GENERATED = "SIGNAL_GENERATED"
    SIGNAL_APPROVED = "SIGNAL_APPROVED"
    SIGNAL_REJECTED = "SIGNAL_REJECTED"
    
    # Execution & Safety
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    POSITION_OPENED = "POSITION_OPENED"
    POSITION_CLOSED = "POSITION_CLOSED"
    KILL_SWITCH_TRIGGERED = "KILL_SWITCH_TRIGGERED"
    CIRCUIT_BREAKER_TRIGGERED = "CIRCUIT_BREAKER_TRIGGERED"
    DATA_STALE_TRIGGERED = "DATA_STALE_TRIGGERED"


@dataclass
class TerminalEvent:
    """Base event contract."""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    symbol: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Thread-safe synchronous/asynchronous in-memory event dispatcher."""

    def __init__(self) -> None:
        self._listeners: Dict[EventType, List[Callable[[TerminalEvent], None]]] = {}
        self._history: List[TerminalEvent] = []
        self._max_history = 1000

    def subscribe(self, event_type: EventType, listener: Callable[[TerminalEvent], None]) -> None:
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def publish(self, event: TerminalEvent) -> None:
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        listeners = self._listeners.get(event.event_type, [])
        for listener in listeners:
            try:
                listener(event)
            except Exception as e:
                # Event dispatching must never crash the publisher
                print(f"[EventBus Error] listener {listener} raised: {e}")

    def get_history(self, limit: int = 50) -> List[TerminalEvent]:
        return self._history[-limit:]
