

from compas_fea2.model import Model
from .viewer import FEA2Viewer
from .viewer import FEA2ModelObject
from .primitives import (
    _BCShape,
    FixBCShape,
    PinBCShape,
    RollerBCShape,
)

__all__ = [
    "FEA2Viewer",
    "_BCShape",
    "FixBCShape",
    "PinBCShape",
    "RollerBCShape",
]


