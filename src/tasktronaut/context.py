"""
Context module.
"""


class Context:  # pylint: disable=too-few-public-methods
    """
    A context object that carries execution information during process execution.

    The Context class serves as a container for state and metadata that may be
    needed by tasks during process execution. Tasks can optionally accept a
    Context parameter to access execution-specific information and maintain
    state across the process.

    This is a minimal class designed to be extended or used as a base for
    storing execution context data passed between tasks in a Tasktronaut process.
    """
