from typing import TYPE_CHECKING
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

from compas.geometry import Point
from compas.geometry import transform_points
from compas.tolerance import TOL

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.config import settings
from compas_fea2.units import _strip_magnitudes
from compas_fea2.units import units_io

if TYPE_CHECKING:
    from compas_fea2.model.model import Model
    from compas_fea2.model.parts import _Part
    from compas_fea2.results import DisplacementResult
    from compas_fea2.results import ReactionResult
    from compas_fea2.results import TemperatureResult


def _parse_mass(mass) -> list[float]:
    """Parse the user‐provided mass into a 6‐element list [mx, my, mz, ixx, iyy, izz]."""
    if mass is None:
        return [0.0] * 6
    if isinstance(mass, float):
        return [mass, mass, mass, 0.0, 0.0, 0.0]

    if isinstance(mass, Sequence):
        seq = [float(m) for m in mass]
        if len(seq) == 3:
            # translational only
            return seq + [0.0, 0.0, 0.0]
        if len(seq) == 6:
            return seq
    raise TypeError("mass must be None, a number, a 3‐element sequence (mx,my,mz), or a 6‐element sequence (mx,my,mz,ixx,iyy,izz).")


class Node(FEAData):
    """Class representing a Node object.

    Parameters
    ----------
    xyz : list[float, float, float] | :class:`compas.geometry.Point`
        The location of the node in the global coordinate system.
    mass : float, tuple, or list, optional
        Lumped nodal mass. If float, same value is used in x,y,z. If sequence of length 3, interpreted as (mx,my,mz). All values in the active unit system ("mass"). Default None.
    temperature : float, optional
        Initial temperature at the node, in the active unit system ("temperature").
    name : str, optional
        Unique identifier. If not provided, it is automatically generated. Set a
        name if you want a more human-readable input file.

    Attributes
    ----------
    name : str
        Unique identifier.
    mass : tuple
        Lumped nodal mass (mx,my,mz) in active mass units.
    key : str, read-only
        The identifier of the node.
    xyz : list[float]
        The location of the node in the global coordinate system.
    x : float
        The X coordinate.
    y : float
        The Y coordinate.
    z : float
        The Z coordinate.
    gkey : str, read-only
        The geometric key of the Node.
    dof : dict
        Dictionary with the active degrees of freedom.
    on_boundary : bool | None, read-only
        `True` if the node is on the boundary mesh of the part, `False`
        otherwise, by default `None`.
    is_reference : bool, read-only
        `True` if the node is a reference point of :class:`compas_fea2.model.RigidPart`,
        `False` otherwise.
    part : :class:`compas_fea2.model._Part`, read-only
        The Part where the element is assigned.
    model : :class:`compas_fea2.model.Model`, read-only
        The Model where the element is assigned.
    point : :class:`compas.geometry.Point`
        The Point equivalent of the Node.
    temperature : float
        Temperature at the Node (active temperature units).

    Notes
    -----
    Nodes are registered to a :class:`compas_fea2.model.Part` object and can
    belong to only one Part. Every time a node is added to a Part, it gets
    registered to that Part.

    All physical attributes are interpreted in the active unit system.

    Examples
    --------
    >>> node = Node(xyz=(1.0, 2.0, 3.0), mass=10.0, temperature=293.15)

    """

    @units_io(types_in=(("length","length","length"), "mass", "temperature"), types_out=None)
    def __init__(self, xyz: Sequence[float], mass: Optional[Union[float, List[float]]] = None, temperature: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)
        self._part_key: Optional[int] = None

        self._xyz = xyz
        self._x = xyz[0]
        self._y = xyz[1]
        self._z = xyz[2]

        self._dof = {"x": True, "y": True, "z": True, "xx": True, "yy": True, "zz": True, "temperature": True, "q": True}

        self._mass = _parse_mass(mass)
        self._temperature = temperature
        self._on_boundary = None
        self._is_reference = False
        # self._connected_elements = set()

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "part_key": self._part_key,
                "xyz": self.xyz,
                "x": self._x,
                "y": self._y,
                "z": self._z,
                "dof": self._dof,
                "mass": self._mass,
                "temperature": self._temperature,
                "on_boundary": self._on_boundary,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        node = cls(
            xyz=data["xyz"],
            mass=data.get("mass"),
            temperature=data.get("temperature"),
        )
        node._on_boundary = data.get("on_boundary")
        node._is_reference = data.get("is_reference")
        return node

    @classmethod
    def from_compas_point(cls, point: Point, mass: Optional[float] = None, temperature: Optional[float] = None) -> "Node":
        """Create a Node from a :class:`compas.geometry.Point`.

        Parameters
        ----------
        point : :class:`compas.geometry.Point`
            The location of the node in the global coordinate system.
        mass : float or tuple, optional
            Lumped nodal mass, by default ``None``. If ``float``, the same value is
            used in all 3 directions. If you want to specify a different mass for each
            direction, provide a ``tuple`` as (mass_x, mass_y, mass_z) in global
            coordinates.
        temperature : float, optional
            The temperature at the Node.
        name : str, optional
            Unique identifier. If not provided, it is automatically generated. Set a
            name if you want a more human-readable input file.

        Returns
        -------
        :class:`compas_fea2.model.Node`
            The Node object.

        Examples
        --------
        >>> from compas.geometry import Point
        >>> point = Point(1.0, 2.0, 3.0)
        >>> node = Node.from_compas_point(point)

        """
        return cls(xyz=[point.x, point.y, point.z], mass=mass, temperature=temperature)

    @property
    def part(self) -> "_Part | None":
        """The Part where the Node is registered."""
        return self._registration

    @property
    def model(self) -> "Model | None":
        if self.part:
            return self.part._registration

    @property
    def part_key(self) -> int | None:
        """The key of the node at the part level."""
        return self._part_key

    @property
    @units_io(types_in=(), types_out=("length","length","length"))
    def xyz(self) -> List[float]:
        """Coordinates [x,y,z] in active length units."""
        return [self._x, self._y, self._z]

    @xyz.setter
    def xyz(self, value: List[float]):
        if len(value) != 3:
            raise ValueError("Provide a 3 element tuple or list")
        self._x = value[0]
        self._y = value[1]
        self._z = value[2]

    @property
    @units_io(types_in=(), types_out="length")
    def x(self) -> float:
        return self._x

    @x.setter
    @units_io(types_in=("length",), types_out=None)
    def x(self, value: float):
        self._x = float(value)

    @property
    @units_io(types_in=(), types_out="length")
    def y(self) -> float:
        return self._y

    @y.setter
    @units_io(types_in=("length",), types_out=None)
    def y(self, value: float):
        self._y = float(value)

    @property
    @units_io(types_in=(), types_out="length")
    def z(self) -> float:
        return self._z

    @z.setter
    @units_io(types_in=("length",), types_out=None)
    def z(self, value: float):
        self._z = float(value)

    @property
    @units_io(types_in=(), types_out=("mass","mass","mass","mass","mass","mass"))
    def mass(self) -> Sequence[float]:
        return self._mass

    @mass.setter
    @units_io(types_in=(("mass",),), types_out=None)
    def mass(self, value: float | Sequence[float]):
        self._mass = _parse_mass(value)

    @property
    @units_io(types_in=(), types_out="temperature")
    def t0(self) -> float | None:
        return self._temperature

    @t0.setter
    @units_io(types_in=("temperature",), types_out=None)
    def t0(self, value: float):
        self._temperature = value

    @property
    def gkey(self) -> str | None:
        if TOL:
            return TOL.geometric_key(self.xyz, precision=settings.PRECISION)

    @property
    def on_boundary(self) -> Optional[bool]:
        return self._on_boundary

    @property
    def is_reference(self) -> bool:
        return self._is_reference

    @property
    def point(self) -> Point:
        return Point(*_strip_magnitudes(self.xyz))

    @property
    def connected_elements(self) -> Optional[Dict]:
        if self.part:
            if self.part.elements:
                return self.part.elements.group_by(key=lambda e: self in e.nodes)
        else:
            raise ValueError("Node is not registered to a Part.")

    def transform(self, transformation) -> None:
        """Transform the node using a transformation matrix.

        Parameters
        ----------
        transformation : list
            A 4x4 transformation matrix.
        """
        self.xyz = transform_points([self.xyz], transformation)[0]  # type: ignore

    def transformed(self, transformation):
        """Return a copy of the node transformed by a transformation matrix.

        Parameters
        ----------
        transformation : list
            A 4x4 transformation matrix.

        Returns
        -------
        :class:`compas_fea2.model.Node`
            A new node object with the transformed coordinates.
        """
        node = self.copy()
        node.transform(transformation)
        return node

    # ==============================================================================
    # Results
    # ==============================================================================

    def displacement(self, step):
        """Get the displacement of the node at a given step.

        Parameters
        ----------
        step : :class:`compas_fea2.model.Step`
            The step for which to get the displacement.

        Returns
        -------
        :class:`compas_fea2.results.DisplacementResult`
            The displacement result at the node for the given step.
        """
        if step.displacement_field:
            return step.displacement_field.get_result_at(location=self)

    def displacements(self, problem) -> "List[DisplacementResult]":
        """Get the displacements of the node for all steps in the model."""
        steps = problem.steps_order
        displacements = []
        for step in steps:
            if step.displacement_field:
                displacements.append(self.displacement(step))
            else:
                raise ValueError(f"Step {step.name} does not have a displacement field.")
        return displacements

    def reaction(self, step) -> "ReactionResult | None":
        """Get the reaction of the node at a given step.

        Parameters
        ----------
        step : :class:`compas_fea2.model.Step`
            The step for which to get the reaction.

        Returns
        -------
        :class:`compas_fea2.results.ReactionResult`
            The reaction result at the node for the given step.
        """

        if step.reaction_field:
            return step.reaction_field.get_result_at(location=self)

    def reactions(self, problem) -> "List[ReactionResult]":
        """Get the reactions of the node for all steps in the model."""
        steps = problem.steps_order
        reactions = []
        for step in steps:
            if step.reaction_field:
                reactions.append(self.reaction(step))
            else:
                raise ValueError(f"Step {step.name}does not have a reaction field.")
        return reactions

    def temperature(self, step):
        """Get the temperature of the node at a given step.

        Parameters
        ----------
        step : :class:`compas_fea2.model.Step`
            The step for which to get the temperature.

        Returns
        -------
        :class:`compas_fea2.results.TemperatureResult`
            The temperature result at the node for the given step.
        """
        if step.temperature_field:
            return step.temperature_field.get_result_at(location=self)

    def temperatures(self, problem) -> "List[TemperatureResult]":
        """Get the temperatures of the node for all steps in the model."""
        steps = problem.steps_order
        temperatures = []
        for step in steps:
            if step.temperature_field:
                temperatures.append(self.temperature(step))
            else:
                raise ValueError(f"Step {step.name} does not have a temperature field.")
        return temperatures
