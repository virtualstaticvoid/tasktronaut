import logging
import pathlib
import sys

import redis
import rq

import tasktronaut as tq
from tasktronaut.backends.rq import RqBackend
from tasktronaut.utils import to_kwargs

LOG_FILE = "smoke_test_rq.log"

# ensure log file cleared
pathlib.Path(LOG_FILE).unlink(missing_ok=True)

file_handler = logging.FileHandler(LOG_FILE)
logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


class SimpleDefinition(tq.ProcessDefinition):
    @tq.task
    def task1(self, a, **_):
        logger.info("Executing task1 with %s", a)

    @tq.task
    def task2(self, a, b, **_):
        logger.info("Executing task2 with %s and %s", a, b)

    @tq.task
    def task3(self, a, **_):
        logger.info("Executing task3 with %s", a)

    def for_each(self, **kwargs):
        yield to_kwargs(kwargs, b="bar")
        yield to_kwargs(kwargs, b="baz")
        yield to_kwargs(kwargs, b="qux")

    def define_process(self, builder: tq.Builder):
        builder.task(self.task1)
        for b in builder.each(self.for_each):
            b.task(self.task2)
        builder.task(self.task3)


def main():
    connection = redis.Redis()
    queue = rq.Queue(connection=connection)
    backend = RqBackend(queue=queue)

    process = SimpleDefinition.build(a="foo")
    job: rq.job.Job = process.enqueue(backend)

    worker = rq.SimpleWorker([queue])

    # blocking call, until all jobs are finished
    # if no jobs, will return immediately
    worker.work(burst=True)

    assert job.is_finished, "ERROR: Process never finished."

    with open(LOG_FILE, "r", encoding="UTF-8") as f:
        logs = f.read()

    print(logs)

    assert "Executing task1 with foo" in logs, "ERROR: task1 never executed"
    assert "Executing task2 with foo and bar" in logs, "ERROR: task2(1) never executed"
    assert "Executing task2 with foo and baz" in logs, "ERROR: task2(2) never executed"
    assert "Executing task2 with foo and qux" in logs, "ERROR: task2(3) never executed"
    assert "Executing task3 with foo" in logs, "ERROR: task3 never executed"

    return 0


if __name__ == "__main__":
    sys.exit(main())
