from typing import Optional
from uuid import UUID

from .material import _Material


class Aluminum(_Material):
    """Aluminum material class for finite element analysis."""

    def __init__(self, name: Optional[str] = None, uuid: Optional[UUID] = None):
        super().__init__(name=name, uuid=uuid)
        self.youngs_modulus = 70e9
        raise NotImplementedError("Aluminum material properties not fully implemented yet.")
