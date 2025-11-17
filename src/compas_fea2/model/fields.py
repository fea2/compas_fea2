from typing import TYPE_CHECKING
from typing import Iterable
from typing import Optional

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.model.bcs import _BoundaryCondition
from compas_fea2.model.groups import NodesGroup
from compas_fea2.model.ics import _InitialCondition
from compas_fea2.model.nodes import Node
from compas_fea2.model.groups import ElementsGroup
from compas_fea2.model.elements import _Element1D
from compas_fea2.model.releases import _BeamEndRelease

if TYPE_CHECKING:
    from compas_fea2.model.bcs import _BoundaryCondition
    from compas_fea2.model.ics import _InitialCondition
    from compas_fea2.model.parts import _Part
    from compas_fea2.model.model import Model


class _ConditionsField(FEAData):
    """A Field is the spatial distribution of a specific set of conditions (initial or boundary conditions).

    Parameters
    ----------
    conditions : `list[:class:compas_fea2.model._BoundaryCondition] | `list[:class:compas_fea2.model._InitialCondition]
        The boundary/initial conditions list assigned to the field.
    distribution : list[:class:compas_fea2.model.Node] | list[:class:compas_fea2.model._Elements]
        The nodes conposing the fields.
    name : str, optional
        Unique identifier for the field.

    Attributes
    ----------
    conditions : `list[:class:compas_fea2.model._BoundaryCondition] | `list[:class:compas_fea2.model._InitialCondition]
        The boundary/initial conditions list assigned to the field.
    distribution : list[:class:compas_fea2.model.Node]
        The nodes conposing the fields.
    name : str, optional
        Unique identifier for the field.
    model : :class:compas_fea2.model.Model | None
        Registered model to the field. None if the field has not been registered.
    """

    def __init__(
        self,
        distribution: "NodesGroup" | Iterable["Node"] | Node,
        condition: "_BoundaryCondition | _InitialCondition",
        **kwargs,
    ):
        super().__init__(**kwargs)
        if not isinstance(distribution, NodesGroup):
            self._distribution = NodesGroup(distribution)
        else:
            self._distribution = distribution
        self._condition = condition
        self._check_registration()

    def _check_registration(self):
        registrations = set([n.model for n in self._distribution])
        if len(registrations) != 1:
            raise ValueError("All nodes in the distribution must be registered to the same model.")
        if self._registration is None:
            self._registration = registrations.pop()

    @property
    def condition(self) -> "_BoundaryCondition | _InitialCondition":
        return self._condition

    @property
    def distribution(self) -> "NodesGroup":
        return self._distribution

    @property
    def node_condition(self):
        """Return a list of tuples with the nodes and their assigned condition."""
        return zip(self.distribution, [self.condition] * len(self.distribution))

    @property
    def model(self) -> "Model":
        if self._registration:
            return self._registration
        else:
            raise ValueError("Register the ConditionField to a model first.")


class BoundaryConditionsField(_ConditionsField):
    __doc__ = """Base field class for the fields implementing boundary conditions."""
    __doc__ += _ConditionsField.__doc__ or ""
    __doc__ += """
    Additional attributes
    ---------------------
    node_bc : zip[(:class:compas_fea2.model.Node, :class:compas_fea2.model._BoundaryCondition)]
        List of tuples of nodes and its associated boundary condition."""

    def __init__(self, distribution: "NodesGroup" | Iterable["Node"] | Node, condition: "_BoundaryCondition", **kwargs):
        super().__init__(distribution, condition, **kwargs)

    @property
    def __data__(self):
        super_data = super().__data__
        data = {
            "distribution": self.distribution.__data__,
            "condition": self.condition.__data__,
        }
        data.update(super_data)
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        """Create a BoundaryConditionsField from data."""
        if registry is None:
            raise ValueError("A registry must be provided to create a BoundaryConditionsField from data.")
        distribution_data = data.get("distribution")
        condition_data = data.get("condition")
        field = cls(
            distribution=registry.add_from_data(distribution_data, duplicate=duplicate),
            condition=registry.add_from_data(condition_data, duplicate=duplicate),
        )
        return field

    @property
    def bc(self) -> "_BoundaryCondition":
        """Return the boundary condition assigned to the field."""
        if isinstance(self.condition, _BoundaryCondition):
            return self.condition
        raise ValueError("Condition is not a _BoundaryCondition.")

    @property
    def node_bc(self):
        """Return a list of tuples with the nodes and the assigned boundary condition."""
        return self.node_condition


class _InitialConditionField(_ConditionsField):
    __doc__ = """Base field class for the fields implementing initial conditions to the model."""

    def __init__(self, distribution, conditions, **kwargs):
        super().__init__(distribution=distribution, condition=conditions, **kwargs)


class InitialTemperatureField(_InitialConditionField):
    """Field class for fields implementing mechanical boundary conditions.

    Parameters
    ----------
    conditions : `list[:class:compas_fea2.model.InitialTemperature]
        The boundary conditions list assigned to the field.
    nodes : list[:class:compas_fea2.model.Node]
        The nodes conposing the fields.
    name : str, optional
        Unique identifier for the field.

    Attributes
    ----------
    conditions : `list[:class:compas_fea2.model.InitialTemperature]
        The boundary conditions list assigned to the field.
    distribution : list[:class:compas_fea2.model.Node]
        The nodes conposing the fields.
    name : str, optional
        Unique identifier for the field.
    model : :class:compas_fea2.model.Model | None
        Registered model to the field. None if the field has not been registered.
    node_bc : zip[(:class:compas_fea2.model.Node, :class:compas_fea2.model.InitialTemperature)]
        List of tuples of nodes and its associated boundary condition.re the displacement is applied.
    """

    def __init__(self, nodes, condition, **kwargs):
        super().__init__(distribution=nodes, conditions=condition, **kwargs)


class InitialStressField(_InitialConditionField):
    def __init__(self, elements, condition, **kwargs):
        super().__init__(distribution=elements, conditions=condition, **kwargs)
        raise NotImplementedError("InitialStressField is not yet implemented.")


# ------------------------------------------------------------------------------
# BEAM END RELEASE FIELDS
# ------------------------------------------------------------------------------

class BeamReleaseField(FEAData):
    """A BeamReleaseField is the spatial distribution of a specific set of beam end releases.

    Parameters
    ----------
    release : `:class:compas_fea2.model._BeamEndRelease`
        The release applied to the field.
    elements : `:class:compas_fea2.model.ElementsGroup`
        The elements composing the fields.
    release_end : str 
        The end to release is applied (start, end or both).
    name : str, optional
        Unique identifier for the field.

    Attributes
    ----------
    release : `:class:compas_fea2.model._BeamEndRelease`
        The release applied to the field.
    elements : `:class:compas_fea2.model.ElementsGroup`
        The elements composing the fields.
    release_end : str
        The end to release is applied (start, end, both)
    name : str, optional
        Unique identifier for the field.
        Registered model to the field. None if the field has not been registered.
    part :  `:class:compas_fea2.model._Part`
        Part of the release field
    """
    def __init__(self, release, elements, end, name = None, **kwargs):
        super().__init__(name, **kwargs)
        if not isinstance(elements, ElementsGroup):
            self._elements = ElementsGroup(elements)
        else:
            self._elements = elements
        for element in self._elements:
            if not isinstance(element, _Element1D):
                raise ValueError('A BeamEndRelease can only applied on 1D elements.')
        self._release = release


        self._end = end
        self._check_registration()

    def _check_registration(self):
        registrations = set([n.model for n in self._elements])
        if len(registrations) != 1:
            raise ValueError("All nodes in the distribution must be registered to the same model.")
        if self._registration is None:
            self._registration = registrations.pop()

    @property
    def release(self) -> "_BeamEndRelease":
        if isinstance(self._release, _BeamEndRelease):
            return self._release
        else :
            raise ValueError("Release is not a _BeamEndRelease.")

    @property
    def elements(self) -> "ElementsGroup":
        return self._elements

    @property
    def end(self) -> str :
        return self._end

    @property
    def elements_end_release(self):
        """Return a list of tuples with the nodes and their assigned condition."""
        return zip(self.elements, [self.end] * len(self.elements), [self.release] * len(self.elements))

    @property
    def part(self) -> "_Part":
        if self._registration:
            return self._registration
        else:
            raise ValueError("Register the ConditionField to a part first.")

    @property
    def model(self) -> "Model":
        return self.part.model
    