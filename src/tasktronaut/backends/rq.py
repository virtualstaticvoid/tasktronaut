from typing import Any, Dict, List, Optional, Union, cast

import rq

from ..backend import Backend, Job
from ..types import Description


# pylint: disable=too-many-arguments,too-many-positional-arguments
class RqBackend(Backend):
    def __init__(self, queue: rq.Queue):
        self.queue = queue

    def enqueue_perform_start(
        self,
        identifier: str,
        module_name: str,
        definition_class: str,
        depends_on: Optional[Job] = None,
    ) -> Job:
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
        return self.queue.enqueue(
            self.perform_complete,
            identifier=identifier,
            module_name=module_name,
            definition_class=definition_class,
            depends_on=depends_on,
        )
