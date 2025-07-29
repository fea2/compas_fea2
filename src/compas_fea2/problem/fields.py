from typing import Iterable

from compas_fea2.base import FEAData
from compas_fea2.problem.loads import GravityLoad
from compas_fea2.problem.loads import HeatFluxLoad

# TODO implement __*__ magic method for combination


class LoadField(FEAData):
    """A pattern is the spatial distribution of a specific set of forces,
    displacements, temperatures, and other effects which act on a structure.
    Any combination of nodes and elements may be subjected to loading and
    kinematic conditions.

    Parameters
    ----------
    load : :class:`compas_fea2.problem._Load` | :class:`compas_fea2.problem.GeneralDisplacement`
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
        loads,
        distribution,
        load_case=None,
        **kwargs,
    ):
        super(LoadField, self).__init__(**kwargs)
        self._distribution = distribution if isinstance(distribution, Iterable) else [distribution]
        self._loads = loads if isinstance(loads, Iterable) else [loads * (1 / len(self._distribution))] * len(self._distribution)
        self.load_case = load_case
        self._registration = None

        self._amplitudes = set()
        for load in self._loads:
            if load.amplitude:
                self._amplitudes.add(load.amplitude)

    @property
    def loads(self):
        return self._loads

    @property
    def amplitudes(self):
        return self._amplitudes

    @property
    def distribution(self):
        return self._distribution

    @property
    def step(self):
        if self._registration:
            return self._registration
        else:
            raise ValueError("Register the LoadField to a Step first.")

    @property
    def problem(self):
        return self.step.problem

    @property
    def model(self):
        return self.problem.model

    # def __add__(self, other):
    #     if not isinstance(other, Pattern):
    #         raise TypeError("Can only combine with another Pattern")
    #     combined_distribution = self._distribution + other._distribution
    #     combined_components = {k: (getattr(self, k) or 0) + (getattr(other, k) or 0) for k in self.components}
    #     return Pattern(
    #         combined_distribution,
    #         x=combined_components["x"],
    #         y=combined_components["y"],
    #         z=combined_components["z"],
    #         xx=combined_components["xx"],
    #         yy=combined_components["yy"],
    #         zz=combined_components["zz"],
    #         load_case=self.load_case or other.load_case,
    #         axes=self.axes,
    #         name=self.name or other.name,
    #     )


class DisplacementField(LoadField):
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

    def __init__(self, displacements, nodes, load_case=None, **kwargs):
        nodes = nodes if isinstance(nodes, Iterable) else [nodes]
        displacements = displacements if isinstance(displacements, Iterable) else [displacements] * len(nodes)
        super(DisplacementField, self).__init__(loads=displacements, distribution=nodes, load_case=load_case, **kwargs)

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


class NodeLoadField(LoadField):
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

    def __init__(self, loads, nodes, load_case=None, **kwargs):
        super(NodeLoadField, self).__init__(loads=loads, distribution=nodes, load_case=load_case, **kwargs)

    @property
    def nodes(self):
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

    def __init__(self, loads, points, load_case=None, tolerance=1, **kwargs):
        self._points = points
        self._tolerance = tolerance
        # FIXME: this is not working, the patternhas no model!
        distribution = [self.model.find_closest_nodes_to_point(point, distance=self._tolerance)[0] for point in self.points]
        super().__init__(loads, distribution, load_case, **kwargs)

    @property
    def points(self):
        return self._points

    @property
    def nodes(self):
        return self._distribution


class GravityLoadField(LoadField):
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

    def __init__(self, g=9.81, parts=None, load_case=None, **kwargs):
        super(GravityLoadField, self).__init__(GravityLoad(g=g), parts, load_case, **kwargs)


class _PrescribedField(FEAData):
    """Base class for all predefined initial conditions.

    Notes
    -----
    Fields are registered to a :class:`compas_fea2.problem.Step`.

    """

    def __init__(self, **kwargs):
        super(_PrescribedField, self).__init__(**kwargs)


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
    
    @classmethod
    def from_file(cls, path, **kwargs):
        cls._path = path
        return cls(path=path, **kwargs)
    
# =====================================================================
# HEAT ANALYSIS
# =====================================================================

class TemperatureField(NodeLoadField):
    def __init__(self, temperature, nodes, **kwargs):
        nodes = nodes if isinstance(nodes, Iterable) else [nodes]
        loads = temperature if isinstance(temperature, Iterable) else [temperature] * len(nodes)
        super().__init__(loads=loads, nodes=nodes,**kwargs)


class SurfaceLoadField(LoadField):
    def __init__(self, loads, surface, **kwargs):
        super().__init__(loads=loads, distribution=surface, **kwargs)
        
    @property
    def surface(self):
        return self.distribution
        
    @property
    def load_surface(self):
        return zip(self.loads, self.surface)


class HeatFluxField(SurfaceLoadField):
    """A distribution of a uniform convection flux on a set of face elements.
    A non-uniform distribution is not yet implemented.

    Parameters
    ----------
    heatflux : object
        The heatflux to be applied.
    face_elements : list
        List of elements face where the surface heat flux is applied.
    load_case : object, optional
        The load case to which this pattern belongs.
    """

    def __init__(self, heatflux: HeatFluxLoad, surface, **kwargs):
        surface = surface if isinstance(surface, Iterable) else [surface]
        heatflux = heatflux if isinstance(heatflux, Iterable) else [heatflux] * len(surface)
        super().__init__(loads=heatflux, surface=surface,**kwargs)
    
    @property
    def heatflux(self):
        return self.loads

class ConvectionField(SurfaceLoadField):
    """
    """

    def __init__(self, h, temperature, surface, **kwargs):
        surface = surface if isinstance(surface, Iterable) else [surface]
        temperature = temperature if isinstance(temperature, Iterable) else [temperature] * len(surface)
        super().__init__(loads=temperature, surface=surface,**kwargs)
        self._h = h

    @property
    def surface(self):
        return self._distribution
    
    @property
    def temperature(self):
        return self._loads

    @property
    def h(self):
        return self._h
    

class RadiationField(SurfaceLoadField):
    """
    """

    def __init__(self, eps, temperature, surface, **kwargs):
        surface = surface if isinstance(surface, Iterable) else [surface]
        temperature = temperature if isinstance(temperature, Iterable) else [temperature] * len(surface)
        super().__init__(loads=temperature, surface=surface,**kwargs)
        self._eps = eps

    @property
    def surface(self):
        return self._distribution

    @property
    def temperature(self):
        return self._loads

    @property
    def eps(self):
        return self._eps
