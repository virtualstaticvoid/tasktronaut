"""
Tasktronaut: A Python library for defining and executing process workflows.

The tasktronaut package provides a framework for building complex process definitions
with support for sequential and concurrent execution, sub-processes, conditional logic,
and iterative patterns.

This module serves as the main entry point, exposing the primary public API for
the library.
"""

from importlib.metadata import PackageNotFoundError, version

from .backend import Backend
from .builder import Builder
from .context import Context
from .decorators import task
from .process import ExecutionMode, ProcessDefinition

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "0.0.0.dev"

__all__ = (
    "Backend",
    "Builder",
    "Context",
    "ExecutionMode",
    "ProcessDefinition",
    "task",
    "__version__",
)
