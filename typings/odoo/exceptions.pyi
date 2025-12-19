# Odoo Exceptions Stubs for Pylance
from typing import Any, Optional

class UserError(Exception):
    """User-facing error that should be displayed to the user."""
    def __init__(self, message: str) -> None: ...

class ValidationError(Exception):
    """Validation error for constraints and field validation."""
    def __init__(self, message: str) -> None: ...

class AccessError(Exception):
    """Access rights error."""
    def __init__(self, message: str) -> None: ...

class MissingError(Exception):
    """Record does not exist or has been deleted."""
    def __init__(self, message: str) -> None: ...

class RedirectWarning(Exception):
    """Warning with a redirect button."""
    def __init__(self, message: str, action: int, button_text: str, additional_context: Optional[dict] = None) -> None: ...

class AccessDenied(Exception):
    """Login/password error."""
    def __init__(self, message: str = ...) -> None: ...

class CacheMiss(Exception):
    """Cache miss error."""
    def __init__(self, record: Any, field: Any) -> None: ...
