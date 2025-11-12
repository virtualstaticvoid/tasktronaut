"""
Utility and supporting methods.
"""

import importlib

from typing import Any, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .process import ProcessDefinition  # noqa


def to_dict(**kwargs: Any) -> dict[str, Any]:
    """
    Convert keyword arguments to a dictionary.

    This utility function packages keyword arguments into a dictionary,
    providing a convenient way to convert variadic keyword arguments
    into a dictionary structure.

    :param kwargs: Arbitrary keyword arguments to convert
    :type kwargs: Dict[str, Any]
    :return: Dictionary containing all passed keyword arguments
    :rtype: dict[str, Any]
    """
    return kwargs


def to_kwargs(base: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """
    Merge a base dictionary with additional keyword arguments.

    Creates a new dictionary by copying the base dictionary and updating
    it with the provided keyword arguments. The original base dictionary
    is not modified. Keyword arguments take precedence over base dictionary
    values in case of key conflicts.

    :param base: Base dictionary to copy and update
    :type base: dict[str, Any]
    :param kwargs: Keyword arguments to merge into the base dictionary
    :type kwargs: Dict[str, Any]
    :return: New dictionary containing merged key-value pairs
    :rtype: dict[str, Any]
    """
    d = base.copy()
    d.update(kwargs)
    return d


def load_definition(
    module_name: str,
    definition_class: str,
) -> "ProcessDefinition":
    """
    Dynamically load and instantiate a process definition class.

    This function provides dynamic loading of ProcessDefinition subclasses
    from specified modules. It imports the module by name, retrieves the
    definition class from that module, and returns a new instance of the class.

    :param module_name: Fully qualified module name to import
    :type module_name: str
    :param definition_class: Name of the ProcessDefinition class to load from the module
    :type definition_class: str
    :return: A new instance of the specified ProcessDefinition class
    :rtype: ProcessDefinition

    :raises ImportError: If the module cannot be imported
    :raises AttributeError: If the definition_class does not exist in the module
    :raises TypeError: If the loaded class cannot be instantiated
    """

    # SECURITY: make sure you trust the module that gets loaded!
    # consider using an allowed list of module names to
    # prevent unknown modules (and definitions) from being
    # loaded dynamically.

    module = importlib.import_module(module_name)
    definition_type = getattr(module, definition_class)
    # return new instance of definition type
    return cast("ProcessDefinition", definition_type())
