import math
from typing import Optional
from uuid import UUID

from matplotlib import pyplot as plt
from compas_fea2.base import Registry

from .material import _Material


class _Composite(_Material):
    """Composite material class for finite element analysis."""

    def __init__(self, name: Optional[str] = None, uuid: Optional[UUID] = None):
        super().__init__(name=name, uuid=uuid)
        raise NotImplementedError("Composite material properties not fully implemented yet.")