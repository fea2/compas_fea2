from operator import itemgetter
from uuid import UUID

from typing import TYPE_CHECKING
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Polyhedron
from compas.geometry import Vector
from compas.geometry import centroid_points
from compas.geometry import distance_point_point
from compas.itertools import pairwise

from compas_fea2.base import FEAData
from compas_fea2.base import Registry

if TYPE_CHECKING:
    from compas_fea2.model.sections import SpringSection
    from compas_fea2.model.sections import _Section
    from compas_fea2.model.sections import _Section1D
    from compas_fea2.model.sections import _Section2D
    from compas_fea2.model.sections import _Section3D
    from compas_fea2.problem import _Step
    from compas_fea2.results import Result
    from compas_fea2.results import ShellStressResult
    from compas_fea2.results import SolidStressResult
    from compas_fea2.results.results import SectionForcesResult

    from .model import Model
    from .nodes import Node
    from .parts import _Part
    from .parts import Part
    from .parts import RigidPart
    from .shapes import Shape


class _Element(FEAData):
    """Initialises a base Element object.

    Parameters
    ----------
    nodes : list[:class:`compas_fea2.model.Node`]
        Ordered list of node identifiers to which the element connects.
    section : :class:`compas_fea2.model._Section`
        Section Object assigned to the element.
    implementation : str, optional
        The name of the backend model implementation of the element.
    rigid : bool, optional
        Define the element as rigid (no deformations allowed) or not. Defaults to False.
    heat : bool, optional
        Define the element as a heat transfer element. Defaults to False.

    Attributes
    ----------
    key : int, read-only
        Identifier of the element in the parent part.
    nodes : list[:class:`compas_fea2.model.Node`]
        Nodes to which the element is connected.
    nodes_key : str, read-only
        Identifier based on the connected nodes.
    section : :class:`compas_fea2.model._Section`
        Section object.
    implementation : str
        The name of the backend model implementation of the element.
    part : :class:`compas_fea2.model.Part` | None
        The parent part.
    on_boundary : bool | None
        `True` if the element has a face on the boundary mesh of the part, `False`
        otherwise, by default `None`.
    model : :class:`compas_fea2.model.Model`, read-only
        The Model where the element is assigned.
    area : float, read-only
        The area of the element.
    volume : float, read-only
        The volume of the element.
    rigid : bool, read-only
        Define the element as rigid (no deformations allowed) or not. For Rigid
        elements sections are not needed.
    heat : bool, read-only
        Define the element as a heat transfer element.

    Notes
    -----
    Elements and their nodes are registered to the same :class:`compas_fea2.model._Part` and can belong to only one Part.

    Warnings
    --------
    When an Element is added to a Part, the nodes of the elements are also added
    and registered to the same part. This might change the original registration
    of the nodes!

    """

    _registration: Optional["_Part"]

    def __init__(
        self,
        nodes: List["Node"],
        section: "Union[_Section, _Section1D, _Section2D, _Section3D, None]",
        implementation: Optional[str] = None,
        rigid: bool = False,
        heat: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._part_key: Union[int, None] = None
        self._nodes = self._check_nodes(nodes)
        self._registration = nodes[0]._registration
        self._section = section
        self._implementation = implementation
        self._frame = None
        self._on_boundary = None
        self._area = 0.0
        self._volume = 0.0
        self._results_format = {}
        self._rigid = rigid
        self._heat = heat
        self._reference_point = None # TODO: should be Node or Point?
        self._shape = None
        self._ndim = 0
        self._faces = []
        self._edges = []
        self._face_indices = {}
        self._length = 0.0

    @property
    def __data__(self):
        """Return a dictionary representation of the element's data."""
        data = super().__data__
        data.update({
                "nodes": [node.__data__ for node in self.nodes],
                "section": self.section.__data__ if self.section else None,
                "implementation": self.implementation,
                "frame": self._frame.__data__ if self._frame else None,
                "on_boundary": self._on_boundary,
                "area": self._area,
                "volume": self._volume,
                "results_format": self._results_format,
                "rigid": self._rigid,
                "heat": self._heat,
                "reference_point": self._reference_point.__data__ if self._reference_point else None,
                "shape": self._shape.__data__ if self._shape else None,
                "ndim": self._ndim,
                "faces": [face.__data__ for face in self._faces],
                "edges": [edge.__data__ for edge in self._edges],
                "face_indices": {face.__data__: indices for face, indices in self._face_indices.items()},
            "length": self._length
        })
        return data

    @classmethod
    def __from_data__(cls, data: dict, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)

        nodes = [
            registry.add_from_data(node_data, "compas_fea2.model.nodes")
            for node_data in data.get("nodes", [])
        ]
        section = registry.add_from_data(data.get("section"), "compas_fea2.model.sections") if data.get("section") else None

        element = cls(
            nodes=nodes,
            section=section,
            implementation=data.get("implementation"),
            rigid=data.get("rigid", False),
            heat=data.get("heat", False),
            faces_uids=[face_data.get("uid") for face_data in data.get("faces", [])] if data.get("faces") else None, # could be extended to names as well
            edges_uids=[edge_data.get("uid") for edge_data in data.get("edges", [])] if data.get("edges") else None, # could be extended to names as well
            uid = UUID(uid) if uid else None,
            name =data.get("name", "")
        )
        element._frame = Frame.__from_data__(data["frame"]) if "frame" in data else None
        element._on_boundary = data.get("on_boundary", None)
        element._area = data.get("area", 0.0)
        element._volume = data.get("volume", 0.0)
        element._results_format = data.get("results_format", {})
        element._reference_point = Point.__from_data__(data["reference_point"]) if "reference_point" in data else None
        element._shape = registry.add_from_data(data.get("shape"), "compas_fea2.model.shapes") if data.get("shape") else None
        element._ndim = data.get("ndim", 0)
        element._length = data.get("length", 0.0)

        if uid:
            registry.add(uid, element)

        return element

    @property
    def registration(self) -> Optional[Union["_Part", "Part", "RigidPart"]]:
        """Get the object where this object is registered to."""
        return self._registration

    @registration.setter
    def registration(self, value: Union["_Part", "Part", "RigidPart"]) -> None:
        """Set the object where this object is registered to."""
        for node in self.nodes:
            if node.registration is not None and node.registration != value:
                raise ValueError("All nodes of the elements must be registered to the same part")
            node.registration = value  # type: ignore
        self._registration = value


    @property
    def part(self) -> "_Part | None":
        """Return the part to which the element is registered."""
        return self._registration

    @property
    def model(self) -> "Model | None":
        """Return the model to which the element belongs."""
        if not self.part:
            return None
        return self.part.model

    @property
    def nodes(self) -> List["Node"]:
        """Return the list of nodes to which the element is connected."""
        return self._nodes

    @nodes.setter
    def nodes(self, value: List["Node"]):
        """Set the nodes of the element.

        Parameters
        ----------
        value : list[:class:`compas_fea2.model.Node`]
            The list of nodes to assign to the element.
        """
        self._nodes = self._check_nodes(value)

    @property
    def nodes_partkey(self) -> List[int]:
        """Return a unique identifier based on the connected nodes."""
        nk = []
        for node in self.nodes:
            if not node.part_key:
                raise ValueError("All nodes must be registered to a part")
            nk.append(node.part_key)
        return nk

    @property
    def nodes_inputkey(self) -> str:
        """Return a string key for input based on the connected nodes."""
        return "-".join(sorted([str(node.key) for node in self.nodes], key=int))

    @property
    def points(self) -> List["Point"]:
        """Return the points corresponding to the element's nodes."""
        return [node.point for node in self.nodes]

    @property
    def section(self) -> "Union[_Section, _Section1D, _Section2D, _Section3D, None]":
        """Return the section object assigned to the element."""
        return self._section

    @section.setter
    def section(self, value: "Union[_Section, _Section1D, _Section2D, _Section3D, None]"):
        """Set the section object for the element.

        Parameters
        ----------
        value : :class:`compas_fea2.model._Section`
            The section object to assign to the element.
        """
        self._section = value

    @property
    def frame(self) -> Optional[Frame]:
        """Return the frame of the element."""
        if not isinstance(self._frame, Frame):
            raise ValueError("Frame must be a valid Frame object")
        return self._frame

    @property
    def implementation(self) -> Optional[str]:
        """Return the implementation name of the element."""
        return self._implementation

    @property
    def on_boundary(self) -> Optional[bool]:
        """Return whether the element has a face on the boundary mesh."""
        return self._on_boundary

    @on_boundary.setter
    def on_boundary(self, value: bool):
        """Set whether the element has a face on the boundary mesh.

        Parameters
        ----------
        value : bool
            True if the element has a face on the boundary mesh, False otherwise.
        """
        self._on_boundary = value

    @staticmethod
    def _check_nodes(nodes: List["Node"]):
        """Check that all nodes are registered to the same part.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`]
            The list of nodes to check.

        Returns
        -------
        list[:class:`compas_fea2.model.Node`]
            The validated list of nodes.

        Raises
        ------
        ValueError
            If at least one node is registered to a different part or not registered.
        """
        registration = set([node._registration for node in nodes])
        if len(registration) != 1:
            raise ValueError("At least one of the nodes is registered to a different part or not registered")
        return nodes

    @property
    def part_key(self) -> int | None:
        """Return the part key of the element."""
        return self._part_key

    @property
    def area(self) -> float:
        """Return the area of the element."""
        return self._area

    @property
    def volume(self) -> float:
        return self._volume

    @property
    def results_format(self) -> Dict:
        """Return the results format for the element.

        Raises
        ------
        NotImplementedError
            If the subclass does not implement this property.
        """
        raise NotImplementedError()

    @property
    def reference_point(self) -> "Point":
        """Return the reference point of the element."""
        if self._reference_point:
            return self._reference_point
        return Point(*centroid_points([node.point for node in self.nodes]))

    @property
    def rigid(self) -> bool:
        """Return whether the element is rigid."""
        return self._rigid

    @property
    def heat(self) -> bool:
        """Return whether the element is a heat transfer element."""
        return self._heat

    @property
    def mass(self) -> float | None:
        """Return the mass of the element."""
        if self.section:
            if self.section.material:
                if self.volume and self.section.material.density:
                    return self.volume * self.section.material.density
        return None

    @property
    def g(self) -> float:
        """Return the gravity constant of the model.

        Raises
        ------
        ValueError
            If the gravity constant is not defined in the model.
        """
        if self.model:
            return self.model.g
        else:
            raise ValueError("Gravity constant not defined")

    @property
    def weight(self) -> float:
        """Return the weight of the element.

        Raises
        ------
        ValueError
            If the gravity constant is not defined in the model.
        """
        if hasattr(self.model, "g") and self.mass:
            return self.mass * self.g
        else:
            raise ValueError("Gravity constant not defined")

    @property
    def nodal_mass(self) -> List[float] | None:
        if self.mass:
            return [self.mass / len(self.nodes)] * 3

    @property
    def ndim(self) -> int:
        return self._ndim

    @property
    def faces(self) -> Optional[List["Face"]]:
        """Return the faces of the element."""
        if self._faces is None:
            raise ValueError("Faces have not been constructed")
        return self._faces

    @property
    def length(self) -> float:
        """Return the length of the element."""
        return self._length


class MassElement(_Element):
    """A 0D element for concentrated point mass."""

    @property
    def __data__(self):
        data = super().__data__
        return data

    @classmethod
    def __from_data__(cls, data):
        element = super().__from_data__(data)
        return element


class _Element0D(_Element):
    """Element with 1 dimension."""

    def __init__(self, nodes: List["Node"], frame: Frame, implementation: Optional[str] = None, **kwargs):
        super().__init__(nodes, section=None, implementation=implementation, rigid=False, heat=False, **kwargs)
        self._frame = frame
        self._ndim = 0

    @property
    def __data__(self):
        data = super().__data__
        data["frame"] = self.frame
        return data


class SpringElement(_Element0D):
    """A 0D spring element.

    Notes
    -----
    Link elements are used within a part. If you want to connect nodes from different parts
    use :class:`compas_fea2.model.connectors.RigidLinkConnector`.

    """

    def __init__(self, nodes: List["Node"], section: "SpringSection", implementation: Optional[str] = None, **kwargs):
        super().__init__(nodes, section=section, implementation=implementation, rigid=False, **kwargs)


class LinkElement(_Element0D):
    """A 0D link element.

    Notes
    -----
    Link elements are used within a part. If you want to connect nodes from different parts
    use :class:`compas_fea2.model.connectors.RigidLinkConnector`.
    """

    def __init__(self, nodes: List["Node"], section: "_Section2D", implementation: Optional[str] = None, rigid: bool = False, **kwargs):
        super().__init__(nodes, section=section, implementation=implementation, rigid=rigid, heat=False, **kwargs)


class _Element1D(_Element):
    """Element with 1 dimension.

    Parameters
    ----------
    nodes : list[:class:`compas_fea2.model.Node`]
        Ordered list of nodes to which the element connects.
    section : :class:`compas_fea2.model._Section`
        Section Object assigned to the element.
    frame : :class:`compas.geometry.Frame` or list
        Frame or local X axis in global coordinates. This is used to define the section orientation.
    implementation : str, optional
        The name of the backend model implementation of the element.
    rigid : bool, optional
        Define the element as rigid (no deformations allowed) or not. For Rigid
        elements sections are not needed.

    Attributes
    ----------
    frame : :class:`compas.geometry.Frame`
        The frame of the element.
    length : float
        The length of the element.
    volume : float
        The volume of the element.
    """

    _section: Optional["_Section1D"]

    def __init__(
        self,
        nodes: List["Node"],
        section: "_Section1D",
        orientation: Optional[Point] = None,
        implementation: Optional[str] = None,
        rigid: bool = False,
        heat: bool = False,
        **kwargs,
    ):
        super().__init__(nodes, section, implementation=implementation, rigid=rigid, heat=heat, **kwargs)
        if not orientation:
            raise ValueError("Frame is required for 1D elements")

        self._orientation = orientation
        n1 = nodes[0].point
        n2 = nodes[1].point
        n3 = orientation or Point(x=0, y=0, z=1)  # Default orientation if not provided
        x = Vector.from_start_end(n1, n2)
        v = Vector.from_start_end(n1, n3)
        y = (v - x * v.dot(x)).unitized()
        self._frame = Frame(n1, x, y)
        self._ndim = 1

    @property
    def section(self) -> "_Section1D | None":
        """Return the section object assigned to the element."""
        return self._section

    @property
    def curve(self) -> Line:
        return Line(self.nodes[0].point, self.nodes[-1].point)

    @property
    def outermesh(self) -> Mesh:
        self._frame.point = self.nodes[0].point
        if not self.section or not self.section.shape:
            raise ValueError("Section shape is required to create the outer mesh")
        self._shape_i = self.section.shape.oriented(self._frame, check_planarity=False)
        self._shape_j = self._shape_i.translated(Vector.from_start_end(self.nodes[0].point, self.nodes[-1].point), check_planarity=False)
        p = self._shape_i.points
        n = len(p)
        self._outermesh = Mesh.from_vertices_and_faces(
            self._shape_i.points + self._shape_j.points, [[p.index(v1), p.index(v2), p.index(v2) + n, p.index(v1) + n] for v1, v2 in pairwise(p)] + [[n - 1, 0, n, 2 * n - 1]]
        )
        return self._outermesh

    @property
    def frame(self) -> Frame:
        return self._frame

    @property
    def shape(self) -> Optional["Shape"]:
        return self._shape

    @property
    def length(self) -> float:
        return distance_point_point(*[node.point for node in self.nodes])

    @property
    def volume(self) -> float | None:
        if self.section:
            return self.section.A * self.length

    def plot_section(self):
        if self.section:
            self.section.plot()

    def plot_stress_distribution(self, step: "_Step", end: str = "end_1", nx: int = 100, ny: int = 100, *args, **kwargs):  # noqa: F821
        """Plot the stress distribution along the element.

        Parameters
        ----------
        step : :class:`compas_fea2.model.Step`
            The step to which the element belongs.
        end : str
            The end of the element to plot the stress distribution. Can be 'start' or 'end'.
        nx : int
            Number of points along the x axis.
        ny : int
            Number of points along the y axis.
        *args : list
            Additional arguments to pass to the plot function.
        **kwargs : dict
            Additional keyword arguments to pass to the plot function.
        """
        if not hasattr(step, "section_forces_field"):
            raise ValueError("The step does not have a section_forces_field")
        r = step.section_forces_field.get_element_forces(self)
        r.plot_stress_distribution(*args, **kwargs)

    def section_forces_result(self, step: "_Step") -> "SectionForcesResult":
        """Get the section forces result for the element.
        Parameters
        ----------
        step : :class:`compas_fea2.model.Step`
            The analysis step.

        Returns
        -------
        :class:`compas_fea2.results.Result`
            The section forces result for the element.
        """

        if not hasattr(step, "section_forces_field"):
            raise ValueError("The step does not have a section_forces_field")
        return step.section_forces_field.get_result_at(self)

    def forces(self, step: "_Step") -> Dict["Node", "Vector"]:
        """Get the forces result for the element.

        Parameters
        ----------
        step : :class:`compas_fea2.model.Step`
            The analysis step.

        Returns
        -------
        :class:`compas_fea2.results.Result`
            The forces result for the element.
        """
        r = self.section_forces_result(step)
        return r.forces

    def moments(self, step: "_Step") -> Dict["Node", "Vector"]:
        """Get the moments result for the element.

        Parameters
        ----------
        step : :class:`compas_fea2.model.Step`
            The analysis step.

        Returns
        -------
        :class:`compas_fea2.results.Result`
            The moments result for the element.
        """
        r = self.section_forces_result(step)
        return r.moments


class BeamElement(_Element1D):
    """A 1D element that resists axial, shear, bending and torsion.

    A beam element is a one-dimensional line element in three-dimensional space
    whose stiffness is associated with deformation of the line (the beam's “axis”).
    These deformations consist of axial stretch; curvature change (bending); and,
    in space, torsion.

    """


class TrussElement(_Element1D):
    """A 1D element that resists axial loads."""

    def __init__(self, nodes: List["Node"], section: "_Section1D", implementation: Optional[str] = None, rigid: bool = False, heat: bool = False, **kwargs):
        super().__init__(nodes, section, orientation=None, implementation=implementation, rigid=rigid, heat=heat, **kwargs)


class StrutElement(TrussElement):
    """A truss element that resists axial compressive loads."""


class TieElement(TrussElement):
    """A truss element that resists axial tensile loads."""


class Edge(FEAData):
    """Element representing an edge.

    Parameters
    ----------
    nodes : list[:class:`compas_fea2.model.Node`]
        Ordered list of nodes to which the element connects.
    tag : str
        The tag of the face.
    element : :class:`compas_fea2.model._Element`
        The element to which the edge belongs.

    Attributes
    ----------
    nodes : list[:class:`compas_fea2.model.Node`]
        Nodes to which the element is connected.
    tag : str
        The tag of the edge.
    elements : :class:`compas_fea2.model._Element`
        The elements to which the edge belongs.
    part : :class:`compas_fea2.model._Part`
        Part to which the edge belongs.
    model : :class:`compas_fea2.model.Model`
        Model to which the edge belongs.
    centroid : list[float]
        Coordinates of the centroid of the edge
    nodes_key : list[int]
        Keys of the nodes defining the edge.
    points : list[:class:`compas.geometry.Point`]
        List of the points defining the edge.
    line : :class:`compas.geometry.Line`
        The line of the edge.
    """
    def __init__(self, nodes: List["Node"], tag: str, **kwargs):
        super().__init__(**kwargs)
        self._nodes = nodes
        self._tag = tag
        self._line = Line(start=nodes[0].point, end=nodes[1].point)  # TODO check when more than 3 nodes

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "nodes": [node.__data__ for node in self.nodes],
                "tag": self.tag,
                "line": self._line.__data__ if self._line else None,
            }
        )

    @classmethod
    def __from_data__(cls, data: dict, registry: Optional[Registry]=None) -> "Edge": 
        # Create a registry if not provided
        if registry is None:
            registry = Registry()
        # check if the object already exists in the registry
        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid) #type: ignore
        # Create a new instance
        nodes = [registry.add_from_data(node_data, "compas_fea2.model.nodes") for node_data in data.get("nodes", [])]
        tag = data.get("tag", "")
        edge = cls(nodes=nodes, tag=tag, uid=UUID(uid) if uid else None, name=data.get("name", ""))
        # Add specific properties
        edge._line = Line.__from_data__(data["line"]) if "line" in data else None
        # Add the object to the registry
        if uid:
            registry.add(uid, edge)
        return edge


    @property
    def nodes(self) -> List["Node"]:
        return self._nodes

    @property
    def tag(self) -> str:
        return self._tag

    @property
    def element(self) -> Optional["_Element"]:
        return self._registration

    @property
    def part(self) -> "_Part | None":
        if self.element:
            return self.element.part

    @property
    def model(self) -> "Model | None":
        if self.element:
            return self.element.model

    @property
    def centroid(self) -> "Point":
        return Point(*centroid_points([node.xyz for node in self.nodes]))

    @property
    def nodes_key(self) -> List:
        return [n._part_key for n in self.nodes]

    @property
    def points(self) -> List["Point"]:
        return [node.point for node in self.nodes]

    @property
    def line(self) -> Line:
        self._line

class Face(FEAData):
    """Element representing a face.

    Parameters
    ----------
    nodes : list[:class:`compas_fea2.model.Node`]
        Ordered list of nodes to which the element connects.
    tag : str
        The tag of the face.
    element : :class:`compas_fea2.model._Element`
        The element to which the face belongs.

    Attributes
    ----------
    nodes : list[:class:`compas_fea2.model.Node`]
        Nodes to which the element is connected.
    tag : str
        The tag of the face.
    element : :class:`compas_fea2.model._Element`
        The element to which the face belongs.
    plane : :class:`compas.geometry.Plane`
        The plane of the face.
    polygon : :class:`compas.geometry.Polygon`
        The polygon of the face.
    area : float
        The area of the face.
    results : dict
        Dictionary with results of the face.

    """

    def __init__(self, nodes: List["Node"], tag: str, element: Optional["_Element"] = None, **kwargs):
        super().__init__(**kwargs)
        if len(nodes) < 3:
            raise ValueError("A face must have at least 3 nodes.")
        # Check for degenerate (zero-area) face
        coords = [node.xyz for node in nodes]
        poly = Polygon(coords)
        if poly.area == 0:
            raise ValueError(f"Degenerate face: area is zero. Vertices {[n.xyz for n in nodes]}")
        self._nodes = nodes
        self._tag = tag
        self._plane = Plane.from_three_points(*[node.xyz for node in nodes[:3]])  # TODO check when more than 3 nodes
        self._registration = element

    @property
    def __data__(self):
        data = super().__data__
        data.update( {
                "nodes": [node.__data__ for node in self.nodes],
                "tag": self.tag,
                "element": self.element.__data__ if self.element else None,
                "plane": self.plane.__data__ if self.plane else None,
        })
        return data

    @classmethod
    def __from_data__(cls, data: dict, registry: Optional[Registry]=None) -> "Face": 
        # Create a registry if not provided
        if registry is None:
            registry = Registry()
        # check if the object already exists in the registry
        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid) #type: ignore
        # Create a new instance
        nodes = [registry.add_from_data(node_data, "compas_fea2.model.nodes") for node_data in data.get("nodes", [])]
        tag = data.get("tag", "")
        face = cls(nodes=nodes, tag=tag, uid=UUID(uid) if uid else None, name=data.get("name", ""))
        # Add base properties
        face._name = data.get("name", "")
        # Add specific properties
        face._plane = Plane.__from_data__(data["plane"]) if "plane" in data else None
        # Add the object to the registry
        if uid:
            registry.add(uid, face)
        return face

    @property
    def nodes(self) -> List["Node"]:
        return self._nodes

    @property
    def tag(self) -> str:
        return self._tag

    @property
    def plane(self) -> Plane:
        return self._plane

    @property
    def element(self) -> Optional["_Element"]:
        return self._registration

    @property
    def part(self) -> "_Part | None":
        """Return the part to which the face belongs."""
        if self.element:
            return self.element.part

    @property
    def model(self) -> "Model | None":
        """Return the model to which the face belongs."""
        if self.element:
            return self.element.model

    @property
    def polygon(self) -> Polygon:
        return Polygon([n.xyz for n in self.nodes])

    @property
    def area(self) -> float:
        return self.polygon.area

    @property
    def centroid(self) -> "Point":
        return Point(*centroid_points([node.xyz for node in self.nodes]))

    @property
    def nodes_key(self) -> List:
        return [n._part_key for n in self.nodes]

    @property
    def normal(self) -> Vector:
        return self.plane.normal

    @property
    def points(self) -> List["Point"]:
        return [node.point for node in self.nodes]

    @property
    def mesh(self) -> Mesh:
        return Mesh.from_vertices_and_faces(self.points, [[c for c in range(len(self.points))]])

    @property
    def node_area(self) -> Iterator[Tuple["Node", float]]:
        mesh = self.mesh
        vertex_area = [mesh.vertex_area(vertex) for vertex in mesh.vertices()]
        return zip(self.nodes, vertex_area)


class _Element2D(_Element):
    """Element with 2 dimensions."""

    __doc__ = __doc__ or ""
    __doc__ += _Element.__doc__ or ""
    __doc__ += """
    Additional Parameters
    ---------------------
    frame :  list, optional.
        Local Y axis in global coordinates (longitudinal axis).
        This can be used to define the local orientation for anisotrop material.
    faces : [:class:`compas_fea2.model.elements.Face]
        The faces of the element.
    face_indices : dict
        Dictionary providing for each face the node indices. For example:
        {'s1': (0,1,2), ...}
    edges : [:class:`compas_fea2.model.elements.Edge]
        The edges of the element.
    edge_indices : dict
        Dictionary providing for each edge the node indices. For example:
        {'e1': (0,1), ...}
    """

    _section: Optional["_Section2D"]

    def __init__(
        self,
        nodes: List["Node"],
        section: Optional["_Section2D"] = None,
        implementation: Optional[str] = None,
        rigid: bool = False,
        heat: bool = False,
        frame: Optional[Frame] = None,
        **kwargs,
    ):
        super().__init__(
            nodes=nodes,
            section=section,
            implementation=implementation,
            rigid=rigid,
            heat=heat,
            **kwargs,
        )

        self._faces: Optional[List[Face]] = None
        self._face_indices: Optional[Dict[str, Tuple[int, ...]]] = None

        self._edges: Optional[List[Edge]] = None
        self._edges_indices: Optional[Dict[str, Tuple[int, ...]]] = None

        self._ndim = 2

        # BUG this is not correct!
        # if frame:
        #     if isinstance(frame, (Vector, List, Tuple)):
        #         compas_polygon = Polygon(points=[node.point for node in nodes])
        #         # the third axis is built from the y-axis (frame input) and z-axis (normal of the element)
        #         x_axis = cross_vectors(frame, compas_polygon.normal)
        #         frame = Frame(nodes[0].point, Vector(*x_axis), Vector(*frame))
        #         self._frame = frame
        #     else:
        #         raise ValueError("The frame must be a Frame object or a Vector object.")

    @property
    def nodes(self) -> List["Node"]:
        return self._nodes

    @nodes.setter
    def nodes(self, value: List["Node"]):
        self._nodes = self._check_nodes(value)
        if self._face_indices:
            self._faces = self._construct_faces(self._face_indices)

    @property
    def section(self) -> "_Section2D | None":
        """Return the section object assigned to the element."""
        return self._section

    @section.setter
    def section(self, value: "_Section2D"):
        """Set the section object for the element.

        Parameters
        ----------
        value : :class:`compas_fea2.model._Section`
            The section object to assign to the element.
        """
        self._section = value

    @property
    def edge_indices(self) -> Optional[Dict[str, Tuple[int, ...]]]:
        """Return the edge indices of the element."""
        return self._edges_indices

    @property
    def edges(self) -> Optional[List[Edge]]:
        return self._edges

    @property
    def face_indices(self) -> Optional[Dict[str, Tuple[int, ...]]]:
        return self._face_indices

    @property
    def faces(self) -> Optional[List[Face]]:
        return self._faces

    @property
    def volume(self) -> float | None:
        if self._faces and self.section:
            return self._faces[0].area * self.section.t

    @property
    def reference_point(self) -> "Point | None":
        if self.faces:
            return Point(*centroid_points([face.centroid for face in self.faces]))

    @property
    def outermesh(self) -> Mesh | None:
        if self.face_indices:
            return Mesh.from_vertices_and_faces(self.points, list(self.face_indices.values()))

    def _construct_faces(self, face_indices: Dict[str, Tuple[int, ...]], uids: Optional[Union[List[UUID], str]] = None) -> List[Face]:
        """Construct the face-nodes dictionary.

        Parameters
        ----------
        face_indices : dict
            Dictionary providing for each face the node indices. For example:
            {'s1': (0,1,2), ...}

        Returns
        -------
        dict
            Dictionary with face names and the corresponding nodes.
        """
        faces = []
        for name_indices, uid in zip(face_indices.items(), uids or [None] * len(face_indices)):
            name, indices = name_indices
            if len(indices) < 3:
                raise ValueError(f"Face '{name}' must have at least 3 nodes, got {len(indices)}")
            face = Face(nodes=itemgetter(*indices)(self.nodes), tag=name, element=self, uid=uid)
            face.registration = self
            faces.append(face)
        return faces

    def _construct_edges(self, edge_indices: Dict[str, Tuple[int, ...]], uids: Optional[Union[List[UUID], str]] = None) -> List[Edge]:
        """Construct the face-nodes dictionary.

        Parameters
        ----------
        face_indices : dict
            Dictionary providing for each face the node indices. For example:
            {'s1': (0,1,2), ...}

        Returns
        -------
        dict
            Dictionary with edge names and the corresponding nodes.
        """
        edges = []
        for name_indices, uid in zip(edge_indices.items(), uids or [None] * len(edge_indices)):
            name, indices = name_indices
            if len(indices) < 2:
                raise ValueError(f"Edge '{name}' must have at least 2 nodes, got {len(indices)}")
            edge = Edge(nodes=itemgetter(*indices)(self.nodes), tag=name, uid=uid)
            edge.registration = self
            edges.append(edge)
        return edges

    def stress_results(self, step: "_Step") -> "Result":
        """Get the stress results for the element.

        Parameters
        ----------
        step : :class:`compas_fea2.model.Step`
            The analysis step.

        Returns
        -------
        :class:`compas_fea2.results.Result`
            The stress results for the element.
        """
        if not hasattr(step, "stress_field"):
            raise ValueError("The step does not have a stress field")
        return step.stress_field.get_result_at(self)


class ShellElement(_Element2D):
    """A 2D element that resists axial, shear, bending and torsion.

    Shell elements are used to model structures in which one dimension, the
    thickness, is significantly smaller than the other dimensions.

    """

    def __init__(self, nodes: List["Node"], section: "_Section2D", implementation: Optional[str] = None, rigid: bool = False, heat: bool = False, **kwargs):
        super().__init__(
            nodes=nodes,
            section=section,
            implementation=implementation,
            rigid=rigid,
            heat=heat,
            **kwargs,
        )

        self._face_indices = {"SPOS": tuple(range(len(nodes))), "SNEG": tuple(range(len(nodes)))[::-1]}
        self._faces = self._construct_faces(self._face_indices, uids=kwargs.get("faces_uids", None))

        self._edges_indices = {f"s{i + 1}": (i, i + 1) if i < len(nodes) - 1 else (i, 0) for i in range(len(nodes))}
        self._edges = self._construct_edges(self._edges_indices, uids=kwargs.get("edges_uids", None))

    @property
    def results_cls(self) -> Dict[str, type]:
        return {"s": ShellStressResult}


class MembraneElement(_Element2D):
    """A shell element that resists only axial loads.

    Notes
    -----
    Membrane elements are used to represent thin surfaces in space that offer
    strength in the plane of the element but have no bending stiffness; for
    example, the thin rubber sheet that forms a balloon. In addition, they are
    often used to represent thin stiffening components in solid structures, such
    as a reinforcing layer in a continuum.

    """


class _Element3D(_Element):
    """A 3D element that resists axial, shear, bending and torsion.
    Solid (continuum) elements can be used for linear analysis
    and for complex nonlinear analyses involving contact, plasticity, and large
    deformations.

    Solid elements are general purpose elements and can be used for multiphysics
    problems.

    """

    def __init__(self, nodes: List["Node"], section: "_Section3D", implementation: Optional[str] = None, frame: Optional[List] = None, rigid=False, heat: bool = False, **kwargs):
        super().__init__(
            nodes=nodes,
            section=section,
            implementation=implementation,
            rigid=rigid,
            heat=heat,
            **kwargs,
        )
        self._faces: Optional[List[Face]] = None
        self._face_indices: Optional[Dict[str, Tuple[int, ...]]] = None

        self._edges: Optional[List[Edge]] = None
        self._edges_indices: Optional[Dict[str, Tuple[int, ...]]] = None

        self._frame = Frame.worldXY()

        self._ndim = 3

    @property
    def results_cls(self) -> Dict[str, type]:
        return {"s": SolidStressResult}

    @property
    def frame(self) -> Frame:
        return self._frame

    @property
    def nodes(self) -> List["Node"]:
        return self._nodes

    @nodes.setter
    def nodes(self, value: List["Node"]):
        self._nodes = value
        if self._face_indices:
            self._faces = self._construct_faces(self._face_indices)

    @property
    def face_indices(self) -> Optional[Dict[str, Tuple[int, ...]]]:
        """Return the face indices of the element."""
        return self._face_indices

    @property
    def faces(self) -> Optional[List[Face]]:
        return self._faces

    @property
    def edges(self) -> Optional[List[Edge]]:
        """Return the edges of the element."""
        return self._edges

    @property
    def centroid(self) -> "Point":
        return Point(*centroid_points([node.point for node in self.nodes]))

    @property
    def reference_point(self) -> "Point":
        return self._reference_point or self.centroid

    def _construct_faces(self, face_indices: Dict[str, Tuple[int, ...]]) -> List[Face]:
        """Construct the face-nodes dictionary.

        Parameters
        ----------
        face_indices : dict
            Dictionary providing for each face the node indices. For example:
            {'s1': (0,1,2), ...}

        Returns
        -------
        dict
            Dictionary with face names and the corresponding nodes.

        """
        return [Face(nodes=itemgetter(*indices)(self.nodes), tag=name, element=self) for name, indices in face_indices.items()]

    @property
    def area(self) -> float:
        return self._area

    @classmethod
    def from_polyhedron(cls, polyhedron: Polyhedron, section: "_Section3D", implementation: Optional[str] = None, **kwargs) -> "_Element3D":
        from compas_fea2.model import Node

        element = cls([Node(vertex) for vertex in polyhedron.vertices], section, implementation, **kwargs)
        return element

    @property
    def outermesh(self) -> Mesh | None:
        if self._face_indices:
            return Polyhedron(self.points, list(self._face_indices.values())).to_mesh()


class TetrahedronElement(_Element3D):
    """A Solid element with 4 or 10 nodes.

    Notes
    -----
    This element can be either:
    - C3D4: A 4-node tetrahedral element.
    - C3D10: A 10-node tetrahedral element (with midside nodes).

    Face labels (for the first 4 corner nodes) are:
    - S1: (0, 1, 2)
    - S2: (0, 1, 3)
    - S3: (1, 2, 3)
    - S4: (0, 2, 3)

    The C3D10 element includes 6 additional midside nodes:
    - Edge (0,1) → Node 4
    - Edge (1,2) → Node 5
    - Edge (2,0) → Node 6
    - Edge (0,3) → Node 7
    - Edge (1,3) → Node 8
    - Edge (2,3) → Node 9

    Attributes
    ----------
    nodes : List["Node"]
        The list of nodes defining the element.
    """

    def __init__(
        self,
        nodes: List["Node"],
        section: "_Section3D",
        implementation: Optional[str] = None,
        **kwargs,
    ):
        if len(nodes) not in {4, 10}:
            raise ValueError("TetrahedronElement must have either 4 (C3D4) or 10 (C3D10) nodes.")

        # self.element_type = "C3D10" if len(nodes) == 10 else "C3D4"

        super().__init__(
            nodes=nodes,
            section=section,
            implementation=implementation,
            **kwargs,
        )

        # Define the face indices for a tetrahedron (first four corner nodes)
        self._face_indices = {
            "s1": (0, 1, 2),
            "s2": (0, 1, 3),
            "s3": (1, 2, 3),
            "s4": (0, 2, 3),
        }

        self._faces = self._construct_faces(self._face_indices)

    # BUG this is not correct!
    # @property
    # def edges(self):
    #     """Yields edges as (start_node, end_node), including midside nodes if present."""
    #     seen = set()
    #     edges = [
    #         (0, 1, 4),
    #         (1, 2, 5),
    #         (2, 0, 6),
    #         (0, 3, 7),
    #         (1, 3, 8),
    #         (2, 3, 9),
    #     ]

    #     for edge in edges:
    #         if self.element_type == "C3D10":
    #             u, v, mid = edge
    #             edge_pairs = [(u, mid), (mid, v)]  # Split each edge into two segments
    #         else:
    #             u, v = edge[:2]
    #             edge_pairs = [(u, v)]

    #         for u, v in edge_pairs:
    #             if (u, v) not in seen:
    #                 seen.add((u, v))
    #                 seen.add((v, u))
    #                 yield u, v

    @property
    def volume(self) -> float:
        """Calculates the volume using the first four corner nodes (C3D4 basis)."""

        def determinant_3x3(m):
            return m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[1][0] * (m[0][1] * m[2][2] - m[0][2] * m[2][1]) + m[2][0] * (m[0][1] * m[1][2] - m[0][2] * m[1][1])

        def subtract(a, b):
            return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

        nodes_coord = [node.xyz for node in self.nodes[:4]]  # Use only first 4 nodes
        a, b, c, d = nodes_coord
        return abs(determinant_3x3((subtract(a, b), subtract(b, c), subtract(c, d)))) / 6.0


class PentahedronElement(_Element3D):
    """A Solid element with 5 faces (extruded triangle)."""


class HexahedronElement(_Element3D):
    """A Solid cuboid element with 6 faces (extruded rectangle)."""

    def __init__(self, nodes: List["Node"], section: "_Section3D", implementation: Optional[str] = None, rigid=False, heat: bool = False, **kwargs):
        super().__init__(
            nodes=nodes,
            section=section,
            implementation=implementation,
            rigid=rigid,
            heat=heat,
            **kwargs,
        )
        self._face_indices = {
            "s1": (0, 1, 2, 3),
            "s2": (4, 5, 6, 7),
            "s3": (0, 1, 4, 5),
            "s4": (1, 2, 5, 6),
            "s5": (2, 3, 6, 7),
            "s6": (0, 3, 4, 7),
        }
        self._faces = self._construct_faces(self._face_indices)
