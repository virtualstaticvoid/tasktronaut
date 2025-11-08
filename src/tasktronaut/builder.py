"""
Builder module.
"""

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
    """
    A builder class for constructing and configuring process workflows.

    The Builder provides a fluent interface for defining task execution graphs,
    including sequential and concurrent execution patterns, argument validation,
    iteration, and transformation capabilities.

    :param process: The process instance being built
    :type process: Process
    :param kwargs: Keyword arguments to pass to tasks and transformations
    :type kwargs: Dict[str, Any]
    :param options: Optional configuration options for the process
    :type options: Optional[Options]
    :param description: Optional description for the builder context
    :type description: Description

    :ivar process: The process instance being constructed
    :type process: Process
    :ivar description: Description for the current builder context
    :type description: Description
    :ivar options: Configuration options converted to SimpleNamespace
    :type options: SimpleNamespace
    :ivar kwargs: Keyword arguments for task execution
    :type kwargs: Dict[str, Any]
    """

    def __init__(
        self,
        process: "Process",
        kwargs: Dict[str, Any],
        options: Optional[Options] = None,
        description: Description = None,
    ):
        self.process = process
        self.description = description
        self.options: SimpleNamespace = self._convert_options(options)
        self.kwargs = kwargs

    @staticmethod
    def _convert_options(options: Optional[Options] = None) -> SimpleNamespace:
        """
        Convert options to a SimpleNamespace for attribute-style access.

        :param options: Options as dict, SimpleNamespace, or None
        :type options: Optional[Options]
        :return: Options as SimpleNamespace
        :rtype: SimpleNamespace
        """
        if options:
            if isinstance(options, SimpleNamespace):
                return options
            if isinstance(options, dict):
                return SimpleNamespace(**options)
        return SimpleNamespace()

    def expected_arguments(self, **kwargs: Optional[Type]):
        """
        Validate that expected arguments are present and of the correct type.

        This method checks that all specified arguments exist in the builder's
        kwargs and validates their types using Pydantic type adapters. Type
        validation is only performed when a non-None type is specified.

        :param kwargs:
            Mapping of argument names to expected types. Use None to skip type
            validation for an argument.
        :type kwargs: Dict[str, Optional[Type]]
        :raises TypeError: If a required argument is not found in kwargs
        :raises ValueError: If an argument's type does not match the expected type

        .. note::
           This method does not check for additional arguments beyond those specified.

        Example::

            builder.expected_arguments(
                foo=str,
                bar=int,
                baz=None,  # No type checking
                qux=Optional[datetime.date]
            )
        """
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
        """
        Create a concurrent execution block where tasks run in parallel.

        This context manager creates a new ConcurrentProcess that executes its
        contained tasks concurrently. The resulting process is appended to the
        parent process's steps.

        :param description: Optional description for the concurrent block
        :type description: Description
        :return: Builder instance for the concurrent process
        :rtype: BuilderIterator
        :yield: Builder configured for concurrent execution

        Example::

            with builder.concurrent() as b:
                b.task(task1)
                b.task(task2)
        """
        from .process import ConcurrentProcess  # pylint: disable=import-outside-toplevel

        yield from self._build_process(ConcurrentProcess, description)

    @contextmanager
    def sequential(self, description: Description = None) -> BuilderIterator:
        """
        Create a sequential execution block where tasks run one after another.

        This context manager creates a new SequentialProcess that executes its
        contained tasks sequentially. The resulting process is appended to the
        parent process's steps.

        :param description: Optional description for the sequential block
        :type description: Description
        :return: Builder instance for the sequential process
        :rtype: BuilderIterator
        :yield: Builder configured for sequential execution

        Example::

            with builder.sequential() as b:
                b.task(task1)
                b.task(task2)
        """
        from .process import SequentialProcess  # pylint: disable=import-outside-toplevel

        yield from self._build_process(SequentialProcess, description)

    def _build_process(
        self, process_type: Type["Process"], description: Description = None
    ) -> BuilderIterator:
        """
        Internal method to create a sub-process of a specific type.

        Creates a new builder with a process of the specified type, yields it
        for configuration, then appends the configured process to the parent's steps.

        :param process_type: The type of process to create (Sequential or Concurrent)
        :type process_type: Type[Process]
        :param description: Optional description for the process
        :type description: Description
        :return: Builder instance for the new process
        :rtype: BuilderIterator
        :yield: Builder configured with the new process
        """
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
        """
        Add a task to the process.

        Creates a Step wrapping the provided function and appends it to the
        process's steps. The task inherits the builder's kwargs and description
        unless overridden.

        :param func:
            The function to execute as a task. Can be a regular method, a method
            accepting a Context parameter, or a ``@task`` decorated method.
        :type func: TaskMethod
        :param description:
            Optional description for the task. If not provided, uses the function's
            'description' attribute or the builder's description.
        :type description: Description

        Example::

            builder.task(my_task)
            builder.task(my_task, description="Custom description")
        """
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
        """
        Embed a sub-process within the current process.

        Creates and configures a new process based on the provided ``ProcessDefinition``,
        then appends it to the parent process's steps. The sub-process inherits
        the current options and kwargs.

        :param definition: A ProcessDefinition class defining the sub-process
        :type definition: ProcessDefinitionType
        :param description: Optional description for the sub-process
        :type description: Description

        Example::

            builder.sub_process(MySubProcess)
            builder.sub_process(MySubProcess, description="Data validation")
        """
        builder = Builder(
            process=definition.execution_mode.value(
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
        """
        Iterate over items yielded by the given ``func`` method, and yields a
        builder for each iteration.

        Executes the provided function to generate items, then yields a Builder
        instance for each item with updated kwargs.

        The provided function can yield either a dict of kwargs or a tuple of (kwargs, description).

        :param func:
            A function that yields dicts or (dict, str) tuples. The function receives the
            current kwargs as parameters.
        :type func: ForEachMethod
        :param description: Optional default description for iterations
        :type description: Description
        :return: Iterator of Builder instances, one per yielded item
        :rtype: BuilderIterator
        :yield: Builder with kwargs updated for each iteration

        Example::

            def items(self, count: int, **_):
                for i in range(count):
                    yield {"index": i}

            for b in builder.each(self.items):
                b.task(task_for_item)

        .. note::
           The provided function can yield either ``dict`` or ``(dict, str)`` tuples,
           where the string provides a per-item description.
        """
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
        """
        Transform kwargs for tasks within a context block.

        Executes the provided function to generate new kwargs, then yields a Builder
        with the transformed kwargs. Tasks defined within the context use the
        transformed arguments. The function can return either a dict or a tuple
        of (dict, description).

        :param func:
            A function that returns a dict of new kwargs or a (dict, str) tuple. The function
            receives the current kwargs as parameters.
        :type func: TransformMethod
        :param description: Optional description for the transformation context
        :type description: Description
        :return: Builder instance with transformed kwargs
        :rtype: BuilderIterator
        :yield: Builder configured with transformed kwargs

        Example::

            def double_value(self, value: int, **_):
                return {"value": value * 2}

            with builder.transform(double_value) as t:
                t.task(task_with_doubled_value)

        .. note::
           The transform function can return either ``dict`` or ``(dict, str)``
           where the string overrides the description for the context.
        """
        kwargs = func(**self.kwargs.copy())
        kwargs, desc = kwargs if isinstance(kwargs, tuple) else (kwargs, None)

        yield Builder(
            process=self.process,
            options=self.options,
            description=desc or description or self.description,
            kwargs=kwargs,
        )

    def option(self, name: str, default: Optional[Value] = None) -> Value:
        """
        Retrieve an option value with optional default.

        Accesses configuration options passed to the builder, returning the
        specified option's value or a default if the option is not set.

        :param name: The name of the option to retrieve
        :type name: str
        :param default: Default value to return if option is not found
        :type default: Optional[Value]
        :return: The option's value or the default
        :rtype: Value

        Example::

            if builder.option("debug", False):
                builder.task(verbose_logging)
        """
        return cast(Value, getattr(self.options, name, default))
