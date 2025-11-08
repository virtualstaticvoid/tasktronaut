"""
Decorators module.
"""

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
    """
    Decorator for marking methods as tasks within a process definition.

    This decorator can be applied to methods with or without arguments and
    optionally assigns a description to the task. When applied, it attaches
    metadata to the decorated function that identifies it as a task and stores
    any provided description.

    :param func:
        The undecorated task method. This parameter is only provided
        when the decorator is used without parentheses (bare decorator form).
        When None, the decorator is being used with keyword arguments and returns
        a decorator function.
    :type func: :class:`UndecoratedTaskMethod` or None
    :param description:
        An optional description of the task's purpose and behavior.
        This description may be used for logging, documentation generation, or
        user-facing displays of the process flow.
    :type description: :class:`Description` or None
    :return:
        Either the decorated method (when used as a bare decorator) or a
        decorator function (when used with keyword arguments).
    :rtype: :class:`DecoratedTaskMethod` or :class:`Callable`

    .. note::
        The decorator supports two usage patterns:

        1. **Bare decorator**: Applied directly without parentheses or with empty
           parentheses, where no description is provided.
        2. **Parameterized decorator**: Applied with the ``description`` keyword
           argument to specify a task description.

    .. seealso::
        :class:`UndecoratedTaskMethod` -- Type for undecorated task methods
        :class:`DecoratedTaskMethod` -- Type for decorated task methods
        :class:`Description` -- Type for task descriptions
    """

    def _wrapper(f: UndecoratedTaskMethod) -> DecoratedTaskMethod:
        setattr(f, "description", description)
        return cast(DecoratedTaskMethod, f)

    if func is not None:
        return _wrapper(func)
    return _wrapper
