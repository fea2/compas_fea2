from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_fea2.base import FEAData


class _PrescribedField(FEAData):
    """Base class for all predefined initial conditions.

    Notes
    -----
    Fields are registered to a :class:`compas_fea2.problem.Step`.

    """

    @property
    def __data__(self):
        return {}

    @classmethod
    def __from_data__(cls, data):
        return cls()

    def __init__(self, **kwargs):
        super(_PrescribedField, self).__init__(**kwargs)


class PrescribedTemperatureField(_PrescribedField):
    """Temperature field"""

    @property
    def __data__(self):
        return {
            "temperature": self.temperature,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            temperature=data["temperature"],
        )

    def __init__(self, temperature, **kwargs):
        super(PrescribedTemperatureField, self).__init__(**kwargs)
        self._t = temperature

    @property
    def temperature(self):
        return self._t

    @temperature.setter
    def temperature(self, value):
        self._t = value
