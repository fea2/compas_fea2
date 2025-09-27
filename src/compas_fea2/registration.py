"""Backend registration for compas_fea2.

- Entry point group: "compas_fea2.backends".
- Plugins expose an entry-point callable that returns a mapping `{BaseClass: ImplClass}`.
- `set_backend(name)` locates the entry point by name and activates it by replacing the registry IMPLS.
"""

from importlib.metadata import entry_points
from typing import Dict, Mapping, Type

_IMPLS: Dict[Type, Type] = {}  # Mapping of base classes to active implementation classes

def _register_backend(mapping: Mapping[Type, Type]):
    """Install the given mapping as the single active backend."""
    _IMPLS.clear()
    _IMPLS.update(dict(mapping))


def set_backend(plugin):
    """Activate a backend by its entry-point name."""

    if _IMPLS:
        raise RuntimeError("A backend is already active; switching backends at runtime is not allowed.")

    eps = entry_points(group="compas_fea2.backends")
    epmap = {getattr(e, "name", None) or getattr(e, "key", None): e for e in eps}
    match = epmap.get(plugin)
    if not match:
        raise RuntimeError(f"Backend entry point '{plugin}' not found. Available: {list(epmap)}")
    loader = match.load()
    result = loader()
    if not isinstance(result, dict):
        raise RuntimeError(f"Backend loader '{plugin}' must return a mapping {{BaseClass: ImplClass}}.")
    _register_backend(result)


def list_backends() -> list[str]:
    return [getattr(e, "name", None) or getattr(e, "key", None) for e in entry_points(group="compas_fea2.backends")]

