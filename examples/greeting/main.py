import redis

from greeting_process import GreetingProcess
from tasktronaut.backends.rq import RqBackend, RqQueue


def main():
    connection = redis.Redis()
    queue = RqQueue(connection=connection)
    backend = RqBackend(queue=queue)

    process = GreetingProcess.build(name="Chris")
    job = process.enqueue(backend=backend)

    print("Process enqueued.")
    print(job)


if __name__ == "__main__":
    main()
