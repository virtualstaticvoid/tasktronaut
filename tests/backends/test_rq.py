import unittest
from unittest import mock

import rq

from tasktronaut.backends.rq import RqBackend
from tests.mocks import MockDefinition


class RqBackendTestCase(unittest.TestCase):
    def setUp(self):
        self.queue = mock.MagicMock()
        self.backend = RqBackend(queue=self.queue)

    def test_enqueue_perform_start(self):
        self.backend.enqueue_perform_start(
            identifier="test",
            module_name="test",
            definition_class="test",
            depends_on=None,
        )
        self.assertTrue(self.queue.enqueue.called)

    def test_enqueue_perform_task(self):
        self.backend.enqueue_perform_task(
            identifier="test",
            module_name="test",
            definition_class="test",
            function_name="test",
            description="test",
            kwargs={},
            depends_on=None,
        )
        self.assertTrue(self.queue.enqueue.called)

    @mock.patch.object(rq, "get_current_job")
    @mock.patch.object(MockDefinition, "task_success")
    def test_rq_perform_task(self, mock_task_success, mock_get_current_job):
        self.backend.rq_perform_task(
            identifier="test",
            module_name=MockDefinition.__module__,
            definition_class=MockDefinition.__qualname__,
            function_name="task_success",
            task_description="test",
            task_kwargs={},
        )
        self.assertTrue(mock_get_current_job.called)
        self.assertTrue(mock_task_success.called)

    def test_enqueue_perform_complete(self):
        self.backend.enqueue_perform_complete(
            identifier="test",
            module_name="test",
            definition_class="test",
            depends_on=None,
        )
        self.assertTrue(self.queue.enqueue.called)
