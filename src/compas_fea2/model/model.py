from __future__ import annotations

import importlib
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from compas.datastructures import Graph
from compas.geometry import Box
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Transformation
from compas.geometry import bounding_box
from compas.geometry import centroid_points
from compas.geometry import centroid_points_weighted

import compas_fea2
from compas_fea2.config import settings
from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.model.bcs import _BoundaryCondition
from compas_fea2.model.connectors import _Connector
from compas_fea2.model.constraints import _Constraint
from compas_fea2.model.elements import _Element
from compas_fea2.model.fields import BoundaryConditionsField
from compas_fea2.model.fields import InitialTemperatureField
from compas_fea2.model.fields import _InitialConditionField
from compas_fea2.model.groups import ConnectorsGroup
from compas_fea2.model.groups import ConstraintsGroup
from compas_fea2.model.groups import ElementsGroup
from compas_fea2.model.groups import FieldsGroup
from compas_fea2.model.groups import InteractionsGroup
from compas_fea2.model.groups import InterfacesGroup
from compas_fea2.model.groups import MaterialsGroup
from compas_fea2.model.groups import NodesGroup
from compas_fea2.model.groups import PartsGroup
from compas_fea2.model.groups import SectionsGroup
from compas_fea2.model.groups import _Group
from compas_fea2.model.ics import InitialTemperature
from compas_fea2.model.ics import _InitialCondition
from compas_fea2.model.interactions import _Interaction
from compas_fea2.model.nodes import Node
from compas_fea2.model.parts import Part
from compas_fea2.model.parts import RigidPart
from compas_fea2.model.parts import _Part
from compas_fea2.utilities._devtools import get_docstring
from compas_fea2.utilities._devtools import part_method

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Union

    from compas.geometry import Frame
    from compas.geometry import Polygon

    from compas_fea2.model.bcs import _BoundaryCondition
    from compas_fea2.model.connectors import _Connector
    from compas_fea2.model.constraints import _Constraint
    from compas_fea2.model.fields import BoundaryConditionsField
    from compas_fea2.model.fields import _InitialConditionField
    from compas_fea2.model.groups import ConnectorsGroup
    from compas_fea2.model.groups import ConstraintsGroup
    from compas_fea2.model.groups import ElementsGroup
    from compas_fea2.model.groups import FieldsGroup
    from compas_fea2.model.groups import InteractionsGroup
    from compas_fea2.model.groups import InterfacesGroup
    from compas_fea2.model.groups import MaterialsGroup
    from compas_fea2.model.groups import SectionsGroup
    from compas_fea2.model.ics import InitialTemperature
    from compas_fea2.model.interactions import _Interaction
    from compas_fea2.model.interfaces import _Interface
    from compas_fea2.model.materials.material import _Material
    from compas_fea2.model.sections import _Section
    from compas_fea2.problem import Problem
    from compas_fea2.units import UnitRegistry


class Model(FEAData):
    """Class representing an FEA model.

    Parameters
    ----------
    description : str, optional
        Some description of the model, by default ``None``.
        This will be added to the input file and can be useful for future reference.
    author : str, optional
        The name of the author of the model, by default ``None``.
        This will be added to the input file and can be useful for future reference.

    Attributes
    ----------
    description : str
        Some description of the model.
    author : str
        The name of the author of the model.
    parts : Set[:class:`compas_fea2.model.Part`]
        The parts of the model.
    bcs : Dict[:class:`compas_fea2.model._BoundaryCondition`, Set[:class:`compas_fea2.model.Node`]]
        Dictionary with the boundary conditions of the model and the nodes where
        these are applied.
    tbcs : Dict[:class:`compas_fea2.model._ThermalBoundaryCondition`, Set[:class:`compas_fea2.model.Node`]]
        Dictionary with the thermal boundary conditions of the model and the nodes where
        these are applied.
    ics : Dict[:class:`compas_fea2.model._InitialCondition`, Set[Union[:class:`compas_fea2.model.Node`, :class:`compas_fea2.model._Element`]]]
        Dictionary with the initial conditions of the model and the nodes/elements
        where these are applied.
    constraints : Set[:class:`compas_fea2.model._Constraint`]
        The constraints of the model.
    partgroups : Set[:class:`compas_fea2.model.PartsGroup`]
        The part groups of the model.
    materials : Set[:class:`compas_fea2.model.Material`]
        The materials assigned in the model.
    sections : Set[:class:`compas_fea2.model.Section`]
        The sections assigned in the model.
    problems : Set[:class:`compas_fea2.problem.Problem`]
        The problems added to the model.
    path : :class:`pathlib.Path`
        Path to the main folder where the problems' results are stored.

    """

    def __init__(self, description: "Optional[str]" = None, author: "Optional[str]" = None, **kwargs):
        super().__init__(**kwargs)
        self.description = description
        self.author = author
        self._key = 0
        self._starting_key = 0

        self._units: "Optional[UnitRegistry]" = None
        self._constants: dict = {"g": None}

        self._path: "Optional[Path]" = None

        self._graph = Graph()

        self._parts: "PartsGroup" = PartsGroup(members=[], name="ALL_PARTS")
        self._interfaces: "InterfacesGroup" = InterfacesGroup(members=[], name="ALL_INTERFACES")
        self._interactions: "InteractionsGroup" = InteractionsGroup(members=[], name="ALL_INTERACTIONS")
        self._connectors: "ConnectorsGroup" = ConnectorsGroup(members=[], name="ALL_CONNECTORS")
        self._constraints: "ConstraintsGroup" = ConstraintsGroup(members=[], name="ALL_CONSTRAINTS")
        self._fields: "FieldsGroup" = FieldsGroup(members=[], name="ALL_FIELDS")
        self._groups: "Set[_Group]" = set([self._parts, self._interfaces, self._interactions, self._connectors, self._constraints, self._fields])

        self._problems: "Set[Problem]" = set()

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "description": self.description,
                "author": self.author,
                "constants": self._constants,
                "parts": [part.__data__ for part in self._parts],
                "interfaces": [interface.__data__ for interface in self._interfaces],
                "interactions": [interaction.__data__ for interaction in self._interactions],
                "constraints": [constraint.__data__ for constraint in self._constraints],
                "fields": [field.__data__ for field in self._fields],
                "connectors": [connector.__data__ for connector in self._connectors],
                "problems": [problem.__data__ for problem in self._problems],
                "path": self.path if self._path else None,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        if registry is None:
            raise ValueError("Registry is required to create a Model from data.")

        model = cls(description=data.get("description"), author=data.get("author"))
        model._path = Path(data.get("path")) if data.get("path") else None
        model._constants = data.get("constants", {})

        for part_data in data.get("parts", []):
            model.add_part(registry.add_from_data(part_data, duplicate=duplicate))

        for interface_data in data.get("interfaces", []):
            model.interfaces.add_member(registry.add_from_data(interface_data, duplicate=duplicate))

        for interaction_data in data.get("interactions", []):
            model.interactions.add_member(registry.add_from_data(interaction_data, duplicate=duplicate))

        for constraint_data in data.get("constraints", []):
            model.constraints.add_member(registry.add_from_data(constraint_data, duplicate=duplicate))

        for connector_data in data.get("connectors", []):
            model.connectors.add_member(registry.add_from_data(connector_data, duplicate=duplicate))

        for problem_data in data.get("problems", []):
            model.add_problem(registry.add_from_data(problem_data, duplicate=duplicate))

        for field_data in data.get("fields", []):
            model.fields.add_member(registry.add_from_data(field_data, duplicate=duplicate))

        return model

    # =========================================================================
    #                       Constructors
    # =========================================================================
    @classmethod
    def from_template(cls, template):
        """Create a Model instance from a template.

        Parameters
        ----------
        template : str
            The path to the template file.

        Returns
        -------
        Model
            The created Model instance.
        Notes
        -----
        This method is not implemented yet.
        """
        raise NotImplementedError("The from_template method is not implemented yet.")

    # =========================================================================
    #                       Attributes
    # =========================================================================
    @property
    def parts(self) -> "PartsGroup":
        """Return all the parts registered to the Model."""
        return self._parts

    @property
    def graph(self) -> "Graph":
        """Return the graph of the model."""
        return self._graph

    @property
    def groups(self) -> "Set[_Group]":
        """Return all the groups registered to the Model."""
        return self._groups

    @property
    def bcs(self) -> "FieldsGroup":
        """Return the boundary conditions of the model."""
        return self._fields.subgroup(lambda x: isinstance(x, BoundaryConditionsField))

    @property
    def bcs_nodes(self) -> dict[_BoundaryCondition, "NodesGroup"]:
        return {field.condition: field.distribution for field in self.bcs if isinstance(field.condition, _BoundaryCondition)}

    @property
    def ics(self) -> "FieldsGroup":
        """Return the initial conditions of the model."""
        return self._fields.subgroup(lambda x: isinstance(x, _InitialConditionField))

    @property
    def ics_nodes(self) -> dict[_InitialCondition, "NodesGroup"]:
        """Return a dictionary with the initial conditions and the nodes where they are applied."""
        return {field.condition: field.distribution for field in self.ics if isinstance(field.condition, _InitialCondition)}

    @property
    def constraints(self) -> "ConstraintsGroup":
        """Return the constraints of the model."""
        return self._constraints

    @property
    def connectors(self) -> "ConnectorsGroup":
        """Return the connectors of the model."""
        return self._connectors

    @property
    def constants(self) -> "dict":
        """Return the constants of the model."""
        return self._constants

    @property
    def fields(self) -> "FieldsGroup":
        """Return the fields of the model."""
        return self._fields

    @property
    def g(self) -> "float":
        """Return the gravitational constant of the model."""
        return self.constants["g"]

    @g.setter
    def g(self, value):
        self._constants["g"] = value

    @property
    def materials(self) -> "MaterialsGroup":
        """Return a set of all materials in the model."""
        return MaterialsGroup(members=set(self.elements.group_by(lambda x: x.material).keys()), name="ALL_MATERIALS")

    @property
    def part_materials(self) -> "Dict[_Part, Set[_Material]]":
        """Return a dictionary with the materials contained in each part in the model."""
        return {part: part.materials.members for part in self.parts if not isinstance(part, RigidPart)}

    @property
    def sections(self) -> "SectionsGroup":
        """Return a set of all sections in the model."""
        return SectionsGroup(members= set(self.elements.group_by(key=lambda x: x.section).keys()), name="ALL_SECTIONS")

    @property
    def part_sections(self) -> "Dict[_Part, Set[_Section]]":
        """Return a dictionary with the sections contained in each part in the model."""
        return {part: part.sections.members for part in self.parts if not isinstance(part, RigidPart)}

    @property
    def section_elements(self) -> "Dict[_Section, ElementsGroup]":
        """Return a dictionary with the elements contained in each section in the model."""
        return self.elements.group_by(key=lambda x: x.section)

    @property
    def interfaces(self) -> "InterfacesGroup":
        """Return a set of all interfaces in the model."""
        return self._interfaces

    @property
    def interactions(self) -> "InteractionsGroup":
        """Return a dictionary of all interactions in the model."""
        return self._interactions

    # TODO change to leverage groups
    @property
    def amplitudes(self):
        amplitudes = set()
        # Amplitude is for now only set for the thermal interfaces.
        for interface in filter(lambda x: hasattr(x.behavior, "temperature"), filter(lambda y: hasattr(y.behavior, "temperature"), self.interfaces)):
            amplitudes.add(interface.behavior.temperature.amplitude)
        return amplitudes

    @property
    def problems(self) -> "Set[Problem]":
        """Return all the problems registered to the Model."""
        return self._problems

    @property
    def path(self) -> "Optional[Path]":
        """Return the path of the model."""
        return self._path

    @path.setter
    def path(self, value: "Union[str, Path]"):
        from pathlib import Path

        if not isinstance(value, Path):
            value = Path(value)
        self._path = value.joinpath(self.name)

    @property
    def nodes(self) -> "NodesGroup":
        """Return a group of all nodes in the model."""
        return NodesGroup(members=list(chain.from_iterable(part.nodes for part in self.parts if part.nodes)))

    @property
    def points(self) -> "list[Point]":
        """Return a list of all node coordinates in the model."""
        return [n.point for n in self.nodes]

    @property
    def elements(self) -> "ElementsGroup":
        """Return a list of all elements in the model."""
        return ElementsGroup(members=list(chain.from_iterable(part.elements for part in self.parts if part.elements)))

    @property
    def bounding_box(self) -> "Optional[Box]":
        """Return the bounding box of the model."""
        try:
            bb = bounding_box(list(chain.from_iterable([part.bounding_box.points for part in self.parts if part.bounding_box])))
        except Exception:
            return None
        return Box.from_bounding_box(bb)

    @property
    def bb_center(self) -> "Point":
        """Return the center of the bounding box of the model."""
        if self.bounding_box:
            return Point(*centroid_points(self.bounding_box.points))
        else:
            raise AttributeError("The model has no bounding box")

    @property
    def center(self) -> "Point":
        """Return the center of the model."""
        return Point(*centroid_points(self.points))

    @property
    def centroid(self) -> "Point":
        """Return the centroid of the model."""
        weights = []
        points = []
        for part in self.parts:
            points.append(part.centroid)
            weights.append(part.weight)
        return Point(*centroid_points_weighted(points=points, weights=weights))

    @property
    def bottom_plane(self) -> "Plane":
        """Return the bottom plane of the model."""
        if self.bounding_box:
            return Plane.from_three_points(*[self.bounding_box.points[i] for i in self.bounding_box.bottom[:3]])
        raise AttributeError("The model has no bounding box")

    @property
    def top_plane(self) -> "Plane":
        """Return the top plane of the model."""
        if self.bounding_box:
            return Plane.from_three_points(*[self.bounding_box.points[i] for i in self.bounding_box.top[:3]])
        raise AttributeError("The model has no bounding box")

    @property
    def volume(self) -> "float":
        """Return the volume of the model."""
        return sum(p.volume for p in self.parts)

    @property
    def units(self) -> "Optional[UnitRegistry]":
        """Return the units of the model."""
        return self._units

    @units.setter
    def units(self, value: "UnitRegistry"):
        from compas_fea2.units import UnitRegistry

        if not isinstance(value, UnitRegistry):
            raise ValueError("Pint UnitRegistry required")
        self._units = value

    def assign_keys(self, start: "int | None" = None, restart=False):
        """Assign keys to the model and its parts.

        Parameters
        ----------
        start : int, optional
            The starting key, by default None (the default starting key is used).
        restart : bool, optional
            If `True`, the keys of nodes and elements are reassigned for each part,
            otherwise they are assigned sequentially across all parts. By default `False`.

        Returns
        -------
        None

        """
        start = start or self._starting_key
        for i, material in enumerate(self.materials):
            material._key = i + start
        for i, section in enumerate(self.sections):
            section._key = i + start
        for i, connector in enumerate(self.connectors):
            connector._key = i + start

        if not restart:
            i = 0
            j = 0
            for part in self.parts:
                for node in part.nodes:
                    node._key = i + start
                    i += 1

                for element in part.elements:
                    element._key = j + start
                    j += 1
        else:
            for part in self.parts:
                for i, node in enumerate(part.nodes):
                    node._key = i + start
                for i, element in enumerate(part.elements):
                    element._key = i + start

    # =========================================================================
    #                             Parts methods
    # =========================================================================

    def find_part_by_name(self, name: str, casefold: bool = False) -> "Optional[_Part]":
        """Find if there is a part with a given name in the model.

        Notes
        -----
        Names in fea2 must don't contain spaces. If so, they
        are replaced by underscores.

        Parameters
        ----------
        name : str
            The name to match
        casefold : bool, optional
            If `True` perform a case insensitive search, by default `False`.

        Returns
        -------
        :class:`compas_fea2.model.Part`

        """
        from compas_fea2.utilities._devtools import normalize_string

        name = normalize_string(name)
        for part in self.parts:
            name_1 = part.name if not casefold else part.name.casefold()
            name_2 = name if not casefold else name.casefold()
            if name_1 == name_2:
                return part
        return None

    def contains_part(self, part: "_Part") -> "bool":
        """Verify that the model contains a specific part.

        Parameters
        ----------
        part : :class:`compas_fea2.model.Part`

        Returns
        -------
        bool

        """
        return part in self.parts

    def add_part(self, part: "Optional[_Part]" = None, **kwargs) -> "_Part":
        """Adds a Part to the Model.

        Parameters
        ----------
        part : :class:`compas_fea2.model._Part`

        Returns
        -------
        :class:`compas_fea2.model._Part`

        Raises
        ------
        TypeError
            If the part is not a part.
        ValueError
            If a part with the same name already exists in the model.

        """
        if not part:
            if "rigid" in kwargs and kwargs["rigid"]:
                part = RigidPart(**kwargs)
            else:
                part = Part(**kwargs)

        if not isinstance(part, _Part):
            raise TypeError("{!r} is not a part.".format(part))

        part._registration = self
        if settings.VERBOSE:
            print("{!r} registered to {!r}.".format(part, self))

        part._key = len(self._parts)
        self._parts.add_member(part)
        self.graph.add_node(part.name, part=part, type="part")
        self.graph.add_edge(self.name, part.name, relation="contains")
        return part

    def add_parts(self, parts: "list[_Part]") -> "list[_Part]":
        """Add multiple parts to the model.

        Parameters
        ----------
        parts : list[:class:`compas_fea2.model.Part`]

        Returns
        -------
        list[:class=`compas_fea2.model.Part`]

        """
        return [self.add_part(part) for part in parts]

    def copy_part(self, part: "_Part", transformation: "Transformation") -> "_Part":
        """Copy a part and apply a transformation.

        Parameters
        ----------
        part : :class=`compas_fea2.model._Part`
            The part to copy.
        transformation : :class=`compas.geometry.Transformation`
            The transformation to apply to the copied part.

        Returns
        -------
        :class=`compas_fea2.model._Part`
            The new, copied part.

        """
        new_part = part.copy(duplicate=False)
        new_part.transform(transformation)
        return self.add_part(new_part)

    def array_parts(self, parts: "list[_Part]", n: int, transformation: "Transformation") -> "list[_Part]":
        """Create an array of parts by applying a transformation multiple times.

        Parameters
        ----------
        parts : list[:class=`compas_fea2.model.Part`]
            The list of parts to array.
        n : int
            The number of copies to create.
        transformation : :class=`compas.geometry.Transformation`
            The transformation to apply for each copy.

        Returns
        -------
        list[:class=`compas_fea2.model.Part`]
            The list of new, arrayed parts.

        """

        new_parts: "list[_Part]" = []
        for i in range(n):
            for part in parts:
                new_part = part.copy()
                new_part.transform(transformation * (i + 1))
                new_parts.append(new_part)
        return self.add_parts(new_parts)

    # =========================================================================
    #                           Materials methods
    # =========================================================================

    def find_material_by_name(self, name: str) -> "Optional[_Material]":
        """Find a material by name.

        Parameters
        ----------
        name : str
            The name of the material.

        Returns
        -------
        :class=`compas_fea2.model.materials.Material`

        """
        for material in self.materials:
            if material.name == name:
                return material
        return None

    def contains_material(self, material: "_Material") -> "bool":
        """Verify that the model contains a specific material.

        Parameters
        ----------
        material : :class=`compas_fea2.model.materials.Material`

        Returns
        -------
        bool

        """
        return material in self.materials

    def find_material_by_key(self, key: int) -> "Optional[_Material]":
        """Find a material by key.

        Parameters
        ----------
        key : int
            The key of the material.

        Returns
        -------
        :class=`compas_fea2.model.materials.Material`

        """
        for material in self.materials:
            if material.key == key:
                return material
        return None

    def find_materials_by_attribute(self, attr: str, value: "Union[str, int, float]", tolerance: float = 1) -> "list[_Material]":
        """Find materials by attribute.

        Parameters
        ----------
        attr : str
            The name of the attribute.
        value : Union[str, int, float]
            The value of the attribute.
        tolerance : float, optional
            The tolerance for the search, by default 1.

        Returns
        -------
        list[:class=`compas_fea2.model.materials.Material`]

        """
        materials = []
        for material in self.materials:
            if abs(getattr(material, attr) - value) < tolerance:
                materials.append(material)
        return materials

    def find_section_by_name(self, name: str) -> "Optional[_Section]":
        """Find a section by name.

        Parameters
        ----------
        name : str
            The name of the section.

        Returns
        -------
        :class=`compas_fea2.model.sections.Section`

        """
        for section in self.sections:
            if section.name == name:
                return section
        return None

    def contains_section(self, section: "_Section") -> "bool":
        """Verify that the model contains a specific section.

        Parameters
        ----------
        section : :class=`compas_fea2.model.sections.Section`

        Returns
        -------
        bool

        """
        return section in self.sections

    def find_section_by_key(self, key: int) -> "Optional[_Section]":
        """Find a section by key.

        Parameters
        ----------
        key : int
            The key of the section.

        Returns
        -------
        :class=`compas_fea2.model.sections.Section`

        """
        for section in self.sections:
            if section.key == key:
                return section
        return None

    def find_sections_by_attribute(self, attr: str, value: "Union[str, int, float]", tolerance: float = 1) -> "list[_Section]":
        """Find sections by attribute.

        Parameters
        ----------
        attr : str
            The name of the attribute.
        value : Union[str, int, float]
            The value of the attribute.
        tolerance : float, optional
            The tolerance for the search, by default 1.

        Returns
        -------
        list[:class=`compas_fea2.model.sections.Section`]

        """
        sections = []
        for section in self.sections:
            if abs(getattr(section, attr) - value) < tolerance:
                sections.append(section)
        return sections

    # =========================================================================
    #                           Nodes methods
    # =========================================================================

    @get_docstring(_Part)
    @part_method
    def find_node_by_key(self, key: int) -> "Any":
        pass

    @get_docstring(_Part)
    @part_method
    def find_node_by_name(self, name: str) -> "Any":
        pass

    @get_docstring(_Part)
    @part_method
    def find_closest_nodes_to_node(self, node: "Node", number_of_nodes: int = 1, plane: "Optional[Plane]" = None) -> "Any":
        pass

    @get_docstring(_Part)
    @part_method
    def find_closest_nodes_to_point(self, point: "Point", number_of_nodes: int = 1, plane: "Optional[Plane]" = None) -> "Any":
        pass

    @get_docstring(_Part)
    @part_method
    def find_nodes_on_plane(self, plane: "Plane", tol: float = 1) -> "Any":
        pass

    @get_docstring(_Part)
    @part_method
    def find_nodes_in_polygon(self, polygon: "Polygon", tol: float = 1.1) -> "Any":
        pass

    @get_docstring(_Part)
    @part_method
    def contains_node(self, node: "Node") -> "Any":
        pass

    # =========================================================================
    #                           Elements methods
    # =========================================================================

    @get_docstring(_Part)
    @part_method
    def find_element_by_key(self, key: int) -> "Any":
        pass

    @get_docstring(_Part)
    @part_method
    def find_element_by_name(self, name: str) -> "Any":
        pass

    # =========================================================================
    #                           Faces methods
    # =========================================================================

    @get_docstring(_Part)
    @part_method
    def find_faces_in_polygon(self, key: int) -> "Any":
        pass

    # =========================================================================
    #                           Groups methods
    # =========================================================================
    def add_group(self, group: "_Group") -> Any:
        """Add a group to the model.

        Parameters
        ----------
        group : :class=`compas_fea2.model.groups._Group`

        Returns
        -------
        :class=`compas_fea2.model.groups._Group`

        """
        if not isinstance(group, _Group):
            raise TypeError("{!r} is not a group.".format(group))
        group._registration = self
        self._groups.add(group)
        return group

    def add_groups(self, groups: "list[_Group]") -> "list[_Group]":
        """Add multiple groups to the model.

        Parameters
        ----------
        groups : list[:class=`compas_fea2.model.groups._Group`]

        Returns
        -------
        list[:class=`compas_fea2.model.groups._Group`]
        """
        return [self.add_group(group) for group in groups]

    def group_parts_where(self, attr: str, value: "Union[str, int, float]") -> "PartsGroup":
        """Create a group of parts with an attribute that satisfies a condition.

        Parameters
        ----------
        attr : str
            The attribute to check.
        value : Union[str, int, float]
            The value of the attribute.

        Returns
        -------
        :class=`compas_fea2.model.PartsGroup`
            The created group.
        """
        parts = [part for part in self.parts if getattr(part, attr) == value]
        return self.add_group(PartsGroup(parts))

    # =========================================================================
    #                           BCs methods
    # =========================================================================
    # FIXME: currently it is possible to bcs to nodes that are not in any part whcih could lead to problems
    def add_bcs(self, bc_fields: "BoundaryConditionsField | List[BoundaryConditionsField]") -> "BoundaryConditionsField | List[BoundaryConditionsField]":
        """Add a :class=`compas_fea2.model.BoundaryConditionsField` to the model.

        Parameters
        ----------
        bc : :class=`compas_fea2.model.BoundaryConditionsField`

        Returns
        -------
        :class=`compas_fea2.model._BoundaryCondition`

        """
        if isinstance(bc_fields, BoundaryConditionsField):
            fields = [bc_fields]
        else:
            fields = bc_fields
        for bc_field in fields:
            self._fields.add_member(bc_field)
            self._groups.add(bc_field.distribution)
            bc_field._registration = self
        return bc_fields

    def _add_bc_type(self, bc_type: str, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs) -> "BoundaryConditionsField | List[BoundaryConditionsField]":
        """Add a :class=`compas_fea2.model.BoundaryCondition` by type.

        Parameters
        ----------
        bc_type : str
            The type of boundary condition to add.
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            The nodes where the boundary condition is applied.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        Returns
        -------
        :class=`compas_fea2.model._BoundaryCondition`
        """
        types = {
            "fix": "FixedBC",
            "pin": "PinnedBC",
            "clampXX": "ClampBCXX",
            "clampYY": "ClampBCYY",
            "clampZZ": "ClampBCZZ",
            "rollerX": "RollerBCX",
            "rollerY": "RollerBCY",
            "rollerZ": "RollerBCZ",
            "thermal": "ThermalBC",
        }
        m = importlib.import_module("compas_fea2.model.bcs")
        bc = getattr(m, types[bc_type])(frame=frame)
        field = BoundaryConditionsField(condition=bc, distribution=nodes, **kwargs)
        return self.add_bcs(field)

    def add_fix_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class=`compas_fea2.model.bcs.FixedBC` to the given nodes.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("fix", nodes, frame, **kwargs)

    def add_pin_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class=`compas_fea2.model.bcs.PinnedBC` to the given nodes.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("pin", nodes, frame, **kwargs)

    def add_clampXX_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class=`compas_fea2.model.bcs.ClampBCXX` to the given nodes.

        This boundary condition clamps all degrees of freedom except rotation about the local XX-axis.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("clampXX", nodes, frame, **kwargs)

    def add_clampYY_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class=`compas_fea2.model.bcs.ClampBCYY` to the given nodes.

        This boundary condition clamps all degrees of freedom except rotation about the local YY-axis.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("clampYY", nodes, frame, **kwargs)

    def add_clampZZ_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class=`compas_fea2.model.bcs.ClampBCZZ` to the given nodes.

        This boundary condition clamps all degrees of freedom except rotation about the local ZZ-axis.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("clampZZ", nodes, frame, **kwargs)

    def add_rollerX_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class=`compas_fea2.model.bcs.RollerBCX` to the given nodes.

        This boundary condition clamps all degrees of freedom except displacement in the local X-direction.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("rollerX", nodes, frame, **kwargs)

    def add_rollerY_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class=`compas_fea2.model.bcs.RollerBCY` to the given nodes.

        This boundary condition clamps all degrees of freedom except displacement in the local Y-direction.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("rollerY", nodes, frame, **kwargs)

    def add_rollerZ_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class=`compas_fea2.model.bcs.RollerBCZ` to the given nodes.

        This boundary condition clamps all degrees of freedom except displacement in the local Z-direction.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("rollerZ", nodes, frame, **kwargs)

    def add_rollerXY_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class:`compas_fea2.model.bcs.RollerBCXY` to the given nodes.

        This boundary condition allows translation along the local XY-plane.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`] or :class:`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("rollerXY", nodes, frame, **kwargs)

    def add_rollerXZ_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class:`compas_fea2.model.bcs.RollerBCXZ` to the given nodes.

        This boundary condition allows translation along the local XZ-plane.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`] or :class:`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("rollerXZ", nodes, frame, **kwargs)

    def add_rollerYZ_bc(self, nodes: "Union[list[Node], NodesGroup]", frame: "Frame" = None, **kwargs):
        """Add a :class:`compas_fea2.model.bcs.RollerBCYZ` to the given nodes.

        This boundary condition allows translation along the local YZ-plane.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`] or :class:`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        frame : :class:`compas.geometry.Frame`, optional
            The frame in which the boundary condition is defined, by default None (global frame).

        """
        return self._add_bc_type("rollerYZ", nodes, frame, **kwargs)

    def add_thermal_bc(self, nodes: "Union[list[Node], NodesGroup]", temperature: "float", **kwargs) -> "BoundaryConditionsField | List[BoundaryConditionsField]":
        """Add a :class:`compas_fea2.model.bcs.ThermalBC` to the model.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            The nodes where the thermal boundary condition is applied.
        temperature : float, optional
            The temperature to apply, by default None (no temperature is applied).

        Returns
        -------
        :class=`compas_fea2.model.bcs.ThermalBC`
            The applied thermal boundary condition.
        """
        from compas_fea2.model.bcs import ImposedTemperature

        it = ImposedTemperature(temperature=temperature)
        if not isinstance(nodes, NodesGroup):
            nodes = NodesGroup(nodes)

        field = BoundaryConditionsField(condition=it, distribution=nodes, axes="global")
        return self.add_bcs(field, **kwargs)

    def remove_bcs(self, field: "BoundaryConditionsField"):
        """Release nodes that were previously restrained.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`]
            List of nodes to release.

        None

        """
        self._fields.remove_member(field)

    def remove_nodes_from_bcs(self, nodes: "Union[list[Node], NodesGroup]", field: "BoundaryConditionsField"):
        """Remove nodes from a boundary condition field.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            The nodes to remove from the boundary condition.
        field : :class:`compas_fea2.model.BoundaryConditionsField`
            The boundary condition field from which to remove the nodes.

        """
        if not isinstance(nodes, NodesGroup):
            nodes = NodesGroup(nodes)
        field.distribution.remove_members(nodes)

    # FIXME: this should be easy to implement
    def add_ics(self, ic: "_InitialCondition", members: "Union[list[Union[Node, _Element]], NodesGroup]") -> "_InitialCondition":
        """Add a :class=`compas_fea2.model._InitialCondition` to the model.

        Parameters
        ----------
        ic : :class=`compas_fea2.model._InitialCondition`
            The initial condition to apply.
        members : list[:class=`compas_fea2.model.Node` or :class=`compas_fea2.model._Element`] or :class=`compas_fea2.model.NodesGroup`
            The nodes/elements where the initial condition is applied.

        Returns
        -------
        :class=`compas_fea2.model._InitialCondition`
            The applied initial condition.
        """
        raise NotImplementedError("This method is not implemented in the base Model class. Please use a specific model subclass.")

        # if not isinstance(ic_field, _InitialConditionField):
        #     raise TypeError("{!r} is not an Initial Condition Field.".format(ic_field))

        # for node in ic_field.distribution:
        #     if not isinstance(node, Node):
        #         raise TypeError("{!r} is not a Node.".format(node))
        #     if not node.part:
        #         raise ValueError("{!r} is not registered to any part.".format(node))
        #     elif node.part not in self.parts:
        #         raise ValueError("{!r} belongs to a part not registered to this model.".format(node))
        #     if isinstance(node.part, RigidPart):
        #         if not node.is_reference:
        #             raise ValueError("For rigid parts bundary conditions can be assigned only to the reference point")
        #     node._bcs.add_members(ic_field.conditions)

        # self._ics_fields.add(ic_field)
        # ic_field._registration = self

        # return ic_field

    def add_ics_fields(self, ics_fields: list["_InitialConditionField"]) -> list["_InitialConditionField"]:
        raise NotImplementedError("This method is not implemented in the base Model class. Please use a specific model subclass.")
        # for ics_field in ics_fields:
        #     self.add_ics_field(ics_field)
        # return ics_field

    def add_uniform_thermal_ics_field(self, T0: float, nodes) -> InitialTemperatureField:
        raise NotImplementedError("This method is not implemented in the base Model class. Please use a specific model subclass.")
        # return self.add_ics_field(InitialTemperatureField(nodes=nodes, conditions=InitialTemperature(T0=T0)))

    # =========================================================================
    #                           Constraints methods
    # =========================================================================
    # FIXME: switch to fields here as well
    def add_constraint(self, constraint: "_Constraint") -> "_Constraint":
        """Add a constraint to the model.

        Parameters
        ----------
        constraint : :class=`compas_fea2.model.constraints._Constraint`
            The constraint to add.

        Returns
        -------
        :class=`compas_fea2.model.constraints._Constraint`
            The added constraint.
        """
        from compas_fea2.model.constraints import _Constraint

        if not isinstance(constraint, _Constraint):
            raise TypeError("{!r} is not a constraint.".format(constraint))
        constraint._registration = self
        self._constraints.add_member(constraint)
        return constraint

    def add_constraints(self, constraints: "list[_Constraint]") -> "list[_Constraint]":
        """Add multiple constraints to the model.

        Parameters
        ----------
        constraints : list[:class=`compas_fea2.model.constraints._Constraint`]
            The constraints to add.

        Returns
        -------
        list[:class=`compas_fea2.model.constraints._Constraint`]
            The added constraints.
        """
        return [self.add_constraint(constraint) for constraint in constraints]

    # =========================================================================
    #                           Connectors methods
    # =========================================================================
    # FIXME: switch to fields here as well
    def add_connector(self, connector: "_Connector") -> "_Connector":
        """Add a connector to the model.

        Parameters
        ----------
        connector : :class=`compas_fea2.model.connectors.Connector`
            The connector to add.

        Returns
        -------
        :class=`compas_fea2.model.connectors.Connector`
            The added connector.
        """
        from compas_fea2.model.connectors import _Connector

        if not isinstance(connector, _Connector):
            raise TypeError("{!r} is not a connector.".format(connector))
        connector._registration = self
        self._connectors.add_member(connector)
        return connector

    # =========================================================================
    #                           Interactions methods
    # =========================================================================
    def add_interaction(self, interaction: "_Interaction") -> "_Interaction":
        """Add an interaction to the model.

        Parameters
        ----------
        interaction : :class=`compas_fea2.model.interactions.Interaction`
            The interaction to add.

        Returns
        -------
        :class=`compas_fea2.model.interactions.Interaction`
            The added interaction.
        """

        interaction._registration = self
        self._interactions.add_member(interaction)
        return interaction

    def add_interactions(self, interactions: "list[_Interaction]") -> "list[_Interaction]":
        """Add multiple interactions to the model.

        Parameters
        ----------
        interactions : list[:class=`compas_fea2.model.interactions.Interaction`]
            The interactions to add.

        Returns
        -------
        list[:class=`compas_fea2.model.interactions.Interaction`]
            The added interactions.
        """
        return [self.add_interaction(interaction) for interaction in interactions]

    def add_interface(self, interface: "_Interface") -> "_Interface":
        """
        :class:`compas_fea2.model.Interface`

        """
        interface._registration = self
        self._interfaces.add_member(interface)
        return interface

    def add_interfaces(self, interfaces):
        """Add multiple :class:`compas_fea2.model.Interface` objects to the model."""
        return [self.add_interface(interface) for interface in interfaces]

    # =========================================================================
    #                           Problems methods
    # =========================================================================
    def add_problem(self, problem: Optional["Problem"] = None, **kwargs) -> "Problem":
        """Add a problem to the model.

        Parameters
        ----------
        problem : :class=`compas_fea2.problem.Problem`
            The problem to add.

        Returns
        -------
        :class=`compas_fea2.problem.Problem`
            The added problem.
        """
        from compas_fea2.problem import Problem

        if not problem:
            problem = Problem(**kwargs)
        if not isinstance(problem, Problem):
            raise TypeError("{!r} is not a problem.".format(problem))
        problem._registration = self
        self._problems.add(problem)
        return problem

    def add_problems(self, problems: "list[Problem]") -> "list[Problem]":
        """Add multiple problems to the model.

        Parameters
        ----------
        problems : list[:class=`compas_fea2.problem.Problem`]
            The problems to add.

        Returns
        -------
        list[:class=`compas_fea2.problem.Problem`]
            The added problems.
        """
        return [self.add_problem(problem) for problem in problems]

    # =========================================================================
    #                           Show methods
    # =========================================================================
    def summary(self) -> str:
        """Return a summary of the model.

        Returns
        -------
        str
            The summary.
        """
        parts_info = []
        for part in self.parts:
            parts_info.append("{:<15} - #nodes: {:<5} #elements: {:<5} #mat: {:<5} #sect: {:<5}".format(part.name, len(part.nodes), len(part.elements), len(part.materials), len(part.sections)))

        bcs_info = []
        for field in self.bcs:
            bcs_info.append("{!r} - # of restrained nodes {}".format(field.condition, len(field.distribution)))

        ics_info = []
        for field in self.ics:
            ics_info.append("{!r} - # of restrained nodes {}".format(field.condition, len(field.distribution)))

        constraints_info = []
        for constraint in self.constraints:
            constraints_info.append("{!r}".format(constraint))

        connectors_info = []
        for connector in self.connectors:
            connectors_info.append("{!r}".format(connector))

        interactions_info = []
        for interaction in self.interactions:
            interactions_info.append("{!r}".format(interaction))

        problems_info = []
        for problem in self.problems:
            problems_info.append("{!r}".format(problem))

        title = "compas_fea2 Model: {}".format(self.name)
        separator = "-" * (len(title))
        return f"""
{title}
{separator}
description: {self.description}
author: {self.author}
path: {self.path}

Parts
-----
{chr(10).join(parts_info)}

Boundary Conditions
-------------------
{chr(10).join(bcs_info)}

Initial Conditions
------------------
{chr(10).join(ics_info)}

Constraints
-----------
{chr(10).join(constraints_info)}

Connectors
----------
{chr(10).join(connectors_info)}

Interactions
------------
{chr(10).join(interactions_info)}

Problems
--------
{chr(10).join(problems_info)}
"""

    def clear(self):
        """Clear the model."""
        self._parts.clear()
        self._materials.clear()
        self._sections.clear()
        self._constraints.clear()
        self._connectors.clear()
        self._interfaces.clear()
        self._problems.clear()
        self._groups.clear()
        self._graph = Graph()

    def reset(self):
        """Reset the model."""
        self.clear()
        self._key = 0
        self._starting_key = 0
        self._units = None
        self._path = None
        self._constants = {"g": None}
