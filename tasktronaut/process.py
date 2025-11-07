import enum
import logging
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator, Optional, Type, cast

from .backend import Backend, Job
from .builder import Builder
from .steps import Steps
from .types import Description, Options
from .utils import to_dict

logger = logging.getLogger(__name__)


class Process(ABC):
    def __init__(self, identifier: str, definition: Type["ProcessDefinition"]):
        self.identifier = identifier
        self.definition: Type[ProcessDefinition] = definition
        self.steps = Steps()

    @property
    def is_process(self) -> bool:
        return True

    @abstractmethod
    def enqueue(
        self, backend: Backend, start_job: Optional[Job] = None
    ) -> Job:  # pragma: no cover
        pass

    def __str__(self):
        return (
            f"{self.__class__.__name__}("
            f"id={self.identifier},"
            f"definition={self.definition.__name__},"
            f"steps={len(self.steps)},"
            ")"
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"id={self.identifier},"
            f"definition={self.definition.__name__},"
            f"steps={len(self.steps)},"
            ")"
        )


class SequentialProcess(Process):
    def enqueue(self, backend: Backend, start_job: Optional[Job] = None) -> Job:
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
    def enqueue(self, backend: Backend, start_job: Optional[Job] = None) -> Job:
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
    SEQUENTIAL = SequentialProcess
    CONCURRENT = ConcurrentProcess


class ProcessDefinition(ABC):
    description: Description = None
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL

    @classmethod
    def create_process(
        cls,
        identifier: str,
        definition: Type["ProcessDefinition"],
    ) -> Process:
        return cast(
            Process,
            cls.execution_mode.value(
                identifier=identifier,
                definition=definition,
            ),
        )

    @classmethod
    def build(
        cls,
        identifier: Optional[str] = None,
        options: Optional[Options] = None,
        **kwargs,
    ) -> Process:
        builder = Builder(
            process=cls.create_process(
                identifier=identifier or uuid.uuid4().hex,
                definition=cls,
            ),
            options=options,
            kwargs=kwargs,
        )
        cls().define_process(builder)
        return builder.process

    @abstractmethod
    def define_process(self, builder: Builder):  # pragma: no cover
        pass

    def on_started(self, identifier: str):
        logger.info("%s started [%s].", self.__class__.__name__, identifier)

    @contextmanager
    def around_task(
        self,
        identifier: str,
        step: str,
        description: Description,
    ) -> Generator[None, None, None]:
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
        logger.info("%s completed [%s].", self.__class__.__name__, identifier)

    def on_failed(self, identifier: str, step: str, e: Exception):
        logger.error(
            "%s failed executing %s step [%s].\n%s",
            self.__class__.__name__,
            step,
            identifier,
            e,
        )

    def on_cancelled(self, identifier: str):
        logger.warning("%s cancelled [%s].", self.__class__.__name__, identifier)
