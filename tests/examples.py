import datetime
from typing import Iterator, List, Optional, Tuple

from tasktronaut import Builder, Context, ExecutionMode, ProcessDefinition, task


# pylint: disable=disallowed-name
class Methods:
    def foo(self, *args, **kwargs):
        pass

    def bar(self, *args, **kwargs):
        pass

    def baz(self, *args, **kwargs):
        pass

    def qux(self, *args, **kwargs):
        pass

    def foo_ctx(self, context: Context, **kwargs):
        pass

    def bar_ctx(self, context: Context, **kwargs):
        pass

    def baz_ctx(self, context: Context, **kwargs):
        pass

    def qux_ctx(self, context: Context, **kwargs):
        pass

    @task(description="My Foo Task")
    def foo_task(self, *args, **kwargs):
        pass

    @task()
    def bar_task(self, *args, **kwargs):
        pass

    @task
    def baz_task(self, *args, **kwargs):
        pass


class SimpleSequential(Methods, ProcessDefinition):
    process_execution_mode = ExecutionMode.SEQUENTIAL

    def define_process(self, builder: Builder):
        builder.task(self.foo)
        builder.task(self.foo_ctx)
        builder.task(self.foo_task)


class SimpleConcurrent(Methods, ProcessDefinition):
    process_execution_mode = ExecutionMode.SEQUENTIAL

    def define_process(self, builder: Builder):
        builder.task(self.foo)
        builder.task(self.foo_ctx)
        builder.task(self.foo_task)


class Arguments(Methods, ProcessDefinition):
    def define_process(self, builder: Builder):
        builder.expected_arguments(
            foo=str,
            bar=int,
            baz=None,
            qux=Optional[datetime.date],
            quux=List[int],
        )


class Options(Methods, ProcessDefinition):
    def define_process(self, builder: Builder):
        if builder.option("bar", False):
            builder.task(self.foo)
            builder.task(self.foo_ctx)
            builder.task(self.foo_task)


class Sequential(Methods, ProcessDefinition):
    def define_process(self, builder: Builder):
        builder.task(self.foo)
        with builder.sequential() as b:
            b.task(self.bar)
            b.task(self.baz)
        builder.task(self.qux)


class Concurrent(Methods, ProcessDefinition):
    def define_process(self, builder: Builder):
        builder.task(self.foo)
        with builder.concurrent() as b:
            b.task(self.bar)
            b.task(self.baz)
        builder.task(self.qux)


class Each(Methods, ProcessDefinition):
    def item(self, count: int, **_):
        for c in range(count):
            yield {
                "bar": c,
            }

    def define_process(self, builder: Builder):
        for b in builder.each(self.item):
            b.task(self.foo)


class EachEmpty(Methods, ProcessDefinition):
    def item(self, count: int, **kwargs) -> Iterator[dict]:
        pass

    def define_process(self, builder: Builder):
        for b in builder.each(self.item):
            b.task(self.foo)


class EachWithDescription(Methods, ProcessDefinition):
    def item(self, count: int, **_) -> Iterator[Tuple[dict, str]]:
        for c in range(count):
            yield (
                {
                    "bar": c,
                },
                f"Item {c}",
            )

    def define_process(self, builder: Builder):
        for b in builder.each(self.item):
            b.task(self.foo)


class Transform(Methods, ProcessDefinition):
    def transform_args(self, foo: int, **_):
        return {
            "bar": foo * 2,
        }

    def define_process(self, builder: Builder):
        with builder.transform(self.transform_args) as t:
            t.task(self.foo)


class TransformWithDescription(Methods, ProcessDefinition):
    def transform_args(self, foo: int, **_):
        return (
            {
                "bar": foo * 2,
            },
            f"Item {foo}",
        )

    def define_process(self, builder: Builder):
        with builder.transform(self.transform_args) as t:
            t.task(self.foo)
            t.task(self.foo_ctx)
            t.task(self.foo_task)


class SubProcessSequential(Methods, ProcessDefinition):
    def define_process(self, builder: Builder):
        builder.task(self.bar)
        builder.sub_process(SimpleSequential)
        builder.task(self.baz)


class SubProcessConcurrent(Methods, ProcessDefinition):
    def define_process(self, builder: Builder):
        builder.task(self.bar)
        builder.sub_process(SimpleConcurrent)
        builder.task(self.baz)
