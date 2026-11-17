"""
RQ Backend implementation for Tasktronaut process execution.

This module provides a concrete implementation of the Backend abstract base class
using the RQ (Redis Queue) job queue library. It enables asynchronous execution
of Tasktronaut processes with support for job dependencies and Redis-backed
job persistence.

Workers executing Tasktronaut processes should use :class:`RqQueue` (or a queue class
including :class:`JobScopedReadyJobRegistryMixin`) as their queue class, so that the
jobs of a process are enqueued as soon as the jobs they depend on have finished. For
example, ``rq worker --queue-class tasktronaut.backends.rq.RqQueue``.
"""

import logging
from typing import Any, Dict, List, Optional, Union, cast

import rq
from redis.exceptions import WatchError
from rq.job import JobStatus
from rq.registry import ReadyJobRegistry
from rq.utils import as_text

from ..backend import Backend, Job
from ..types import Description

logger = logging.getLogger(__name__)


class JobScopedReadyJobRegistry(ReadyJobRegistry):
    """
    Ready job registry whose claim of a job only conflicts with changes to that job.

    RQ 3.0 claims each ready dependent job in an optimistic transaction which watches
    the queue's shared ready job registry as well as the job. Every worker writes to
    that registry when readying or enqueueing any dependent job, so concurrent
    hand-offs of unrelated jobs abort each other, and the aborted job waits for worker
    maintenance, which can be up to ten minutes later. Meanwhile, the subsequent steps
    of the process sit in the deferred job registry.

    Watching only the job keeps the guarantee against enqueueing a job twice: every
    successful claim, and every deletion or cancellation of a job, writes the job's
    hash in its transaction, so a competing change to the same job still aborts the
    claim.
    """

    def enqueue_jobs(self, job_ids: List[str]) -> List[rq.job.Job]:
        """
        Move ready jobs from the registry onto the queue.

        Mirrors RQ 3.0's :meth:`rq.registry.ReadyJobRegistry.enqueue_jobs` except for
        the keys it watches; re-check it against RQ's implementation when upgrading
        RQ. A job whose claim conflicts with a concurrent change to that job is
        skipped and left for :meth:`cleanup`.

        :param job_ids: Ids of the jobs to enqueue, in enqueue order
        :type job_ids: List[str]
        :return: The jobs that were enqueued
        :rtype: List[rq.job.Job]
        """
        if not job_ids:
            return []

        queue = rq.Queue(
            name=self.name,
            connection=self.connection,
            job_class=self.job_class,
            serializer=self.serializer,
        )
        fetched = self.job_class.fetch_many(
            job_ids, connection=self.connection, serializer=self.serializer
        )

        enqueued: List[rq.job.Job] = []
        for job_id, job in zip(job_ids, fetched):
            if job is None:
                self.connection.zrem(self.key, job_id)
                continue
            if job.get_status(refresh=False) != JobStatus.READY_TO_ENQUEUE:
                self.connection.zrem(self.key, job_id)
                continue
            try:
                with self.connection.pipeline() as pipe:
                    # NOTE: RQ also watches `self.key`, the shared registry
                    pipe.watch(job.key)

                    if pipe.zscore(self.key, job.id) is None:
                        pipe.unwatch()
                        continue

                    status = pipe.hget(job.key, "status")
                    # NOTE: `isinstance` narrows the type of `status` for both the
                    #  loosely (redis < 8) and precisely (redis >= 8) typed `hget`
                    if (
                        not status
                        or not isinstance(status, (bytes, str))
                        or JobStatus(as_text(status)) != JobStatus.READY_TO_ENQUEUE
                    ):
                        pipe.multi()
                        self.remove(job, pipeline=pipe)
                        pipe.execute()
                        continue

                    pipe.multi()
                    self.remove(job, pipeline=pipe)
                    # pylint: disable=protected-access
                    if job.has_rate_limit:
                        queue._enqueue_rate_limited_job(job, pipeline=pipe)
                    else:
                        queue._enqueue_job(
                            job,
                            pipeline=pipe,
                            at_front=job.should_enqueue_at_front(),
                        )
                    pipe.execute()
            except WatchError:
                logger.info(
                    "Ready job %s changed while enqueueing; skipping for now", job_id
                )
                continue
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception(
                    "Failed to enqueue ready job %s; leaving in ReadyJobRegistry",
                    job_id,
                )
                continue
            enqueued.append(job)
        return enqueued


class JobScopedReadyJobRegistryMixin:  # pylint: disable=too-few-public-methods
    """
    Queue mixin which hands off ready dependent jobs via the job-scoped registry.

    A worker enqueues the dependents of a finished job through the
    ``ready_job_registry`` of its queue class, so mix this into the queue class
    workers are configured with. For example, with ``django-rq``::

        class ApplicationQueue(JobScopedReadyJobRegistryMixin, DjangoRQ):
            pass

        RQ = {"QUEUE_CLASS": "myapp.queues.ApplicationQueue"}
    """

    @property
    def ready_job_registry(self) -> JobScopedReadyJobRegistry:
        queue = cast(rq.Queue, self)
        return JobScopedReadyJobRegistry(
            queue=queue, job_class=queue.job_class, serializer=queue.serializer
        )


class RqQueue(JobScopedReadyJobRegistryMixin, rq.Queue):
    """
    RQ queue which hands off ready dependent jobs via :class:`JobScopedReadyJobRegistry`.

    Use it as the queue class of workers executing Tasktronaut processes, e.g.
    ``rq worker --queue-class tasktronaut.backends.rq.RqQueue``.
    """


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
