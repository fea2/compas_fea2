from typing import Dict
from typing import Optional
from typing import Any

from compas_fea2.base import FEAData

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
temp : float (False otherwise)
    Imposed temperature for heat analysis.
components : dict
    Dictionary with component-value pairs summarizing the boundary condition.
axes : str
    The reference axes.
"""


class _BoundaryCondition(FEAData):
    """Base class for all zero-valued boundary conditions."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, axes: str = "global", **kwargs):
        super().__init__(**kwargs)
        self._axes = axes
        self._x = False
        self._y = False
        self._z = False
        self._xx = False
        self._yy = False
        self._zz = False
        self._temp = False

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
    def temp(self) -> bool:
        return self._temp

    @property
    def axes(self) -> str:
        return self._axes

    @axes.setter
    def axes(self, value: str):
        self._axes = value

    @property
    def components(self) -> Dict[str, bool]:
        return {c: getattr(self, c) for c in ["x", "y", "z", "xx", "yy", "zz"]}

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data.update({
            "axes": self._axes,
            "x": self._x,
            "y": self._y,
            "z": self._z,
            "xx": self._xx,
            "yy": self._yy,
            "zz": self._zz,
            "temp": self._temp,
        })
        return data

    @classmethod
    def __from_data__(cls, data: dict):
        bc = cls(axes=data.get("axes", "global"))
        bc._x = data.get("x", False)
        bc._y = data.get("y", False)
        bc._z = data.get("z", False)
        bc._xx = data.get("xx", False)
        bc._yy = data.get("yy", False)
        bc._zz = data.get("zz", False)
        bc._name = data.get("name", "")
        return bc

    def __add__(self, other: '_BoundaryCondition') -> 'GeneralBC':
        """Combine two boundary conditions by OR-ing their component restraints."""
        if not isinstance(other, _BoundaryCondition):
            return NotImplemented
        combined = GeneralBC(
            x=self.x or other.x,
            y=self.y or other.y,
            z=self.z or other.z,
            xx=self.xx or other.xx,
            yy=self.yy or other.yy,
            zz=self.zz or other.zz,
            axes=self.axes,
        )
        combined._temp = self.temp or other.temp
        return combined
        


class GeneralBC(_BoundaryCondition):
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
        super().__init__(**kwargs)
        self._x = x
        self._y = y
        self._z = z
        self._xx = xx
        self._yy = yy
        self._zz = zz


class FixedBC(_BoundaryCondition):
    """A fixed nodal displacement boundary condition."""
    __doc__ = __doc__ or ""
    __doc__ += docs 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._x = True
        self._y = True
        self._z = True
        self._xx = True
        self._yy = True
        self._zz = True


class FixedBCX(_BoundaryCondition):
    """A fixed nodal displacement boundary condition along and around X."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._x = True
        self._xx = True


class FixedBCY(_BoundaryCondition):
    """A fixed nodal displacement boundary condition along and around Y."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._y = True
        self._yy = True


class FixedBCZ(_BoundaryCondition):
    """A fixed nodal displacement boundary condition along and around Z."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._z = True
        self._zz = True


class PinnedBC(_BoundaryCondition):
    """A pinned nodal displacement boundary condition."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._x = True
        self._y = True
        self._z = True


class ClampBCXX(PinnedBC):
    """A pinned nodal displacement boundary condition clamped in XX."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._xx = True


class ClampBCYY(PinnedBC):
    """A pinned nodal displacement boundary condition clamped in YY."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._yy = True


class ClampBCZZ(PinnedBC):
    """A pinned nodal displacement boundary condition clamped in ZZ."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._zz = True


class RollerBCX(PinnedBC):
    """A pinned nodal displacement boundary condition released in X."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._x = False


class RollerBCY(PinnedBC):
    """A pinned nodal displacement boundary condition released in Y."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._y = False


class RollerBCZ(PinnedBC):
    """A pinned nodal displacement boundary condition released in Z."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._z = False


class RollerBCXY(PinnedBC):
    """A pinned nodal displacement boundary condition released in X and Y."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._x = False
        self._y = False


class RollerBCYZ(PinnedBC):
    """A pinned nodal displacement boundary condition released in Y and Z."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._y = False
        self._z = False


class RollerBCXZ(PinnedBC):
    """A pinned nodal displacement boundary condition released in X and Z."""
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._x = False
        self._z = False

#===================================================================
# HEAT ANALYSIS
#===================================================================

class _ThermalBoundaryCondition(FEAData):
    """Base class for temperature boundary conditions.

    Parameters
    ----------
    temp : float, optional
        Imposed temperature for heat analysis. Defaults to None.
    """
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, temperature: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)
        self._temperature = temperature

    @property
    def __data__(self) -> Dict[str, Any]:
        data = super().__data__
        if not isinstance(data, dict):
            data = {}
        data.update({
            "temperature": self._temperature,
        })
        return data

    @classmethod
    def __from_data__(cls, data: Dict[str, Any]):
        temperature = data.get("temperature", None)
        if temperature is not None and not isinstance(temperature, float):
            raise TypeError(f"'temp' must be a float or None, got {type(temperature).__name__}")
        return cls(temp=temperature)


class ImposedTemperature(_ThermalBoundaryCondition):
    """Imposed temperature conidtion for heat analysis.
    
    Additional Parameters
---------------------
temp : float
    Value of imposed temperature applied
    """
    __doc__ = __doc__ or ""
    __doc__ += docs

    def __init__(self, temp: float, **kwargs):
        super().__init__(temperature=temp, **kwargs)

