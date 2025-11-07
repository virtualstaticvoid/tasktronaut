from types import SimpleNamespace
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    Optional,
    Protocol,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeAlias,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from .builder import Builder
    from .process import ProcessDefinition
    from .context import Context

UndecoratedTaskMethod: TypeAlias = Callable[..., None]


class DecoratedTaskMethod(Protocol):  # pylint: disable=too-few-public-methods
    __name__: str
    description: Optional[str]

    def __call__(
        self, *args, context: Optional["Context"] = None, **kwargs
    ):  # pragma: no cover
        pass


TaskMethod: TypeAlias = Union[UndecoratedTaskMethod, DecoratedTaskMethod]

Description: TypeAlias = Optional[str]

TaskArgs: TypeAlias = Union[Dict[str, Any], Tuple[Dict[str, Any], Description]]

ForEachReturn: TypeAlias = Iterator[TaskArgs]

ForEachMethod: TypeAlias = Callable[..., ForEachReturn]

TransformMethod: TypeAlias = Callable[..., TaskArgs]

BuilderIterator: TypeAlias = Iterator["Builder"]

ProcessDefinitionType: TypeAlias = Type["ProcessDefinition"]

Options: TypeAlias = Union[SimpleNamespace, Dict[str, Any]]

Value = TypeVar("Value")
