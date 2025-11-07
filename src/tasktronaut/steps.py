from typing import Any, Dict, TYPE_CHECKING, Union

from .types import Description, TaskMethod

if TYPE_CHECKING:
    from .process import Process  # noqa


class Step:
    def __init__(
        self,
        func: TaskMethod,
        description: Description,
        kwargs: Dict[str, Any],
    ):
        self.func = func
        self.description = description
        self.kwargs = kwargs

    @property
    def is_process(self) -> bool:
        return False

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(func={self.func.__name__},kwargs={self.kwargs!r},)"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(func={self.func.__name__},kwargs={self.kwargs!r},)"


class Steps(list[Union[Step, "Process"]]):  # pragma: no cover
    pass
