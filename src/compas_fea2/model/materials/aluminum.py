from typing import Optional
from uuid import UUID

from compas_fea2.units import MPa

from .material import _Material


class Aluminum(_Material):
    """Aluminum material class for finite element analysis."""

    def __init__(self, name: Optional[str] = None, uuid: Optional[UUID] = None):
        super().__init__(name=name, uuid=uuid)
        self.youngs_modulus = 70 * MPa
        raise NotImplementedError("Aluminum material properties not fully implemented yet.")
