from typing import Optional

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data


class _InitialCondition(FEAData):
    """Base class for all predefined initial conditions.

    Notes
    -----
    InitialConditions are registered to a :class:`compas_fea2.model.Model`. The
    same InitialCondition can be assigned to Nodes or Elements in multiple Parts

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class InitialTemperature(_InitialCondition):
    """Initial temperature object for initial temperature field.

    Parameters
    ----------
    T0 : float
        The temperature value.

    Attributes
    ----------
    T0 : float
        The temperature value.

    Notes
    -----
    InitialConditions are registered to a :class:`compas_fea2.model.Model`. The
    same InitialCondition can be assigned to Nodes or Elements in multiple Parts

    """

    def __init__(self, T0, **kwargs):
        super().__init__(**kwargs)
        self._T0 = T0

    @property
    def T0(self):
        return self._T0

    @T0.setter
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
        The stress values.

    Attributes
    ----------
    stress : tuple(float, float, float)
        The stress values.

    Notes
    -----
    InitialConditions are registered to a :class:`compas_fea2.model.Model`
    The same InitialCondition can be assigned to Nodes or Elements in multiple Parts.

    """

    def __init__(self, stress, **kwargs):
        raise NotImplementedError("InitialStressField is not implemented for the current backend. ")
        super().__init__(**kwargs)
        self._s = stress

    @property
    def stress(self):
        return self._s

    @stress.setter
    def stress(self, value):
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
