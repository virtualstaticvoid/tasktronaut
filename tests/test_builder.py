import datetime
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest import mock

from tasktronaut.builder import Builder
from tasktronaut.utils import to_dict
from . import mocks


class BuilderTestCase(unittest.TestCase):
    @contextmanager
    def assertWith(self, context):  # pylint: disable=invalid-name
        result = False
        with context as var:
            yield var
            result = True

        self.assertTrue(result, f"Failed to enter {context} context.")

    def setUp(self):
        self.description = "corge"
        self.kwargs = to_dict(
            foo="bar",
            baz=1,
            qux=datetime.date(2025, 1, 1),
        )
        self.options = SimpleNamespace(a=True, b=False, c="quux")
        self.builder = Builder(
            process=mock.MagicMock(),
            kwargs=self.kwargs,
            options=self.options,
            description=self.description,
        )

    def test_expected_arguments_valid(self):
        self.builder.expected_arguments(
            foo=str,
            baz=int,
            qux=datetime.date,
        )

    def test_expected_arguments_valid_without_types(self):
        self.builder.expected_arguments(
            foo=None,
            baz=None,
            qux=None,
        )

    def test_expected_arguments_missing(self):
        self.assertRaises(
            TypeError,
            self.builder.expected_arguments,
            quux=int,
        )

    def test_expected_arguments_invalid_type(self):
        self.assertRaises(
            ValueError,
            self.builder.expected_arguments,
            foo=int,
        )

    def test_concurrent_yields_builder(self):
        # pylint: disable=no-member
        with self.assertWith(self.builder.concurrent()) as builder:
            self.assertIsInstance(builder, Builder)
            self.assertEqual(self.kwargs, builder.kwargs)
            self.assertEqual(self.options, builder.options)
            self.assertEqual(self.description, builder.description)

    def test_concurrent_adds_step(self):
        with self.assertWith(self.builder.concurrent()) as b2:
            self.assertIsInstance(b2, Builder)

        self.assertTrue(self.builder.process.steps.append.called)

    def test_sequential_yields_builder(self):
        # pylint: disable=no-member
        with self.assertWith(self.builder.sequential()) as builder:
            self.assertIsInstance(builder, Builder)

            self.assertEqual(self.kwargs, builder.kwargs)
            self.assertEqual(self.options, builder.options)
            self.assertEqual(self.description, builder.description)

    def test_sequential_adds_step(self):
        with self.assertWith(self.builder.sequential()) as b2:
            self.assertIsInstance(b2, Builder)

        self.assertTrue(self.builder.process.steps.append.called)

    def test_task(self):
        self.builder.task(mocks.task_basic)
        self.assertTrue(self.builder.process.steps.append.called)
        step, *_ = self.builder.process.steps.append.call_args[0]
        self.assertIsNone(step.description)

    def test_task_with_description(self):
        self.builder.task(
            mocks.task_with_description,
        )
        self.assertTrue(self.builder.process.steps.append.called)
        step, *_ = self.builder.process.steps.append.call_args[0]
        self.assertEqual("foo-bar-baz", step.description)

    def test_task_override_description(self):
        self.builder.task(mocks.task_with_description, description="foo")
        self.assertTrue(self.builder.process.steps.append.called)
        step, *_ = self.builder.process.steps.append.call_args[0]
        self.assertEqual("foo", step.description)

    def test_sub_process(self):
        pass

    def test_each(self):
        def _item(**_):
            yield {}
            yield {}
            yield {}

        count = 0
        for b2 in self.builder.each(_item):
            self.assertIsInstance(b2, Builder)
            count += 1

        self.assertEqual(3, count)

    def test_each_with_description(self):
        def _item(**_):
            yield {}, "1"
            yield {}, "2"
            yield {}, "3"

        for i, b2 in enumerate(self.builder.each(_item), start=1):
            self.assertIsInstance(b2, Builder)
            self.assertEqual(str(i), b2.description)

    def test_transform(self):
        def _transform(**_):
            return {}

        with self.assertWith(self.builder.transform(_transform)) as b2:
            self.assertIsInstance(b2, Builder)

    def test_transform_with_description(self):
        def _transform(**_):
            return (
                {},
                "baz",
            )

        with self.assertWith(self.builder.transform(_transform)) as b2:
            self.assertIsInstance(b2, Builder)
            self.assertEqual("baz", b2.description)

    def test_option(self):
        self.assertTrue(self.builder.option("a"))
        self.assertFalse(self.builder.option("b"))
        self.assertEqual("quux", self.builder.option("c"))
        self.assertEqual("bar", self.builder.option("baz", "bar"))
        self.assertIsNone(self.builder.option("baz"))

    # pylint: disable=protected-access
    def test_convert_options(self):
        # simple namespace
        self.assertEqual(self.options, self.builder._convert_options(self.options))

        # dict
        self.assertEqual(
            self.options,
            self.builder._convert_options(
                {
                    "a": True,
                    "b": False,
                    "c": "quux",
                }
            ),
        )

        # none
        self.assertIsNotNone(self.builder._convert_options())

        # invalid
        self.assertIsInstance(
            self.builder._convert_options(1),  # type: ignore
            SimpleNamespace,
        )
