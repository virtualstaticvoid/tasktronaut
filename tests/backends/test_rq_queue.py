import unittest
import uuid
from unittest import mock

import fakeredis
import rq
from redis.client import Pipeline
from rq.job import JobStatus

from tasktronaut.backends.rq import JobScopedReadyJobRegistry, RqQueue


def succeed() -> None:
    return None


class RedisTestCase(unittest.TestCase):
    def setUp(self):
        self.connection = fakeredis.FakeStrictRedis()
        self.queue_name = f"test-{uuid.uuid4().hex}"
        self.queue = rq.Queue(self.queue_name, connection=self.connection)

    def tearDown(self):
        self.connection.flushall()

    def enqueue_job_and_dependent(self):
        job = self.queue.enqueue(succeed)
        dependent = self.queue.enqueue(succeed, depends_on=job)
        return job, dependent

    def patch_execute(self, before_execute):
        """Run `before_execute` once, ahead of the first watched transaction it accepts."""
        execute = Pipeline.execute
        called = []

        def side_effect(pipeline, *args, **kwargs):
            if pipeline.watching and not called and before_execute():
                called.append(True)
            return execute(pipeline, *args, **kwargs)

        return (
            mock.patch.object(
                Pipeline, "execute", autospec=True, side_effect=side_effect
            ),
            called,
        )

    def write_ready_registry(self, key: str) -> bool:
        # another worker readies and enqueues a dependent of its own
        self.connection.zadd(key, {"concurrent-writer": 0})
        self.connection.zrem(key, "concurrent-writer")
        return True


class JobScopedReadyJobRegistryTestCase(RedisTestCase):
    """A ready job's claim must only conflict with changes to that job."""

    def make_dependent_ready(self):
        job, dependent = self.enqueue_job_and_dependent()
        job.set_status(JobStatus.FINISHED)
        self.queue.move_dependents_to_ready(job)
        return dependent

    def test_enqueues_ready_job_when_ready_registry_changes_concurrently(self):
        dependent = self.make_dependent_ready()
        registry = JobScopedReadyJobRegistry(queue=self.queue)

        patcher, called = self.patch_execute(
            lambda: self.write_ready_registry(registry.key)
        )
        with patcher:
            enqueued = registry.enqueue_jobs([dependent.id])

        self.assertTrue(called)
        self.assertEqual([j.id for j in enqueued], [dependent.id])
        self.assertNotIn(dependent, registry)
        self.assertEqual(dependent.get_status(), JobStatus.QUEUED)
        self.assertEqual(self.queue.get_job_ids().count(dependent.id), 1)

    def test_does_not_enqueue_ready_job_claimed_concurrently(self):
        dependent = self.make_dependent_ready()
        registry = JobScopedReadyJobRegistry(queue=self.queue)

        def claim_concurrently():
            # worker maintenance claims and enqueues the same job
            self.queue.ready_job_registry.cleanup()
            return True

        patcher, called = self.patch_execute(claim_concurrently)
        with patcher:
            enqueued = registry.enqueue_jobs([dependent.id])

        self.assertTrue(called)
        self.assertEqual(enqueued, [])
        self.assertEqual(dependent.get_status(), JobStatus.QUEUED)
        self.assertEqual(self.queue.get_job_ids().count(dependent.id), 1)

    def test_enqueue_jobs_without_job_ids(self):
        registry = JobScopedReadyJobRegistry(queue=self.queue)
        self.assertEqual(registry.enqueue_jobs([]), [])

    def test_drops_missing_job(self):
        registry = JobScopedReadyJobRegistry(queue=self.queue)
        self.connection.zadd(registry.key, {"missing": 0})

        self.assertEqual(registry.enqueue_jobs(["missing"]), [])
        self.assertIsNone(self.connection.zscore(registry.key, "missing"))

    def test_skips_ready_job_not_in_registry(self):
        dependent = self.make_dependent_ready()
        registry = JobScopedReadyJobRegistry(queue=self.queue)
        self.connection.zrem(registry.key, dependent.id)

        self.assertEqual(registry.enqueue_jobs([dependent.id]), [])
        self.assertEqual(dependent.get_status(), JobStatus.READY_TO_ENQUEUE)
        self.assertNotIn(dependent.id, self.queue.get_job_ids())

    def test_drops_job_no_longer_ready(self):
        dependent = self.make_dependent_ready()
        dependent.set_status(JobStatus.CANCELED)
        registry = JobScopedReadyJobRegistry(queue=self.queue)

        self.assertEqual(registry.enqueue_jobs([dependent.id]), [])
        self.assertNotIn(dependent, registry)
        self.assertNotIn(dependent.id, self.queue.get_job_ids())


class RqQueueTestCase(RedisTestCase):
    """A dependent must be enqueued once its dependency succeeds, despite contention."""

    def test_ready_job_registry(self):
        queue = RqQueue(self.queue_name, connection=self.connection)
        self.assertIsInstance(queue.ready_job_registry, JobScopedReadyJobRegistry)

    def test_dependent_is_enqueued_when_ready_registry_changes_concurrently(self):
        _, dependent = self.enqueue_job_and_dependent()
        queue = RqQueue(self.queue_name, connection=self.connection)
        key = queue.ready_job_registry.key

        def is_enqueueing_ready_dependent():
            if self.connection.zscore(key, dependent.id) is None:
                return False
            return self.write_ready_registry(key)

        worker = rq.SimpleWorker(
            [queue], connection=self.connection, queue_class=RqQueue
        )
        patcher, called = self.patch_execute(is_enqueueing_ready_dependent)
        with patcher:
            worker.work(burst=True)

        self.assertTrue(called)
        self.assertNotIn(dependent, queue.ready_job_registry)
        self.assertEqual(dependent.get_status(), JobStatus.FINISHED)
