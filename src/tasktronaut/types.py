"""
Type definitions and protocols.
"""

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
"""
Type alias for an undecorated task method.

Represents a callable that accepts any arguments and keyword arguments,
and returns None. These are regular methods that can be registered as
tasks without explicit decoration.

:type: Callable[..., None]
"""


class DecoratedTaskMethod(Protocol):  # pylint: disable=too-few-public-methods
    """
    Protocol for a task method decorated with the ``@task`` decorator.

    Defines the interface that decorated task methods must implement. Decorated
    tasks have metadata attributes and can optionally accept a ``Context`` parameter.

    :ivar __name__: The name of the task method.
    :type __name__: str
    :ivar description: An optional human-readable description of the task.
    :type description: Optional[str]
    """

    __name__: str
    description: Optional[str]

    def __call__(
        self, *args, context: Optional["Context"] = None, **kwargs
    ):  # pragma: no cover
        """
        Task method signature.

        :param args: Positional arguments to pass to the task.
        :type args: Any
        :param context: An optional execution context for the task.
        :type context: Optional[Context]
        :param kwargs: Keyword arguments to pass to the task.
        :type kwargs: Dict[str, Any]
        """


TaskMethod: TypeAlias = Union[UndecoratedTaskMethod, DecoratedTaskMethod]
"""
Type alias for any task method.

Represents either a decorated or undecorated task method. This is the primary
type used when registering methods as tasks with a builder.

:type: Union[UndecoratedTaskMethod, DecoratedTaskMethod]
"""

Description: TypeAlias = Optional[str]
"""
Type alias for an optional task or item description.

Used to provide human-readable descriptions for tasks, items in iterations,
or other process elements.

:type: Optional[str]
"""

TaskArgs: TypeAlias = Union[Dict[str, Any], Tuple[Dict[str, Any], Description]]
"""
Type alias for task arguments.

Represents arguments passed to a task, which can be either a dictionary
of arguments or a tuple containing a dictionary of arguments and an
optional description string.

:type: Union[Dict[str, Any], Tuple[Dict[str, Any], Description]]
"""

ForEachReturn: TypeAlias = Iterator[TaskArgs]
"""
Type alias for the return type of the ``each`` method.

Represents an iterator that yields task arguments. Used in the ``each``
pattern to iterate over a collection of items, yielding arguments for
each iteration.

:type: Iterator[TaskArgs]
"""

ForEachMethod: TypeAlias = Callable[..., ForEachReturn]
"""
Type alias for the ``each`` method.

Represents a callable that accepts any arguments and keyword arguments,
and returns an iterator of task arguments. Used to define iteration
methods for the ``each`` pattern.

:type: Callable[..., ForEachReturn]
"""

TransformMethod: TypeAlias = Callable[..., TaskArgs]
"""
Type alias for a transformation method.

Represents a callable that accepts any arguments and keyword arguments,
and returns task arguments. Used to define transformation methods for
the ``transform`` pattern to modify arguments before task execution.

:type: Callable[..., TaskArgs]
"""

BuilderIterator: TypeAlias = Iterator["Builder"]
"""
Type alias for an iterator of ``Builder`` instances.

Represents an iterator that yields Builder objects, typically used in
control flow patterns such as sequential, concurrent, or each blocks.

:type: Iterator[Builder]
"""

ProcessDefinitionType: TypeAlias = Type["ProcessDefinition"]
"""
Type alias for a ``ProcessDefinition`` class.

Represents a class type that inherits from ProcessDefinition, used when
specifying sub-processes or other process references.

:type: Type[ProcessDefinition]
"""

Options: TypeAlias = Union[SimpleNamespace, Dict[str, Any]]
"""
Type alias for process options.

Represents configuration options that can be passed to a process, either
as a ``SimpleNamespace`` object or as a dictionary.

:type: Union[SimpleNamespace, Dict[str, Any]]
"""

Value = TypeVar("Value")
"""
Generic type variable for generic operations.

Used in generic function or class definitions where a type parameter
is needed to represent any arbitrary type.

:type: TypeVar
"""
