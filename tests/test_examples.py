import datetime
import unittest
from unittest import mock

from tasktronaut import Backend
from tasktronaut.process import ConcurrentProcess, SequentialProcess
from .examples import (
    Arguments,
    Concurrent,
    Each,
    EachWithDescription,
    Options,
    Sequential,
    SimpleConcurrent,
    SimpleSequential,
    SubProcessConcurrent,
    SubProcessSequential,
    Transform,
    TransformWithDescription,
)


class ProcessTestCase(unittest.TestCase):
    def test_build_sequential(self):
        process = SimpleSequential.build()
        self.assertEqual(3, len(process.steps))

    def test_build_concurrent(self):
        process = SimpleConcurrent.build()
        self.assertEqual(3, len(process.steps))

    def test_build_kwargs(self):
        process = SimpleSequential.build(foo="bar")
        self.assertEqual(3, len(process.steps))
        for step in process.steps:
            self.assertEqual({"foo": "bar"}, step.kwargs)

    def test_expected_arguments(self):
        process = Arguments.build(
            foo="bar",
            bar=1,
            baz="whatever",
            qux=None,  # optional
            quux=[1, 2, 3],
        )
        self.assertIsNotNone(process)

        process = Arguments.build(
            foo="bar",
            bar=1,
            baz="whatever",
            qux=datetime.date(2025, 7, 3),
            quux=[1, 2, 3],
        )
        self.assertIsNotNone(process)

        # missing arguments
        self.assertRaises(
            TypeError,
            Arguments.build,
            foo="bar",
        )

        # invalid values
        self.assertRaises(
            ValueError,
            Arguments.build,
            foo=None,  # invalid, should be str
            bar=None,
            baz=None,
            qux=None,
            quux=None,
        )

        self.assertRaises(
            ValueError,
            Arguments.build,
            foo=1,  # invalid, should be str
            bar=None,
            baz=None,
            qux=None,
            quux=None,
        )

        self.assertRaises(
            ValueError,
            Arguments.build,
            foo="bar",
            bar=1,
            baz="whatever",
            qux="not a date",  # invalid
            quux=[1, 2, 3],
        )

        self.assertRaises(
            ValueError,
            Arguments.build,
            foo="bar",
            bar=1,
            baz="whatever",
            qux="not a date",
            quux=1,  # invalid
        )

    def test_build_options(self):
        process = Options.build(options={"bar": True})
        self.assertEqual(3, len(process.steps))

        process = Options.build(options={"bar": False})
        self.assertEqual(0, len(process.steps))

        process = Options.build()
        self.assertEqual(0, len(process.steps))

    def test_sequential(self):
        process = Sequential.build(foo="bar")
        self.assertEqual(3, len(process.steps))
        sequential = process.steps[1]
        self.assertTrue(sequential.is_process)
        self.assertIsInstance(sequential, SequentialProcess)
        self.assertEqual(2, len(sequential.steps))

        for step in sequential.steps:
            self.assertEqual({"foo": "bar"}, step.kwargs)

    def test_concurrent(self):
        process = Concurrent.build(foo="bar")
        self.assertEqual(3, len(process.steps))
        concurrent = process.steps[1]
        self.assertTrue(concurrent.is_process)
        self.assertIsInstance(concurrent, ConcurrentProcess)
        self.assertEqual(2, len(concurrent.steps))

        for step in concurrent.steps:
            self.assertEqual({"foo": "bar"}, step.kwargs)

    def test_each(self):
        process = Each.build(count=3)
        self.assertEqual(3, len(process.steps))
        for i, step in enumerate(process.steps):
            self.assertEqual({"bar": i}, step.kwargs)
            self.assertIsNone(step.description)

    def test_each_with_description(self):
        process = EachWithDescription.build(count=3)
        self.assertEqual(3, len(process.steps))
        for i, step in enumerate(process.steps):
            self.assertEqual({"bar": i}, step.kwargs)
            self.assertIsNotNone(step.description)

    def test_transform(self):
        process = Transform.build(foo=4)
        self.assertEqual(1, len(process.steps))
        for step in process.steps:
            self.assertEqual({"bar": 8}, step.kwargs)
            self.assertIsNone(step.description)

    def test_transform_with_description(self):
        process = TransformWithDescription.build(foo=4)
        self.assertEqual(3, len(process.steps))
        for step in process.steps:
            self.assertEqual({"bar": 8}, step.kwargs)
            self.assertIsNotNone(step.description)

    def test_sub_process_sequential(self):
        process = SubProcessSequential.build(foo="bar")
        self.assertEqual(3, len(process.steps))

        subprocess = process.steps[1]
        self.assertTrue(subprocess.is_process)
        self.assertIsInstance(subprocess, SequentialProcess)
        self.assertEqual(3, len(subprocess.steps))
        for step in subprocess.steps:
            self.assertEqual({"foo": "bar"}, step.kwargs)

    def test_sub_process_concurrent(self):
        process = SubProcessConcurrent.build(foo="bar")
        self.assertEqual(3, len(process.steps))

        subprocess = process.steps[1]
        self.assertTrue(subprocess.is_process)
        self.assertIsInstance(subprocess, SequentialProcess)
        self.assertEqual(3, len(subprocess.steps))
        for step in subprocess.steps:
            self.assertEqual({"foo": "bar"}, step.kwargs)

    def test_sequential_enqueue(self):
        backend = mock.Mock(spec=Backend)

        process = SimpleSequential.build(foo=1)
        process.enqueue(backend=backend)

        self.assertTrue(backend.enqueue_perform_start.called)
        self.assertTrue(backend.enqueue_perform_task.called)
        self.assertTrue(backend.enqueue_perform_complete.called)

        kwargs = backend.enqueue_perform_task.call_args.kwargs.get("kwargs")
        self.assertEqual(1, kwargs.get("foo"))

    def test_concurrent_enqueue(self):
        backend = mock.Mock(spec=Backend)

        process = SimpleSequential.build(foo=1)
        process.enqueue(backend=backend)

        self.assertTrue(backend.enqueue_perform_start.called)
        self.assertTrue(backend.enqueue_perform_task.called)
        self.assertTrue(backend.enqueue_perform_complete.called)

        kwargs = backend.enqueue_perform_task.call_args.kwargs.get("kwargs")
        self.assertEqual(1, kwargs.get("foo"))
