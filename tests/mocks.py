from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Union

from tasktronaut import Builder, ProcessDefinition, task
from tasktronaut.backend import Backend, Job
from tasktronaut.errors import CancelProcessError, NonRetryableProcessError
from tasktronaut.types import Description


class MockJob:
    def cancel(self):  # pragma: no cover
        pass

    def delete_dependents(self):  # pragma: no cover
        pass


class MockBackend(Backend):
    def enqueue_perform_complete(
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        depends_on: Optional[Union[Job, List[Job]]] = None,
    ) -> Job:
        pass

    def enqueue_perform_start(
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        depends_on: Optional[Job] = None,
    ) -> Job:
        pass

    def enqueue_perform_task(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        function_name: str,
        description: Description,
        kwargs: Dict[str, Any],
        depends_on: Optional[Job] = None,
    ) -> Job:
        pass


class MockBasicDefinition(ProcessDefinition):
    def define_process(self, builder: Builder):
        pass


class MockDefinition(ProcessDefinition):
    @task
    def task_success(self, *_, **__):
        pass

    @task
    def task_fail(self, *_, **__):
        raise NotImplementedError()

    @task
    def task_fail_no_retry(self, *_, **__):
        raise NonRetryableProcessError()

    @task
    def task_cancel(self, *_, **__):
        raise CancelProcessError()

    def define_process(self, builder: Builder):
        pass

    def on_started(self, identifier: str):
        super().on_started(identifier=identifier)

    @contextmanager
    def around_task(
        self,
        identifier: str,
        step: str,
        description: Description,
    ) -> Generator[None, None, None]:
        with super().around_task(
            identifier=identifier,
            step=step,
            description=description,
        ):
            yield

    def on_completed(self, identifier: str):
        super().on_completed(identifier=identifier)

    def on_failed(self, identifier: str, step: str, e: Exception):
        super().on_failed(identifier=identifier, step=step, e=e)

    def on_cancelled(self, identifier: str):
        super().on_cancelled(identifier=identifier)


@task
def task_basic(*_, **__):
    pass


@task(description="foo-bar-baz")
def task_with_description(*_, **__):
    pass


@task
def task_fail(*_, **__):
    raise NotImplementedError()


@task
def task_fail_no_retry(*_, **__):
    raise NonRetryableProcessError()


@task
def task_cancel(*_, **__):
    raise CancelProcessError()
