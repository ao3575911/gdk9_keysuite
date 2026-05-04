from __future__ import annotations


class KeySuiteError(Exception):
    """Base class for KeySuite-specific failures."""


class ConfigurationError(KeySuiteError):
    """Raised when configuration cannot be loaded or coerced."""


class GrammarVersionError(KeySuiteError):
    """Raised when a grammar is not compatible with the runtime."""


class TokenValidationError(KeySuiteError):
    """Raised when an input token is malformed or unsupported."""


class MacroExpansionError(KeySuiteError):
    """Raised when macro expansion fails or recurses unsafely."""


class RuntimeLimitError(KeySuiteError):
    """Raised when runtime safety limits are exceeded."""


class HistoryError(KeySuiteError):
    """Raised when undo/redo history cannot satisfy a request."""


class SessionNotFoundError(KeySuiteError):
    """Raised when a requested session does not exist."""

