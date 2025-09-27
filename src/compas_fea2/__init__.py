# Public API and metadata
from .registration import (
    BACKENDS_ENTRYPOINTS,
    _get_backend_implementation,
    get_active_backend,
    register_backend,
    set_backend,
)

__author__ = ["Francesco Ranaudo"]
__copyright__ = "COMPAS Association"
__license__ = "MIT License"
__email__ = "francesco.ranaudo@gmail.com"
__version__ = "0.3.1"

__all__ = [
    "BACKENDS_ENTRYPOINTS",
    "register_backend",
    "set_backend",
    "get_active_backend",
    "_get_backend_implementation",
]

