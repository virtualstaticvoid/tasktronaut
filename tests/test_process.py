import unittest
from abc import ABC
from typing import Optional, Type
from unittest import mock

from tasktronaut import Backend
from tasktronaut.backend import Job
from tasktronaut.process import ConcurrentProcess, Process, SequentialProcess
from tasktronaut.steps import Step
from . import mocks


class MockProcess(Process):
    def enqueue(self, backend: Backend, start_job: Optional[Job] = None) -> Job:
        pass


class ProcessTestCase(unittest.TestCase):
    def setUp(self):
        self.process = MockProcess(
            identifier="foo",
            definition=mocks.MockDefinition,
        )

    def test_is_process(self):
        self.assertTrue(self.process.is_process)

    def test_str(self):
        result = str(self.process)
        self.assertIsNotNone(result)
        self.assertTrue("foo" in result)

    def test_repr(self):
        result = repr(self.process)
        self.assertIsNotNone(result)
        self.assertTrue("foo" in result)


class ProcessDefinitionTestCase(unittest.TestCase):
    def test_create_process(self):
        result = mocks.MockDefinition.create_process(
            identifier="foo",
            definition=mocks.MockDefinition,
        )
        self.assertIsNotNone(result)

    @mock.patch.object(mocks.MockDefinition, "define_process")
    def test_build(self, mock_define_process):
        result = mocks.MockDefinition.build(
            identifier="foo",
            definition=mocks.MockDefinition,
        )
        self.assertIsNotNone(result)
        self.assertTrue(mock_define_process.called)

    def test_on_started(self):
        mocks.MockBasicDefinition().on_started(
            identifier="foo",
        )

    def test_around_task(self):
        called = False
        with mocks.MockBasicDefinition().around_task(
            identifier="foo",
            step="bar",
            description="baz",
        ):
            called = True

        self.assertTrue(called)

    def test_on_completed(self):
        mocks.MockBasicDefinition().on_completed(
            identifier="foo",
        )

    def test_on_failed(self):
        mocks.MockBasicDefinition().on_failed(
            identifier="foo",
            step="bar",
            e=NotImplementedError(),
        )

    def test_on_cancelled(self):
        mocks.MockBasicDefinition().on_cancelled(
            identifier="foo",
        )


class ProcessTestCaseBase(ABC, unittest.TestCase):
    process_type: Type[Process]

    @classmethod
    def setUpClass(cls):
        if cls is ProcessTestCaseBase:
            raise unittest.SkipTest("Abstract test case; skipping.")
        super().setUpClass()

    def setUp(self):
        # sanity check
        self.assertIsNotNone(self.process_type)

        self.process = self.process_type(
            identifier="foo",
            definition=mocks.MockDefinition,
        )

    def test_enqueue_no_steps(self):
        backend = mock.MagicMock(spec=Backend)
        self.process.enqueue(backend)
        self.assertTrue(backend.enqueue_perform_start.called)
        self.assertTrue(backend.enqueue_perform_complete.called)

    @mock.patch.object(MockProcess, "enqueue")
    def test_enqueue_with_steps(self, mock_process_enqueue):
        backend = mock.MagicMock(spec=Backend)
        self.process.steps.extend(
            [
                Step(
                    func=mocks.task_basic,
                    description="foo",
                    kwargs={},
                ),
                MockProcess(
                    identifier="bar",
                    definition=mocks.MockDefinition,
                ),
                Step(
                    func=mocks.task_basic,
                    description="baz",
                    kwargs={},
                ),
            ]
        )
        self.process.enqueue(backend)
        self.assertTrue(backend.enqueue_perform_start.called)
        self.assertEqual(2, backend.enqueue_perform_task.call_count)
        self.assertTrue(backend.enqueue_perform_complete.called)
        self.assertTrue(mock_process_enqueue.called)


class SequentialProcessTestCase(ProcessTestCaseBase):
    process_type = SequentialProcess


class ConcurrentProcessTestCase(ProcessTestCaseBase):
    process_type = ConcurrentProcess
