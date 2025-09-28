from typing import TYPE_CHECKING
from typing import Optional

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.units import units_io

if TYPE_CHECKING:
    from compas_fea2.model.model import Model


# FIXME: switch to fields here as well
class _Constraint(FEAData):
    """Base class for constraints.

    Notes
    -----
    A constraint removes degrees of freedom of nodes in the model.
    All numerical quantities in subclasses (like tolerances) are expressed in the
    active unit system of the session. See :mod:`compas_fea2.units`.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @property
    def __data__(self):
        return {
            # Add other attributes as needed
        }

    @property
    def registration(self) -> Optional["Model"]:
        """Get the object where this object is registered to."""
        return self._registration

    @registration.setter
    def registration(self, value: "Model") -> None:
        """Set the object where this object is registered to."""
        self._registration = value

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        raise NotImplementedError("LinearConnector does not support from_data method yet.")


# ------------------------------------------------------------------------------
# MPC
# ------------------------------------------------------------------------------


class _MultiPointConstraint(_Constraint):
    """A MultiPointConstraint (MPC) links a node (master) to other nodes (slaves) in the model.

    Parameters
    ----------
    constraint_type : str
        Type of the constraint.
    master : :class:`compas_fea2.model.Node`
        Node that acts as master.
    slaves : List[:class:`compas_fea2.model.Node`] | :class:`compas_fea2.model.NodesGroup`
        List or Group of nodes that act as slaves.
    tol : float
        Constraint tolerance (distance limit between master and slaves).
        Expressed as a magnitude in the active unit system ("length").

    Attributes
    ----------
    constraint_type : str
        Type of the constraint.
    master : :class:`compas_fea2.model.Node`
        Node that acts as master.
    slaves : List[:class:`compas_fea2.model.Node`] | :class:`compas_fea2.model.NodesGroup`
        List or Group of nodes that act as slaves.
    tol : float
        Constraint tolerance (distance limit between master and slaves).
        Expressed as a magnitude in the active unit system ("length").

    Notes
    -----
    Constraints are registered to a :class:`compas_fea2.model.Model`.

    """

    @units_io(types_in=(None,), types_out=None)
    def __init__(self, constraint_type: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.constraint_type = constraint_type

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "constraint_type": self.constraint_type,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        raise NotImplementedError("LinearConnector does not support from_data method yet.")


class TieMPC(_MultiPointConstraint):
    """Tie MPC that constraints axial translations (e.g., along the length of the member)."""


class BeamMPC(_MultiPointConstraint):
    """Beam MPC that constraints axial translations and rotations."""


# TODO check!
class _SurfaceConstraint(_Constraint):
    """A SurfaceConstraint links a surface (master) to another surface (slave) in the model.

    Parameters
    ----------
    master : :class:`compas_fea2.model.Node`
        Node that acts as master.
    slaves : List[:class:`compas_fea2.model.Node`] | :class:`compas_fea2.model.NodesGroup`
        List or Group of nodes that act as slaves.
    tol : float
        Constraint tolerance, distance limit between master and slaves.
        Magnitude in the active unit system ("length").

    Attributes
    ----------
    master : :class:`compas_fea2.model.Node`
        Node that acts as master.
    slaves : List[:class:`compas_fea2.model.Node`] | :class:`compas_fea2.model.NodesGroup`
        List or Group of nodes that act as slaves.
    tol : float
        Constraint tolerance, distance limit between master and slaves.
        Magnitude in the active unit system ("length").

    Notes
    -----
    Constraints are registered to a :class:`compas_fea2.model.Model`.

    """

    @units_io(types_in=("length",), types_out=None)
    def __init__(self, tol: float | None = None, **kwargs):
        super().__init__(**kwargs)
        self.tol = tol

    @property
    def __data__(self):
        data = super().__data__
        # Add specific attributes for surface constraints
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        raise NotImplementedError("LinearConnector does not support from_data method yet.")


class TieConstraint(_SurfaceConstraint):
    """Tie constraint between two surfaces.

    Notes
    -----
    The tolerance (if used) is interpreted in the active unit system ("length").
    """
