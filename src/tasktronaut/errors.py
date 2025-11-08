"""
Errors module.
"""


class NonRetryableProcessError(Exception):  # pragma: no cover
    """Exception to indicate a process error that should not be retried.

    This exception is used to signal that a process has encountered an error
    condition that is permanent and attempting to retry the process would be
    futile. When this exception is raised during process execution, the process
    will terminate without attempting any configured retry logic.

    :raises NonRetryableProcessError: When a process encounters an unrecoverable error.
    """


class CancelProcessError(Exception):  # pragma: no cover
    """Raised to cancel the execution of a process.

    This exception is used to signal that a process should be cancelled and
    terminated immediately. When raised during process execution, it will halt
    the current process and any pending tasks without completing the normal
    process flow.

    Whilst a ``NonRetryableProcessError` has the same effect; to cancel the
    execution of a process, ``CancelProcessError`` causes any enqueued tasks
    to be removed from the queue.

    :raises CancelProcessError: When a process needs to be cancelled.
    """
