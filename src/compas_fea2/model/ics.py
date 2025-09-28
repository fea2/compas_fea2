from typing import Optional

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.units import units_io


class _InitialCondition(FEAData):
    """Base class for all predefined initial conditions.

    Notes
    -----
    InitialConditions are registered to a :class:`compas_fea2.model.Model`.
    All physical quantities (temperature, stress, etc.) are expressed in the
    active unit system of the session. See :mod:`compas_fea2.units`.

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class InitialTemperature(_InitialCondition):
    """Initial temperature object for initial temperature field.

    Parameters
    ----------
    T0 : float
        Initial temperature magnitude in the active unit system ("temperature").

    Attributes
    ----------
    T0 : float
        Initial temperature magnitude in the active unit system ("temperature").

    Notes
    -----
    InitialConditions are registered to a :class:`compas_fea2.model.Model`. The
    same InitialCondition can be assigned to Nodes or Elements in multiple Parts

    """

    @units_io(types_in=("temperature",), types_out=None)
    def __init__(self, T0, **kwargs):
        super().__init__(**kwargs)
        self._T0 = T0

    @property
    @units_io(types_in=(), types_out="temperature")
    def T0(self):
        return self._T0

    @T0.setter
    @units_io(types_in=("temperature",), types_out=None)
    def T0(self, value):
        self._T0 = value

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "temperature": self._T0,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        T0 = data.get("T0")
        ic = cls(T0)
        return ic

    @classmethod
    def from_file(cls, path, **kwargs):
        return NotImplementedError("InitialTemperatureField is not implemented for the current backend. ")


class InitialStressField(_InitialCondition):
    """Stress field.

    Parameters
    ----------
    stress : tuple(float, float, float)
        Initial stress components (σx, σy, σz) in the active unit system ("stress").

    Attributes
    ----------
    stress : tuple(float, float, float)
        Stress values in the active unit system ("stress").

    Notes
    -----
    InitialConditions are registered to a :class:`compas_fea2.model.Model`
    The same InitialCondition can be assigned to Nodes or Elements in multiple Parts.

    """

    @units_io(types_in=("stress", "stress", "stress"), types_out=None)
    def __init__(self, stress, **kwargs):
        raise NotImplementedError("InitialStressField is not implemented for the current backend. ")
        super().__init__(**kwargs)
        self._s = stress

    @property
    @units_io(types_in=(), types_out=("stress", "stress", "stress"))
    def stress(self):
        return self._s

    @stress.setter
    @units_io(types_in=("stress", "stress", "stress"), types_out=None)
    def stress(self, value):
        """Set stress as a 3-component tuple (σx, σy, σz) in active stress units."""
        if not isinstance(value, tuple) or len(value) != 3:
            raise TypeError("you must provide a tuple with 3 elements")
        self._s = value

    @property
    def __data__(self):
        data = super().__data__
        data.update({"stress": self._s})
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        stress = data.get("stress")
        ic = cls(stress)
        return ic
