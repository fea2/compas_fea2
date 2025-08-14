import os
from collections import defaultdict
from dotenv import load_dotenv
from compas.tolerance import Tolerance
from compas.geometry import Frame
from contextlib import contextmanager
from contextvars import ContextVar
from importlib import import_module
try:
    from importlib.metadata import entry_points
except Exception:
    entry_points = None  # Python <3.8 fallback


__author__ = ["Francesco Ranaudo"]
__copyright__ = "COMPAS Association"
__license__ = "MIT License"
__email__ = "francesco.ranaudo@gmail.com"
__version__ = "0.3.1"


def init_fea2(verbose=False, point_overlap=True, global_tolerance=1, precision=3, part_nodes_limit=100000):
    """Create a default environment file if it doesn't exist and loads its variables.

    Parameters
    ----------
    verbose : bool, optional
        Be verbose when printing output, by default False
    point_overlap : bool, optional
        Allow two nodes to be at the same location, by default True
    global_tolerance : int, optional
        Tolerance for the model, by default 1
    precision : str, optional
        Values approximation, by default '3'.
        See `compas.tolerance.Tolerance.precision` for more information.
    part_nodes_limit : int, optional
        Limit of nodes for a part, by default 100000.
    """
    env_path = os.path.abspath(os.path.join(HERE, ".env"))
    if not os.path.exists(env_path):
        with open(env_path, "x") as f:
            f.write(
                "\n".join(
                    [
                        "VERBOSE={}".format(verbose),
                        "POINT_OVERLAP={}".format(point_overlap),
                        "GLOBAL_TOLERANCE={}".format(global_tolerance),
                        "PRECISION={}".format(precision),
                    ]
                )
            )
    load_dotenv(env_path)


# pluggable function to be
def _register_backend():
    """Create the class registry for the plugin.

    Raises
    ------
    NotImplementedError
        This function is implemented within the backend plugin implementation.
    """
    raise NotImplementedError


def register_backend(name: str):
    """Return the registry dict for a backend name, creating it if needed."""
    reg = BACKENDS.get(name)
    if reg is None:
        reg = {}
        BACKENDS[name] = reg
    return reg


def set_backend(plugin: str):
    """Set the active backend by plugin name.

    Keeps compatibility with plugins exposing _register_backend().
    """
    global BACKEND
    BACKEND = plugin
    CURRENT_BACKEND.set(plugin)

    # Try to import plugin and call its registration hook (legacy mode).
    try:
        mod = import_module(plugin)
        if hasattr(mod, "_register_backend"):
            mod._register_backend()
    except ImportError:
        print("backend plugin not found. Make sure that you have installed it before.")


@contextmanager
def use_backend(plugin: str):
    """Temporarily activate a backend within a 'with' block."""
    token = CURRENT_BACKEND.set(plugin)
    try:
        # lazy import/registration for legacy plugins
        try:
            mod = import_module(plugin)
            if hasattr(mod, "_register_backend"):
                mod._register_backend()
        except ImportError:
            print("backend plugin not found. Make sure that you have installed it before.")
        yield
    finally:
        CURRENT_BACKEND.reset(token)


def discover_backends():
    """Load plugins registered via entry points: group 'compas_fea2.backends'."""
    if not entry_points:
        return
    eps = entry_points()
    group = getattr(eps, "select", None)
    if group:
        eps = group(group="compas_fea2.backends")
    else:
        eps = eps.get("compas_fea2.backends", [])
    for ep in eps:
        try:
            # Expect callable that registers itself when invoked
            loader = ep.load()
            if callable(loader):
                loader()
        except Exception as e:
            print(f"Failed to load backend entry point {ep.name}: {e}")


def _get_backend_implementation(cls):
    """Resolve implementation from the active backend, falling back to BACKEND."""
    active = CURRENT_BACKEND.get() or BACKEND
    registry = BACKENDS.get(active, {})
    return registry.get(cls)


HERE = os.path.dirname(__file__)

HOME = os.path.abspath(os.path.join(HERE, "../../"))
DATA = os.path.abspath(os.path.join(HOME, "data"))
UMAT = os.path.abspath(os.path.join(DATA, "umat"))
DOCS = os.path.abspath(os.path.join(HOME, "docs"))
TEMP = os.path.abspath(os.path.join(HOME, "temp"))

if not load_dotenv():
    init_fea2()

VERBOSE = os.getenv("VERBOSE").lower() == "true"
POINT_OVERLAP = os.getenv("POINT_OVERLAP").lower() == "true"
GLOBAL_TOLERANCE = float(os.getenv("GLOBAL_TOLERANCE"))
GLOBAL_FRAME = Frame.worldXY()
PRECISION = int(os.getenv("PRECISION"))

# ensure these exist
try:
    BACKENDS  # type: ignore
except NameError:
    BACKENDS = {}  # type: ignore

try:
    BACKEND  # type: ignore
except NameError:
    BACKEND = None  # default backend name (optional)

CURRENT_BACKEND: ContextVar[str] = ContextVar("CURRENT_BACKEND", default=BACKEND)

__all__ = ["HOME", "DATA", "DOCS", "TEMP"]
