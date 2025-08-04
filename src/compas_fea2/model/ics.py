from typing import Optional

from uuid import UUID

from compas_fea2.base import FEAData
from compas_fea2.base import Registry


class _InitialCondition(FEAData):
    """Base class for all predefined initial conditions.

    Notes
    -----
    InitialConditions are registered to a :class:`compas_fea2.model.Model`. The
    same InitialCondition can be assigned to Nodes or Elements in multiple Parts

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def __data__(self) -> dict:
        data = super().__data__
        return data

    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)

        ic = cls()
        # Add base properties
        ic._uid = UUID(uid) if uid else None
        # ic._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        ic._name = data.get("name", "")

        if uid:
            registry.add(uid, ic)
        return ic



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
                "temperature": self._t,
            }
        )
        return data

    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)

        T0 = data.get("T0")
        ic = cls(T0)
        # Add base properties
        ic._uid = UUID(uid) if uid else None
        # ic._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        ic._name = data.get("name", "")

        if uid:
            registry.add(uid, ic)
        return ic
        

    @classmethod
    def from_file(cls, path, **kwargs):
        return NotImplementedError("InitialTemperatureField is not implemented for the current backend. ")


class InitialStress(_InitialCondition):
    """Initial stress for an initial stress field.

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

    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)

        stress = data.get("stress")
        ic = cls(stress)
        # Add base properties
        ic._uid = UUID(uid) if uid else None
        # ic._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        ic._name = data.get("name", "")

        if uid:
            registry.add(uid, ic)
        return ic
