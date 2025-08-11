from typing import Any
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

from uuid import UUID

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data

if TYPE_CHECKING:
    from compas_fea2.model.model import Model

docs = """
Note
----
BoundaryConditions are registered to a :class:`compas_fea2.model.Model`.

Warning
-------
The `axes` parameter is WIP. Currently only global axes can be used.

Parameters
----------
name : str, optional
    Unique identifier. If not provided it is automatically generated. Set a
    name if you want a more human-readable input file.
axes : str, optional
    The reference axes.

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
axes : str
    The reference axes.
"""


class _BoundaryCondition(FEAData):
    """Base class for all boundary conditions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def registration(self) -> Optional["Model"]:
        """Get the object where this object is registered to."""
        return self._registration

    @registration.setter
    def registration(self, value: "Model") -> None:
        """Set the object where this object is registered to."""
        self._registration = value


class MechanicalBC(_BoundaryCondition):
    """Base class for all zero-valued mechanical boundary conditions."""

    __doc__ = __doc__ or ""
    __doc__ += docs

    DOF_MASK: Dict[str, bool] | None = None

    def __init__(self, x: bool = False, y: bool = False, z: bool = False, xx: bool = False, yy: bool = False, zz: bool = False, axes: str = "global", **kwargs):
        super().__init__(**kwargs)
        self._axes = axes
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
                "axes": self._axes,
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
    def __from_data__(cls: type["MechanicalBC"], data: dict, registry: Optional[Registry] = None) -> "MechanicalBC":
        bc = cls(axes=data.get("axes", "global"))
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
        if self.axes != other.axes:
            raise ValueError(f"Cannot combine BCs with different axes: {self.axes!r} vs {other.axes!r}")
        combined = MechanicalBC(
            x=self.x or other.x,
            y=self.y or other.y,
            z=self.z or other.z,
            xx=self.xx or other.xx,
            yy=self.yy or other.yy,
            zz=self.zz or other.zz,
            axes=self.axes,
        )
        return combined

    @property
    def x(self) -> bool:
        return self._x

    @property
    def y(self) -> bool:
        return self._y

    @property
    def z(self) -> bool:
        return self._z

    @property
    def xx(self) -> bool:
        return self._xx

    @property
    def yy(self) -> bool:
        return self._yy

    @property
    def zz(self) -> bool:
        return self._zz

    @property
    def axes(self) -> str:
        return self._axes

    @axes.setter
    def axes(self, value: str):
        self._axes = value

    @property
    def components(self) -> Dict[str, Any]:
        return {c: getattr(self, c) for c in ["x", "y", "z", "xx", "yy", "zz"]}


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
    def __from_data__(cls: type["ImposedTemperature"], data: Dict[str, Any], registry: Optional[Registry] = None) -> "ImposedTemperature":
        temperature = data.get("temperature")
        if temperature is None:
            raise ValueError("ImposedTemperature requires a 'temperature' value in the data.")
        obj = cls(temperature=float(temperature))
        return obj
