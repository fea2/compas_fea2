# Public API and metadata
from .registration import (
    BACKENDS_ENTRYPOINT_GROUP,
    _get_backend_implementation,
    register_backend,
    set_backend,
)

__author__ = ["Francesco Ranaudo"]
__copyright__ = "COMPAS Association"
__license__ = "MIT License"
__email__ = "francesco.ranaudo@gmail.com"
__version__ = "0.3.1"

__all__ = [
    "BACKENDS_ENTRYPOINT_GROUP",
    "register_backend",
    "set_backend",
    "_get_backend_implementation",
]

