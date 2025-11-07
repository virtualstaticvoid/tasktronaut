import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union

from .context import Context
from .errors import CancelProcessError, NonRetryableProcessError
from .types import Description
from .utils import load_definition

logger = logging.getLogger(__name__)


class Job(Protocol):
    def cancel(self):  # pragma: no cover
        pass

    def delete_dependents(self):  # pragma: no cover
        pass


# pylint: disable=too-many-arguments,too-many-positional-arguments
class Backend(ABC):
    @abstractmethod
    def enqueue_perform_start(
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        depends_on: Optional[Job] = None,
    ) -> Job:  # pragma: no cover
        pass

    @staticmethod
    def perform_start(
        identifier: str,
        module_name: str,
        definition_class: str,
    ):
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
        pass

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
        definition = load_definition(module_name, definition_class)
        task_func = getattr(definition, function_name)
        context = Context()
        try:
            with definition.around_task(
                identifier=identifier,
                step=function_name,
                description=description,
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
        pass

    @staticmethod
    def perform_complete(
        identifier: str,
        module_name: str,
        definition_class: str,
    ):
        definition = load_definition(module_name, definition_class)
        definition.on_completed(identifier)
