import logging
from importlib import import_module
from itertools import groupby
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Set
from typing import TypeVar
from typing import TYPE_CHECKING


from compas_fea2.base import FEAData

# Define a generic type for members
T = TypeVar("T")
G = TypeVar("G", bound="_Group")

if TYPE_CHECKING:
    from compas_fea2.model.parts import _Part
    from compas_fea2.model.sections import _Section
    from compas_fea2.model.materials.material import _Material
    from compas_fea2.model.interfaces import Interface
    from compas_fea2.model.bcs import _BoundaryCondition
    from compas_fea2.model.connectors import Connector
    from compas_fea2.model.model import Model
    from compas_fea2.model.nodes import Node
    from compas_fea2.model.elements import _Element
    from compas_fea2.model.elements import Edge
    from compas_fea2.model.elements import Face
    from compas_fea2.model.releases import _BeamEndRelease
    from compas_fea2.model.constraints import _Constraint
    from compas_fea2.model.interactions import _Interaction

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class _Group(FEAData):
    """
    Base class for all groups.

    Parameters
    ----------
    members : Iterable, optional
        An iterable containing members belonging to the group.
        Members can be nodes, elements, faces, or parts. Default is None.

    Attributes
    ----------
    _members : Set[T]
        The set of members belonging to the group.
    """

    def __init__(self, member_class:type, members: Iterable[T] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._members_class = member_class
        if self._members_class and members:
            if any(not isinstance(member, self._members_class) for member in members):
                raise TypeError(f"All members must be of type {self._members_class.__name__}.")
        self._members = set(members) if members else set()
        self._part = None
        self._model = None

    def __len__(self) -> int:
        """Return the number of members in the group."""
        return len(self._members)

    def __contains__(self, item: object) -> bool:
        """Check if an item is in the group."""
        return item in self._members

    def __iter__(self):
        """Return an iterator over the members."""
        return iter(self._members)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {len(self._members)} members>"

    def __add__(self: G, other: G) -> G:
        if not isinstance(other, type(self)):
            raise TypeError("Can only add same group types together.")
        return self.__class__(members=self._members | other._members, member_class=self._members_class)

    def __sub__(self:G, other: G) -> G:
        if not isinstance(other, type(self)):
            raise TypeError("Can only subtract same group types from each other.")
        return self.__class__(members=self._members - other._members, member_class=self._members_class)

    def to_list(self) -> list:
        """Return the members of the group as a list."""
        return list(self._members)

    @property
    def members(self) -> set[Any]:
        """Return the members of the group."""
        return self._members

    @property
    def sorted(self) -> List[Any]:
        """
        Return the members of the group sorted in ascending order.

        Returns
        -------
        List[object]
            A sorted list of group members.
        """
        return sorted(self._members, key=lambda x: getattr(x, "key", str(x)))

    def sorted_by(self, key: Callable[[T], object], reverse: bool = False) -> List[T]:
        """
        Return the members of the group sorted based on a custom key function.

        Parameters
        ----------
        key : Callable[[T], object]
            A function that extracts a key from a member for sorting.
        reverse : bool, optional
            Whether to sort in descending order. Default is False.

        Returns
        -------
        List[T]
            A sorted list of group members based on the key function.
        """
        return sorted(self._members, key=key, reverse=reverse)

    def subgroup(self: G, condition: Callable[[T], bool], **kwargs) -> G:
        """
        Create a subgroup based on a given condition.

        Parameters
        ----------
        condition : Callable[[T], bool]
            A function that takes a member as input and returns True if the member
            should be included in the subgroup.

        Returns
        -------
        G
            A new group (of the same type as self) containing the members that satisfy the condition.
        """
        filtered_members = set(filter(condition, self._members))
        return self.__class__(filtered_members, **kwargs)

    def group_by(self: G, key: Callable[[T], Any]) -> Dict[Any, G]:
        """
        Group members into multiple subgroups based on a key function.

        Parameters
        ----------
        key : Callable[[T], Any]
            A function that extracts a key from a member for grouping.

        Returns
        -------
        Dict[Any, G]
            A dictionary where keys are the grouping values and values are group instances of the same type as self.
        """
        sorted_members = sorted(self._members, key=key)
        grouped_members = {k: set(v) for k, v in groupby(sorted_members, key=key)}
        return {k: self.__class__(v, name=getattr(self, 'name', None)) for k, v in grouped_members.items()}

    def union(self: G, other: "_Group") -> G:
        """
        Create a new group containing all members from this group and another group.

        Parameters
        ----------
        other : _Group
            Another group whose members should be combined with this group.

        Returns
        -------
        _Group
            A new group containing all members from both groups.
        """
        if not isinstance(other, _Group):
            raise TypeError("Can only perform union with another _Group instance.")
        return self.__class__(self._members | other._members)

    def intersection(self: G, other: "_Group") -> G:
        """
        Create a new group containing only members that are present in both groups.

        Parameters
        ----------
        other : _Group
            Another group to find common members with.

        Returns
        -------
        _Group
            A new group containing only members found in both groups.
        """
        if not isinstance(other, _Group):
            raise TypeError("Can only perform intersection with another _Group instance.")
        return self.__class__(self._members & other._members)

    def difference(self: G, other: "_Group") -> G:
        """
        Create a new group containing members that are in this group but not in another.

        Parameters
        ----------
        other : _Group
            Another group whose members should be removed from this group.

        Returns
        -------
        _Group
            A new group containing members unique to this group.
        """
        if not isinstance(other, _Group):
            raise TypeError("Can only perform difference with another _Group instance.")
        return self.__class__(self._members - other._members)

    def _add_member(self, member: T) -> T:
        if self._members_class and not isinstance(member, self._members_class):
            raise TypeError(f"Member must be of type {self._members_class.__name__}.")
        self._members.add(member)
        return member

    def _add_members(self, members: Iterable[T]) -> List[T]:
        added = []
        for member in members:
            added.append(self._add_member(member))
        return added

    def _remove_member(self, member: object) -> bool:
        """
        Remove a member from the group.

        Parameters
        ----------
        member : T
            The member to remove.

        Returns
        -------
        bool
            True if the member was removed, False if not found.
        """
        if member in self._members:
            self._members.remove(member)
            return True
        logger.warning(f"Member {member} not found in the group.")
        return False

    def _remove_members(self, members: Iterable[T]) -> List[T]:
        """
        Remove multiple members from the group.

        Parameters
        ----------
        members : Iterable[T]
            The members to remove.

        Returns
        -------
        List[T]
            The members that were actually removed.
        """
        removed = []
        for member in members:
            if member in self._members:
                self._members.remove(member)
                removed.append(member)
            else:
                logger.warning(f"Member {member} not found in the group.")
        return removed

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the group to a dictionary.

        Returns
        -------
        Dict[str, Any]
            A dictionary representation of the group.
        """
        return {"members": list(self._members)}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "_Group":
        """
        Deserialize a dictionary to create a `_Group` instance.

        Parameters
        ----------
        data : Dict[str, Any]
            A dictionary representation of the group.

        Returns
        -------
        _Group
            A `_Group` instance with the deserialized members.
        """
        return cls(set(data.get("members", [])))

    def clear(self) -> None:
        """Remove all members from the group."""
        self._members.clear()


class NodesGroup(_Group):
    """Base class nodes groups.

    Parameters
    ----------
    nodes : list[:class:`compas_fea2.model.Node`]
        The nodes belonging to the group.

    Attributes
    ----------
    nodes : list[:class:`compas_fea2.model.Node`]
        The nodes belonging to the group.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.

    Notes
    -----
    NodesGroups are registered to the same :class:`compas_fea2.model._Part` as its nodes
    and can belong to only one Part.

    """

    def __init__(self, nodes: Iterable["Node"], **kwargs) -> None:
        from compas_fea2.model.nodes import Node
        super().__init__(members=nodes, member_class=Node, **kwargs)

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"nodes": [node.__data__ for node in self.nodes]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "NodesGroup":
        from compas_fea2.model.nodes import Node
        return cls(nodes=[Node.__from_data__(node) for node in data["nodes"]])

    @property
    def part(self) -> Any:
        return self._part

    @property
    def model(self) -> Any:
        return self._model

    @property
    def nodes(self) -> Set["Node"]:
        return self._members

    def add_node(self, node: "Node") -> "Node":
        """
        Add a node to the group.

        Parameters
        ----------
        node : :class:`compas_fea2.model.Node`
            The node to add.

        Returns
        -------
        :class:`compas_fea2.model.Node`
            The node added.
        """
        return self._add_member(node)

    def add_nodes(self, nodes: Iterable["Node"]) -> List["Node"]:
        """
        Add multiple nodes to the group.

        Parameters
        ----------
        nodes : [:class:`compas_fea2.model.Node`]
            The nodes to add.

        Returns
        -------
        [:class:`compas_fea2.model.Node`]
            The nodes added.
        """
        return self._add_members(nodes)


class ElementsGroup(_Group):
    """Base class for elements groups.

    Parameters
    ----------
    elements : list[:class:`compas_fea2.model.Element`]
        The elements belonging to the group.

    Attributes
    ----------
    elements : list[:class:`compas_fea2.model.Element`]
        The elements belonging to the group.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.

    Notes
    -----
    ElementsGroups are registered to the same :class:`compas_fea2.model.Part` as
    its elements and can belong to only one Part.

    """

    def __init__(self, elements: Iterable["_Element"], **kwargs) -> None:
        from compas_fea2.model.elements import _Element
        super().__init__(members=elements, member_class=_Element, **kwargs)

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"elements": [element.__data__ for element in self.elements]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "ElementsGroup":
        elements_module = import_module("compas_fea2.model.elements")
        elements = [getattr(elements_module, element_data["class"]).__from_data__(element_data) for element_data in data["elements"]]
        return cls(elements=elements)

    @property
    def part(self) -> Any:
        return self._registration

    @property
    def model(self) -> Any:
        return self.part._registration

    @property
    def elements(self) -> Set["_Element"]:
        return self._members

    def add_element(self, element: "_Element") -> "_Element":
        """
        Add an element to the group.

        Parameters
        ----------
        element : :class:`compas_fea2.model.Element`
            The element to add.

        Returns
        -------
        :class:`compas_fea2.model.Element`
            The element added.
        """
        return self._add_member(element)

    def add_elements(self, elements: Iterable["_Element"]) -> List["_Element"]:
        """
        Add multiple elements to the group.

        Parameters
        ----------
        elements : [:class:`compas_fea2.model.Element`]
            The elements to add.

        Returns
        -------
        [:class:`compas_fea2.model.Element`]
            The elements added.
        """
        return self._add_members(elements)

class EdgesGroup(_Group):
    """Base class elements edges groups.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    edges : Set[:class:`compas_fea2.model.Edge`]
        The Edges belonging to the group.

    Attributes
    ----------
    name : str
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    edges : Set[:class:`compas_fea2.model.Edge`]
        The Edges belonging to the group.
    nodes : Set[:class:`compas_fea2.model.Node`]
        The Nodes of the edges belonging to the group.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.

    Notes
    -----
    EdgesGroups are registered to the same :class:`compas_fea2.model.Part` as the
    elements of its edges.

    """

    def __init__(self, edges: Iterable["Edge"], **kwargs) -> None:
        from compas_fea2.model.elements import Edge
        super().__init__(members=edges, member_class=Edge, **kwargs)

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"edges": list(self.edges)})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "EdgesGroup":
        obj = cls(edges=set(data["edges"]))
        obj._registration = data["registration"]
        return obj

    @property
    def model(self) -> "Model | None":
        return self._registration

    @property
    def edges(self) -> Set["Edge"]:
        return self._members

    @property
    def nodes(self) -> Set["Node"]:
        nodes_set: Set[Any] = set()
        for edge in self.edges:
            for node in edge.nodes:
                nodes_set.add(node)
        return nodes_set

    def add_edge(self, edge: "Edge") -> "Edge":
        """
        Add a face to the group.

        Parameters
        ----------
        face : :class:`compas_fea2.model.Face`
            The face to add.

        Returns
        -------
        :class:`compas_fea2.model.Face`
            The face added.
        """
        return self._add_member(edge)

    def add_edges(self, edges: Iterable["Edge"]) -> List["Edge"]:
        """
        Add multiple faces to the group.

        Parameters
        ----------
        faces : [:class:`compas_fea2.model.Face`]
            The faces to add.

        Returns
        -------
        [:class:`compas_fea2.model.Face`]
            The faces added.
        """
        return self._add_members(edges)

class FacesGroup(_Group):
    """Base class elements faces groups.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    faces : Set[:class:`compas_fea2.model.Face`]
        The Faces belonging to the group.

    Attributes
    ----------
    name : str
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    faces : Set[:class:`compas_fea2.model.Face`]
        The Faces belonging to the group.
    nodes : Set[:class:`compas_fea2.model.Node`]
        The Nodes of the faces belonging to the group.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.

    Notes
    -----
    FacesGroups are registered to the same :class:`compas_fea2.model.Part` as the
    elements of its faces.

    """

    def __init__(self, faces: Iterable["Face"], **kwargs) -> None:
        from compas_fea2.model.elements import Face
        super().__init__(members=faces, member_class=Face, **kwargs)

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"faces": list(self.faces)})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "FacesGroup":
        obj = cls(faces=set(data["faces"]))
        obj._registration = data["registration"]
        return obj

    @property
    def part(self) -> "_Part":
        return self._registration

    @property
    def model(self) -> "Model":
        return self.part._registration

    @property
    def faces(self) -> Set["Face"]:
        return self._members

    @property
    def nodes(self) -> Set["Node"]:
        nodes_set = set()
        for face in self.faces:
            for node in face.nodes:
                nodes_set.add(node)
        return nodes_set
    
    @property
    def area(self) -> float:
        """Calculate the total area of the faces in the group."""
        return sum(face.area for face in self.faces)
    
    @property
    def normal(self) -> List[float]:
        """Calculate the average normal vector of the faces in the group."""
        from compas.geometry import normalize_vector
        normals = [face.normal for face in self.faces]
        if normals:
            avg_normal = [sum(components) / len(normals) for components in zip(*normals)]
            return normalize_vector(avg_normal)
        raise AttributeError("Could not calculate the average normal vector, no faces in the group.")

    def add_face(self, face: "Face") -> "Face":
        """
        Add a face to the group.

        Parameters
        ----------
        face : :class:`compas_fea2.model.Face`
            The face to add.

        Returns
        -------
        :class:`compas_fea2.model.Face`
            The face added.
        """
        return self._add_member(face)

    def add_faces(self, faces: Iterable["Face"]) -> List["Face"]:
        """
        Add multiple faces to the group.

        Parameters
        ----------
        faces : [:class:`compas_fea2.model.Face`]
            The faces to add.

        Returns
        -------
        [:class:`compas_fea2.model.Face`]
            The faces added.
        """
        return self._add_members(faces)


class PartsGroup(_Group):
    """Base class for parts groups.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    parts : list[:class:`compas_fea2.model.Part`]
        The parts belonging to the group.

    Attributes
    ----------
    parts : list[:class:`compas_fea2.model.Part`]
        The parts belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.

    Notes
    -----
    PartsGroups are registered to the same :class:`compas_fea2.model.Model` as its
    parts and can belong to only one Model.

    """

    def __init__(self, parts: Iterable["_Part"], **kwargs) -> None:
        from compas_fea2.model.parts import _Part
        super().__init__(members=parts, member_class=_Part, **kwargs)

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"parts": [part.__data__ for part in self.parts]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "PartsGroup":
        from compas_fea2.model.parts import _Part

        part_classes = {cls.__name__: cls for cls in _Part.__subclasses__()}
        parts = [part_classes[part_data["class"]].__from_data__(part_data) for part_data in data["parts"]]
        return cls(parts=parts)

    @property
    def model(self) -> "Model":
        return self._registration

    @property
    def parts(self) -> Set["_Part"]:
        return self._members

    def add_part(self, part: "_Part") -> "_Part":
        """
        Add a part to the group.

        Parameters
        ----------
        part : :class:`compas_fea2.model.Part`
            The part to add.

        Returns
        -------
        :class:`compas_fea2.model.Part`
            The part added.
        """
        return self._add_member(part)

    def add_parts(self, parts: Iterable["_Part"]) -> List["_Part"]:
        """
        Add multiple parts to the group.

        Parameters
        ----------
        parts : [:class:`compas_fea2.model.Part`]
            The parts to add.

        Returns
        -------
        [:class:`compas_fea2.model.Part`]
            The parts added.
        """
        return self._add_members(parts)


class SectionsGroup(_Group):
    """Base class for sections groups."""

    def __init__(self, sections: Iterable["_Section"], **kwargs) -> None:
        from compas_fea2.model.sections import _Section
        super().__init__(members=sections, member_class=_Section, **kwargs)

    @property
    def sections(self) -> Set["_Section"]:
        return self._members

    def add_section(self, section: "_Section") -> "_Section":
        return self._add_member(section)

    def add_sections(self, sections: Iterable["_Section"]) -> List["_Section"]:
        return self._add_members(sections)


class MaterialsGroup(_Group):
    """Base class for materials groups."""

    def __init__(self, materials: Iterable["_Material"], **kwargs) -> None:
        from compas_fea2.model.materials.material import _Material
        super().__init__(members=materials, member_class=_Material, **kwargs)

    @property
    def materials(self) -> Set["_Material"]:
        return self._members

    def add_material(self, material: "_Material") -> "_Material":
        return self._add_member(material)

    def add_materials(self, materials: Iterable["_Material"]) -> List["_Material"]:
        return self._add_members(materials)


class InterfacesGroup(_Group):
    """Base class for interfaces groups."""

    def __init__(self, interfaces: Iterable["Interface"], **kwargs) -> None:
        from compas_fea2.model.interfaces import Interface
        super().__init__(members=interfaces, member_class=Interface, **kwargs)

    @property
    def interfaces(self) -> Set["Interface"]:
        return self._members

    def add_interface(self, interface: "Interface") -> "Interface":
        return self._add_member(interface)

    def add_interfaces(self, interfaces: Iterable["Interface"]) -> List["Interface"]:
        return self._add_members(interfaces)


class BCsGroup(_Group):
    """Base class for boundary conditions groups."""

    def __init__(self, bcs: Iterable["_BoundaryCondition"], **kwargs) -> None:
        from compas_fea2.model.bcs import _BoundaryCondition
        super().__init__(members=bcs, member_class=_BoundaryCondition, **kwargs)

    @property
    def bcs(self) -> Set["_BoundaryCondition"]:
        return self._members

    def add_bc(self, bc: "_BoundaryCondition") -> "_BoundaryCondition":
        return self._add_member(bc)

    def add_bcs(self, bcs: Iterable["_BoundaryCondition"]) -> List["_BoundaryCondition"]:
        return self._add_members(bcs)


class ConnectorsGroup(_Group):
    """Base class for connectors groups."""

    def __init__(self, connectors: Iterable["Connector"], **kwargs) -> None:
        from compas_fea2.model.connectors import Connector
        super().__init__(members=connectors, member_class=Connector, **kwargs)

    @property
    def connectors(self) -> Set["Connector"]:
        return self._members

    def add_connector(self, connector: "Connector") -> "Connector":
        return self._add_member(connector)

    def add_connectors(self, connectors: Iterable["Connector"]) -> List["Connector"]:
        return self._add_members(connectors)


class ConstraintsGroup(_Group):
    """Base class for constraints groups."""

    def __init__(self, constraints: Iterable["_Constraint"], **kwargs) -> None:
        from compas_fea2.model.constraints import _Constraint
        super().__init__(members=constraints, member_class=_Constraint, **kwargs)

    @property
    def constraints(self) -> Set["_Constraint"]:
        return self._members

    def add_constraint(self, constraint: "_Constraint") -> "_Constraint":
        return self._add_member(constraint)

    def add_constraints(self, constraints: Iterable["_Constraint"]) -> List["_Constraint"]:
        return self._add_members(constraints)


class ICsGroup(_Group):
    """Base class for initial conditions groups."""

    def __init__(self, ics: Iterable["_InitialCondition"], **kwargs) -> None:
        from compas_fea2.model.ics import _InitialCondition
        super().__init__(members=ics, member_class=_InitialCondition, **kwargs)

    @property
    def ics(self) -> Set["_InitialCondition"]:
        return self._members

    def add_ic(self, ic: "_InitialCondition") -> "_InitialCondition":
        return self._add_member(ic)

    def add_ics(self, ics: Iterable["_InitialCondition"]) -> List["_InitialCondition"]:
        return self._add_members(ics)


class ReleasesGroup(_Group):
    """Base class for releases groups."""

    def __init__(self, releases: Iterable["_BeamEndRelease"], **kwargs) -> None:
        from compas_fea2.model.releases import _BeamEndRelease
        super().__init__(members=releases, member_class=_BeamEndRelease, **kwargs)

    @property
    def releases(self) -> Set["_BeamEndRelease"]:
        return self._members

    def add_release(self, release: "_BeamEndRelease") -> "_BeamEndRelease":
        return self._add_member(release)

    def add_releases(self, releases: Iterable["_BeamEndRelease"]) -> List["_BeamEndRelease"]:
        return self._add_members(releases)
