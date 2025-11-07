from typing import Callable, Optional, Union, cast, overload

from .types import DecoratedTaskMethod, Description, UndecoratedTaskMethod


@overload
def task(func: UndecoratedTaskMethod, /) -> DecoratedTaskMethod: ...


@overload
def task(
    *, description: Description = None
) -> Callable[[UndecoratedTaskMethod], DecoratedTaskMethod]: ...


def task(
    func: Optional[UndecoratedTaskMethod] = None,
    /,
    *,
    description: Description = None,
) -> Union[Callable[[UndecoratedTaskMethod], DecoratedTaskMethod], DecoratedTaskMethod]:
    def _wrapper(f: UndecoratedTaskMethod) -> DecoratedTaskMethod:
        setattr(f, "description", description)
        return cast(DecoratedTaskMethod, f)

    if func is not None:
        return _wrapper(func)
    return _wrapper
