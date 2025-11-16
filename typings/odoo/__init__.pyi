from typing import Any, Callable, TypeVar, Optional

_T = TypeVar("_T")

class Environment:
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

class api:
    @staticmethod
    def model(method: _T) -> _T: ...

    @staticmethod
    def depends(*args: Any, **kwargs: Any) -> Callable[[ _T ], _T]: ...

    @staticmethod
    def constrains(*args: Any, **kwargs: Any) -> Callable[[ _T ], _T]: ...

    @staticmethod
    def onchange(*args: Any, **kwargs: Any) -> Callable[[ _T ], _T]: ...

    @staticmethod
    def model_create_multi(method: _T) -> _T: ...

class fields:
    Char = Any
    Text = Any
    Boolean = Any
    Integer = Any
    Float = Any
    Monetary = Any
    Date = Any
    Datetime = Any
    Many2one = Any
    Many2many = Any
    One2many = Any
    Selection = Any
    Html = Any
    Binary = Any
    Json = Any

class models:
    class Model:
        env: Environment
        id: int
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    class TransientModel(Model): ...

    class AbstractModel(Model): ...

_ = lambda message, **kwargs: message
