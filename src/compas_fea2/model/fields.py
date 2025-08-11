from typing import Iterable

from compas_fea2.base import FEAData
from compas_fea2.model.bcs import ImposedTemperature
from compas_fea2.model.bcs import _BoundaryCondition
from compas_fea2.model.groups import NodesGroup
from compas_fea2.model.ics import InitialTemperature
from compas_fea2.model.ics import _InitialCondition
from compas_fea2.model.nodes import Node


class _ConditionsField(FEAData):
    """A Field is the spatial distribution of a specific set of condition (initial or boundary).

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
        distribution,
        conditions,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._distribution: list["Node"] = list(distribution) if isinstance(distribution, Iterable) else [distribution]
        self._conditions = conditions if isinstance(conditions, Iterable) else [conditions] * len(self._distribution)
        self._registration = None

    @property
    def conditions(self) -> list["_BoundaryCondition"] | list["_InitialCondition"]:
        return self._conditions

    @property
    def distribution(self) -> "NodesGroup":
        return self._distribution

    @property
    def model(self):
        if self._registration:
            return self._registration
        else:
            raise ValueError("Register the ConditionField to a model first.")

    def remove_nodes(self, nodes):
        if not isinstance(nodes, Iterable):
            nodes = [nodes]
        for node in nodes:
            index = self._distribution.index(node)
            cond = self._conditions.pop(index)
            self._distribution.pop(index)
            node._bcs.remove_member(cond)


class _BoundaryConditionsField(_ConditionsField):
    __doc__ = """Base field class for the fields implementing boundary conditions."""
    __doc__ += _ConditionsField.__doc__
    __doc__ += """
    Additional attributes
    ---------------------
    node_bc : zip[(:class:compas_fea2.model.Node, :class:compas_fea2.model._BoundaryCondition)]
        List of tuples of nodes and its associated boundary condition."""

    def __init__(self, distribution, conditions, **kwargs):
        super().__init__(distribution, conditions, **kwargs)
        if not all(isinstance(condition, _BoundaryCondition) for condition in self.conditions):
            raise ValueError("At least one of the conditions is not a boundary condition.")

    @property
    def node_bc(self):
        """Return a list of tuples with the nodes and the assigned boundary condition."""
        return zip(self.distribution, self.conditions)


class MechanicalBCField(_BoundaryConditionsField):
    """Field class for fields implementing mechanical boundary conditions.

    Parameters
    ----------
    conditions : `list[:class:compas_fea2.model._BoundaryCondition]
        The boundary conditions list assigned to the field.
    distribution : list[:class:compas_fea2.model.Node]
        The nodes conposing the fields.
    name : str, optional
        Unique identifier for the field.

    Attributes
    ----------
    conditions : `list[:class:compas_fea2.model._BoundaryCondition]
        The boundary conditions list assigned to the field.
    distribution : list[:class:compas_fea2.model.Node]
        The nodes conposing the fields.
    name : str, optional
        Unique identifier for the field.
    model : :class:compas_fea2.model.Model | None
        Registered model to the field. None if the field has not been registered.
    node_bc : zip[(:class:compas_fea2.model.Node, :class:compas_fea2.model._BoundaryCondition)]
        List of tuples of nodes and its associated boundary condition.

    """

    def __init__(self, nodes, conditions, **kwargs):
        super().__init__(distribution=nodes, conditions=conditions, **kwargs)
        if not all(isinstance(condition, _BoundaryCondition) for condition in self.conditions):
            raise ValueError("At least one of the conditions is not a mechanical boundary condition.")


class ThermalBCField(_BoundaryConditionsField):
    """Field class for fields implementing mechanical boundary conditions.

    Parameters
    ----------
    conditions : `list[:class:compas_fea2.model.ImposedTemperature]
        The boundary conditions list assigned to the field.
    distribution : list[:class:compas_fea2.model.Node]
        The nodes conposing the fields.
    name : str, optional
        Unique identifier for the field.

    Attributes
    ----------
    conditions : `list[:class:compas_fea2.model.ImposedTemperature]
        The boundary conditions list assigned to the field.
    distribution : list[:class:compas_fea2.model.Node]
        The nodes conposing the fields.
    name : str, optional
        Unique identifier for the field.
    model : :class:compas_fea2.model.Model | None
        Registered model to the field. None if the field has not been registered.
    node_bc : zip[(:class:compas_fea2.model.Node, :class:compas_fea2.model.ImposedTemperature)]
        List of tuples of nodes and its associated boundary condition.re the displacement is applied.
    """

    def __init__(self, nodes, temperature, **kwargs):
        super().__init__(nodes, conditions=ImposedTemperature(temperature=temperature), **kwargs)
        if not all(isinstance(condition, ImposedTemperature) for condition in self.conditions):
            raise ValueError("At least one of the conditions is not a thermal boundary condition.")


class _InitialConditionField(_ConditionsField):
    __doc__ = """Base field class for the fields implementing initial conditions to the model."""

    def __init__(self, distribution, conditions, **kwargs):
        super().__init__(distribution=distribution, conditions=conditions, **kwargs)
        if not all(isinstance(condition, _InitialCondition) for condition in self.conditions):
            raise ValueError("At least one of the conditions is not am initial condition.")


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

    def __init__(self, nodes, conditions, **kwargs):
        super().__init__(distribution=nodes, conditions=conditions, **kwargs)
        if not all(isinstance(condition, InitialTemperature) for condition in self.conditions):
            raise ValueError("At least one of the conditions is not a thermal initial condition.")

    @property
    def node_ic(self):
        """Return a list of tuples with the nodes and their assigned initial temperature."""
        return zip(self.distribution, self.conditions)

    def from_file(self):
        pass


class InitialStressField(_InitialConditionField):
    def __init__(self, elements, conditions, **kwargs):
        super().__init__(distribution=elements, conditions=conditions, **kwargs)

    @property
    def element_ic(self):
        """Return a list of tuples with the elements and their assigned initial stress condition."""
        return zip(self.distribution, self.conditions)

    def from_file(self):
        pass
