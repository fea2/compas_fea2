try:
    from importlib.metadata import entry_points
except Exception:
    entry_points = None

BACKENDS_ENTRYPOINTS = "compas_fea2.backends"
_IMPLS = {}
_ACTIVE_BACKEND = None


def register_backend(mapping, *, backend_name=None):
    """Replace the active backend implementations with the given mapping."""
    global _ACTIVE_BACKEND
    _IMPLS.clear()
    _IMPLS.update(mapping)
    if backend_name:
        _ACTIVE_BACKEND = backend_name


def set_backend(plugin):
    """Load exactly one backend by entry point name and make it active."""
    eps = list(entry_points(group=BACKENDS_ENTRYPOINTS)) if entry_points else []  # type: ignore[arg-type]

    # Find the matching entry point by name/key
    match = None
    for ep in eps:
        name = getattr(ep, "name", None) or getattr(ep, "key", None)
        if name == plugin:
            match = ep
            break
    if not match:
        available = [getattr(e, "name", None) or getattr(e, "key", None) for e in eps]
        raise RuntimeError(f"Backend entry point '{plugin}' not found. Available: {available}")

    # Load the backend loader callable
    loader = match.load()

    # Call loader: either accepts register function or returns a mapping
    global _ACTIVE_BACKEND
    try:
        result = loader(register_backend)
    except TypeError:
        result = loader()

    if isinstance(result, dict):
        register_backend(result, backend_name=plugin)
    elif _ACTIVE_BACKEND is None:
        _ACTIVE_BACKEND = plugin


def get_active_backend():
    return _ACTIVE_BACKEND


def _get_backend_implementation(base):
    return _IMPLS.get(base)


__all__ = [
    "BACKENDS_ENTRYPOINTS",
    "register_backend",
    "set_backend",
    "get_active_backend",
    "_get_backend_implementation",
]
