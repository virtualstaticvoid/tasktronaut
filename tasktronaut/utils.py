import importlib

from typing import Any, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .process import ProcessDefinition  # noqa


def to_dict(**kwargs: Any) -> dict[str, Any]:
    return kwargs


def to_kwargs(base: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    d = base.copy()
    d.update(kwargs)
    return d


def load_definition(
    module_name: str,
    definition_class: str,
) -> "ProcessDefinition":
    module = importlib.import_module(module_name)
    definition_type = getattr(module, definition_class)
    # return new instance of definition type
    return cast("ProcessDefinition", definition_type())
