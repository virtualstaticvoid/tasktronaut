"""
Process module.
"""

import enum
import logging
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator, Optional, Type

from .backend import Backend, Job
from .builder import Builder
from .context import Context
from .steps import Steps
from .types import Description, Options
from .utils import to_dict

logger = logging.getLogger(__name__)


class Process(ABC):
    """Abstract base class for process execution workflows.

    A Process represents an executable workflow composed of multiple steps that can be
    enqueued and executed by a backend. Processes are created with an identifier and
    a process definition that specifies the workflow structure.

    This is an abstract base class that must be subclassed to implement specific
    execution strategies (e.g., sequential, concurrent).

    :param identifier: Unique identifier for this process instance
    :type identifier: str
    :param definition: The ProcessDefinition class that defines the workflow structure
    :type definition: Type[ProcessDefinition]

    :ivar identifier: Unique identifier for this process instance
    :type identifier: str
    :ivar definition: The ProcessDefinition class associated with this process
    :type definition: Type[ProcessDefinition]
    :ivar steps: Collection of steps that comprise this process workflow
    :type steps: Steps
    """

    def __init__(self, identifier: str, definition: Type["ProcessDefinition"]):
        """Initialize a new Process instance.

        :param identifier: Unique identifier for this process instance
        :type identifier: str
        :param definition: The ProcessDefinition class that defines the workflow
        :type definition: Type[ProcessDefinition]
        """
        self.identifier = identifier
        self.definition: Type[ProcessDefinition] = definition
        self.steps = Steps()

    @property
    def is_process(self) -> bool:
        """Check if this object is a Process.

        This property provides a consistent way to identify Process instances
        throughout the framework.

        :return: Always returns True
        :rtype: bool
        """
        return True

    @abstractmethod
    def enqueue(
        self, backend: Backend, start_job: Optional[Job] = None
    ) -> Job:  # pragma: no cover
        """Enqueue this process for execution on the specified backend.

        This abstract method must be implemented by subclasses to define how the
        process and its steps are queued for execution. Different execution modes
        (sequential, concurrent) will have different enqueueing strategies.

        :param backend: The execution backend that will run the process
        :type backend: Backend
        :param start_job:
            Optional job to execute before this process begins.
            Used for chaining processes together.
        :type start_job: Optional[Job]

        :return: A Job representing the enqueued process execution
        :rtype: Job

        :raises NotImplementedError: If subclass does not implement this method

        .. note::
           Subclasses must implement this method to define their specific
           execution strategy (sequential vs concurrent ordering, dependency
           management, etc.)
        """

    def __str__(self):
        """Return a human-readable string representation of the Process."""
        return (
            f"{self.__class__.__name__}("
            f"id={self.identifier},"
            f"definition={self.definition.__name__},"
            f"steps={len(self.steps)},"
            ")"
        )

    def __repr__(self):
        """Return a developer-focused string representation of the Process."""
        return (
            f"{self.__class__.__name__}("
            f"id={self.identifier},"
            f"definition={self.definition.__name__},"
            f"steps={len(self.steps)},"
            ")"
        )


class SequentialProcess(Process):
    """A process that executes its steps in sequential order.

    SequentialProcess is a concrete implementation of the Process base class that
    enqueues steps for execution in a strict sequential manner. Each step must
    complete before the next step begins, creating a chain of dependent jobs.
    """

    def enqueue(self, backend: Backend, start_job: Optional[Job] = None) -> Job:
        """Enqueue this process for execution on the specified backend."""
        base_kwargs = to_dict(
            identifier=self.identifier,
            module_name=self.definition.__module__,
            definition_class=self.definition.__qualname__,
        )

        job = start_job or backend.enqueue_perform_start(**base_kwargs)

        for step in self.steps:
            if isinstance(step, Process):
                job = step.enqueue(backend=backend, start_job=job)
                continue

            kwargs = base_kwargs.copy()
            kwargs.update(
                **to_dict(
                    function_name=step.func.__name__,
                    depends_on=job,
                ),
                description=step.description,
                kwargs=step.kwargs,
            )
            job = backend.enqueue_perform_task(**kwargs)

        return backend.enqueue_perform_complete(
            depends_on=job,
            **base_kwargs,
        )


class ConcurrentProcess(Process):
    """A process that executes its steps concurrently in parallel.

    ConcurrentProcess is a concrete implementation of the Process base class that
    enqueues steps for parallel execution. All steps depend only on the initial
    start job and can execute simultaneously, with a final completion job that
    depends on all step jobs finishing.
    """

    def enqueue(self, backend: Backend, start_job: Optional[Job] = None) -> Job:
        """Enqueue this process for execution on the specified backend."""
        base_kwargs = to_dict(
            identifier=self.identifier,
            module_name=self.definition.__module__,
            definition_class=self.definition.__qualname__,
        )

        job = backend.enqueue_perform_start(**base_kwargs)

        jobs = []
        for step in self.steps:
            if isinstance(step, Process):
                jobs.append(step.enqueue(backend=backend, start_job=job))
                continue

            kwargs = base_kwargs.copy()
            kwargs.update(
                **to_dict(
                    function_name=step.func.__name__,
                    depends_on=job,
                ),
                description=step.description,
                kwargs=step.kwargs,
            )
            jobs.append(backend.enqueue_perform_task(**kwargs))

        return backend.enqueue_perform_complete(
            depends_on=jobs,
            **base_kwargs,
        )


class ExecutionMode(enum.Enum):
    """
    Defines the available execution modes for the process.

    The execution mode determines how tasks within a process are executed.
    Sequential execution runs tasks one after another in order, while
    concurrent execution allows tasks to run in parallel.
    """

    SEQUENTIAL = SequentialProcess
    """
    Sequential execution mode. Tasks are executed one at a time in the
    order they are defined. Each task completes before the next begins.
    This is the default execution mode for processes.
    """

    CONCURRENT = ConcurrentProcess
    """
    Concurrent execution mode. Tasks are executed in parallel, allowing
    multiple tasks to run simultaneously. This mode is suitable for processes
    with independent tasks that can benefit from parallel execution.
    """


class ProcessDefinition(ABC):
    """Base class for defining workflow processes in Tasktronaut.

    This class serves as the foundation for creating custom process definitions.
    Subclasses must implement the :meth:`define_process` method to specify the
    workflow structure using the provided :class:`Builder` instance.

    :ivar description: Optional description of the process. Defaults to None.
    :type description: Optional[Description]
    :ivar execution_mode:
        The execution mode for the process (SEQUENTIAL or CONCURRENT).
        Defaults to SEQUENTIAL.
    :type execution_mode: ExecutionMode

    Example::

            class MyProcess(ProcessDefinition):
                execution_mode = ExecutionMode.SEQUENTIAL

                def define_process(self, builder: Builder):
                    builder.task(self.my_task)

                @task
                def my_task(self, context, **kwargs):
                    print("Executing task")
    """

    description: Description = None
    """Optional description of the process. Defaults to None."""

    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    """The execution mode for the process (SEQUENTIAL or CONCURRENT)."""

    @abstractmethod
    def define_process(self, builder: Builder):  # pragma: no cover
        """Define the workflow process structure.

        This method must be implemented by subclasses to specify the
        tasks and execution flow of the process using the provided builder.

        :param builder:
            The builder instance used to construct the process workflow.
        :type builder: Builder
        :raises NotImplementedError: If not implemented by subclass.

        Example::

                def define_process(self, builder: Builder):
                    builder.task(self.first_task)
                    with builder.concurrent():
                        builder.task(self.second_task)
                        builder.task(self.third_task)
                    builder.task(self.forth_task)
        """

    @classmethod
    def build(
        cls,
        identifier: Optional[str] = None,
        options: Optional[Options] = None,
        **kwargs,
    ) -> Process:
        """Build and return a Process instance from this definition.

        This class method constructs a complete process by instantiating the
        definition class, invoking :meth:`define_process`, and returning the
        fully configured process.

        :param identifier:
            Unique identifier for the process instance. If not provided,
            a random UUID hex string is generated.
        :type identifier: Optional[str]
        :param options:
            Configuration options to pass to the builder for conditional
            process logic.
        :type options: Optional[Options]
        :param kwargs:
            Additional keyword arguments passed to tasks during execution.
        :type kwargs: Dict[str, Any]
        :return: A fully configured process ready for execution.
        :rtype: Process

        Example::

                process = MyProcess.build(
                    identifier="my-process-001",
                    options={"debug": True},
                    user_id=123
                )
        """

        builder = Builder(
            process=cls.execution_mode.value(
                identifier=identifier or uuid.uuid4().hex,
                definition=cls,
            ),
            options=options,
            kwargs=kwargs,
        )
        cls().define_process(builder)
        return builder.process

    def on_started(self, identifier: str):
        """Lifecycle hook called when the process starts execution.

        This method is invoked automatically when process execution begins.
        Override to implement custom startup logic such as resource initialization
        or logging.

        :param identifier: The unique identifier of the process instance.
        :type identifier: str

        Note:
            The default implementation logs an informational message indicating
            the process has started.
        """
        logger.info("%s started [%s].", self.__class__.__name__, identifier)

    @contextmanager
    def around_task(
        self,
        identifier: str,
        step: str,
        description: Description,
        context: Context,  # pylint: disable=unused-argument
    ) -> Generator[None, None, None]:
        """Lifecycle hook called around an executing a task. It is a context manager
        that wraps individual task execution.

        This method provides a context for task execution, allowing pre- and
        post-task actions such as logging, metrics collection, or resource
        management. Override to implement custom behavior around task execution.

        :param identifier: The unique identifier of the process instance.
        :type identifier: str
        :param step: The step identifier within the process.
        :type step: str
        :param description: Human-readable description of the task being executed.
        :type description: Description
        :param context:
            The context for the invocation of the task. This object can be used to pass
            additional metadata to the task if needed.
        :type context: Context

        :yield: Control is yielded during task execution.
        :rtype: Generator[None, None, None]

        Example::

                @contextmanager
                def around_task(self, identifier, step, description, context):
                    start_time = time.time()
                    with super().around_task(context, identifier, step, description):
                        yield
                    duration = time.time() - start_time
                    logger.info(f"Task took {duration:.2f}s")

        Note:
            The default implementation logs when task execution begins and completes.
        """
        logger.info(
            "Executing '%s' (%s) of %s process [%s].",
            description,
            step,
            self.__class__.__name__,
            identifier,
        )

        yield

        logger.info(
            "Completed '%s' (%s) of %s process [%s].",
            description,
            step,
            self.__class__.__name__,
            identifier,
        )

    def on_completed(self, identifier: str):
        """Lifecycle hook called when the process completes successfully.

        This method is invoked automatically when all process tasks complete
        without errors. Override to implement custom completion logic such as
        cleanup, notifications, or result processing.

        :param identifier: The unique identifier of the process instance.
        :type identifier: str

        Note:
            The default implementation logs an informational message indicating
            the process has completed.
        """
        logger.info("%s completed [%s].", self.__class__.__name__, identifier)

    def on_failed(self, identifier: str, step: str, e: Exception):
        """Lifecycle hook called when the process fails due to an exception.

        This method is invoked automatically when a task raises an exception
        during process execution. Override to implement custom error handling
        such as rollback operations, error notifications, or recovery attempts.

        :param identifier: The unique identifier of the process instance.
        :type identifier: str
        :param step: The step identifier where the failure occurred.
        :type step: str
        :param e: The exception that caused the failure.
        :type e: Exception

        Note:
            The default implementation logs an error message with the exception details.
        """
        logger.error(
            "%s failed executing %s step [%s].\n%s",
            self.__class__.__name__,
            step,
            identifier,
            e,
        )

    def on_cancelled(self, identifier: str):
        """Lifecycle hook called when the process is cancelled.

        This method is invoked automatically when process execution is
        deliberately cancelled before completion. Override to implement custom
        cancellation logic such as cleanup or state restoration.

        :param identifier: The unique identifier of the process instance.
        :type identifier: str

        Note:
            The default implementation logs a warning message indicating
            the process was cancelled.
        """
        logger.warning("%s cancelled [%s].", self.__class__.__name__, identifier)
