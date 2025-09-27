from __future__ import annotations

import os
from dataclasses import dataclass
from compas.geometry import Frame

# Paths
HERE = os.path.dirname(__file__)
HOME = os.path.abspath(os.path.join(HERE, "../../"))
DATA = os.path.abspath(os.path.join(HOME, "data"))
UMAT = os.path.abspath(os.path.join(DATA, "umat"))
DOCS = os.path.abspath(os.path.join(HOME, "docs"))
TEMP = os.path.abspath(os.path.join(HOME, "temp"))


def _getenv_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


def _getenv_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _getenv_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    VERBOSE: bool
    POINT_OVERLAP: bool
    GLOBAL_TOLERANCE: float
    PRECISION: int
    GLOBAL_FRAME: Frame

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            VERBOSE=_getenv_bool("VERBOSE", False),
            POINT_OVERLAP=_getenv_bool("POINT_OVERLAP", True),
            GLOBAL_TOLERANCE=_getenv_float("GLOBAL_TOLERANCE", 1.0),
            PRECISION=_getenv_int("PRECISION", 3),
            GLOBAL_FRAME=Frame.worldXY(),
        )


# Snapshot of current env-based settings at import time.
settings: Settings = Settings.from_env()


def reload_settings() -> Settings:
    """Re-read environment variables into a new Settings snapshot."""
    global settings
    settings = Settings.from_env()
    return settings