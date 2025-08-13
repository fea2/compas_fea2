from typing import TYPE_CHECKING
from typing import Optional

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data

if TYPE_CHECKING:
    from compas_fea2.model.model import Model


class _Constraint(FEAData):
    """Base class for constraints.

    A constraint removes degree of freedom of nodes in the model.
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
        Constraint tolerance, distance limit between master and slaves.

    Attributes
    ----------
    constraint_type : str
        Type of the constraint.
    master : :class:`compas_fea2.model.Node`
        Node that acts as master.
    slaves : List[:class:`compas_fea2.model.Node`] | :class:`compas_fea2.model.NodesGroup`
        List or Group of nodes that act as slaves.
    tol : float
        Constraint tolerance, distance limit between master and slaves.

    Notes
    -----
    Constraints are registered to a :class:`compas_fea2.model.Model`.

    """

    def __init__(self, constraint_type: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.constraint_type = constraint_type

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "constraint_type": self.constraint_type,
                # Add other attributes as needed
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        raise NotImplementedError("LinearConnector does not support from_data method yet.")


class TieMPC(_MultiPointConstraint):
    """Tie MPC that constraints axial translations."""


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

    Attributes
    ----------
    master : :class:`compas_fea2.model.Node`
        Node that acts as master.
    slaves : List[:class:`compas_fea2.model.Node`] | :class:`compas_fea2.model.NodesGroup`
        List or Group of nodes that act as slaves.
    tol : float
        Constraint tolerance, distance limit between master and slaves.

    """

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
    """Tie constraint between two surfaces."""
