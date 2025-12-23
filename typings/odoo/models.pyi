from typing import Any, Sequence

class Model:
    _name: str
    _description: str
    _inherit: Sequence[str]

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...
