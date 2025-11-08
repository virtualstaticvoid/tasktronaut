"""
RQ Backend implementation for Tasktronaut process execution.

This module provides a concrete implementation of the Backend abstract base class
using the RQ (Redis Queue) job queue library. It enables asynchronous execution
of Tasktronaut processes with support for job dependencies and Redis-backed
job persistence.
"""

from typing import Any, Dict, List, Optional, Union, cast

import rq

from ..backend import Backend, Job
from ..types import Description


# pylint: disable=too-many-arguments,too-many-positional-arguments
class RqBackend(Backend):
    """
    Backend implementation using RQ (Redis Queue) for process execution.

    This backend enqueues process start, task, and completion callbacks to an RQ queue
    for asynchronous execution. It leverages RQ's job dependency features to ensure
    proper task ordering and provides Redis-backed persistence of job state.

    :param queue: The RQ Queue instance to which jobs will be enqueued
    :type queue: rq.Queue
    """

    def __init__(self, queue: rq.Queue):
        """
        Initialize the RQ backend with a queue instance.

        :param queue: The RQ Queue instance to which jobs will be enqueued
        :type queue: rq.Queue
        """
        self.queue = queue

    def enqueue_perform_start(
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        depends_on: Optional[Job] = None,
    ) -> Job:
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
        return self.queue.enqueue(
            self.perform_start,
            identifier=identifier,
            module_name=module_name,
            definition_class=definition_class,
            depends_on=depends_on,
        )

    def enqueue_perform_task(
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        function_name: str,
        description: Optional[str],
        kwargs: Dict[str, Any],
        depends_on: Optional[Job] = None,
    ) -> Job:
        """
        Enqueue a process task for execution to the RQ queue.

        Schedules the execution of a specific task function within a process definition
        by enqueueing the rq_perform_task method to the configured RQ queue. Uses a
        wrapper method to handle RQ-specific parameter handling.

        :param identifier: Unique identifier for the process execution instance
        :type identifier: str
        :param module_name: Fully qualified module name containing the process definition
        :type module_name: str
        :param definition_class: Name of the process definition class to instantiate
        :type definition_class: str
        :param function_name: Name of the task method to execute
        :type function_name: str
        :param description: Human-readable description of the task
        :type description: Optional[str]
        :param kwargs: Keyword arguments to pass to the task function
        :type kwargs: Dict[str, Any]
        :param depends_on:
            Optional job that this job depends on. If provided,
            this job will not execute until the dependency completes.
        :type depends_on: Optional[Job]
        :return: RQ Job object representing the enqueued task
        :rtype: Job
        """

        # NOTE: `description` and `kwargs` are used by rq
        return self.queue.enqueue(
            self.rq_perform_task,
            identifier=identifier,
            module_name=module_name,
            definition_class=definition_class,
            function_name=function_name,
            task_description=description,
            task_kwargs=kwargs,
            depends_on=depends_on,
        )

    @classmethod
    def rq_perform_task(
        cls,
        identifier: str,
        module_name: str,
        definition_class: str,
        function_name: str,
        task_description: Description,
        task_kwargs: Dict[str, Any],
    ):
        """
        Execute a process task from within an RQ job context.

        This classmethod serves as the RQ job entry point for task execution. It retrieves
        the current RQ job, and delegates to the perform_task method.

        :param identifier: Unique identifier for the process execution instance
        :type identifier: str
        :param module_name: Fully qualified module name containing the process definition
        :type module_name: str
        :param definition_class: Name of the process definition class to instantiate
        :type definition_class: str
        :param function_name: Name of the task method to execute
        :type function_name: str
        :param task_description: Human-readable description of the task
        :type task_description: Description
        :param task_kwargs: Keyword arguments to pass to the task function
        :type task_kwargs: Dict[str, Any]
        """

        job = cast(Job, rq.get_current_job())

        super().perform_task(
            job=job,
            identifier=identifier,
            module_name=module_name,
            definition_class=definition_class,
            function_name=function_name,
            description=task_description,
            kwargs=task_kwargs,
        )

    def enqueue_perform_complete(
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        depends_on: Optional[Union[Job, List[Job]]] = None,
    ) -> Job:
        """
        Enqueue a process completion callback to the RQ queue.

        Schedules the execution of the process completion callback by enqueueing the
        perform_complete method to the configured RQ queue. The job will optionally
        depend on one or more other jobs before execution.

        :param identifier: Unique identifier for the process execution instance
        :type identifier: str
        :param module_name: Fully qualified module name containing the process definition
        :type module_name: str
        :param definition_class: Name of the process definition class to instantiate
        :type definition_class: str
        :param depends_on:
            Optional job or list of jobs that this job depends on.
            If provided, this job will not execute until all dependencies complete.
        :type depends_on: Optional[Union[Job, List[Job]]]
        :return: RQ Job object representing the enqueued task
        :rtype: Job
        """

        return self.queue.enqueue(
            self.perform_complete,
            identifier=identifier,
            module_name=module_name,
            definition_class=definition_class,
            depends_on=depends_on,
        )
