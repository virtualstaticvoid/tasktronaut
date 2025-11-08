"""
Steps module.
"""

from typing import Any, Dict, TYPE_CHECKING, Union

from .types import Description, TaskMethod

if TYPE_CHECKING:
    from .process import Process  # noqa


class Step:
    """
    Represents a single executable step in a process.

    A ``Step`` encapsulates a task function along with its metadata and execution parameters.

    Steps form the building blocks of process definitions and are executed by the process
    engine according to the defined execution mode.

    :ivar func: The callable function or method that performs the task
    :type func: TaskMethod
    :ivar description: Human-readable description of the step
    :type description: Description
    :ivar kwargs: Keyword arguments to be passed to the function during execution
    :type kwargs: Dict[str, Any]

    :param func: The task function to execute
    :type func: TaskMethod
    :param description: A description of what this step does
    :type description: Description
    :param kwargs: Additional keyword arguments for the task function
    :type kwargs: Dict[str, Any]
    """

    def __init__(
        self,
        func: TaskMethod,
        description: Description,
        kwargs: Dict[str, Any],
    ):
        """
        Initialize a Step instance.

        :param func: The callable function or method to be executed as a task
        :type func: TaskMethod
        :param description: A description of the step's purpose
        :type description: Description
        :param kwargs: Keyword arguments to pass to the function
        :type kwargs: Dict[str, Any]
        """
        self.func = func
        self.description = description
        self.kwargs = kwargs

    @property
    def is_process(self) -> bool:
        """
        Determine if this step represents a process.

        :return: Always returns ``False`` since a Step is not a Process
        :rtype: bool
        """
        return False

    def __str__(self) -> str:
        """String representation of the Step."""
        return f"{self.__class__.__name__}(func={self.func.__name__},kwargs={self.kwargs!r},)"

    def __repr__(self) -> str:
        """String representation of the Step."""
        return f"{self.__class__.__name__}(func={self.func.__name__},kwargs={self.kwargs!r},)"


class Steps(list[Union[Step, "Process"]]):  # pragma: no cover
    """
    A container for holding a collection of steps and sub-processes.

    This class extends the built-in list type to provide a typed container that holds
    both Step instances and Process instances. It is used internally to manage the
    collection of execution items within a process definition.

    :inherits: list[Union[Step, Process]]
    """
