from collections import defaultdict
from itertools import groupby
from typing import TYPE_CHECKING
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Union

import networkx as nx
import numpy as np
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polyline
from compas.geometry import Scale
from compas.geometry import Transformation
from compas.geometry import Vector
from compas.geometry import bounding_box
from compas.geometry import centroid_points
from compas.geometry import centroid_points_weighted
from compas.geometry import is_coplanar
from compas.geometry import is_point_in_polygon_xy
from compas.geometry import is_point_on_plane
from compas.tolerance import TOL
from scipy.spatial import KDTree

import compas_fea2
from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data

from .elements import BeamElement
from .elements import HexahedronElement
from .elements import ShellElement
from .elements import TetrahedronElement
from .elements import _Element
from .elements import _Element1D
from .elements import _Element2D
from .elements import _Element3D
from .groups import NodesGroup
from .groups import EdgesGroup
from .groups import ElementsGroup
from .groups import EdgesGroup
from .groups import FacesGroup
from .groups import MaterialsGroup
from .groups import SectionsGroup
from .groups import InteractionsGroup
from .groups import InterfacesGroup
from .groups import ReleasesGroup
from .materials.material import _Material
from .nodes import Node
from .releases import _BeamEndRelease
from .sections import ShellSection
from .sections import SolidSection
from .sections import _Section
from .sections import _Section1D
from .sections import _Section2D
from .sections import _Section3D

if TYPE_CHECKING:
    from compas.geometry import Polygon

    from compas_fea2.model.bcs import _BoundaryCondition
    from compas_fea2.model.elements import Face
    from compas_fea2.model.elements import _Element
    from compas_fea2.model.elements import _Element1D
    from compas_fea2.model.elements import _Element2D
    from compas_fea2.model.elements import _Element3D
    from compas_fea2.model.groups import EdgesGroup
    from compas_fea2.model.groups import ElementsGroup
    from compas_fea2.model.groups import FacesGroup
    from compas_fea2.model.groups import InteractionsGroup
    from compas_fea2.model.groups import InterfacesGroup
    from compas_fea2.model.groups import MaterialsGroup
    from compas_fea2.model.groups import NodesGroup
    from compas_fea2.model.groups import SectionsGroup
    from compas_fea2.model.groups import ReleasesGroup
    from compas_fea2.model.materials.material import _Material
    from compas_fea2.model.model import Model
    from compas_fea2.model.nodes import Node
    from compas_fea2.model.sections import _Section
    from compas_fea2.model.sections import _Section2D
    from compas_fea2.model.sections import _Section3D
    from compas_fea2.model.parts import _Part, Parts, RigidPart


GroupType = Union["NodesGroup", "ElementsGroup", "FacesGroup", "MaterialsGroup", "SectionsGroup", "InterfacesGroup", "InteractionsGroup"]


class _Part(FEAData):
    """Base class for Parts.

    Parameters
    ----------
    None

    Attributes
    ----------
    name : str
        Unique identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    model : :class:`compas_fea2.model.Model`
        The parent model of the part.
    nodes : Set[:class:`compas_fea2.model.Node`]
        The nodes belonging to the part.
    nodes_count : int
        Number of nodes in the part.
    gkey_node : Dict[str, :class:`compas_fea2.model.Node`]
        Dictionary that associates each node and its geometric key.
    materials : Set[:class:`compas_fea2.model._Material`]
        The materials belonging to the part.
    sections : Set[:class:`compas_fea2.model._Section`]
        The sections belonging to the part.
    elements : Set[:class:`compas_fea2.model._Element`]
        The elements belonging to the part.
    element_types : Dict[:class:`compas_fea2.model._Element`, List[:class:`compas_fea2.model._Element`]]
        Dictionary with the elements of the part for each element type.
    element_count : int
        Number of elements in the part.
    boundary_mesh : :class:`compas.datastructures.Mesh`
        The outer boundary mesh enveloping the Part.
    discretized_boundary_mesh : :class:`compas.datastructures.Mesh`
        The discretized outer boundary mesh enveloping the Part.

    Notes
    -----
    Parts are registered to a :class:`compas_fea2.model.Model`.

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._registration: Optional["Model"] = None
        self._ndm = None
        self._ndf = None
        self._graph = nx.DiGraph()
        self._nodes: "NodesGroup" = NodesGroup(members=[], name=f"{self.name}_nodes_all")
        self._elements: "ElementsGroup" = ElementsGroup(members=[], name=f"{self.name}_elements_all")

        self._groups: Set[GroupType] = set()

        self._boundary_mesh: Optional[Mesh] = None
        self._discretized_boundary_mesh: Optional[Mesh] = None

        self._reference_node: Optional[Node] = None

    @property
    def __data__(self):
        data = super().__data__
        data.update({
            "ndm": self._ndm,
            "ndf": self._ndf,
            "nodes": self._nodes.__data__,
            "elements": self._elements.__data__,
            "groups": [group.__data__ for group in self._groups],
            "boundary_mesh": self._boundary_mesh.__data__ if self._boundary_mesh else None,
            "discretized_boundary_mesh": self._discretized_boundary_mesh.__data__ if self._discretized_boundary_mesh else None,
            "reference_node": self._reference_node.__data__ if self._reference_node else None,
        })
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional["Registry"] = None):
        if not registry:
            raise ValueError("A registry is required to create a Part from data.")
        part = cls()
        part._name = data.get("name", "")
        part._ndm = data.get("ndm")
        part._ndf = data.get("ndf")
        
        nodes = NodesGroup.__from_data__(data["nodes"], registry=registry) # type: ignore
        part.add_nodes(nodes) 
        part._nodes._uid = data.get("nodes", {}).get("uid", None) # change the uid of the nodes group
        
        elements = ElementsGroup.__from_data__(data["elements"], registry=registry)  # type: ignore
        part.add_elements(elements)  # type: ignore
        part._elements._uid = data.get("elements", {}).get("uid", None) # change the uid of the nodes group

        part._groups = set([registry.add_from_data(group, module_name="compas_fea2.model.groups") for group in data.get("groups", [])])
        
        part._boundary_mesh = Mesh.__from_data__(data["boundary_mesh"]) if data.get("boundary_mesh") else None
        part._discretized_boundary_mesh = Mesh.__from_data__(data["discretized_boundary_mesh"]) if data.get("discretized_boundary_mesh") else None
        
        part._reference_node = registry.add_from_data(data["reference_node"], "compas_fea2.model.nodes") if data.get("reference_node") else None

        return part

    # =========================================================================
    #                       Constructors
    # =========================================================================
    @classmethod
    def from_compas_lines_discretized(
        cls, lines: List["Line"], targetlength: float, element_cls: type, section: "_Section2D", frame: "Union[Frame, List[float], Vector]", **kwargs
    ):
        """Generate a discretized model from a list of :class:`compas.geometry.Line`.

        Parameters
        ----------
        compas_lines : dict
            Dictionary providing for each compas line the targetlenght of the mesh, the element class, the section and frame. For example:
            {'L1': [targetlenght1, BeamElement, section1, frame1], 'L2': [targetlenght2, BeamElement, section2, frame2]...}
        target_length : int
            The targetted lenght of the discretization of the lines.
        section : :class:`compas_fea2.model.Section1D`
            The section to be assigned to the elements, by default None.
        element_model : str, optional
            Implementation model for the element, by default 'BeamElement'.
        frame : :class:`compas.geometry.Vector` or list[float], optional
            Local frame of the element or x-axis of the frame by default [0,1,0].
        name : str, optional
            The name of the part, by default None (one is automatically generated).

        Returns
        -------
        :class:`compas_fea2.model.Part`
            The part.

        """
        polyline = Polyline(points=[line.start for line in lines] + [lines[-1].end])
        dividedline_points = polyline.divide_by_length(targetlength, strict=False)
        prt = Part.from_compas_lines(
            lines=[Line(start=dividedline_points[i], end=dividedline_points[i + 1]) for i in range(len(dividedline_points) - 1)],
            section=section,
            element_cls=element_cls,
            frame=frame,
            **kwargs,
        )

        return prt

    @classmethod
    def from_compas_lines(
        cls,
        lines: List["Line"],
        element_cls: type = BeamElement,
        frame: "Union[Frame, List[float], Vector]" = [0, 1, 0],
        section: Optional["_Section"] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> "_Part":
        """Generate a part from a list of :class:`compas.geometry.Line`.

        Parameters
        ----------
        lines : list[:class:`compas.geometry.Line`]
            The lines to be converted.
        element_cls : type, optional
            Implementation model for the element, by default BeamElement.
        frame : :class:`compas.geometry.Line` or list[float], optional
            The x-axis direction, by default [0,1,0].
        section : :class:`compas_fea2.model.Section1D`, optional
            The section to be assigned to the elements, by default None.
        name : str, optional
            The name of the part, by default None (one is automatically generated).

        Returns
        -------
        :class:`compas_fea2.model.Part`
            The part.

        """
        prt = cls(name=name)
        mass = kwargs.get("mass", None)
        for line in lines:
            if not (isinstance(frame, Frame)):
                frame = Frame(line.start, frame, line.vector)
            nodes = []
            for p in [line.start, line.end]:
                if g := prt.nodes.subgroup(condition=lambda node: node.point == p):
                    nodes.append(list(g.nodes)[0])
                else:
                    nodes.append(Node(list(p), mass=mass))

            prt.add_nodes(nodes)
            element = element_cls(nodes=nodes, section=section, frame=frame)
            if not isinstance(element, _Element1D):
                raise ValueError("Provide a 1D element")
            prt.add_element(element)
        return prt

    @classmethod
    def shell_from_compas_mesh(cls, mesh, section: ShellSection, name: Optional[str] = None, **kwargs) -> "_Part":
        """Creates a Part object from a :class:`compas.datastructures.Mesh`.

        To each face of the mesh is assigned a :class:`compas_fea2.model.ShellElement`
        object. Currently, the same section is applied to all the elements.

        Parameters
        ----------
        mesh : :class:`compas.datastructures.Mesh`
            Mesh to convert to a Part.
        section : :class:`compas_fea2.model.ShellSection`
            Shell section assigned to each face.
        name : str, optional
            Name of the new part. If ``None``, a unique identifier is assigned
            automatically.

        Returns
        -------
        :class:`compas_fea2.model.Part`
            The part.

        """
        implementation = kwargs.get("implementation", None)
        ndm = kwargs.get("ndm", None)
        heat = kwargs.get("heat", False)
        part = cls(name=name, ndm=ndm) if ndm else cls(name=name)
        vertex_node = {vertex: part.add_node(Node(mesh.vertex_coordinates(vertex))) for vertex in mesh.vertices()}

        for face in mesh.faces():
            nodes = [vertex_node[vertex] for vertex in mesh.face_vertices(face)]
            element = ShellElement(nodes=nodes, section=section, implementation=implementation, heat=heat, **kwargs)
            part.add_element(element)

        part._boundary_mesh = mesh
        part._discretized_boundary_mesh = mesh

        return part

    @classmethod
    def from_gmsh(cls, gmshModel, element_cls: Optional[type | None] = None, section: "Optional[Union[_Section2D, _Section3D]]" = None, **kwargs) -> "_Part":
        """Create a Part object from a gmshModel object with support for C3D4 and C3D10 elements.

        Parameters
        ----------
        gmshModel : object
            Gmsh Model to convert.
        section : Union[SolidSection, ShellSection], optional
            The section type (`SolidSection` or `ShellSection`).

        Returns
        -------
        _Part
            The part meshed.

        Notes
        -----
        - Detects whether elements are C3D4 (4-node) or C3D10 (10-node) and assigns correctly.
        - The `gmshModel` should have the correct dimensions for the given section.

        """
        # Get parameters
        name = kwargs.get("name", None)
        verbose = kwargs.get("verbose", False)
        rigid = kwargs.get("rigid", False)
        implementation = kwargs.get("implementation", None)
        heat = kwargs.get("heat", False)

        dimension = 2 if isinstance(section, _Section3D) else 1
        # gmshModel.set_option("Mesh.ElementOrder", 2)
        # gmshModel.set_option("Mesh.Optimize", 1)
        # gmshModel.set_option("Mesh.OptimizeNetgen", 1)
        # gmshModel.set_option("Mesh.SecondOrderLinear", 0)
        # gmshModel.set_option("Mesh.OptimizeNetgen", 1)

        # Get nodes and elements from the gmsh model
        gmshModel.heal()
        gmshModel.generate_mesh(3)
        model = gmshModel.model
        node_coords = model.mesh.get_nodes()[1].reshape((-1, 3), order="C")
        gmsh_elements = model.mesh.get_elements()
        ntags_per_element = np.split(gmsh_elements[2][dimension] - 1, len(gmsh_elements[1][dimension]))  # gmsh keys start from 1

        # Create a new part instance
        part = cls(name=name)
        fea2_nodes = np.array([part.add_node(Node(coords)) for coords in node_coords])
        # Select element classes mapping (nodes - cls)
        # Base mapping for element classes by node count
        mapping = {
            3: ShellElement,
            4: ShellElement if isinstance(section, ShellSection) else TetrahedronElement,
            8: HexahedronElement,
            10: TetrahedronElement,
        }
        # Extend mapping if a dict is provided
        if isinstance(element_cls, dict):
            mapping.update(element_cls)

        for ntags in ntags_per_element:
            count = ntags.size
            # Use element_cls directly if it's a single class
            if element_cls and not isinstance(element_cls, dict):
                elem_to_use = element_cls
            else:
                elem_to_use = mapping.get(count)
            if not elem_to_use:
                raise NotImplementedError(f"Element with {count} nodes not supported")
            element = elem_to_use(nodes=fea2_nodes[ntags], section=section, rigid=rigid, implementation=implementation, heat=heat)
            part.add_element(element)
            if isinstance(element, _Element3D):
                part._ndf = 3
            if verbose:
                print(f"Element {ntags} added")

        if not part._boundary_mesh:
            gmshModel.generate_mesh(2)
            part._boundary_mesh = gmshModel.mesh_to_compas()

        if not part._discretized_boundary_mesh:
            part._discretized_boundary_mesh = part._boundary_mesh

        if rigid:
            if not part._discretized_boundary_mesh:
                raise ValueError("Discretized boundary mesh is required for rigid parts.")
            point = part._discretized_boundary_mesh.centroid()
            part.reference_node = Node(xyz=point)

        return part

    @staticmethod
    def _apply_gmsh_mesh_options(gmshModel, **kwargs):
        """Apply mesh size options to a gmshModel instance."""
        mesh_size_at_vertices = kwargs.get("mesh_size_at_vertices")
        target_point_mesh_size = kwargs.get("target_point_mesh_size")
        meshsize_max = kwargs.get("meshsize_max")
        meshsize_min = kwargs.get("meshsize_min")

        if mesh_size_at_vertices:
            for vertex, target in mesh_size_at_vertices.items():
                gmshModel.mesh_targetlength_at_vertex(vertex, target)

        if target_point_mesh_size:
            gmshModel.heal()
            for point, target in target_point_mesh_size.items():
                tag = gmshModel.model.occ.addPoint(*point, target)
                gmshModel.model.occ.mesh.set_size([(0, tag)], target)

        if meshsize_max is not None:
            gmshModel.heal()
            gmshModel.options.mesh.meshsize_max = meshsize_max
        if meshsize_min is not None:
            gmshModel.heal()
            gmshModel.options.mesh.meshsize_min = meshsize_min

    @classmethod
    def from_boundary_mesh(cls, boundary_mesh, name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a Part object from a 3-dimensional :class:`compas.datastructures.Mesh`
        object representing the boundary envelope of the Part. The Part is
        discretized uniformly in Tetrahedra of a given mesh size.
        The same section is applied to all the elements.

        Parameters
        ----------
        boundary_mesh : :class:`compas.datastructures.Mesh`
            Boundary envelope of the Part.
        name : str, optional
            Name of the new Part.
        target_mesh_size : float, optional
            Target mesh size for the discretization, by default 1.
        mesh_size_at_vertices : dict, optional
            Dictionary of vertex keys and target mesh sizes, by default None.
        target_point_mesh_size : dict, optional
            Dictionary of point coordinates and target mesh sizes, by default None.
        meshsize_max : float, optional
            Maximum mesh size, by default None.
        meshsize_min : float, optional
            Minimum mesh size, by default None.

        Returns
        -------
        _Part
            The part.

        """
        from compas_gmsh.models import MeshModel

        target_mesh_size = kwargs.get("target_mesh_size", 1)
        gmshModel = MeshModel.from_mesh(boundary_mesh, targetlength=target_mesh_size)  # type: ignore[call-arg]

        cls._apply_gmsh_mesh_options(gmshModel, **kwargs)

        part = cls.from_gmsh(gmshModel=gmshModel, name=name, **kwargs)

        if gmshModel:
            del gmshModel

        return part

    @classmethod
    def from_step_file(cls, step_file: str, name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a Part object from a STEP file.

        Parameters
        ----------
        step_file : str
            Path to the STEP file.
        name : str, optional
            Name of the new Part.

        Returns
        -------
        _Part
            The part.

        """
        from compas_gmsh.models import MeshModel

        gmshModel = MeshModel.from_step(step_file)
        cls._apply_gmsh_mesh_options(gmshModel, **kwargs)

        part = cls.from_gmsh(gmshModel=gmshModel, name=name, **kwargs)

        if gmshModel:
            del gmshModel
        print("Part created.")

        return part

    @classmethod
    def from_brep(cls, brep, name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a Part object from a BREP file.

        Parameters
        ----------
        brep : str
            Path to the BREP file.
        name : str, optional
            Name of the new Part.

        Returns
        -------
        _Part
            The part.
        """
        from compas_gmsh.models import MeshModel

        gmshModel = MeshModel.from_brep(brep)
        cls._apply_gmsh_mesh_options(gmshModel, **kwargs)

        part = cls.from_gmsh(gmshModel=gmshModel, name=name, **kwargs)

        if gmshModel:
            del gmshModel
        print("Part created.")

        return part

    # =========================================================================
    #                       Properties
    # =========================================================================
    @property
    def registration(self) -> Optional["Model"]:
        """Get the object where this object is registered to."""
        return self._registration

    @registration.setter
    def registration(self, value: "Model") -> None:
        """Set the object where this object is registered to."""
        self._registration = value

    @property
    def reference_node(self) -> Optional[Node]:
        """The reference point of the part."""
        return self._reference_node

    @reference_node.setter
    def reference_node(self, value: Node):
        self._reference_node = self.add_node(value)
        value._is_reference = True

    @property
    def graph(self):
        """The directed graph of the part."""
        return self._graph
    
    @property
    def nodes(self) -> NodesGroup:
        """The nodes of the part."""
        return self._nodes

    @property
    def nodes_sorted(self) -> List[Node]:
        """The nodes of the part sorted by their part key."""
        return self.nodes.sorted_by(key=lambda x: x.part_key if x.part_key is not None else -1)

    @property
    def points(self) -> List[Point]:
        """The points of the part's nodes."""
        return [node.point for node in self._nodes]

    @property
    def points_sorted(self) -> List[Point]:
        """The points of the part's nodes sorted by their part key."""
        return [node.point for node in self.nodes.sorted_by(key=lambda x: x.part_key if x.part_key is not None else -1)]

    @property
    def elements(self) -> ElementsGroup:
        """The elements of the part."""
        return self._elements

    @property
    def edges(self) -> EdgesGroup:
        """The edges of the part's elements."""
        edges = []
        for element in self.elements:
            if hasattr(element, "edges"):
                element_edges = getattr(element, "edges")
                if element_edges is not None:
                    edges.extend(element_edges)
        return EdgesGroup(edges)

    @property
    def faces(self) -> FacesGroup:
        """The faces of the part's elements."""
        return FacesGroup([face for element in self.elements if element.faces is not None for face in element.faces])

    @property
    def elements_sorted(self) -> List[_Element]:
        """The elements of the part sorted by their part key."""
        return self.elements.sorted_by(key=lambda x: x.part_key if x.part_key is not None else -1)

    @property
    def elements_grouped(self) -> Dict[type, List[_Element]]:
        """The elements of the part grouped by their element type."""
        sub_groups = self.elements.group_by(key=lambda x: x.__class__.__base__)
        return {key: group.members for key, group in sub_groups}

    @property
    def elements_faces(self) -> Dict[_Element, FacesGroup]:
        """The faces of the part's elements grouped by element."""
        face_group = FacesGroup([face for element in self.elements if element.faces is not None for face in element.faces])
        return face_group.group_by(key=lambda x: getattr(x, "element", None))

    @property
    def elements_faces_grouped(self) -> Dict[int, List[List["Face"]]]:
        """The faces of the part's elements grouped by element key."""
        return {
            key.__name__.__hash__(): [element.faces for element in elements if hasattr(element, "faces") and element.faces is not None]
            for key, elements in self.elements_grouped.items()
        }

    @property
    def elements_faces_indices(self) -> List[List[List[float]]]:
        """The indices of the faces of the part's elements."""
        return [[list(map(float, face.nodes_partkey))] for face in self.elements_faces]

    @property
    def elements_faces_indices_grouped(self) -> Dict[int, List[List[float]]]:
        """The indices of the faces of the part's elements grouped by element key."""
        return {
            hash(key): [face.nodes_key for elem in element for face in getattr(elem, "faces", []) if getattr(elem, "faces", None) is not None]
            for key, element in self.elements_grouped.items()
        }

    @property
    def elements_connectivity(self) -> List[List[int]]:
        """The connectivity of the part's elements."""
        return [element.nodes_partkey for element in self.elements]

    @property
    def elements_connectivity_grouped(self) -> Dict[int, List[List[float]]]:
        """The connectivity of the part's elements grouped by element type."""
        elements_group = groupby(self.elements, key=lambda x: x.__class__.__base__)
        return {hash(key): [list(map(float, element.nodes_partkey)) for element in group] for key, group in elements_group}

    @property
    def elements_centroids(self) -> List[List[float]]:
        """The centroids of the part's elements."""
        return [list(np.mean([node.xyz for node in element.nodes], axis=0)) for element in self.elements]

    @property
    def sections(self) -> SectionsGroup:
        """All the materials associated with the part. If the part is registered to a model,
        it is faster to use the model's sections property."""
        sections = set()
        for element in self.elements:
            if hasattr(element, "section") and element.section is not None:
                sections.add(element.section)
        return SectionsGroup(members=list(sections), name=f"{self.name}_sections_all")

    @property
    def sections_sorted(self) -> List[_Section]:
        """The sections of the part sorted by their part key."""
        return self.sections.sorted_by(key=lambda x: x.key if x.key is not None else "")

    @property
    def sections_grouped_by_element(self) -> Dict[type, List[_Section]]:
        """The sections of the part grouped by their type."""
        sections_group = self.sections.group_by(key=lambda x: type(x))
        return {key: group.members for key, group in sections_group}

    @property
    def materials(self) -> MaterialsGroup:
        """All the materials associated with the part. If the part is registered to a model,
        it is faster to use the model's meaterials property."""
        materials = set()
        for section in self.sections:
            if hasattr(section, "material") and section.material is not None:
                materials.add(section.material)
        return MaterialsGroup(members=list(materials), name=f"{self.name}_materials_all")

    @property
    def materials_sorted(self) -> List[_Material]:
        """The materials of the part sorted by their name."""
        return self.materials.sorted_by(key=lambda x: x.name)

    @property
    def materials_grouped_by_name(self) -> Dict[str, List[_Material]]:
        """The materials of the part grouped by their name."""
        materials_group = self.materials.group_by(key=lambda x: x.name)
        return {key: group.members for key, group in materials_group}

    # @property
    # def releases(self) -> "ReleasesGroup | None":
    #     """The releases of the part."""
    #     for element in self.elements:
    #         if hasattr(element, "releases") and element.releases is not None:
    #             return ReleasesGroup(members=element.releases, name=f"{self.name}_releases_all")

    @property
    def gkey_node(self) -> Dict[str, Node]:
        """A dictionary that associates each node and its geometric key."""
        return self.nodes.gkey_node

    @property
    def boundary_mesh(self):
        """The outer boundary mesh of the part."""
        return self._boundary_mesh

    @property
    def discretized_boundary_mesh(self):
        """The discretized outer boundary mesh of the part."""
        return self._discretized_boundary_mesh

    @property
    def outer_faces(self):
        """Extract the outer faces of the part."""
        # FIXME: extend to shell elements
        face_count = defaultdict(int)
        for tet in self.elements_connectivity:
            faces = [
                tuple(sorted([tet[0], tet[1], tet[2]])),
                tuple(sorted([tet[0], tet[1], tet[3]])),
                tuple(sorted([tet[0], tet[2], tet[3]])),
                tuple(sorted([tet[1], tet[2], tet[3]])),
            ]
            for face in faces:
                face_count[face] += 1
        # Extract faces that appear only once (boundary faces)
        outer_faces = np.array([face for face, count in face_count.items() if count == 1])
        return outer_faces

    @property
    def outer_mesh(self):
        """Extract the outer mesh of the part."""
        unique_vertices, unique_indices = np.unique(self.outer_faces, return_inverse=True)
        vertices = np.array(self.points_sorted)[unique_vertices]
        faces = unique_indices.reshape(self.outer_faces.shape).tolist()
        return Mesh.from_vertices_and_faces(vertices.tolist(), faces)

    @property
    def bounding_box(self) -> Box:
        """The bounding box of the part."""
        # FIXME: add bounding box for linear elements (bb of the section outer boundary)
        return Box.from_bounding_box(bounding_box([n.xyz for n in self.nodes]))

    @property
    def bb_center(self) -> Point:
        """The geometric center of the part."""
        return Point(*centroid_points(self.bounding_box.points))

    @property
    def center(self) -> Point:
        """The geometric center of the part."""
        return Point(*centroid_points(self.points))

    @property
    def centroid(self) -> Point:
        """The geometric center of the part."""
        self.compute_nodal_masses()
        points = [node.point for node in self.nodes]
        weights = [sum(node.mass) / len(node.mass) for node in self.nodes]
        return Point(*centroid_points_weighted(points, weights))

    @property
    def bottom_plane(self) -> Plane:
        """The bottom plane of the part's bounding box."""
        return Plane.from_three_points(*[self.bounding_box.points[i] for i in self.bounding_box.bottom[:3]])

    @property
    def top_plane(self) -> Plane:
        """The top plane of the part's bounding box."""
        return Plane.from_three_points(*[self.bounding_box.points[i] for i in self.bounding_box.top[:3]])

    @property
    def volume(self) -> float:
        """The total volume of the part."""
        self._volume = 0.0
        for element in self.elements:
            if element.volume:
                self._volume += element.volume
        return self._volume

    @property
    def weight(self) -> float:
        """The total weight of the part."""
        self._weight = 0.0
        for element in self.elements:
            if element.weight:
                self._weight += element.weight
        return self._weight

    @property
    def model(self):
        """The model to which the part belongs."""
        return self._registration

    @property
    def nodes_count(self) -> int:
        """The number of nodes in the part."""
        return len(self.nodes) - 1

    @property
    def elements_count(self) -> int:
        """The number of elements in the part."""
        return len(self.elements) - 1

    @property
    def element_types(self) -> Dict[type, List[_Element]]:
        """The types of elements in the part grouped by their type."""
        element_types = {}
        for element in self.elements:
            element_types.setdefault(type(element), []).append(element)
        return element_types

    @property
    def groups(self) -> Set[GroupType]:
        """The groups of the part."""
        return self._groups

    # =========================================================================
    #                       Methods
    # =========================================================================

    def transform(self, transformation: Transformation) -> None:
        """Transform the part.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`
            The transformation to apply.

        """
        for node in self.nodes:
            node.transform(transformation)
        self._boundary_mesh.transform(transformation) if self._boundary_mesh else None
        self._discretized_boundary_mesh.transform(transformation) if self._discretized_boundary_mesh else None

    def transformed(self, transformation: Transformation) -> "_Part":
        """Return a transformed copy of the part.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`
            The transformation to apply.
        """
        part = self.copy()
        part.transform(transformation)
        return part

    def elements_by_dimension(self, dimension: int = 1) -> Iterable["_Element"]:
        dimenstion_map = {1: _Element1D, 2: _Element2D, 3: _Element3D}
        if dimension not in dimenstion_map:
            raise ValueError(f"Invalid dimension {dimension}. Valid dimensions are {list(dimenstion_map.keys())}.")
        return self.elements.subgroup(condition=lambda x: isinstance(x, dimenstion_map[dimension])).elements


    # =========================================================================
    #                           Materials methods
    # =========================================================================
       
    def find_materials_by_name(self, name: str) -> Set[_Material]:
        """Find all materials with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        List[_Material]
        """
        return self.materials.subgroup(condition=lambda x: x.name == name).materials
    
    def find_material_by_name(self, name: str) -> Optional[_Material]:
        """Find a material with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        Optional[_Material]
        """
        subset = self.find_materials_by_name(name)
        if len(subset) == 1:
            return subset.pop()
        if len(self.materials) == 0:
            print(f"No materials found in part {self.name}.")
            return None
        if len(subset) > 1:
            raise ValueError(f"Multiple materials found with name '{name}' in part '{self.name}'. Please use find_materials_by_name to retrieve all matching materials.")
        

    def find_material_by_uid(self, uid: str) -> Optional[_Material]:
        """Find a material with a given unique identifier.

        Parameters
        ----------
        uid : str

        Returns
        -------
        Optional[_Material]
        """
        for material in self.materials:
            if material._uid == uid:
                return material
        return None

    def contains_material(self, material: _Material) -> bool:
        """Verify that the part contains a specific material.

        Parameters
        ----------
        material : _Material

        Returns
        -------
        bool
        """
        return material in self.materials


    # =========================================================================
    #                        Sections methods
    # =========================================================================

    def find_sections_by_name(self, name: str) -> Set[_Section]:
        """Find all sections with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        List[_Section]
        """
        return self.sections.subgroup(condition=lambda x: x.name == name).sections
    
    def find_section_by_name(self, name: str) -> Optional[_Section]:
        """Find a section with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        Optional[_Section]
        """
        subset = self.find_sections_by_name(name)
        if len(subset) == 1:
            return subset.pop()
        if len(self.sections) == 0:
            print(f"No sections found in part {self.name}.")
            return None
        if len(subset) > 1:
            raise ValueError(f"Multiple sections found with name '{name}' in part '{self.name}'. Please use find_sections_by_name to retrieve all matching sections.")

    def find_section_by_uid(self, uid: str) -> Optional[_Section]:
        """Find a section with a given unique identifier.

        Parameters
        ----------
        uid : str

        Returns
        -------
        Optional[_Section]
        """
        for section in self.sections:
            if section._uid == uid:
                return section
        return None

    def contains_section(self, section: _Section) -> bool:
        """Verify that the part contains a specific section.

        Parameters
        ----------
        section : _Section

        Returns
        -------
        bool
        """
        return section in self.sections

    # =========================================================================
    #                           Nodes methods
    # =========================================================================
    def find_node_by_uid(self, uid: str) -> Optional[Node]:
        """Retrieve a node in the part using its unique identifier.

        Parameters
        ----------
        uid : str
            The node's unique identifier.

        Returns
        -------
        Optional[Node]
            The corresponding node, or None if not found.

        """
        for node in self._nodes:
            if node._uid == uid:
                return node
        return None

    def find_node_by_key(self, key: int) -> Optional[Node]:
        """Retrieve a node in the model using its key.

        Parameters
        ----------
        key : int
            The node's key.

        Returns
        -------
        Optional[Node]
            The corresponding node, or None if not found.

        """
        for node in self._nodes:
            if node.key == key:
                return node
        print(f"No nodes found with key {key}")
        return None

    def find_node_by_name(self, name: str) -> Set[Node]:
        """Find a node with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        List[Node]
            List of nodes with the given name.

        """
        return self.nodes.subgroup(condition=lambda x: x.name == name).members

    def find_nodes_on_plane(self, plane: Plane, tol: float = 1.0) -> NodesGroup:
        """Find all nodes on a given plane.

        Parameters
        ----------
        plane : Plane
            The plane.
        tol : float, optional
            Tolerance for the search, by default 1.0.

        Returns
        -------
        List[Node]
            List of nodes on the given plane.
        """
        return self.nodes.subgroup(condition=lambda x: is_point_on_plane(x.point, plane, tol))

    def find_closest_nodes_to_point(
        self, point: List[float], number_of_nodes: int = 1, report: Optional[bool] = False, single: bool = False
    ) -> "NodesGroup | None | Dict[Node, float]":
        """
        Find the closest number_of_nodes nodes to a given point.

        Parameters
        ----------
        point : :class:`compas.geometry.Point` | List[float]
            Point or List of coordinates representing the point in x, y, z.
        number_of_nodes : int
            The number of closest points to find.
        report : bool
            Whether to return distances along with the nodes.

        Returns
        -------
        List[Node] or Dict[Node, float]
            A list of the closest nodes, or a dictionary with nodes
            and distances if report=True.
        """
        if number_of_nodes > len(self.nodes):
            if compas_fea2.VERBOSE:
                print(f"The number of nodes to find exceeds the available nodes. Capped to {len(self.nodes)}")
            number_of_nodes = len(self.nodes)
        if number_of_nodes < 0:
            raise ValueError("The number of nodes to find must be positive")

        if number_of_nodes == 0:
            return None

        tree = KDTree([n.xyz for n in self.nodes])
        distances, indices = tree.query(point, k=number_of_nodes)
        if number_of_nodes == 1:
            if single:
                return NodesGroup([list(self.nodes)[indices]])
            else:
                distances = [distances]
                indices = [indices]
                closest_nodes = [list(self.nodes)[i] for i in indices]

        closest_nodes = [list(self.nodes)[i] for i in indices]  # type: ignore[assignment]

        if report:
            # Return a dictionary with nodes and their distances
            return {node: distance for node, distance in zip(closest_nodes, distances)}

        return NodesGroup(closest_nodes)

    def find_closest_nodes_to_node(self, node: Node, number_of_nodes: int = 1, report: Optional[bool] = False, single: bool = False) -> "NodesGroup | None | Dict[Node, float]":
        """Find the n closest nodes around a given node (excluding the node itself).

        Parameters
        ----------
        node : Node
            The given node.
        distance : float
            Distance from the location.
        number_of_nodes : int
            Number of nodes to return.
        plane : Optional[Plane], optional
            Limit the search to one plane.

        Returns
        -------
        List[Node]
            List of the closest nodes.
        """
        return self.find_closest_nodes_to_point(node.xyz, number_of_nodes, report=report, single=single)

    def find_nodes_in_polygon(self, polygon: "Polygon", tol: float = 1.1) -> "NodesGroup | None":
        """Find the nodes of the part that are contained within a planar polygon.

        Parameters
        ----------
        polygon : compas.geometry.Polygon
            The polygon for the search.
        tol : float, optional
            Tolerance for the search, by default 1.1.

        Returns
        -------
        List[Node]
            List of nodes within the polygon.
        """
        S = Scale.from_factors([tol] * 3, polygon.frame)
        T = Transformation.from_frame_to_frame(Frame.from_plane(polygon.plane), Frame.worldXY())
        nodes_on_plane: NodesGroup = self.find_nodes_on_plane(Plane.from_frame(polygon.plane))
        polygon_xy = polygon.transformed(S)
        polygon_xy = polygon.transformed(T)
        return nodes_on_plane.subgroup(condition=lambda x: is_point_in_polygon_xy(Point(*x.xyz).transformed(T), polygon_xy))

    def find_nodes_around_point(
        self,
        point: Point,
        distance: float = 1.0,
    ) -> "NodesGroup | None | Dict[Node, float]":
        """Find the nodes around a given point within a specified distance.

        Parameters
        ----------
        point : Point
            The point to search around.
        distance : float
            The distance from the point to search for nodes.
        report : bool, optional
            Whether to return distances along with the nodes.
        single : bool, optional
            Whether to return a single node or a group of nodes.

        Returns
        -------
        NodesGroup or None or Dict[Node, float]
            A group of nodes within the specified distance, or a dictionary with nodes and distances if report=True.
        """
        if not isinstance(point, Point):
            raise TypeError(f"{point!r} is not a Point.")

        if distance < 0:
            raise ValueError("The distance must be positive")

        if distance == 0:
            return None

        # Create a KDTree for efficient nearest neighbor search
        tree = KDTree([n.xyz for n in self.nodes])
        xyz = [point.x, point.y, point.z]  # Ensure point is in the correct format
        indices = tree.query_ball_point(xyz, r=distance)

        if not indices:
            return None

        closest_nodes = [list(self.nodes)[i] for i in indices]

        return NodesGroup(closest_nodes) if len(closest_nodes) > 1 else closest_nodes[0]

    def contains_node(self, node: Node) -> bool:
        """Verify that the part contains a given node.

        Parameters
        ----------
        node : Node
            The node to check.

        Returns
        -------
        bool
            True if the node is in the part, False otherwise.
        """
        return node in self.nodes

    def add_node(self, node: Node) -> Node:
        """Add a node to the part.

        Parameters
        ----------
        node : :class:`compas_fea2.model.Node`
            The node.

        Returns
        -------
        :class:`compas_fea2.model.Node`
            The identifier of the node in the part.

        Raises
        ------
        TypeError
            If the node is not a node.

        Notes
        -----
        By adding a Node to the part, it gets registered to the part.

        Examples
        --------
        >>> part = Part()
        >>> node = Node(xyz=(1.0, 2.0, 3.0))
        >>> part.add_node(node)

        """
        if not isinstance(node, Node):
            raise TypeError("{!r} is not a node.".format(node))

        if node not in self._nodes:
            node._part_key = len(self.nodes)
            self._nodes.add_member(node)
            node._registration = self
            if compas_fea2.VERBOSE:
                print("Node {!r} registered to {!r}.".format(node, self))
        return node

    def add_nodes(self, nodes: Union[List[Node], NodesGroup]) -> List[Node]:
        """Add multiple nodes to the part.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`]
            The list of nodes.

        Returns
        -------
        list[:class:`compas_fea2.model.Node`]

        Examples
        --------
        >>> part = Part()
        >>> node1 = Node([1.0, 2.0, 3.0])
        >>> node2 = Node([3.0, 4.0, 5.0])
        >>> node3 = Node([3.0, 4.0, 5.0])
        >>> nodes = part.add_nodes([node1, node2, node3])

        """
        return [self.add_node(node) for node in nodes]

    def remove_node(self, node: Node) -> None:
        """Remove a :class:`compas_fea2.model.Node` from the part.

        Warnings
        --------
        Removing nodes can cause inconsistencies.

        Parameters
        ----------
        node : :class:`compas_fea2.model.Node`
            The node to remove.

        """
        if self.contains_node(node):
            self.nodes.remove_member(node)
            if node.gkey is not None:
                self.gkey_node.pop(node.gkey)
            node._registration = None
            if compas_fea2.VERBOSE:
                print(f"Node {node!r} removed from {self!r}.")

    def remove_nodes(self, nodes: List[Node]) -> None:
        """Remove multiple :class:`compas_fea2.model.Node` from the part.

        Warnings
        --------
        Removing nodes can cause inconsistencies.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`]
            List with the nodes to remove.

        """
        for node in nodes:
            self.remove_node(node)

    def compute_nodal_masses(self) -> List[float]:
        """Compute the nodal mass of the part from the mass of each element.
        it uses the nodal mass of each element to compute the total nodal mass.

        Warnings
        --------
        Rotational masses are not considered.

        Returns
        -------
        list
            List with the nodal masses.

        """
        # clear masses
        for node in self.nodes:
            node.mass = [0.0 for _ in range(6)]
        for element in self.elements:
            elNodalMass = getattr(element, "nodal_mass")
            if element and elNodalMass:
                for node in element.nodes:
                    node.mass = [a + b for a, b in zip(node.mass[:3], elNodalMass[:3])] + [0.0, 0.0, 0.0]
        return [sum(node.mass[i] for node in self.nodes) for i in range(3)]

    # =========================================================================
    #                           Elements methods
    # =========================================================================
    def find_element_by_key(self, key: int) -> Union["_Element", "_Element1D", "_Element2D", "_Element3D", None]:
        """Retrieve an element in the model using its key.

        Parameters
        ----------
        key : int
            The element's key.

        Returns
        -------
        Optional[_Element]
            The corresponding element, or None if not found.
        """
        for element in self.elements:
            if element.key == key:
                return element
        return None

    def find_element_by_name(self, name: str) -> Union["_Element", "_Element1D", "_Element2D", "_Element3D", None]:
        """Find all elements with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        List[_Element]
            List of elements with the given name.
        """
        for element in self.elements:
            if element.key == name:
                return element
        return None

    def contains_element(self, element: _Element) -> bool:
        """Verify that the part contains a specific element.

        Parameters
        ----------
        element : _Element

        Returns
        -------
        bool
        """
        return element in self.elements

    def add_element(self, element: Union["_Element", "_Element1D", "_Element2D", "_Element3D"]) -> Union["_Element", "_Element1D", "_Element2D", "_Element3D"]:
        """Add an element to the part.

        Parameters
        ----------
        element : _Element
            The element instance.

        Returns
        -------
        _Element

        Raises
        ------
        TypeError
            If the element is not an instance of _Element.
        """

        self.add_nodes(element.nodes)
        for node in element.nodes:
            node.connected_elements.add(element)
        if not element.section:
            raise ValueError("Element must have a section defined before adding it to the part.")

        element._part_key = len(self.elements)
        self._elements.add_member(element)
        element._registration = self

        self.graph.add_node(element, type="element")
        for node in element.nodes:
            self.graph.add_node(node, type="node")
            self.graph.add_edge(element, node, relation="connects")

        if compas_fea2.VERBOSE:
            print(f"Element {element!r} registered to {self!r}.")

        return element

    def add_elements(self, elements: List[_Element]) -> List[_Element]:
        """Add multiple elements to the part.

        Parameters
        ----------
        elements : List[_Element]

        Returns
        -------
        List[_Element]
        """
        return [self.add_element(element) for element in elements]

    def remove_element(self, element: _Element) -> None:
        """Remove an element from the part.

        Parameters
        ----------
        element : _Element
            The element to remove.

        Warnings
        --------
        Removing elements can cause inconsistencies.
        """
        if self.contains_element(element):
            self.elements.elements.remove(element)
            element._registration = None
            for node in element.nodes:
                node.connected_elements.remove(element)
            if compas_fea2.VERBOSE:
                print(f"Element {element!r} removed from {self!r}.")

    def remove_elements(self, elements: List[_Element]) -> None:
        """Remove multiple elements from the part.

        Parameters
        ----------
        elements : List[_Element]
            List of elements to remove.

        Warnings
        --------
        Removing elements can cause inconsistencies.
        """
        for element in elements:
            self.remove_element(element)

    def is_element_on_boundary(self, element: _Element) -> bool:
        """Check if the element belongs to the boundary mesh of the part.

        Parameters
        ----------
        element : _Element
            The element to check.

        Returns
        -------
        bool
            True if the element is on the boundary, False otherwise.
        """

        discretized_boundary_mesh = getattr(self, "_discretized_boundary_mesh", None)

        if element.on_boundary is None:
            if all(node.on_boundary for node in element.nodes):
                element.on_boundary = True
            elif all(node.on_boundary is False for node in element.nodes):
                element.on_boundary = False
            else:
                element_faces = getattr(element, "faces", None)
                if not discretized_boundary_mesh or not element_faces:
                    raise ValueError("Discretized boundary mesh or element faces not defined for checking boundary condition.")
                if isinstance(element, _Element3D):
                    if any(TOL.geometric_key(centroid_points([node.xyz for node in face.nodes])) in discretized_boundary_mesh.centroid_face for face in element_faces):
                        element.on_boundary = True
                    else:
                        element.on_boundary = False
                elif isinstance(element, _Element2D):
                    centroid = centroid_points([node.xyz for node in element.nodes])
                    geometric_key = TOL.geometric_key(centroid)
                    if geometric_key in discretized_boundary_mesh.centroid_face:
                        element.on_boundary = True
                    else:
                        element.on_boundary = False
        return bool(element.on_boundary)

    # =========================================================================
    #                           Faces methods
    # =========================================================================

    def find_faces_on_plane(self, plane: Plane, tol: float = 1) -> FacesGroup:
        """Find the faces of the elements that belong to a given plane, if any.

        Parameters
        ----------
        plane : :class:`compas.geometry.Plane`
            The plane where the faces should belong.

        Returns
        -------
        list[:class:`compas_fea2.model.Face`]
            List with the faces belonging to the given plane.

        Notes
        -----
        The search is limited to solid elements.
        """
        elements_sub_group = self.elements.subgroup(condition=lambda x: isinstance(x, (_Element2D, _Element3D)))
        faces = []
        for element in elements_sub_group:
            element_faces = getattr(element, "faces", None)
            if not element_faces:
                raise ValueError(f"Element {element} does not have faces defined.")
            for face in element_faces:
                faces.append(face)
        faces_group = FacesGroup(faces)
        faces_subgroup = faces_group.subgroup(condition=lambda x: all(is_point_on_plane(node.xyz, plane, tol=tol) for node in x.nodes))
        return faces_subgroup

    def find_faces_in_polygon(self, polygon: "Polygon", tol: float = 1.1) -> FacesGroup:
        """Find the faces of the elements that are contained within a planar polygon.

        Parameters
        ----------
        polygon : compas.geometry.Polygon
            The polygon for the search.
        tol : float, optional
            Tolerance for the search, by default 1.1.

        Returns
        -------
        :class:`compas_fea2.model.FaceGroup`]
            Subgroup of the faces within the polygon.
        """
        # filter elements with faces
        elements_sub_group = self.elements.subgroup(condition=lambda x: isinstance(x, (_Element2D, _Element3D)))
        faces = []
        for element in elements_sub_group:
            element_faces = getattr(element, "faces", None)
            if not element_faces:
                raise ValueError(f"Element {element} does not have faces defined.")
            for face in element_faces:
                faces.append(face)
        faces_group = FacesGroup(faces)

        # find faces on the plane of the polygon
        if not is_coplanar(polygon.points):
            raise ValueError("The polygon is not planar.")

        plane = getattr(polygon, "plane", None) or Plane.from_points(polygon.points[:3])
        frame = Frame.from_plane(plane)

        faces_subgroup = faces_group.subgroup(condition=lambda face: all(is_point_on_plane(node.xyz, plane) for node in face.nodes))
        # find faces within the polygon
        S = Scale.from_factors([tol] * 3, frame)
        T = Transformation.from_frame_to_frame(frame, Frame.worldXY())
        polygon_xy = polygon.transformed(S)
        polygon_xy = polygon.transformed(T)
        faces_subgroup.subgroup(condition=lambda face: all(is_point_in_polygon_xy(Point(*node.xyz).transformed(T), polygon_xy) for node in face.nodes))
        return faces_subgroup

    def find_boudary_faces(self) -> "FacesGroup":
        """Find the boundary faces of the part.

        Returns
        -------
        list[:class:`compas_fea2.model.Face`]
            List with the boundary faces.
        """
        return self.faces.subgroup(condition=lambda x: all(node.on_boundary for node in x.nodes))

    # =========================================================================
    #                           Groups methods
    # =========================================================================
    # BUG it is possible to have multiple groups with the same name, this should be fixed
    def find_group_by_name(self, name: str) -> GroupType | None:
        """Find all groups with a given name.

        Parameters
        ----------
        name : str
            The name of the group.

        Returns
        -------
        List[Union[NodesGroup, ElementsGroup, FacesGroup]]
            List of groups with the given name.
        """
        for group in self.groups:
            if group.name == name:
                return group
        print(f"No groups found with name {name}")
        return None

    def add_group(self, group: GroupType) -> GroupType:
        """Add a node or element group to the part.

        Parameters
        ----------
        group : :class:`compas_fea2.model.NodesGroup` | :class:`compas_fea2.model.ElementsGroup` |
                :class:`compas_fea2.model.FacesGroup`

        Returns
        -------
        :class:`compas_fea2.model.Group`

        Raises
        ------
        TypeError
            If the group is not a node or element group.

        """
        group.registration = self
        
        self._groups.add(group)
        return group

    def add_groups(self, groups: List[GroupType]) -> List[GroupType]:
        """Add multiple groups to the part.

        Parameters
        ----------
        groups : list[:class:`compas_fea2.model.Group`]

        Returns
        -------
        list[:class:`compas_fea2.model.Group`]

        """
        return [self.add_group(group) for group in groups]

    # ==============================================================================
    # Results methods
    # ==============================================================================

    # def sorted_nodes_by_displacement(self, step: "_Step", component: str = "length") -> List[Node]:  # noqa: F821
    #     """Return a list with the nodes sorted by their displacement

    #     Parameters
    #     ----------
    #     step : :class:`compas_fea2.problem._Step`
    #         The step.
    #     component : str, optional
    #         One of ['x', 'y', 'z', 'length'], by default 'length'.

    #     Returns
    #     -------
    #     list[:class:`compas_fea2.model.Node`]
    #         The nodes sorted by displacement (ascending).

    #     """
    #     return self.nodes.sorted_by(lambda n: getattr(Vector(*n.results[step].get("U", None)), component))

    # def get_max_displacement(
    #     self,
    #     problem: "Problem",  # noqa: F821
    #     step: Optional["_Step"] = None,  # noqa: F821
    #     component: str = "length",
    # ) -> Tuple[Node, float]:
    #     """Retrieve the node with the maximum displacement

    #     Parameters
    #     ----------
    #     problem : :class:`compas_fea2.problem.Problem`
    #         The problem.
    #     step : :class:`compas_fea2.problem._Step`, optional
    #         The step, by default None. If not provided, the last step of the
    #         problem is used.
    #     component : str, optional
    #         One of ['x', 'y', 'z', 'length'], by default 'length'.

    #     Returns
    #     -------
    #     :class:`compas_fea2.model.Node`, float
    #         The node and the displacement.

    #     """
    #     step = step or problem._steps_order[-1]
    #     node = self.sorted_nodes_by_displacement(step=step, component=component)[-1]
    #     displacement = getattr(Vector(*node.results[problem][step].get("U", None)), component)
    #     return node, displacement

    # def get_min_displacement(
    #     self,
    #     problem: "Problem",  # noqa: F821
    #     step: Optional["_Step"] = None,  # noqa: F821
    #     component: str = "length",
    # ) -> Tuple[Node, float]:  # noqa: F821
    #     """Retrieve the node with the minimum displacement

    #     Parameters
    #     ----------
    #     problem : :class:`compas_fea2.problem.Problem`
    #         The problem.
    #     step : :class:`compas_fea2.problem._Step`, optional
    #         The step, by default None. If not provided, the last step of the
    #         problem is used.
    #     component : str, optional
    #         One of ['x', 'y', 'z', 'length'], by default 'length'.

    #     Returns
    #     -------
    #     :class:`compas_fea2.model.Node`, float
    #         The node and the displacement.

    #     """
    #     step = step or problem._steps_order[-1]
    #     node = self.sorted_nodes_by_displacement(step=step, component=component)[0]
    #     displacement = getattr(Vector(*node.results[problem][step].get("U", None)), component)
    #     return node, displacement

    # def get_average_displacement_at_point(
    #     self,
    #     problem: "Problem",  # noqa: F821
    #     point: "Point",
    #     distance: float,
    #     step: Optional["_Step"] = None,  # noqa: F821
    #     component: str = "length",
    # ) -> Tuple[List[float], float]:
    #     """Compute the average displacement around a point

    #     Parameters
    #     ----------
    #     problem : :class:`compas_fea2.problem.Problem`
    #         The problem.
    #     step : :class:`compas_fea2.problem._Step`, optional
    #         The step, by default None. If not provided, the last step of the
    #         problem is used.
    #     component : str, optional
    #         One of ['x', 'y', 'z', 'length'], by default 'length'.
    #     project : bool, optional
    #         If True, project the point onto the plane, by default False.

    #     Returns
    #     -------
    #     List[float], float
    #         The point and the average displacement.

    #     """
    #     step = step or problem._steps_order[-1]
    #     nodes = self.find_nodes_around_point(point=point, distance=distance)
    #     if nodes:
    #         displacements = [getattr(Vector(*node.results[problem][step].get("U", None)), component) for node in nodes]
    #         return point, sum(displacements) / len(displacements)
    #     return point, 0.0


class Part(_Part):
    """Deformable part."""

    __doc__ = __doc__ or ""
    __doc__ += _Part.__doc__ or ""
    __doc__ += """
    Additional Attributes
    ---------------------
    materials : Set[:class:`compas_fea2.model._Material`]
        The materials belonging to the part.
    sections : Set[:class:`compas_fea2.model._Section`]
        The sections belonging to the part.
    releases : Set[:class:`compas_fea2.model._BeamEndRelease`]
        The releases belonging to the part.

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    # =========================================================================
    #                       Constructor methods
    # =========================================================================
    @classmethod
    def frame_from_compas_mesh(cls, mesh: "Mesh", section: "_Section1D", name: Optional[str] = None, **kwargs) -> "_Part":
        """
        Creates a Part object from a compas Mesh by converting each edge into a BeamElement with a third orientation node.

        Parameters
        ----------
        mesh : Mesh
            The compas mesh to convert.
        section : _Section1D
            Section to assign to all frame elements.
        name : str, optional
            Name of the part.

        Returns
        -------
        _Part
            The created Part.
        """
        part = cls(name=name, **kwargs)

        # Add main mesh nodes
        vertex_node = {vertex: part.add_node(Node(mesh.vertex_coordinates(vertex))) for vertex in mesh.vertices()}  # type: ignore

        # Process each edge
        for edge in mesh.edges():
            n1, n2 = [vertex_node[vertex] for vertex in edge]
            p1 = Point(*n1.xyz)
            p2 = Point(*n2.xyz)

            # Get averaged normal from adjacent faces
            faces = mesh.edge_faces(edge)
            normals = [Vector(*mesh.face_normal(f)) for f in faces if f is not None]
            if not normals:
                raise ValueError(f"Edge {edge} has no adjacent faces to determine orientation.")
            normal = sum(normals, Vector(0, 0, 0)).unitized()

            # Compute orientation point offset from node 1 in the direction of the normal
            offset = 1e-3  # Small offset to define orientation plane
            orientation_point = p1 + normal * offset

            # Beam element with 3 nodes
            part.add_element(BeamElement(nodes=[n1, n2], orientation=orientation_point, section=section))
        return part

    @classmethod
    def from_gmsh(cls, gmshModel: object, section: Union["SolidSection", "ShellSection"], name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a Part object from a gmshModel object.

        Parameters
        ----------
        gmshModel : object
            gmsh Model to convert.
        section : Union[compas_fea2.model.SolidSection, compas_fea2.model.ShellSection]
            Section to assign to the elements.
        name : str, optional
            Name of the new part.

        Returns
        -------
        _Part
            The part created from the gmsh model.
        """
        return super().from_gmsh(gmshModel, section=section, name=name, **kwargs)

    @classmethod
    def from_boundary_mesh(cls, boundary_mesh: "Mesh", section: Union["SolidSection", "ShellSection"], name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a Part object from a 3-dimensional :class:`compas.datastructures.Mesh`
        object representing the boundary envelope of the Part.

        Parameters
        ----------
        boundary_mesh : :class:`compas.datastructures.Mesh`
            Boundary envelope of the Part.
        section : Union[compas_fea2.model.SolidSection, compas_fea2.model.ShellSection]
            Section to assign to the elements.
        name : str, optional
            Name of the new part.

        Returns
        -------
        _Part
            The part created from the boundary mesh.
        """
        return super().from_boundary_mesh(boundary_mesh, section=section, name=name, **kwargs)

    # =========================================================================
    #                           Releases methods
    # =========================================================================

    def add_beam_release(self, element: BeamElement, location: str, release: _BeamEndRelease) -> _BeamEndRelease:
        """Add a :class:`compas_fea2.model._BeamEndRelease` to an element in the part.

        Parameters
        ----------
        element : :class:`compas_fea2.model.BeamElement`
            The element to release.
        location : str
            'start' or 'end'.
        release : :class:`compas_fea2.model._BeamEndRelease`
            Release type to apply.

        Returns
        -------
        :class:`compas_fea2.model._BeamEndRelease`
            The release applied to the element.
        """
        raise NotImplementedError("Beam releases are not implemented in Part class. Use RigidPart instead.")
        if not isinstance(release, _BeamEndRelease):
            raise TypeError(f"{release!r} is not a beam release element.")
        release.element = element
        release.location = location
        self._releases.add_member(release)
        return release


class RigidPart(_Part):
    """Rigid part."""

    __doc__ = __doc__ or ""
    __doc__ += _Part.__doc__ or ""
    __doc__ += """
    Additional Attributes
    ---------------------
    reference_node : :class:`compas_fea2.model.Node`
        A node acting as a reference point for the part, by default `None`. This
        is required if the part is rigid as it controls its movement in space.

    """

    def __init__(self, reference_node: Optional[Node] = None, **kwargs):
        super().__init__(**kwargs)
        self._reference_node = reference_node


    @classmethod
    def from_gmsh(cls, gmshModel: object, name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a RigidPart object from a gmshModel object.

        Parameters
        ----------
        gmshModel : object
            gmsh Model to convert.
        name : str, optional
            Name of the new part.

        Returns
        -------
        _Part
            The part created from the gmsh model.
        """
        kwargs["rigid"] = True
        return super().from_gmsh(gmshModel, name=name, **kwargs)

    @classmethod
    def from_boundary_mesh(cls, boundary_mesh: "Mesh", name: Optional[str] = None, **kwargs) -> _Part:
        """Create a RigidPart object from a 3-dimensional :class:`compas.datastructures.Mesh`
        object representing the boundary envelope of the Part.

        Parameters
        ----------
        boundary_mesh : :class:`compas.datastructures.Mesh`
            Boundary envelope of the RigidPart.
        name : str, optional
            Name of the new part.

        Returns
        -------
        _Part
            The part created from the boundary mesh.
        """
        kwargs["rigid"] = True
        return super().from_boundary_mesh(boundary_mesh, name=name, **kwargs)

    # =========================================================================
    #                        Elements methods
    # =========================================================================
    def add_element(self, element: _Element) -> _Element:
        # type: (_Element) -> _Element
        """Add an element to the part.

        Parameters
        ----------
        element : :class:`compas_fea2.model._Element`
            The element instance.

        Returns
        -------
        :class:`compas_fea2.model._Element`

        Raises
        ------
        TypeError
            If the element is not an element.

        """
        if not hasattr(element, "rigid"):
            raise TypeError("The element type cannot be assigned to a RigidPart")
        if not getattr(element, "rigid"):
            raise TypeError("Rigid parts can only have rigid elements")
        return super().add_element(element)
