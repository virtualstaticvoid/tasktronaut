from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, Dict, Optional, TYPE_CHECKING, Type, cast

from pydantic import TypeAdapter, ValidationError

from .steps import Step
from .types import (
    BuilderIterator,
    Description,
    ForEachMethod,
    Options,
    ProcessDefinitionType,
    TaskMethod,
    TransformMethod,
    Value,
)

if TYPE_CHECKING:
    from .process import Process


class Builder:
    def __init__(
        self,
        process: "Process",
        kwargs: Dict[str, Any],
        options: Optional[Options] = None,
        description: Description = None,
    ):
        self.process = process
        self.description = description
        self.options = self._convert_options(options)
        self.kwargs = kwargs

    @staticmethod
    def _convert_options(options: Optional[Options] = None) -> SimpleNamespace:
        if options:
            if isinstance(options, SimpleNamespace):
                return options
            if isinstance(options, dict):
                return SimpleNamespace(**options)
        return SimpleNamespace()

    def expected_arguments(self, **kwargs: Optional[Type]):
        # NOTE: this doesn't check for additional arguments
        for name, expected_type in kwargs.items():
            if name not in self.kwargs:
                raise TypeError(f"Argument '{name}' not found.")

            if expected_type is not None:
                arg_type = self.kwargs[name]
                type_adapter = TypeAdapter(expected_type)
                try:
                    type_adapter.validate_python(arg_type)
                except ValidationError as e:
                    raise ValueError(
                        f"Argument '{name}' is expected to be of type '{arg_type}'."
                    ) from e

    @contextmanager
    def concurrent(self, description: Description = None) -> BuilderIterator:
        from .process import ConcurrentProcess  # pylint: disable=import-outside-toplevel

        yield from self._build_process(ConcurrentProcess, description)

    @contextmanager
    def sequential(self, description: Description = None) -> BuilderIterator:
        from .process import SequentialProcess  # pylint: disable=import-outside-toplevel

        yield from self._build_process(SequentialProcess, description)

    def _build_process(
        self, process_type: Type["Process"], description: Description = None
    ) -> BuilderIterator:
        builder = Builder(
            process=process_type(
                identifier=self.process.identifier,
                definition=self.process.definition,
            ),
            options=self.options,
            description=description or self.description,
            kwargs=self.kwargs,
        )
        yield builder
        self.process.steps.append(builder.process)

    def task(
        self,
        func: TaskMethod,
        description: Description = None,
    ):
        self.process.steps.append(
            Step(
                func=func,
                description=(
                    description or getattr(func, "description", self.description)
                ),
                kwargs=self.kwargs,
            )
        )

    def sub_process(
        self,
        definition: ProcessDefinitionType,
        description: Description = None,
    ):
        builder = Builder(
            process=definition.create_process(
                identifier=self.process.identifier,
                definition=definition,
            ),
            options=self.options,
            description=description or self.description,
            kwargs=self.kwargs,
        )
        definition().define_process(builder)
        self.process.steps.append(builder.process)

    def each(
        self,
        func: ForEachMethod,
        description: Description = None,
    ) -> BuilderIterator:
        for kwargs in func(**self.kwargs.copy()):
            kwargs, desc = kwargs if isinstance(kwargs, tuple) else (kwargs, None)
            yield Builder(
                process=self.process,
                options=self.options,
                description=desc or description or self.description,
                kwargs=kwargs,
            )

    @contextmanager
    def transform(
        self,
        func: TransformMethod,
        description: Description = None,
    ) -> BuilderIterator:
        kwargs = func(**self.kwargs.copy())
        kwargs, desc = kwargs if isinstance(kwargs, tuple) else (kwargs, None)

        yield Builder(
            process=self.process,
            options=self.options,
            description=desc or description or self.description,
            kwargs=kwargs,
        )

    def option(self, name: str, default: Optional[Value] = None) -> Value:
        return cast(Value, getattr(self.options, name, default))
