from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Optional

from compas.geometry import Frame

from compas_fea2.base import FEAData
from compas_fea2.base import Frameable
from compas_fea2.base import Registry
from compas_fea2.base import from_data

if TYPE_CHECKING:
    pass

docs = """
Note
----
BoundaryConditions are registered to a :class:`compas_fea2.model.Model`.


Parameters
----------
name : str, optional
    Unique identifier. If not provided it is automatically generated. Set a
    name if you want a more human-readable input file.
frame : :class:`compas.geometry.Frame`, optional
    The reference frame for the boundary condition. Defaults to the world XY plane.
    
Warning
-------
The frame is a WIP feature and may change in future versions.

Attributes
----------
name : str
    Unique identifier.
x : bool
    Restrain translations along the x axis.
y : bool
    Restrain translations along the y axis.
z : bool
    Restrain translations along the z axis.
xx : bool
    Restrain rotations around the x axis.
yy : bool
    Restrain rotations around the y axis.
zz : bool
    Restrain rotations around the z axis.
frame : :class:`compas.geometry.Frame`
    The reference frame for the boundary condition.
"""


class _BoundaryCondition(FEAData):
    """Base class for all boundary conditions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MechanicalBC(_BoundaryCondition, Frameable):
    """Base class for all zero-valued mechanical boundary conditions.

    Users set local DOF restraints with lowercase (x,y,z,xx,yy,zz). If no
    frame is provided the global frame is used (local == global). Uppercase
    (X,Y,Z,XX,YY,ZZ) are derived GLOBAL restraints: a global axis is
    restrained only if every contributing local axis (non-zero directional
    cosine) is locally restrained.
    """

    __doc__ = __doc__ or ""
    __doc__ += docs

    DOF_MASK: Dict[str, bool] | None = None

    def __init__(self, x: bool = False, y: bool = False, z: bool = False, xx: bool = False, yy: bool = False, zz: bool = False, frame: Frame | None = None, **kwargs):
        _BoundaryCondition.__init__(self, **kwargs)
        Frameable.__init__(self, frame=frame)
        self._x = x
        self._y = y
        self._z = z
        self._xx = xx
        self._yy = yy
        self._zz = zz

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data.update(
            {
                "frame": self._frame_data(),
                "x": self._x,
                "y": self._y,
                "z": self._z,
                "xx": self._xx,
                "yy": self._yy,
                "zz": self._zz,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls: type["MechanicalBC"], data: dict, registry: Optional[Registry] = None, duplicate=True) -> "MechanicalBC":
        frame_obj = None
        frame_data = data.get("frame")
        if frame_data:
            try:
                # Try compas Frame deserialization patterns
                if hasattr(Frame, "__from_data__"):
                    frame_obj = Frame.__from_data__(frame_data)  # type: ignore[attr-defined]
                elif hasattr(Frame, "from_data"):
                    frame_obj = Frame.from_data(frame_data)  # type: ignore[attr-defined]
            except Exception:
                frame_obj = None
        frame: Frame | None = frame_obj if isinstance(frame_obj, Frame) else None
        bc = cls(frame=frame)
        bc._x = data.get("x", False)
        bc._y = data.get("y", False)
        bc._z = data.get("z", False)
        bc._xx = data.get("xx", False)
        bc._yy = data.get("yy", False)
        bc._zz = data.get("zz", False)
        mask = getattr(cls, "DOF_MASK", None)
        if mask:
            for k, v in mask.items():
                setattr(bc, f"_{k}", v)
        return bc

    def __add__(self, other: "MechanicalBC") -> "MechanicalBC":
        """Combine two boundary conditions by OR-ing their component restraints."""
        if not isinstance(other, MechanicalBC):
            return NotImplemented
        if self.frame != other.frame:
            raise ValueError(f"Cannot combine BCs with different frame: {self.frame!r} vs {other.frame!r}")
        combined = MechanicalBC(
            x=self.x or other.x,
            y=self.y or other.y,
            z=self.z or other.z,
            xx=self.xx or other.xx,
            yy=self.yy or other.yy,
            zz=self.zz or other.zz,
            frame=self._frame,
        )
        return combined

    @property
    def x(self) -> bool:
        """Return the local x restraint boolean."""
        return self._x

    @property
    def y(self) -> bool:
        """Return the local y restraint boolean."""
        return self._y

    @property
    def z(self) -> bool:
        """Return the local z restraint boolean."""
        return self._z

    @property
    def xx(self) -> bool:
        """Return the local xx restraint boolean."""
        return self._xx

    @property
    def yy(self) -> bool:
        """Return the local yy restraint boolean."""
        return self._yy

    @property
    def zz(self) -> bool:
        """Return the local zz restraint boolean."""
        return self._zz

    @property
    def components(self) -> Dict[str, Any]:
        """Return the local restraint booleans."""
        return {c: getattr(self, c) for c in ["x", "y", "z", "xx", "yy", "zz"]}

    @property
    def global_components(self) -> Dict[str, bool]:
        """Return the global (uppercase) restraint booleans."""
        return {c: getattr(self, c) for c in ["X", "Y", "Z", "XX", "YY", "ZZ"]}

    def _global_axis_restrained(self, axis: str, tol: float = 1e-12) -> bool:
        from compas.geometry import Vector

        # Fast path if local == global
        if not self.has_local_frame or self.is_axis_aligned():
            mapping = {"X": self._x, "Y": self._y, "Z": self._z, "XX": self._xx, "YY": self._yy, "ZZ": self._zz}
            return mapping[axis]
        lx, ly, lz = self.direction_cosines()  # local axes as global vectors
        if axis in ("X", "Y", "Z"):
            g = {"X": Vector(1, 0, 0), "Y": Vector(0, 1, 0), "Z": Vector(0, 0, 1)}[axis]
            coeffs = [g.dot(lx), g.dot(ly), g.dot(lz)]
            flags = [self._x, self._y, self._z]
        else:  # rotational analogous mapping
            g = {"XX": Vector(1, 0, 0), "YY": Vector(0, 1, 0), "ZZ": Vector(0, 0, 1)}[axis]
            coeffs = [g.dot(lx), g.dot(ly), g.dot(lz)]
            flags = [self._xx, self._yy, self._zz]
        for c, f in zip(coeffs, flags):
            if abs(c) > tol and not f:
                return False
        return True

    @property
    def X(self) -> bool:
        """Return the global X restraint boolean."""
        return self._global_axis_restrained("X")

    @property
    def Y(self) -> bool:
        """Return the global Y restraint boolean."""
        return self._global_axis_restrained("Y")

    @property
    def Z(self) -> bool:
        """Return the global Z restraint boolean."""
        return self._global_axis_restrained("Z")

    @property
    def XX(self) -> bool:
        """Return the global XX restraint boolean."""
        return self._global_axis_restrained("XX")

    @property
    def YY(self) -> bool:
        """Return the global YY restraint boolean."""
        return self._global_axis_restrained("YY")

    @property
    def ZZ(self) -> bool:
        """Return the global ZZ restraint boolean."""
        return self._global_axis_restrained("ZZ")

    def global_constraint_equations(self) -> list[tuple[Dict[str, float], float]]:
        """Return linear constraint equations in global translational DOFs implied by local restraints.

        Each equation corresponds to a local restrained translational DOF.
        Equation format: ( { 'UX': a, 'UY': b, 'UZ': c }, 0.0 ) meaning
        a*UX + b*UY + c*UZ = 0.
        Rotational mapping can be extended similarly when needed.
        """
        eqs: list[tuple[Dict[str, float], float]] = []
        if not any([self._x, self._y, self._z]):
            return eqs
        lx, ly, lz = self.direction_cosines()
        eq_map = [(self._x, lx), (self._y, ly), (self._z, lz)]
        for flag, vec in eq_map:
            if flag:
                eqs.append(({"UX": float(vec.x), "UY": float(vec.y), "UZ": float(vec.z)}, 0.0))
        return eqs


class GeneralBC(MechanicalBC):
    """Customized boundary condition."""

    __doc__ = __doc__ or ""
    __doc__ += docs

    __doc__ += """
Additional Parameters
---------------------
x : bool
    Restrain translations along the x axis.
y : bool
    Restrain translations along the y axis.
z : bool
    Restrain translations along the z axis.
xx : bool
    Restrain rotations around the x axis.
yy : bool
    Restrain rotations around the y axis.
zz : bool
    Restrain rotations around the z axis.
    """

    def __init__(self, x: bool = False, y: bool = False, z: bool = False, xx: bool = False, yy: bool = False, zz: bool = False, **kwargs):
        super().__init__(x=x, y=y, z=z, xx=xx, yy=yy, zz=zz, **kwargs)


class FixedBC(MechanicalBC):
    """A fixed nodal displacement boundary condition."""

    DOF_MASK = dict(x=True, y=True, z=True, xx=True, yy=True, zz=True)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=True, y=True, z=True, xx=True, yy=True, zz=True, **kwargs)


class FixedBCX(MechanicalBC):
    """A fixed nodal displacement boundary condition along and around X."""

    DOF_MASK = dict(x=True, y=False, z=False, xx=True, yy=False, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=True, y=False, z=False, xx=True, yy=False, zz=False, **kwargs)


class FixedBCY(MechanicalBC):
    """A fixed nodal displacement boundary condition along and around Y."""

    DOF_MASK = dict(x=False, y=True, z=False, xx=False, yy=True, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=False, y=True, z=False, xx=False, yy=True, zz=False, **kwargs)


class FixedBCZ(MechanicalBC):
    """A fixed nodal displacement boundary condition along and around Z."""

    DOF_MASK = dict(x=False, y=False, z=True, xx=False, yy=False, zz=True)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=False, y=False, z=True, xx=False, yy=False, zz=True, **kwargs)


class PinnedBC(MechanicalBC):
    """A pinned nodal displacement boundary condition."""

    DOF_MASK = dict(x=True, y=True, z=True, xx=False, yy=False, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=True, y=True, z=True, **kwargs)


class ClampBCXX(MechanicalBC):
    """A pinned nodal displacement boundary condition clamped in XX."""

    DOF_MASK = dict(x=True, y=True, z=True, xx=True, yy=False, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=True, y=True, z=True, xx=True, **kwargs)


class ClampBCYY(MechanicalBC):
    """A pinned nodal displacement boundary condition clamped in YY."""

    DOF_MASK = dict(x=True, y=True, z=True, xx=False, yy=True, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=True, y=True, z=True, yy=True, **kwargs)


class ClampBCZZ(MechanicalBC):
    """A pinned nodal displacement boundary condition clamped in ZZ."""

    DOF_MASK = dict(x=True, y=True, z=True, xx=False, yy=False, zz=True)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=True, y=True, z=True, zz=True, **kwargs)


class RollerBCX(MechanicalBC):
    """A pinned nodal displacement boundary condition released in X."""

    DOF_MASK = dict(x=False, y=True, z=True, xx=False, yy=False, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=False, y=True, z=True, **kwargs)


class RollerBCY(MechanicalBC):
    """A pinned nodal displacement boundary condition released in Y."""

    DOF_MASK = dict(x=True, y=False, z=True, xx=False, yy=False, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=True, y=False, z=True, **kwargs)


class RollerBCZ(MechanicalBC):
    """A pinned nodal displacement boundary condition released in Z."""

    DOF_MASK = dict(x=True, y=True, z=False, xx=False, yy=False, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=True, y=True, z=False, **kwargs)


class RollerBCXY(MechanicalBC):
    """A pinned nodal displacement boundary condition released in X and Y."""

    DOF_MASK = dict(x=False, y=False, z=True, xx=False, yy=False, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=False, y=False, z=True, **kwargs)


class RollerBCYZ(MechanicalBC):
    """A pinned nodal displacement boundary condition released in Y and Z."""

    DOF_MASK = dict(x=True, y=False, z=False, xx=False, yy=False, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=True, y=False, z=False, **kwargs)


class RollerBCXZ(MechanicalBC):
    """A pinned nodal displacement boundary condition released in X and Z."""

    DOF_MASK = dict(x=False, y=True, z=False, xx=False, yy=False, zz=False)

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(x=False, y=True, z=False, **kwargs)


# ===================================================================
# HEAT ANALYSIS
# ===================================================================


class _ThermalBoundaryCondition(_BoundaryCondition):
    """Base class for thermal boundary conditions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ImposedTemperature(_ThermalBoundaryCondition):
    """Imposed temperature condition for analysis involving temperature.

        Additional Parameters
    ---------------------
    temperature : float
        Value of imposed temperature applied
    """

    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, temperature: float, **kwargs):
        super().__init__(**kwargs)
        self._temperature = float(temperature)

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        data.update({"temperature": self._temperature})
        return data

    @from_data
    @classmethod
    def __from_data__(cls: type["ImposedTemperature"], data: Dict[str, Any], registry: Optional[Registry] = None, duplicate=True) -> "ImposedTemperature":
        temperature = data.get("temperature")
        if temperature is None:
            raise ValueError("ImposedTemperature requires a 'temperature' value in the data.")
        obj = cls(temperature=float(temperature))
        return obj
