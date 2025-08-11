from __future__ import annotations

import importlib
from itertools import chain
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
from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.model.bcs import _BoundaryCondition
from compas_fea2.model.bcs import _ThermalBoundaryCondition
from compas_fea2.model.connectors import _Connector
from compas_fea2.model.constraints import _Constraint
from compas_fea2.model.groups import ConnectorsGroup
from compas_fea2.model.groups import ConstraintsGroup
from compas_fea2.model.groups import ElementsGroup
from compas_fea2.model.groups import InteractionsGroup
from compas_fea2.model.groups import InterfacesGroup
from compas_fea2.model.groups import MaterialsGroup
from compas_fea2.model.groups import NodesGroup
from compas_fea2.model.groups import PartsGroup
from compas_fea2.model.groups import SectionsGroup
from compas_fea2.model.groups import _Group
from compas_fea2.model.ics import _InitialCondition
from compas_fea2.model.nodes import Node
from compas_fea2.model.parts import Part
from compas_fea2.model.parts import RigidPart
from compas_fea2.model.parts import _Part
from compas_fea2.problem import Problem
from compas_fea2.utilities._utils import get_docstring
from compas_fea2.utilities._utils import part_method

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Union

    from compas.geometry import Polygon

    from compas_fea2.model.bcs import _BoundaryCondition
    from compas_fea2.model.bcs import _ThermalBoundaryCondition
    from compas_fea2.model.connectors import _Connector
    from compas_fea2.model.constraints import _Constraint
    from compas_fea2.model.fields import _BoundaryConditionsField
    from compas_fea2.model.fields import _InitialConditionField
    from compas_fea2.model.groups import ConnectorsGroup
    from compas_fea2.model.groups import ConstraintsGroup
    from compas_fea2.model.groups import ElementsGroup
    from compas_fea2.model.groups import InteractionsGroup
    from compas_fea2.model.groups import InterfacesGroup
    from compas_fea2.model.groups import MaterialsGroup
    from compas_fea2.model.groups import SectionsGroup
    from compas_fea2.model.ics import InitialTemperature
    from compas_fea2.model.interactions import _Interaction
    from compas_fea2.model.materials.material import _Material
    from compas_fea2.model.sections import _Section
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
        self._materials: "MaterialsGroup" = MaterialsGroup(members=[], name="ALL_MATERIALS")
        self._sections: "SectionsGroup" = SectionsGroup(members=[], name="ALL_SECTIONS")
        self._interfaces: "InterfacesGroup" = InterfacesGroup(members=[], name="ALL_INTERFACES")
        self._interactions: "InteractionsGroup" = InteractionsGroup(members=[], name="ALL_INTERACTIONS")
        self._connectors: "ConnectorsGroup" = ConnectorsGroup(members=[], name="ALL_CONNECTORS")
        self._constraints: "ConstraintsGroup" = ConstraintsGroup(members=[], name="ALL_CONSTRAINTS")
        self._groups: "Set[_Group]" = set([self._parts, self._materials, self._sections, self._interfaces, self._interactions, self._connectors, self._constraints])

        self._problems: "Set[Problem]" = set()
        self._bcs_fields: "Set[_BoundaryConditionsField]" = set()
        self._ics_fields: "Set[_InitialConditionField]" = set()

    @property
    def __data__(self):
        return {
            "class": self.__class__.__name__,
            "description": self.description,
            "author": self.author,
            "parts": [part.__data__ for part in self.parts],
            "materials": [material.__data__ for material in self.materials],
            "sections": [section.__data__ for section in self.sections],
            "interfaces": [interface.__data__ for interface in self.interfaces],
            "interactions": [interaction.__data__ for interaction in self.interactions],
            "constraints": [constraint.__data__ for constraint in self.constraints],
            "connectors": [connector.__data__ for connector in self.connectors],
            "problems": [problem.__data__ for problem in self.problems],
            "path": str(self.path) if self.path else None,
            "constants": self.constants,
            "name": self.name,
        }

    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        model = cls(description=data.get("description"), author=data.get("author"))
        model._path = data.get("path")
        model._constants = data.get("constants", {})
        model._name = data.get("name", model._name)

        for part_data in data.get("parts", []):
            model.add_part(registry.add_from_data(part_data, "compas_fea2.model.parts"))

        for material_data in data.get("materials", []):
            model.add_material(registry.add_from_data(material_data, "compas_fea2.model.materials.material"))

        for section_data in data.get("sections", []):
            model.add_section(registry.add_from_data(section_data, "compas_fea2.model.sections"))

        for interface_data in data.get("interfaces", []):
            model.interfaces.add_member(registry.add_from_data(interface_data, "compas_fea2.model.interfaces"))

        for interaction_data in data.get("interactions", []):
            model.interactions.add_member(registry.add_from_data(interaction_data, "compas_fea2.model.interactions"))

        for constraint_data in data.get("constraints", []):
            model.constraints.add_member(registry.add_from_data(constraint_data, "compas_fea2.model.constraints"))

        for connector_data in data.get("connectors", []):
            model.connectors.add_member(registry.add_from_data(connector_data, "compas_fea2.model.connectors"))

        for problem_data in data.get("problems", []):
            model.add_problem(registry.add_from_data(problem_data, "compas_fea2.problem"))

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
    def partgroups(self) -> "List[PartsGroup]":
        """Return all the part groups registered to the Model."""
        return [group for group in self._groups if isinstance(group, PartsGroup)]

    @property
    def materialgroups(self) -> "List[MaterialsGroup]":
        """Return all the materials groups of the model."""
        return [group for group in self._groups if isinstance(group, MaterialsGroup)]

    @property
    def elementgroups(self) -> "List[ElementsGroup]":
        """Return all the element groups of the model."""
        return [group for group in self._groups if isinstance(group, ElementsGroup)]

    @property
    def secionggroups(self) -> "List[SectionsGroup]":
        """Return all the section groups of the model."""
        return [group for group in self._groups if isinstance(group, SectionsGroup)]

    @property
    def interactiongroups(self) -> "List[InteractionsGroup]":
        """Return all the interaction groups of the model."""
        return [group for group in self._groups if isinstance(group, InteractionsGroup)]

    @property
    def connectorgroups(self) -> "List[ConnectorsGroup]":
        """Return all the connector groups of the model."""
        return [group for group in self._groups if isinstance(group, ConnectorsGroup)]

    @property
    def constraintsgroups(self) -> "List[ConstraintsGroup]":
        """Return all the constraints groups of the model."""
        return [group for group in self._groups if isinstance(group, ConstraintsGroup)]

    @property
    def interfacesgroups(self) -> "InterfacesGroup":
        """Return all the interfaces groups of the model."""
        return [group for group in self._groups if isinstance(group, InterfacesGroup)][0] if self._groups else InterfacesGroup(members=[])

    @property
    def bcs(self) -> "Dict[Union[_BoundaryCondition, _ThermalBoundaryCondition], Set[Node]]":
        """Return the boundary conditions of the model."""
        return self._bcs

    @property
    def bcs_nodes(self)  -> dict[_BoundaryCondition, "NodesGroup"]:
        bcs_nodes = {}
        for bc in self.bcs:
            nodes = NodesGroup(self.nodes).subgroup(lambda p: (isinstance(xbc, type(bc)) for xbc in p.bcs))
            if len(nodes) == 0:
                self.bcs.remove(bc)
            else :
                bcs_nodes[bc] = nodes
        return bcs_nodes

    @property
    def ics(self) -> "Dict[_InitialCondition, Set[Union[Node, _Element]]]":
        """Return the initial conditions of the model."""
        return self._ics

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
    def g(self) -> "float":
        """Return the gravitational constant of the model."""
        return self.constants["g"]

    @g.setter
    def g(self, value):
        self._constants["g"] = value

    @property
    def materials_dict(self) -> "dict[_Part, MaterialsGroup]":
        """Return a dictionary with the materials assigned to each part in the model."""
        materials = {part: part.materials for part in self.parts if not isinstance(part, RigidPart)}
        if not materials:
            raise ValueError("No materials found in the model.")
        return materials

    @property
    def materials(self) -> "Set[_Material]":
        """Return a set of all materials in the model."""
        part_materials = chain.from_iterable(part.materials for part in self.parts if not isinstance(part, RigidPart))
        return set(chain(part_materials, self._materials))

    @property
    def sections_dict(self) -> "dict[_Part, SectionsGroup]":
        """Return a dictionary with the sections contained in each part in the model."""
        sections = {part: part.sections for part in self.parts if not isinstance(part, RigidPart)}
        return sections

    @property
    def sections(self) -> "Set[_Section]":
        """Return a set of all sections in the model."""
        part_sections = chain.from_iterable(part.sections for part in self.parts if not isinstance(part, RigidPart))
        return set(chain(part_sections, self._sections))

    @property
    def interfaces(self) -> "InterfacesGroup":
        """Return a set of all interfaces in the model."""
        return self._interfaces

    @property
    def interactions(self) -> "InteractionsGroup":
        """Return a dictionary of all interactions in the model."""
        return self._interactions

    @property
    def amplitudes(self):
        amplitudes = set()
        #Amplitude is for now only set for the thermal interfaces.
        for interface in filter(lambda x: hasattr(x.behavior, "temperature"), filter(lambda y : hasattr(y.behavior, "temperature"), self.interfaces)):
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
        return NodesGroup(members=list(chain.from_iterable(part.nodes for part in self.parts)))

    @property
    def points(self) -> "list[Point]":
        """Return a list of all node coordinates in the model."""
        return [n.point for n in self.nodes]

    @property
    def elements(self) -> "ElementsGroup":
        """Return a list of all elements in the model."""
        return ElementsGroup(members=list(chain.from_iterable(part.elements for part in self.parts)))

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
            for i, node in enumerate(self.nodes):
                node._key = i + start

            for i, element in enumerate(self.elements):
                element._key = i + start
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
        if compas_fea2.VERBOSE:
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
        new_part = part.copy()
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

    def add_material(self, material: "_Material") -> "_Material":
        """Add a material to the model.

        Parameters
        ----------
        material : :class=`compas_fea2.model.materials.Material`

        Returns
        -------
        :class=`compas_fea2.model.materials.Material`

        """
        from compas_fea2.model.materials.material import _Material

        if not isinstance(material, _Material):
            raise TypeError("{!r} is not a material.".format(material))
        material._registration = self
        material._key = len(self._materials)
        self._materials.add_member(material)
        return material

    def add_materials(self, materials: "list[_Material]") -> "list[_Material]":
        """Add multiple materials to the model.

        Parameters
        ----------
        materials : list[:class=`compas_fea2.model.materials.Material`]

        Returns
        -------
        list[:class=`compas_fea2.model.materials.Material`]

        """
        return [self.add_material(material) for material in materials]

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

    # =========================================================================
    #                           Sections methods
    # =========================================================================

    def add_section(self, section: "_Section") -> "_Section":
        """Add a section to the model.

        Parameters
        ----------
        section : :class=`compas_fea2.model.sections.Section`

        Returns
        -------
        :class=`compas_fea2.model.sections.Section`

        """
        from compas_fea2.model.sections import _Section

        if not isinstance(section, _Section):
            raise TypeError("{!r} is not a section.".format(section))
        self.add_material(section.material)
        section._registration = self
        section._key = len(self._sections)
        self._sections.add_member(section)
        return section

    def add_sections(self, sections: "list[_Section]") -> "list[_Section]":
        """Add multiple sections to the model.

        Parameters
        ----------
        sections : list[:class=`compas_fea2.model.sections.Section`]

        Returns
        -------
        list[:class=`compas_fea2.model.sections.Section`]

        """
        return [self.add_section(section) for section in sections]

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
    def add_bcs_field(self, bc_field: "_BoundaryConditionsField") -> "_BoundaryCondition":
        """Add a :class=`compas_fea2.model._BoundaryCondition` to the model.

        Parameters
        ----------
        bc : :class=`compas_fea2.model._BoundaryCondition`
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        Returns
        -------
        :class=`compas_fea2.model._BoundaryCondition`

        """
        if not isinstance(bc_field, _BoundaryConditionsField):
            raise TypeError("{!r} is not a Boundary Condition Field.".format(bc))

        for node in bc_field.distribution:
            if not isinstance(node, Node):
                raise TypeError("{!r} is not a Node.".format(node))
            if not node.part:
                raise ValueError("{!r} is not registered to any part.".format(node))
            elif node.part not in self.parts:
                raise ValueError("{!r} belongs to a part not registered to this model.".format(node))
            if isinstance(node.part, RigidPart):
                if not node.is_reference:
                    raise ValueError("For rigid parts bundary conditions can be assigned only to the reference point")
            node._bcs.add_members(bc_field.conditions)

        self._bcs_fields.add(bc_field)
        bc_field._registration = self

        return bc_field

    def add_bcs_fields(self, bc_fields: List["_BoundaryConditionsField"]) -> "_BoundaryCondition":
        for field in bc_fields:
            self.add_bcs_field(bc_field=field)
        return bc_fields

    def _add_bcfield_type(self, bc_type: str, nodes: "Union[list[Node], NodesGroup]", axes="global") -> "_BoundaryCondition":
        """Add a :class=`compas_fea2.model.BoundaryCondition` by type.

        Parameters
        ----------
        bc_type : str
            The type of boundary condition to add.
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            The nodes where the boundary condition is applied.
        axes : str, optional
            The coordinate system of the boundary condition, by default 'global'.

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
        bc = getattr(m, types[bc_type])()
        return self.add_bcs(bc, nodes, axes)

    def add_fix_bc(self, nodes, axes="global"):
        """Add a :class=`compas_fea2.model.bcs.FixedBC` to the given nodes.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        """
        return self._add_bcfield_type("fix", nodes, axes)

    def add_pin_bc(self, nodes, axes="global"):
        """Add a :class=`compas_fea2.model.bcs.PinnedBC` to the given nodes.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        """
        return self._add_bcfield_type("pin", nodes, axes)

    def add_clampXX_bc(self, nodes, axes="global"):
        """Add a :class=`compas_fea2.model.bcs.ClampBCXX` to the given nodes.

        This boundary condition clamps all degrees of freedom except rotation about the local XX-axis.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        """
        return self._add_bcfield_type("clampXX", nodes, axes)

    def add_clampYY_bc(self, nodes, axes="global"):
        """Add a :class=`compas_fea2.model.bcs.ClampBCYY` to the given nodes.

        This boundary condition clamps all degrees of freedom except rotation about the local YY-axis.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        """
        return self._add_bcfield_type("clampYY", nodes, axes)

    def add_clampZZ_bc(self, nodes, axes="global"):
        """Add a :class=`compas_fea2.model.bcs.ClampBCZZ` to the given nodes.

        This boundary condition clamps all degrees of freedom except rotation about the local ZZ-axis.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        """
        return self._add_bcfield_type("clampZZ", nodes, axes)

    def add_rollerX_bc(self, nodes, axes="global"):
        """Add a :class=`compas_fea2.model.bcs.RollerBCX` to the given nodes.

        This boundary condition clamps all degrees of freedom except displacement in the local X-direction.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        """
        return self._add_bcfield_type("rollerX", nodes, axes)

    def add_rollerY_bc(self, nodes, axes="global"):
        """Add a :class=`compas_fea2.model.bcs.RollerBCY` to the given nodes.

        This boundary condition clamps all degrees of freedom except displacement in the local Y-direction.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        """
        return self._add_bcfield_type("rollerY", nodes, axes)

    def add_rollerZ_bc(self, nodes, axes="global"):
        """Add a :class=`compas_fea2.model.bcs.RollerBCZ` to the given nodes.

        This boundary condition clamps all degrees of freedom except displacement in the local Z-direction.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] or :class=`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        """
        return self._add_bcfield_type("rollerZ", nodes, axes)

    def add_rollerXY_bc(self, nodes, axes="global"):
        """Add a :class:`compas_fea2.model.bcs.RollerBCXY` to the given nodes.

        This boundary condition allows translation along the local XY-plane.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`] or :class:`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        """
        return self._add_bc_type("rollerXY", nodes, axes)

    def add_rollerXZ_bc(self, nodes, axes="global"):
        """Add a :class:`compas_fea2.model.bcs.RollerBCXZ` to the given nodes.

        This boundary condition allows translation along the local XZ-plane.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`] or :class:`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes of the boundary condition, by default 'global'.

        """
        return self._add_bc_type("rollerXZ", nodes, axes)

    def add_rollerYZ_bc(self, nodes, axes="global"):
        """Add a :class:`compas_fea2.model.bcs.RollerBCYZ` to the given nodes.

        This boundary condition allows translation along the local YZ-plane.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`] or :class:`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes_ of the boundary condition, by default 'global'.

        """
        return self._add_bc_type("rollerYZ", nodes, axes)
    
    def add_thermal_bc(
        self,
        nodes: "Union[list[Node], NodesGroup]",
        temperature: "float",
    ) -> "_ThermalBoundaryCondition":
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

        it = ImposedTemperature(temp=temperature)
        if isinstance(nodes, _Group):
            nodeset = nodes.members
        else:
            nodeset = set(nodes)
        return self.add_bcs(it, nodeset)

    def add_imposedHeatFlux_bc(self, q, surface, axes="global"):
        """Add a :class:`compas_fea2.model.bcs.RollerBCYZ` to the given nodes.

        This boundary condition allows translation along the local YZ-plane.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`] or :class:`compas_fea2.model.NodesGroup`
            List or Group with the nodes where the boundary condition is assigned.
        axes : str, optional
            Axes_ of the boundary condition, by default 'global'.

        """
        from compas_fea2.model.groups import FacesGroup
        m = importlib.import_module("compas_fea2.model.bcs")
        bc = getattr(m, "ImposedHeatFlux")
        dic = {}
        for face in surface :
            if face.part in dic :
                dic[face.part].add_face(face)
            else :
                dic[face.part] = FacesGroup(faces=[face])
        for part, faces in dic.items():
            part.add_group(faces)
            self.add_bcs(bc(q, faces), faces.nodes)

    def remove_bcs(self, nodes):
        """Release nodes that were previously restrained.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`]
            List of nodes to release.

        None

        """
        for _, nodes in self.bcs.items():
            self.remove_bcs(nodes)

        if isinstance(nodes, Node):
            nodes = [nodes]

        for node in nodes:
            node.bcs=set()
            if node.dof:
                self.bcs[node.dof].remove(node)
                node.dof = None
            else:
                print("WARNING: {!r} was not restrained. skipped!".format(node))
        
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

        if not isinstance(ic_field, _InitialConditionField):
            raise TypeError("{!r} is not an Initial Condition Field.".format(ic_field))

        for node in ic_field.distribution:
            if not isinstance(node, Node):
                raise TypeError("{!r} is not a Node.".format(node))
            if not node.part:
                raise ValueError("{!r} is not registered to any part.".format(node))
            elif node.part not in self.parts:
                raise ValueError("{!r} belongs to a part not registered to this model.".format(node))
            if isinstance(node.part, RigidPart):
                if not node.is_reference:
                    raise ValueError("For rigid parts bundary conditions can be assigned only to the reference point")
            node._bcs.add_members(ic_field.conditions)

        self._ics_fields.add(ic_field)
        ic_field._registration = self

        return ic_field

    def add_ics_fields(self, ics_fields: list["_InitialConditionField"]) -> list["_InitialConditionField"]:
        for ics_field in ics_fields:
            self.add_ics_field(ics_field)
        return ics_field

    def add_uniform_thermal_ics_field(self, T0: float, nodes) -> InitialTemperatureField:
        return self.add_ics_field(InitialTemperatureField(nodes=nodes, conditions=InitialTemperature(T0=T0)))

    # =========================================================================
    #                           Constraints methods
    # =========================================================================
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
        if not isinstance(interaction, _Interaction):
            raise TypeError("{!r} is not an interaction.".format(interaction))
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

    def add_interface(self, interface):
        """
            :class:`compas_fea2.model.Interface`

        """
        if not isinstance(interface, _Interface):
            raise TypeError("{!r} is not an Interface.".format(interface))
        self._interfaces.add(interface)
        interface._registration = self
        return interface

    def add_interfaces(self, interfaces):
        """Add multiple :class:`compas_fea2.model.Interface` objects to the model.
        """
        return [self.add_interface(interface) for interface in interfaces]
    # =========================================================================
    #                           Problems methods
    # =========================================================================
    def add_problem(self, problem: "Problem") -> "Problem":
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
            parts_info.append(
                "{:<15} - #nodes: {:<5} #elements: {:<5} #mat: {:<5} #sect: {:<5}".format(part.name, len(part.nodes), len(part.elements), len(part.materials), len(part.sections))
            )

        bcs_info = []
        for field in self.bcs_fields:
            bcs_info.append("{!r} - # of restrained nodes {}".format(field.conditions[0], len(field.distribution)))

        ics_info = []
        for field in self.ics_fields:
            ics_info.append("{!r} - # of restrained nodes {}".format(field.conditions[0], len(field.distribution)))

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
        self._bcs_fields.clear()
        self._ics_fields.clear()
        self._constraints.clear()
        self._connectors.clear()
        self._interfaces.members.clear()
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
