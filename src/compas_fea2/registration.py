"""Backend registration for compas_fea2 (minimal, single-backend).

- Entry point group: "compas_fea2.backends".
- Plugins expose an entry-point callable that either:
  1) accepts a register function and calls it with {BaseClass: ImplClass}, or
  2) returns that mapping directly.
- set_backend(name) locates the entry point by name and activates it by replacing the registry.
"""

BACKENDS_ENTRYPOINT_GROUP = "compas_fea2.backends"
_IMPLS = {}


def register_backend(mapping, *, backend_name=None):
    """Install the given mapping as the single active backend."""
    _IMPLS.clear()
    _IMPLS.update(mapping)


def set_backend(plugin):
    """Activate a backend by its entry-point name."""
    from importlib.metadata import entry_points

    eps = list(entry_points(group=BACKENDS_ENTRYPOINT_GROUP)) if entry_points else []

    def name_of(ep):
        return getattr(ep, "name", None) or getattr(ep, "key", None)

    match = next((ep for ep in eps if name_of(ep) == plugin), None)
    if not match:
        available = [name_of(e) for e in eps]
        raise RuntimeError(f"Backend entry point '{plugin}' not found. Available: {available}")

    loader = match.load()

    try:
        result = loader(register_backend)
    except TypeError:
        result = loader()

    if isinstance(result, dict):
        register_backend(result)
    elif not _IMPLS:
        raise RuntimeError(
            f"Backend loader '{plugin}' did not return a mapping or register anything.")


def _get_backend_implementation(base):
    """Return the implementation class for the given base type, or None."""
    return _IMPLS.get(base)


__all__ = [
    "BACKENDS_ENTRYPOINT_GROUP",
    "register_backend",
    "set_backend",
    "_get_backend_implementation",
]
