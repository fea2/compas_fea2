import logging
from importlib import import_module
from itertools import groupby
from typing import Any, Callable, Dict, Iterable, Iterator, List, Set, TypeVar, Union, Generic, cast
from typing import TYPE_CHECKING


from compas_fea2.base import FEAData

# Type-checking imports to avoid circular dependencies at runtime
if TYPE_CHECKING:
    from compas_fea2.model.parts import _Part
    from compas_fea2.model.sections import _Section
    from compas_fea2.model.materials.material import _Material
    from compas_fea2.model.interfaces import _Interface
    from compas_fea2.model.bcs import _BoundaryCondition
    from compas_fea2.model.connectors import _Connector
    from compas_fea2.model.model import Model
    from compas_fea2.model.nodes import Node
    from compas_fea2.model.elements import _Element
    from compas_fea2.model.elements import Edge
    from compas_fea2.model.elements import Face
    from compas_fea2.model.releases import _BeamEndRelease
    from compas_fea2.model.constraints import _Constraint
    from compas_fea2.model.interactions import _Interaction
    from compas_fea2.model.ics import _InitialCondition


# Define a generic type for members of _Group
_MemberType = TypeVar("_MemberType")

# Define a generic type for the _Group class itself, used for __add__, __sub__, etc.
G = TypeVar("G", bound="_Group[Any]") # G must be a subclass of _Group

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

        self._part = None
        self._model = None

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
        return self.__class__(members=self._members | other._members) #type: ignore

    def __sub__(self:G, other: G) -> G:
        if not isinstance(other, type(self)):
            raise TypeError("Can only subtract same group types from each other.")
        return self.__class__(members=self._members - other._members) #type: ignore

    def to_list(self) -> List[_MemberType]:
        """Return the members of the group as a list."""
        return list(self._members)

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
        return sorted(self._members, key=lambda x: getattr(x, "key", str(x)))

    def sorted_by(self, key: Callable[[_MemberType], object], reverse: bool = False) -> List[_MemberType]:
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
        sorted_members = sorted(self._members, key=key)
        grouped_members = {k: set(v) for k, v in groupby(sorted_members, key=key)}
        return {k: self.__class__(members=v, name=getattr(self, 'name', None)) for k, v in grouped_members.items()}  #type: ignore

    def union(self: G, other: G) -> G: # Changed other: "_Group[Any]" to other: G
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
        if not isinstance(other, type(self)): # Added type check
            raise TypeError("Can only perform union with the same group type.")
        return self.__class__(members=self._members | other._members)  #type: ignore

    def intersection(self: G, other: G) -> G: # Changed other: "_Group[Any]" to other: G
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
        if not isinstance(other, type(self)): # Added type check
            raise TypeError("Can only perform intersection with the same group type.")
        return self.__class__(members=self._members & other._members)  #type: ignore

    def difference(self: G, other: G) -> G: # Changed other: "_Group[Any]" to other: G
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
        if not isinstance(other, type(self)): # Added type check
            raise TypeError("Can only perform difference with the same group type.")
        return self.__class__(members=self._members - other._members)  #type: ignore

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
        if self._members_class and not isinstance(member, self._members_class):
            raise TypeError(f"Member must be of type {self._members_class.__name__}.")
        self._members.add(member)
        return member

    def add_members(self, members: Iterable[_MemberType]) -> List[_MemberType]:
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

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the group to a dictionary.

        Returns
        -------
        Dict[str, Any]
            A dictionary representation of the group.
        """
        # This serialization is generic, but subclasses will override to handle complex members
        return {"members": list(self._members)}

    @property
    def __data__(self) -> Dict[str, Any]:
        """
        Data representation of the group for serialization.
        """
        members_data = []
        for member in self._members:
            if hasattr(member, "__data__"):
                members_data.append(member.__data__)
            else:
                members_data.append(member)
        return {"members": members_data}

    @classmethod
    def deserialize(cls: type[G], data: Dict[str, Any]) -> G:
        """
        Deserialize a dictionary to create a `_Group` instance.
        Note: This base deserialize is very basic and will likely be overridden
        by subclasses to properly handle complex member types.

        Parameters
        ----------
        data : Dict[str, Any]
            A dictionary representation of the group.

        Returns
        -------
        G
            A `_Group` instance with the deserialized members.
        """
        # This assumes members are directly deserializable, which might not be true for complex types
        # Subclasses should override this.
        raise NotImplementedError("Subclasses should implement their own deserialize method.")


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

    def __init__(self, members: Iterable["Node"], **kwargs) -> None:
        from compas_fea2.model.nodes import Node
        super().__init__(members=members, member_class=Node, **kwargs)

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [node.__data__ for node in self.nodes]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "NodesGroup":
        from compas_fea2.model.nodes import Node
        nodes = [Node.__from_data__(node_data) for node_data in data["members"]]
        return cls(members=nodes)

    @property
    def part(self) -> Any:
        return self._part

    @property
    def model(self) -> Any:
        return self._model

    @property
    def nodes(self) -> Set["Node"]:
        return self._members


class ElementsGroup(_Group["_Element"]):
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
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [element.__data__ for element in self.elements]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "ElementsGroup":
        elements_module = import_module("compas_fea2.model.elements")
        elements = [getattr(elements_module, element_data["class"]).__from_data__(element_data) for element_data in data["members"]]
        return cls(members=elements)

    @property
    def part(self) -> Any:
        return self._registration

    @property
    def model(self) -> Any:
        return self.part._registration

    @property
    def elements(self) -> Set["_Element"]:
        return self._members


class EdgesGroup(_Group["Edge"]):
    """Base class elements edges groups."""

    def __init__(self, members: Iterable["Edge"], **kwargs) -> None:
        from compas_fea2.model.elements import Edge
        super().__init__(members=members, member_class=Edge, **kwargs)

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [edge.__data__ for edge in self.edges]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "EdgesGroup":
        from compas_fea2.model.elements import Edge
        edges = [Edge.__from_data__(edge_data) for edge_data in data["members"]]
        obj = cls(members=edges)
        return obj

    @property
    def model(self) -> "Model | None":
        return self._registration

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
    """Base class elements faces groups."""

    def __init__(self, members: Iterable["Face"], **kwargs) -> None:
        from compas_fea2.model.elements import Face
        super().__init__(members=members, member_class=Face, **kwargs)

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [face.__data__ for face in self.faces]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "FacesGroup":
        from compas_fea2.model.elements import Face
        faces = [Face.__from_data__(face_data) for face_data in data["members"]]
        obj = cls(members=faces)
        return obj

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


class PartsGroup(_Group["_Part"]):
    """Base class for parts groups."""

    def __init__(self, members: Iterable["_Part"], **kwargs) -> None:
        from compas_fea2.model.parts import _Part
        super().__init__(members=members, member_class=_Part, **kwargs)

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [part.__data__ for part in self.parts]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "PartsGroup":
        from compas_fea2.model.parts import _Part

        part_classes = {subcls.__name__: subcls for subcls in _Part.__subclasses__() + [_Part]} # Include _Part itself if it can be instantiated
        parts = [part_classes[part_data["class"]].__from_data__(part_data) for part_data in data["members"]]
        return cls(members=parts)

    @property
    def model(self) -> "Model | None":
        return self._registration

    @property
    def parts(self) -> Set["_Part"]:
        return self._members


class SectionsGroup(_Group["_Section"]): 
    """Base class for sections groups."""

    def __init__(self, members: Iterable["_Section"], **kwargs) -> None:
        from compas_fea2.model.sections import _Section
        super().__init__(members=members, member_class=_Section, **kwargs)

    @property
    def sections(self) -> Set["_Section"]:
        return self._members
    
    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [section.__data__ for section in self.sections]})
        return data
    
    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "SectionsGroup":
        from compas_fea2.model.sections import _Section

        section_classes = {subcls.__name__: subcls for subcls in _Section.__subclasses__() + [_Section]} # Include _Section itself if it can be instantiated
        sections = [section_classes[section_data["class"]].__from_data__(section_data) for section_data in data["members"]]
        return cls(members=sections)
    


class MaterialsGroup(_Group["_Material"]):
    """Base class for materials groups."""

    def __init__(self, members: Iterable["_Material"], **kwargs) -> None:
        from compas_fea2.model.materials.material import _Material
        super().__init__(members=members, member_class=_Material, **kwargs)

    @property
    def materials(self) -> Set["_Material"]:
        return self._members

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [mat.__data__ for mat in self.materials]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "MaterialsGroup":
        from compas_fea2.model.materials.material import _Material
        mats = [_Material.__from_data__(md) for md in data["members"]]
        return cls(members=mats)


class InterfacesGroup(_Group["_Interface"]):
    """Base class for interfaces groups."""

    def __init__(self, members: Iterable["_Interface"], **kwargs) -> None:
        from compas_fea2.model.interfaces import _Interface
        super().__init__(members=members, member_class=_Interface, **kwargs)

    @property
    def interfaces(self) -> Set["_Interface"]:
        return self._members

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [iface.__data__ for iface in self.interfaces]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "InterfacesGroup":
        from compas_fea2.model.interfaces import _Interface
        ifaces = [_Interface.__from_data__(dd) for dd in data["members"]]
        return cls(members=ifaces)

class InteractionsGroup(_Group["_Interaction"]):
    """Base class for interactions groups."""

    def __init__(self, members: Iterable["_Interaction"], **kwargs) -> None:
        from compas_fea2.model.interactions import _Interaction
        super().__init__(members=members, member_class=_Interaction, **kwargs)

    @property
    def interactions(self) -> Set["_Interaction"]:
        return self._members

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [interaction.__data__ for interaction in self.interactions]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "InteractionsGroup":
        from compas_fea2.model.interactions import _Interaction
        interactions = [_Interaction.__from_data__(dd) for dd in data["members"]]
        return cls(members=interactions)

class BCsGroup(_Group["_BoundaryCondition"]):
    """Base class for boundary conditions groups."""

    def __init__(self, members: Iterable["_BoundaryCondition"], **kwargs) -> None:
        from compas_fea2.model.bcs import _BoundaryCondition
        super().__init__(members=members, member_class=_BoundaryCondition, **kwargs)

    @property
    def bcs(self) -> Set["_BoundaryCondition"]:
        return self._members

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [bc.__data__ for bc in self.bcs]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "BCsGroup":
        from compas_fea2.model.bcs import _BoundaryCondition
        bcs = [_BoundaryCondition.__from_data__(bd) for bd in data["members"]]
        return cls(members=bcs)


class ConnectorsGroup(_Group["_Connector"]):
    """Base class for connectors groups."""

    def __init__(self, members: Iterable["_Connector"], **kwargs) -> None:
        from compas_fea2.model.connectors import _Connector
        super().__init__(members=members, member_class=_Connector, **kwargs)

    @property
    def connectors(self) -> Set["_Connector"]:
        return self._members

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [conn.__data__ for conn in self.connectors]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "ConnectorsGroup":
        from compas_fea2.model.connectors import _Connector
        conns = [_Connector.__from_data__(d) for d in data["members"]]
        return cls(members=conns)


class ConstraintsGroup(_Group["_Constraint"]):
    """Base class for constraints groups."""

    def __init__(self, members: Iterable["_Constraint"], **kwargs) -> None:
        from compas_fea2.model.constraints import _Constraint
        super().__init__(members=members, member_class=_Constraint, **kwargs)

    @property
    def constraints(self) -> Set["_Constraint"]:
        return self._members

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [c.__data__ for c in self.constraints]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "ConstraintsGroup":
        from compas_fea2.model.constraints import _Constraint
        cons = [_Constraint.__from_data__(dd) for dd in data["members"]]
        return cls(members=cons)


class ICsGroup(_Group["_InitialCondition"]):
    """Base class for initial conditions groups."""

    def __init__(self, members: Iterable["_InitialCondition"], **kwargs) -> None:
        from compas_fea2.model.ics import _InitialCondition
        super().__init__(members=members, member_class=_InitialCondition, **kwargs)

    @property
    def ics(self) -> Set["_InitialCondition"]:
        return self._members

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [ic.__data__ for ic in self.ics]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "ICsGroup":
        from compas_fea2.model.ics import _InitialCondition
        ics = [_InitialCondition.__from_data__(dd) for dd in data["members"]]
        return cls(members=ics)


class ReleasesGroup(_Group["_BeamEndRelease"]):
    """Base class for releases groups."""

    def __init__(self, members: Iterable["_BeamEndRelease"], **kwargs) -> None:
        from compas_fea2.model.releases import _BeamEndRelease
        super().__init__(members=members, member_class=_BeamEndRelease, **kwargs)

    @property
    def releases(self) -> Set["_BeamEndRelease"]:
        return self._members

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"members": [r.__data__ for r in self.releases]})
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]) -> "ReleasesGroup":
        from compas_fea2.model.releases import _BeamEndRelease
        rels = [_BeamEndRelease.__from_data__(dd) for dd in data["members"]]
        return cls(members=rels)