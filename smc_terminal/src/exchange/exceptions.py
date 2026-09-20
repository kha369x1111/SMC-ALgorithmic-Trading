"""
SMC Algorithmic Trading Terminal - Explicit Exception Hierarchy.
Strictly prohibits silent exception suppression.
"""


class TerminalException(Exception):
    """Base exception for all SMC Terminal errors."""
    def __init__(self, message: str, code: str = "ERR_INTERNAL", details: dict = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class DataError(TerminalException):
    """Raised when market data is corrupt, missing, out of sequence, or stale."""
    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(message, code="ERR_DATA_INVALID", details=details)


class ExchangeError(TerminalException):
    """Raised when communication or parsing with exchange fails."""
    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(message, code="ERR_EXCHANGE_COMM", details=details)


class OrderError(TerminalException):
    """Raised when order parameters violate symbol filters or exchange constraints."""
    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(message, code="ERR_ORDER_REJECTED", details=details)


class RiskError(TerminalException):
    """Raised when a signal or order violates strict risk limits."""
    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(message, code="ERR_RISK_BREACH", details=details)


class ConfigurationError(TerminalException):
    """Raised when config.yaml has invalid parameters or missing keys."""
    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(message, code="ERR_CONFIG_INVALID", details=details)


class AuthenticationError(TerminalException):
    """Raised when exchange credentials are invalid or missing."""
    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(message, code="ERR_AUTH_FAILED", details=details)


class ExecutionError(TerminalException):
    """Raised when order dispatch, reconciliation, or cancellation fails."""
    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(message, code="ERR_EXECUTION_FAILED", details=details)


class CircuitBreakerError(TerminalException):
    """Raised when system protection triggers an operational trading lock."""
    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(message, code="ERR_CIRCUIT_BREAKER", details=details)
