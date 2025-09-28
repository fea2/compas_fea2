import logging
from importlib import import_module
from itertools import groupby
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generic
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from typing import Set
from typing import TypeVar
from typing import Union
from typing import cast

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.units import units_io

# Type-checking imports to avoid circular dependencies at runtime
if TYPE_CHECKING:
    from compas_fea2.model.bcs import _BoundaryCondition
    from compas_fea2.model.connectors import _Connector
    from compas_fea2.model.constraints import _Constraint
    from compas_fea2.model.elements import Edge
    from compas_fea2.model.elements import Face
    from compas_fea2.model.elements import _Element
    from compas_fea2.model.elements import _Element1D
    from compas_fea2.model.elements import _Element2D
    from compas_fea2.model.elements import _Element3D
    from compas_fea2.model.fields import _ConditionsField
    from compas_fea2.model.ics import _InitialCondition
    from compas_fea2.model.interactions import _Interaction
    from compas_fea2.model.interfaces import _Interface
    from compas_fea2.model.materials.material import _Material
    from compas_fea2.model.model import Model
    from compas_fea2.model.nodes import Node
    from compas_fea2.model.parts import Part
    from compas_fea2.model.parts import RigidPart
    from compas_fea2.model.parts import _Part
    from compas_fea2.model.releases import _BeamEndRelease
    from compas_fea2.model.sections import _Section
    from compas.datastructures import Mesh


# Define a generic type for members of _Group
_MemberType = TypeVar("_MemberType")

# Define a generic type for the _Group class itself, used for __add__, __sub__, etc.
G = TypeVar("G", bound="_Group[Any]")  # G must be a subclass of _Group

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class _Group(FEAData, Generic[_MemberType]):
    """
    Base class for all groups.

    Parameters
    ----------
    member_class : type
        The type that all members of this group must conform to.
    members : Iterable, optional
        An iterable containing members belonging to the group.
        Default is None.

    Attributes
    ----------
    members : Set[_MemberType]
        The set of members belonging to the group.
    members_class : type
        The expected class type for all members in this group.
    part : Any
        Reference to the parent Part, if applicable.
    model : Any
        Reference to the parent Model, if applicable.
    """

    _members: Set[_MemberType]
    _members_class: type
    _part: Any
    _model: Any

    def __init__(self, member_class: type, members: Iterable[_MemberType] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._members_class = member_class
        if members:
            # Type check members if provided
            if any(not isinstance(member, self._members_class) for member in members):
                raise TypeError(f"All members must be of type {self._members_class.__name__}.")
            self._members = set(members)
        else:
            self._members = set()

    @property
    def __data__(self) -> Dict[str, Any]:
        """
        Data representation of the group for serialization.
        """
        data = super().__data__
        data.update(
            {
                "members": [member.__data__ for member in self._members],  # type: ignore
                "member_class": self._members_class.__name__ if self._members_class else None,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional["Registry"] = None, duplicate=True) -> Union["_Group[Any]", "NodesGroup", "ElementsGroup", "EdgesGroup", "FacesGroup"]:
        member_class_name = data.get("member_class")
        members = [registry.add_from_data(member, duplicate=duplicate) for member in data.get("members", [])]  # type: ignore

        # Prefer the actual runtime class of deserialized members (handles plugin-registered classes)
        member_class = None
        if members:
            # infer class from first member instance
            member_class = type(next(iter(members)))
        elif member_class_name:
            # fallback: try to resolve from the core compas_fea2.model module
            try:
                member_class = import_module("compas_fea2.model").__dict__.get(member_class_name)
            except Exception:
                member_class = None

        # If this class expects an explicit member_class argument (base _Group), pass it; otherwise rely on subclass constructors
        if "member_class" in cls.__dict__:
            group = cls(member_class=member_class, members=members)  # type: ignore
        else:
            group = cls(members=members)  # type: ignore (specific group subclasses provide their own member_class)
        return group

    def __len__(self) -> int:
        """Return the number of members in the group."""
        return len(self._members)

    def __contains__(self, item: object) -> bool:
        """Check if an item is in the group."""
        return item in self._members

    def __iter__(self) -> Iterator[_MemberType]:
        """Return an iterator over the members."""
        return iter(self._members)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {len(self._members)} members>"

    def __add__(self: G, other: G) -> G:
        if type(self) is _Group:
            raise TypeError("Cannot add base _Group, use a specific group type.")
        if not isinstance(other, type(self)):
            raise TypeError("Can only add same group types together.")
        return self.__class__(members=self._members | other._members)  # type: ignore

    def __sub__(self: G, other: G) -> G:
        if not isinstance(other, type(self)):
            raise TypeError("Can only subtract same group types from each other.")
        return self.__class__(members=self._members - other._members)  # type: ignore

    def __getitem__(self, key: int) -> _MemberType:
        """
        Get a member by index.

        Parameters
        ----------
        key : int
            The index of the member to retrieve.

        Returns
        -------
        _MemberType
            The member at the specified index or with the specified key.
        """
        return list(self._members)[key]  # type: ignore

    def to_list(self) -> List[_MemberType]:
        """Return the members of the group as a list."""
        return list(self._members)

    @property
    def part(self) -> Union["_Part", "Part", "RigidPart", None]:
        if isinstance(self._registration, _Part):
            return self._part

    @property
    def model(self) -> Union["Model", None]:
        if isinstance(self._registration, Model):
            return self._model

    @property
    def members(self) -> Set[_MemberType]:
        """Return the members of the group."""
        return self._members

    @property
    def sorted(self) -> List[_MemberType]:
        """
        Return the members of the group sorted in ascending order based on their key.

        Returns
        -------
        List[_MemberType]
            A sorted list of group members.
        """

        return sorted(self._members, key=lambda x: getattr(x, "key", 0))

    def sorted_by(self, key: Callable[[_MemberType], Union[str, int, float]], reverse: bool = False) -> List[_MemberType]:
        """
        Return the members of the group sorted based on a custom key function.

        Parameters
        ----------
        key : Callable[[_MemberType], object]
            A function that extracts a key from a member for sorting.
        reverse : bool, optional
            Whether to sort in descending order. Default is False.

        Returns
        -------
        List[_MemberType]
            A sorted list of group members based on the key function.
        """
        return sorted(self._members, key=key, reverse=reverse)

    def subgroup(self: G, condition: Callable[[_MemberType], bool], **kwargs) -> G:
        """
        Create a subgroup based on a given condition.

        Parameters
        ----------
        condition : Callable[[_MemberType], bool]
            A function that takes a member as input and returns True if the member
            should be included in the subgroup.

        Returns
        -------
        G
            A new group (of the same type as self) containing the members that satisfy the condition.
        """
        filtered_members = set(filter(condition, self._members))
        return self.__class__(members=filtered_members, **kwargs)

    def group_by(self: G, key: Callable[[_MemberType], Any]) -> Dict[Any, G]:
        """
        Group members into multiple subgroups based on a key function.

        Parameters
        ----------
        key : Callable[[_MemberType], Any]
            A function that extracts a key from a member for grouping.

        Returns
        -------
        Dict[Any, G]
            A dictionary where keys are the grouping values and values are group instances of the same type as self.
        """
        if type(self) is _Group:
            raise TypeError("Cannot group base _Group, use a specific group type.")
        try:
            sorted_members = sorted(self._members, key=key)
        except TypeError:
            sorted_members = self._members
        grouped_members = {k: set(v) for k, v in groupby(sorted_members, key=key)}
        return {k: self.__class__(members=v, name=getattr(self, "name", None)) for k, v in grouped_members.items()}  # type: ignore

    def union(self: G, other: G) -> G:  # Changed other: "_Group[Any]" to other: G
        """
        Create a new group containing all members from this group and another group.

        Parameters
        ----------
        other : G
            Another group whose members should be combined with this group. Must be of the same group type.

        Returns
        -------
        G
            A new group containing all members from both groups.
        """
        if type(self) is _Group:
            raise TypeError("Cannot perform union on base _Group, use a specific group type.")
        if not isinstance(other, type(self)):  # Added type check
            raise TypeError("Can only perform union with the same group type.")
        return self.__class__(members=self._members | other._members)  # type: ignore

    def intersection(self: G, other: G) -> G:  # Changed other: "_Group[Any]" to other: G
        """
        Create a new group containing only members that are present in both groups.

        Parameters
        ----------
        other : G
            Another group to find common members with. Must be of the same group type.

        Returns
        -------
        G
            A new group containing only members found in both groups.
        """
        if type(self) is _Group:
            raise TypeError("Cannot perform intersection on base _Group, use a specific group type.")
        if not isinstance(other, type(self)):  # Added type check
            raise TypeError("Can only perform intersection with the same group type.")
        return self.__class__(members=self._members & other._members)  # type: ignore

    def difference(self: G, other: G) -> G:  # Changed other: "_Group[Any]" to other: G
        """
        Create a new group containing members that are in this group but not in another.

        Parameters
        ----------
        other : G
            Another group whose members should be removed from this group. Must be of the same group type.

        Returns
        -------
        G
            A new group containing members unique to this group.
        """
        if type(self) is _Group:
            raise TypeError("Cannot perform difference on base _Group, use a specific group type.")
        if not isinstance(other, type(self)):  # Added type check
            raise TypeError("Can only perform difference with the same group type.")
        return self.__class__(members=self._members - other._members)  # type: ignore

    def unique(self: G, key: Callable[[_MemberType], Any] | None = None) -> G:
        """
        Return a new group containing only unique members.

        If a key function is provided, uniqueness is determined by key(member), otherwise by member identity.
        """
        if key is None:
            unique_members = set(self._members)
        else:
            seen = set()
            unique_list: List[_MemberType] = []
            for member in self._members:
                k = key(member)
                if k not in seen:
                    seen.add(k)
                    unique_list.append(member)
            unique_members = unique_list
        return self.__class__(member_class=self._members_class, members=unique_members)

    def add_member(self, member: _MemberType) -> _MemberType:
        """Add a single member to the group."""
        if self._members_class and not isinstance(member, self._members_class):
            raise TypeError(f"Member must be of type {self._members_class.__name__}.")
        self._members.add(member)
        return member

    def add_members(self, members: Iterable[_MemberType]) -> List[_MemberType]:
        """Add multiple members to the group."""
        added = []
        for member in members:
            added.append(self.add_member(member))
        return added

    def remove_member(self, member: object) -> bool:
        """
        Remove a member from the group.

        Parameters
        ----------
        member : _MemberType
            The member to remove.

        Returns
        -------
        bool
            True if the member was removed, False if not found.
        """
        if member in self._members:
            self._members.remove(cast(_MemberType, member))
            return True
        logger.warning(f"Member {member} not found in the group.")
        return False

    def remove_members(self, members: Iterable[_MemberType]) -> List[_MemberType]:
        """
        Remove multiple members from the group.

        Parameters
        ----------
        members : Iterable[_MemberType]
            The members to remove.

        Returns
        -------
        List[_MemberType]
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

    def clear(self) -> None:
        """Clear all members from the group."""
        self._members.clear()


class NodesGroup(_Group["Node"]):
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

    def __init__(self, members: Iterable["Node"] | "Node", **kwargs) -> None:
        from compas_fea2.model.nodes import Node

        if isinstance(members, Node):
            members = [members]
        super().__init__(members=members, member_class=Node, **kwargs)

    @property
    def nodes(self) -> Set["Node"]:
        return self._members

    @property
    def gkey_node(self) -> Dict[str, "Node"]:
        """Return a dictionary mapping gkeys to nodes."""
        gkey_node_map = {}
        for node in self.nodes:
            if node.gkey is not None:
                gkey_node_map[node.gkey] = node
            else:
                # Handle case where node.gkey is None
                logger.warning(f"Node {node} has no gkey, skipping in gkey_node_map.")
        return gkey_node_map


class ElementsGroup(_Group[Union["_Element", "_Element1D", "_Element2D", "_Element3D"]]):
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

    def __init__(self, members: Iterable["_Element"], **kwargs) -> None:
        from compas_fea2.model.elements import _Element

        super().__init__(members=members, member_class=_Element, **kwargs)

    @property
    def elements(self) -> Set[Union["_Element", "_Element1D", "_Element2D", "_Element3D"]]:
        return self._members


class EdgesGroup(_Group["Edge"]):
    """Base class elements edges groups."""

    def __init__(self, members: Iterable["Edge"], **kwargs) -> None:
        from compas_fea2.model.elements import Edge

        super().__init__(members=members, member_class=Edge, **kwargs)

    @property
    def edges(self) -> Set["Edge"]:
        return self._members

    @property
    def nodes(self) -> Set["Node"]:
        nodes_set: Set["Node"] = set()
        for edge in self.edges:
            for node in edge.nodes:
                nodes_set.add(node)
        return nodes_set


class FacesGroup(_Group["Face"]):
    """Base class elements faces groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.Face`]
        The faces belonging to the group.

    Attributes
    ----------
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    faces : Set[:class:`compas_fea2.model.Face`]
        The faces belonging to the group.
    nodes : Set[:class:`compas_fea2.model.Node`]
        The nodes belonging to the faces in the group.
    area : float
        The total area of the faces in the group.
    normal : List[float]
        The average normal vector of the faces in the group.
    """

    def __init__(self, members: Iterable["Face"], **kwargs) -> None:
        from compas_fea2.model.elements import Face

        super().__init__(members=members, member_class=Face, **kwargs)

    @property
    def part(self) -> "_Part | None":
        return self._registration

    @property
    def model(self) -> "Model | None":
        if not self.part:
            return None
        return self.part._registration

    @property
    def faces(self) -> Set["Face"]:
        return self._members

    @property
    def nodes(self) -> Set["Node"]:
        nodes_set: Set["Node"] = set()
        for face in self.faces:
            for node in face.nodes:
                nodes_set.add(node)
        return nodes_set

    @property
    @units_io(types_in=(), types_out="area")
    def area(self) -> float:
        """Total area of the faces in the group (active unit system)."""
        return sum(face.area for face in self.faces)

    @property
    def normal(self) -> List[float]:
        """Average normal of the faces in the group (dimensionless unit vector)."""
        from compas.geometry import normalize_vector

        normals = [face.normal for face in self.faces]
        if normals:
            avg_normal = [sum(components) / len(normals) for components in zip(*normals)]
            return normalize_vector(avg_normal)
        raise AttributeError("Could not calculate the average normal vector, no faces in the group.")

    @property
    @units_io(types_in=(), types_out=("length", "length", "length"))
    def centroid(self) -> List[float]:
        """Centroid of the faces in the group (x, y, z) in the active length unit."""
        from compas.geometry import centroid_points

        all_face_centroids = [face.centroid for face in self.faces]
        if all_face_centroids:
            return centroid_points(all_face_centroids)
        raise AttributeError("Could not calculate the centroid, no faces in the group.")

    @property
    def mesh(self) -> "Mesh":
        """Return a COMPAS mesh representing the faces in the group."""
        from compas.datastructures import Mesh
        from compas_fea2.model.elements import Face

        vertices = []
        faces = []
        vertex_index = {}
        index = 0

        for face in self.faces:
            if not isinstance(face, Face):
                raise TypeError("All members must be of type Face to create a mesh.")
            face_vertex_indices = []
            for node in face.nodes:
                if node.key not in vertex_index:
                    vertex_index[node.key] = index
                    vertices.append(node.xyz)
                    index += 1
                face_vertex_indices.append(vertex_index[node.key])
            faces.append(face_vertex_indices)

        return Mesh.from_vertices_and_faces(vertices, faces)

    @property
    def boundary(self):
        from compas.geometry import Polygon

        pts = []
        vertices = []
        for e in self.mesh.edges_on_boundary():
            for v in e:
                if v not in vertices:
                    vertices.append(v)
                    pts.append(self.mesh.vertex_coordinates(v))

        return Polygon(pts)


class PartsGroup(_Group["_Part"]):
    """Base class for parts groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.Part`]
        The parts belonging to the group.

    Attributes
    ----------
    parts : Set[:class:`compas_fea2.model.Part`]
        The parts belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_Part"], **kwargs) -> None:
        from compas_fea2.model.parts import _Part

        super().__init__(members=members, member_class=_Part, **kwargs)

    @property
    def parts(self) -> Set["_Part"]:
        return self._members


class SectionsGroup(_Group["_Section"]):
    """Base class for sections groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.Section`]
        The sections belonging to the group.

    Attributes
    ----------
    sections : Set[:class:`compas_fea2.model.Section`]
        The sections belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_Section"], **kwargs) -> None:
        from compas_fea2.model.sections import _Section

        super().__init__(members=members, member_class=_Section, **kwargs)

    @property
    def sections(self) -> Set["_Section"]:
        return self._members


class MaterialsGroup(_Group["_Material"]):
    """Base class for materials groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.Material`]
        The materials belonging to the group.

    Attributes
    ----------
    materials : Set[:class:`compas_fea2.model.Material`]
        The materials belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_Material"], **kwargs) -> None:
        from compas_fea2.model.materials.material import _Material

        super().__init__(members=members, member_class=_Material, **kwargs)

    @property
    def materials(self) -> Set["_Material"]:
        return self._members


class InterfacesGroup(_Group["_Interface"]):
    """Base class for interfaces groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.Interface`]
        The interfaces belonging to the group.

    Attributes
    ----------
    interfaces : Set[:class:`compas_fea2.model.Interface`]
        The interfaces belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_Interface"], **kwargs) -> None:
        from compas_fea2.model.interfaces import _Interface

        super().__init__(members=members, member_class=_Interface, **kwargs)

    @property
    def interfaces(self) -> Set["_Interface"]:
        return self._members


class InteractionsGroup(_Group["_Interaction"]):
    """Base class for interactions groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.Interaction`]
        The interactions belonging to the group.

    Attributes
    ----------
    interactions : Set[:class:`compas_fea2.model.Interaction`]
        The interactions belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_Interaction"], **kwargs) -> None:
        from compas_fea2.model.interactions import _Interaction

        super().__init__(members=members, member_class=_Interaction, **kwargs)

    @property
    def interactions(self) -> Set["_Interaction"]:
        return self._members


class BCsGroup(_Group["_BoundaryCondition"]):
    """Base class for boundary conditions groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.BoundaryCondition`]
        The boundary conditions belonging to the group.

    Attributes
    ----------
    bcs : Set[:class:`compas_fea2.model.BoundaryCondition`]
        The boundary conditions belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_BoundaryCondition"], **kwargs) -> None:
        from compas_fea2.model.bcs import _BoundaryCondition

        super().__init__(members=members, member_class=_BoundaryCondition, **kwargs)

    @property
    def bcs(self) -> Set["_BoundaryCondition"]:
        return self._members


class ConnectorsGroup(_Group["_Connector"]):
    """Base class for connectors groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.Connector`]
        The connectors belonging to the group.

    Attributes
    ----------
    connectors : Set[:class:`compas_fea2.model.Connector`]
        The connectors belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_Connector"], **kwargs) -> None:
        from compas_fea2.model.connectors import _Connector

        super().__init__(members=members, member_class=_Connector, **kwargs)

    @property
    def connectors(self) -> Set["_Connector"]:
        return self._members


class ConstraintsGroup(_Group["_Constraint"]):
    """Base class for constraints groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.Constraint`]
        The constraints belonging to the group.

    Attributes
    ----------
    constraints : Set[:class:`compas_fea2.model.Constraint`]
        The constraints belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_Constraint"], **kwargs) -> None:
        from compas_fea2.model.constraints import _Constraint

        super().__init__(members=members, member_class=_Constraint, **kwargs)

    @property
    def constraints(self) -> Set["_Constraint"]:
        return self._members


class ICsGroup(_Group["_InitialCondition"]):
    """Base class for initial conditions groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.InitialCondition`]
        The initial conditions belonging to the group.

    Attributes
    ----------
    ics : Set[:class:`compas_fea2.model.InitialCondition`]
        The initial conditions belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_InitialCondition"], **kwargs) -> None:
        from compas_fea2.model.ics import _InitialCondition

        super().__init__(members=members, member_class=_InitialCondition, **kwargs)

    @property
    def ics(self) -> Set["_InitialCondition"]:
        return self._members


class ReleasesGroup(_Group["_BeamEndRelease"]):
    """Base class for releases groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.BeamEndRelease`]
        The beam end releases belonging to the group.

    Attributes
    ----------
    releases : Set[:class:`compas_fea2.model.BeamEndRelease`]
        The beam end releases belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_BeamEndRelease"], **kwargs) -> None:
        from compas_fea2.model.releases import _BeamEndRelease

        super().__init__(members=members, member_class=_BeamEndRelease, **kwargs)

    @property
    def releases(self) -> Set["_BeamEndRelease"]:
        return self._members


class FieldsGroup(_Group["_ConditionsField"]):
    """Base class for fields groups.

    Parameters
    ----------
    members : Iterable[:class:`compas_fea2.model.ConditionsField`]
        The fields belonging to the group.

    Attributes
    ----------
    fields : Set[:class:`compas_fea2.model.ConditionsField`]
        The fields belonging to the group.
    model : :class:`compas_fea2.model.Model`
        The model where the group is registered, by default `None`.
    part : :class:`compas_fea2.model._Part`
        The part where the group is registered, by default `None`.
    """

    def __init__(self, members: Iterable["_ConditionsField"], **kwargs) -> None:
        from compas_fea2.model.fields import _ConditionsField

        super().__init__(members=members, member_class=_ConditionsField, **kwargs)

    @property
    def fields(self) -> Set["_ConditionsField"]:
        return self._members
