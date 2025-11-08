"""
Backend module.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union

from .context import Context
from .errors import CancelProcessError, NonRetryableProcessError
from .types import Description
from .utils import load_definition

logger = logging.getLogger(__name__)


class Job(Protocol):
    """
    Protocol defining the interface for a job object.

    A job represents an enqueued unit of work in the backend system and provides
    methods to manage its lifecycle.
    """

    def cancel(self):  # pragma: no cover
        """
        Cancel the execution of this job.

        Stops the job from being executed if it hasn't already started.
        """

    def delete_dependents(self):  # pragma: no cover
        """
        Delete all jobs that depend on this job.

        Removes any downstream jobs that were scheduled to run after completion
        of this job.
        """


# pylint: disable=too-many-arguments,too-many-positional-arguments
class Backend(ABC):
    """
    Abstract base class defining the interface for process execution backends.

    Backends are responsible for enqueueing tasks, managing job dependencies, and
    executing process lifecycle callbacks. Subclasses must implement the abstract
    enqueue methods to integrate with specific job queue systems.

    The backend handles three main phases of process execution:
    - Process start callbacks
    - Individual task execution with error handling
    - Process completion callbacks
    """

    @abstractmethod
    def enqueue_perform_start(
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        depends_on: Optional[Job] = None,
    ) -> Job:  # pragma: no cover
        """
        Enqueue a process start callback.

        Schedules the execution of the process start callback, which allows the
        process definition to perform initialization logic when execution begins.

        :param identifier: Unique identifier for the process execution instance
        :type identifier: str
        :param module_name: Fully qualified module name containing the process definition
        :type module_name: str
        :param definition_class: Name of the process definition class to instantiate
        :type definition_class: str
        :param depends_on:
            Optional job that this job depends on. If provided,
            this job will not execute until the dependency completes.
        :type depends_on: Optional[Job]
        :return: Job object representing the enqueued task
        :rtype: Job
        """

    @staticmethod
    def perform_start(
        identifier: str,
        module_name: str,
        definition_class: str,
    ):
        """
        Execute the process start callback.

        Loads the process definition and invokes its start callback. This method
        is typically called by the backend after the job has been dequeued.

        It is implemented as a staticmethod, to allow for the most flexibility in
        backend implementations.

        :param identifier: Unique identifier for the process execution instance
        :type identifier: str
        :param module_name: Fully qualified module name containing the process definition
        :type module_name: str
        :param definition_class: Name of the process definition class to instantiate
        :type definition_class: str
        """

        definition = load_definition(module_name, definition_class)
        definition.on_started(identifier)

    @abstractmethod
    def enqueue_perform_task(
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        function_name: str,
        description: Description,
        kwargs: Dict[str, Any],
        depends_on: Optional[Job] = None,
    ) -> Job:  # pragma: no cover
        """
        Enqueue a process task for execution.

        Schedules the execution of a specific task function within a process definition.
        The task will be executed with the provided keyword arguments and can optionally
        depend on another job.

        :param identifier: Unique identifier for the process execution instance
        :type identifier: str
        :param module_name: Fully qualified module name containing the process definition
        :type module_name: str
        :param definition_class: Name of the process definition class to instantiate
        :type definition_class: str
        :param function_name: Name of the task method to execute
        :type function_name: str
        :param description: Human-readable description of the task
        :type description: Description
        :param kwargs: Keyword arguments to pass to the task function
        :type kwargs: Dict[str, Any]
        :param depends_on:
            Optional job that this job depends on. If provided,
            this job will not execute until the dependency completes.
        :type depends_on: Optional[Job]
        :return: Job object representing the enqueued task
        :rtype: Job
        """

    @classmethod
    def perform_task(
        cls,
        job: Job,
        identifier: str,
        module_name: str,
        definition_class: str,
        function_name: str,
        description: Description,
        kwargs: Dict[str, Any],
    ):
        """
        Execute a process task with comprehensive error handling.

        Loads the process definition, creates an execution context, and invokes the
        specified task function. Handles three categories of errors:

        - NonRetryableProcessError: Logs error, calls on_failed callback, and re-raises
        - CancelProcessError: Cancels the job and its dependents, calls on_cancelled callback
        - Other exceptions: Logs error, calls on_failed callback, and re-raises for retry

        The task execution is wrapped with the definition's around_task context manager,
        allowing the definition to perform setup and teardown logic.

        :param job: Job object that can be cancelled or have dependents deleted
        :type job: Job
        :param identifier: Unique identifier for the process execution instance
        :type identifier: str
        :param module_name: Fully qualified module name containing the process definition
        :type module_name: str
        :param definition_class: Name of the process definition class to instantiate
        :type definition_class: str
        :param function_name: Name of the task method to execute
        :type function_name: str
        :param description: Human-readable description of the task
        :type description: Description
        :param kwargs: Keyword arguments to pass to the task function
        :type kwargs: Dict[str, Any]

        :raises NonRetryableProcessError: When task execution raises a non-retryable error
        :raises Exception: When task execution raises an unhandled error (retryable)
        """

        definition = load_definition(module_name, definition_class)
        task_func = getattr(definition, function_name)
        context = Context()
        try:
            with definition.around_task(
                identifier=identifier,
                step=function_name,
                description=description,
                context=context,
            ):
                task_func(context=context, **kwargs)

        except NonRetryableProcessError as e:
            logger.error(
                "Failed to execute task '%s', a non-retryable error was raised.",
                function_name,
                exc_info=True,
                stack_info=True,
            )
            definition.on_failed(identifier, function_name, e)
            # re-raise error to fail job
            raise

        except CancelProcessError:
            logger.error(
                "Failed to execute task '%s', the process was cancelled.",
                function_name,
                exc_info=True,
                stack_info=True,
            )
            job.cancel()
            job.delete_dependents()  # clean up
            definition.on_cancelled(identifier)
            # ignore error

        except Exception as e:
            logger.error(
                "Failed to execute task '%s' due to an unhandled error. "
                "The task will be retried.",
                function_name,
                exc_info=True,
                stack_info=True,
            )
            definition.on_failed(identifier, function_name, e)
            # re-raise error to fail job
            raise

    @abstractmethod
    def enqueue_perform_complete(
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        depends_on: Optional[Union[Job, List[Job]]] = None,
    ) -> Job:  # pragma: no cover
        """
        Enqueue a process completion callback.

        Schedules the execution of the process completion callback, which allows the
        process definition to perform finalization logic when all tasks have completed.
        Can depend on one or more jobs.

        :param identifier: Unique identifier for the process execution instance
        :type identifier: str
        :param module_name: Fully qualified module name containing the process definition
        :type module_name: str
        :param definition_class: Name of the process definition class to instantiate
        :type definition_class: str
        :param depends_on: Optional job or list of jobs that this job depends on.
            If provided, this job will not execute until all dependencies complete.
        :type depends_on: Optional[Union[Job, List[Job]]]
        :return: Job object representing the enqueued task
        :rtype: Job
        """

    @staticmethod
    def perform_complete(
        identifier: str,
        module_name: str,
        definition_class: str,
    ):
        """
        Execute the process completion callback.

        Loads the process definition and invokes its completion callback. This method
        is typically called by the backend after all process tasks have completed
        successfully.

        It is implemented as a staticmethod, to allow for the most flexibility in
        backend implementations.

        :param identifier: Unique identifier for the process execution instance
        :type identifier: str
        :param module_name: Fully qualified module name containing the process definition
        :type module_name: str
        :param definition_class: Name of the process definition class to instantiate
        :type definition_class: str
        """

        definition = load_definition(module_name, definition_class)
        definition.on_completed(identifier)
