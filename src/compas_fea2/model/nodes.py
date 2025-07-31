from typing import Dict
from typing import List
from typing import Sequence
from typing import Optional
from typing import Union
from typing import TYPE_CHECKING

import numbers

from compas.geometry import Point
from compas.geometry import transform_points
from compas.tolerance import TOL

import compas_fea2
from compas_fea2.base import FEAData
from compas_fea2.model.bcs import _BoundaryCondition
from compas_fea2.model.bcs import GeneralBC

if TYPE_CHECKING:
    from compas_fea2.model.parts import _Part
    from compas_fea2.model.model import Model
    from compas_fea2.problem.steps import _Step
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
    raise TypeError("mass must be None, a number, a 3‐element sequence (mx,my,mz), " "or a 6‐element sequence (mx,my,mz,ixx,iyy,izz).")


class Node(FEAData):
    """Class representing a Node object.

    Parameters
    ----------
    xyz : list[float, float, float] | :class:`compas.geometry.Point`
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

    Attributes
    ----------
    name : str
        Unique identifier.
    mass : tuple
        Lumped nodal mass in the 3 global directions (mass_x, mass_y, mass_z).
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
        The temperature at the Node.

    Notes
    -----
    Nodes are registered to a :class:`compas_fea2.model.Part` object and can
    belong to only one Part. Every time a node is added to a Part, it gets
    registered to that Part.

    Examples
    --------
    >>> node = Node(xyz=(1.0, 2.0, 3.0))

    """
    
    _registration: Optional["_Part"]

    def __init__(self, xyz: Sequence[float], mass: Optional[Union[float, List[float]]] = None, temperature: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)
        self._registration: Optional["_Part"] = None
        self._key: Optional[int] = None
        self._part_key: Optional[int] = None

        self._xyz = xyz
        self._x = xyz[0]
        self._y = xyz[1]
        self._z = xyz[2]

        self._dof = {"x": True, "y": True, "z": True, "xx": True, "yy": True, "zz": True}

        self._bcs = set()
        self._mass = _parse_mass(mass)
        self._temperature = temperature

        self._on_boundary = None
        self._is_reference = False

        self._loads = {}
        self._total_load = None

        self._connected_elements = set()

    @property
    def __data__(self):
        return {
            "class": self.__class__.__base__,
            "part_key": self._part_key,
            "uid": self.uid,
            "xyz": self.xyz,
            "mass": self._mass,
            "temperature": self._temperature,
            "on_boundary": self._on_boundary,
            "is_reference": self._is_reference,
        }

    @classmethod
    def __from_data__(cls, data):
        node = cls(
            xyz=data["xyz"],
            mass=data.get("mass"),
            temperature=data.get("temperature"),
        )
        node.uid = data.get("uid")
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
    def xyz(self) -> List[float]:
        return [self._x, self._y, self._z]

    @xyz.setter
    def xyz(self, value: List[float]):
        if len(value) != 3:
            raise ValueError("Provide a 3 element tuple or list")
        self._x = value[0]
        self._y = value[1]
        self._z = value[2]

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float):
        self._x = float(value)

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float):
        self._y = float(value)

    @property
    def z(self) -> float:
        return self._z

    @z.setter
    def z(self, value: float):
        self._z = float(value)

    @property
    def mass(self) -> Sequence[float]:
        return self._mass

    @mass.setter
    def mass(self, value: float | Sequence[float]):
        self._mass = _parse_mass(value)

    @property
    def t0(self) -> float | None:
        return self._temperature

    @t0.setter
    def t0(self, value: float):
        self._temperature = value

    @property
    def gkey(self) -> str | None:
        if TOL:
            return TOL.geometric_key(self.xyz, precision=compas_fea2.PRECISION)

    @property
    def dof(self) -> Dict[str, bool]:
        """Dictionary with the active degrees of freedom."""
        gen_bc = GeneralBC()
        for bc in self._bcs:
            gen_bc += bc
        return {attr: not bool(getattr(gen_bc, attr)) for attr in ["x", "y", "z", "xx", "yy", "zz"]}

    @property
    def bcs(self):
        """List of boundary conditions applied to the node."""
        return self._bcs

    @property
    def on_boundary(self) -> Optional[bool]:
        return self._on_boundary

    @property
    def is_reference(self) -> bool:
        return self._is_reference

    @property
    def point(self) -> Point:
        return Point(*self.xyz)

    @property
    def connected_elements(self) -> set:
        return self._connected_elements

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
    # BCs Methods
    # ==============================================================================
    def add_bc(self, bc):
        """Add a boundary condition to the node.

        Parameters
        ----------
        bc : :class:`compas_fea2.model.bcs.BoundaryCondition`
            The boundary condition to add.
        """
        if self.part is None:
            raise ValueError("Node must be registered to a part before adding boundary conditions.")
        self.part.add_bc(nodes=[self], bc=bc)

    def add_bcs(self, bcs: Sequence[_BoundaryCondition]) -> None:
        """Add multiple boundary conditions to the node.

        Parameters
        ----------
        bcs : Sequence[:class:`compas_fea2.model.bcs.BoundaryCondition`]
            A sequence of boundary conditions to add.
        """
        for bc in bcs:
            self.add_bc(bc)

    def remove_bc(self, bc):
        """Remove a boundary condition from the node.

        Parameters
        ----------
        bc : :class:`compas_fea2.model.bcs.BoundaryCondition`
            The boundary condition to remove.
        """
        if not isinstance(bc, _BoundaryCondition):
            raise TypeError("Boundary condition must be an instance of _BoundaryCondition")
        self._bcs.discard(bc)

    def remove_bcs(self, bcs: Sequence[_BoundaryCondition]) -> None:
        """Remove multiple boundary conditions from the node.

        Parameters
        ----------
        bcs : Sequence[:class:`compas_fea2.model.bcs.BoundaryCondition`]
            A sequence of boundary conditions to remove.
        """
        for bc in bcs:
            self.remove_bc(bc)

    # ==============================================================================
    # Results
    # ==============================================================================
    @property
    def results_cls(self):
        """Return a dictionary of result classes associated with the node."""
        from compas_fea2.results import DisplacementResult
        from compas_fea2.results import ReactionResult
        from compas_fea2.results import TemperatureResult

        return {"u": DisplacementResult, "rf": ReactionResult, "t": TemperatureResult}

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
