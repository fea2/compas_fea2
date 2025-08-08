from typing import TYPE_CHECKING
from typing import Iterable
from typing import Optional

from compas_fea2.base import FEAData
from compas_fea2.problem.loads import ScalarLoad
from compas_fea2.problem.loads import VectorLoad

if TYPE_CHECKING:
    from compas.geometry import Point

    from compas_fea2.model import Model
    from compas_fea2.model.groups import FacesGroup
    from compas_fea2.model.nodes import Node
    from compas_fea2.problem import Problem
    from compas_fea2.problem.displacements import GeneralDisplacement
    from compas_fea2.problem.loads import _Load
    from compas_fea2.problem.steps import _Step

# TODO implement __*__ magic method for combination


class _LoadField(FEAData):
    """A Field is the spatial distribution of a specific set of forces,
    displacements, temperatures, and other effects which act on a structure.

    Parameters
    ----------
    load : list[:class:`compas_fea2.problem._Load`] | list[:class:`compas_fea2.problem.GeneralDisplacement`]
        The load/displacement assigned to the pattern.
    distribution : list
        List of :class:`compas_fea2.model.Node` or :class:`compas_fea2.model._Element`. The
        application in space of the load/displacement.
    load_case : str, optional
        The load case to which this pattern belongs.
    axes : str, optional
        Coordinate system for the load components. Default is "global".
    name : str, optional
        Unique identifier for the pattern.

    Attributes
    ----------
    load : :class:`compas_fea2.problem._Load`
        The load of the pattern.
    distribution : list
        List of :class:`compas_fea2.model.Node` or :class:`compas_fea2.model._Element`.
    name : str
        Unique identifier.

    Notes
    -----
    Patterns are registered to a :class:`compas_fea2.problem._Step`.
    """

    def __init__(
        self,
        loads: Iterable["_Load"] | Iterable["GeneralDisplacement"],
        distribution: "Node | Iterable[Node]",
        load_case: Optional[str] = None,
        **kwargs,
    ):
        super(_LoadField, self).__init__(**kwargs)
        self._distribution: list["Node"] = list(distribution) if isinstance(distribution, Iterable) else [distribution]
        self._loads = loads if isinstance(loads, Iterable) else [loads * (1 / len(self._distribution))] * len(self._distribution)
        self._load_case = load_case
        self._registration: "_Step | None" = None

    @property
    def loads(self) -> Iterable["_Load"] | Iterable["GeneralDisplacement"] | list[float]:
        return self._loads

    @property
    def distribution(self) -> list["Node"]:
        return self._distribution

    @property
    def step(self) -> "_Step":
        if self._registration:
            return self._registration
        else:
            raise ValueError("Register the LoadField to a Step first.")

    @property
    def problem(self) -> "Problem":
        return self.step.problem

    @property
    def model(self) -> "Model":
        return self.problem.model

    @property
    def load_case(self) -> str | None:
        """Return the load case to which this pattern belongs."""
        return self._load_case

    @load_case.setter
    def load_case(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Load case must be a string.")
        self._load_case = value


class _PrescribedField(FEAData):
    """Base class for all predefined initial conditions.

    Notes
    -----
    Fields are registered to a :class:`compas_fea2.problem.Step`.

    """

    def __init__(self, **kwargs):
        super(_PrescribedField, self).__init__(**kwargs)


class DisplacementField(_LoadField):
    """A distribution of a set of displacements over a set of nodes.

    Parameters
    ----------
    displacement : object
        The displacement to be applied.
    nodes : list
        List of nodes where the displacement is applied.
    load_case : object, optional
        The load case to which this pattern belongs.
    """

    def __init__(self, displacements: Iterable["GeneralDisplacement"], nodes: Iterable["Node"], load_case=None, **kwargs):
        nodes = nodes if isinstance(nodes, Iterable) else [nodes]
        displacements = displacements if isinstance(displacements, Iterable) else [displacements] * len(nodes)
        super().__init__(loads=displacements, distribution=nodes, load_case=load_case, **kwargs)

    @property
    def nodes(self):
        return self._distribution

    @property
    def displacements(self):
        return self._loads

    @property
    def node_displacement(self):
        """Return a list of tuples with the nodes and the assigned displacement."""
        return zip(self.nodes, self.displacements)


class NodeLoadField(_LoadField):
    """A distribution of a set of concentrated loads over a set of nodes.

    Parameters
    ----------
    load : object
        The load to be applied.
    nodes : list
        List of nodes where the load is applied.
    load_case : object, optional
        The load case to which this pattern belongs.
    """

    def __init__(self, loads: Iterable["VectorLoad"] | Iterable["ScalarLoad"], nodes: Iterable["Node"], load_case: str | None = None, **kwargs):
        super().__init__(loads=loads, distribution=nodes, load_case=load_case, **kwargs)

    @property
    def nodes(self) -> Iterable["Node"]:
        return self._distribution

    @property
    def loads(self):
        return self._loads

    @property
    def node_load(self):
        """Return a list of tuples with the nodes and the assigned load."""
        return zip(self.nodes, self.loads)


class PointLoadField(NodeLoadField):
    """A distribution of a set of concentrated loads over a set of points.
    The loads are applied to the closest nodes to the points.

    Parameters
    ----------
    load : object
        The load to be applied.
    points : list
        List of points where the load is applied.
    load_case : object, optional
        The load case to which this pattern belongs.
    tolerance : float, optional
        Tolerance for finding the closest nodes to the points.
    """

    def __init__(self, loads: Iterable["_Load"], points: Iterable["Point"], load_case: str | None = None, **kwargs):
        self._points = points
        distribution = [self.model.find_closest_nodes_to_point(point) for point in self.points]
        super().__init__(loads, distribution, load_case, **kwargs)

    @property
    def points(self):
        return self._points

    @property
    def nodes(self):
        return self._distribution


class UniformSurfaceLoadField(NodeLoadField):
    def __init__(self, load: float, surface: "FacesGroup", direction: list[float] | None = None, **kwargs):
        """A distribution of a set of loads over a set of surface elements.

        Parameters
        ----------
        loads : Iterable[_Load]
            The loads to be applied in Force/area units."""
        from compas_fea2.problem.loads import VectorLoad

        distribution = surface.nodes
        area = surface.area
        direction = direction or surface.normal
        amplitude = kwargs.pop("amplitude", None)

        components = [i * load * area for i in direction] if isinstance(load, (int, float)) else [l * area for l in load.components.values()]
        vector_load = VectorLoad(*components, amplitude=amplitude)

        super().__init__(loads=vector_load, nodes=distribution, **kwargs)
        self._surface = surface

    @property
    def surface(self):
        return self._surface


class GravityLoadField(NodeLoadField):
    """Volume distribution of a gravity load case.

    Parameters
    ----------
    g : float
        Value of gravitational acceleration.
    parts : list
        List of parts where the load is applied.
    load_case : object, optional
        The load case to which this pattern belongs.
    """

    def __init__(self, g=9.81, direction=[0, 0, -1], parts=None, load_case=None, **kwargs):
        load = VectorLoad(x=g * direction[0], y=g * direction[1], z=g * direction[2], name="gravity_load", load_case=load_case)
        nodes = []
        if parts:
            for part in parts:
                nodes.extend(part.nodes)
        else:
            nodes = self.model.nodes
        super().__init__(loads=[load] * len(nodes), nodes=nodes, load_case=load_case, **kwargs)


class PrescribedTemperatureField(_PrescribedField):
    """Temperature field."""

    def __init__(self, temperature=None, **kwargs):
        super(PrescribedTemperatureField, self).__init__(**kwargs)
        self._t = temperature

    @property
    def temperature(self):
        return self._t

    @temperature.setter
    def temperature(self, value):
        self._t = value


# =====================================================================
# HEAT ANALYSIS
# =====================================================================


class TemperatureField(NodeLoadField):
    """A distribution of a set of temperature over a set of nodes.

    Parameters
    ----------
    temperature : float
        Value of temperature.
    nodes : list[Node] | compas_fea2.model.groups.NodeGroup
        List of parts where the load is applied.
    load_case : object, optional
        The load case to which this pattern belongs.


    """

    def __init__(self, temperature: float, nodes: Iterable["Node"], **kwargs):
        nodes = list(nodes) if not isinstance(nodes, list) else nodes
        loads = temperature if isinstance(temperature, Iterable) else [temperature] * len(nodes)
        super().__init__(loads=loads, nodes=nodes, **kwargs)
