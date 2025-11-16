from typing import Any, Callable, Dict, Iterable, Iterator, Optional, TypeVar

_T = TypeVar("_T")

class Environment:
    context: Dict[str, Any]
    user: Any

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    def __getitem__(self, model_name: str) -> Any: ...

    def ref(self, xmlid: str, raise_if_not_found: bool = True) -> Any: ...


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


class _FieldCallable:
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


class _DateField(_FieldCallable):
    @staticmethod
    def context_today(*args: Any, **kwargs: Any) -> Any: ...

    @staticmethod
    def today(*args: Any, **kwargs: Any) -> Any: ...

    @staticmethod
    def to_string(*args: Any, **kwargs: Any) -> str: ...

    @staticmethod
    def to_date(*args: Any, **kwargs: Any) -> Any: ...


class _DatetimeField(_FieldCallable):
    @staticmethod
    def now(*args: Any, **kwargs: Any) -> Any: ...

    @staticmethod
    def to_string(*args: Any, **kwargs: Any) -> str: ...


class fields:
    Char = _FieldCallable()
    Text = _FieldCallable()
    Boolean = _FieldCallable()
    Integer = _FieldCallable()
    Float = _FieldCallable()
    Monetary = _FieldCallable()
    Date = _DateField()
    Datetime = _DatetimeField()
    Many2one = _FieldCallable()
    Many2many = _FieldCallable()
    One2many = _FieldCallable()
    Selection = _FieldCallable()
    Html = _FieldCallable()
    Binary = _FieldCallable()
    Json = _FieldCallable()


class _RecordIterator(Iterator["ModelBase"]):
    def __next__(self) -> "ModelBase": ...


class ModelBase(Iterable[Any]):
    env: Environment
    _context: Dict[str, Any]
    _name: str
    id: int
    create_date: Any
    write_date: Any
    create_uid: Any
    write_uid: Any

    def __iter__(self) -> Iterator[Any]: ...

    def __len__(self) -> int: ...

    def __getitem__(self, index: int) -> Any: ...

    def mapped(self, *args: Any, **kwargs: Any) -> Any: ...

    def filtered(self, *args: Any, **kwargs: Any) -> Any: ...

    def create(self, *args: Any, **kwargs: Any) -> Any: ...

    def write(self, vals: Any) -> bool: ...

    def copy(self, default: Optional[Dict[str, Any]] = None) -> Any: ...

    def unlink(self) -> bool: ...

    def ensure_one(self) -> None: ...

    def sudo(self) -> Any: ...

    def browse(self, ids: Any) -> Any: ...

    def search(self, domain: Any, limit: Optional[int] = None) -> Any: ...

    def search_count(self, domain: Any) -> int: ...

    def read(self, fields: Any) -> Any: ...

    def with_context(self, *args: Any, **kwargs: Any) -> Any: ...

    def action_confirm(self, *args: Any, **kwargs: Any) -> Any: ...


class models:
    class Model(ModelBase):
        ...

    class TransientModel(ModelBase): ...

    class AbstractModel(ModelBase): ...


def _(message: str, **kwargs: Any) -> str: ...
