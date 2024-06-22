from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .step import GeneralStep


class QuasiStaticStep(GeneralStep):
    """Step for quasi-static analysis."""

    @property
    def __data__(self):
        return {
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raise NotImplementedError


class DirectCyclicStep(GeneralStep):
    """Step for a direct cyclic analysis."""

    @property
    def __data__(self):
        return {
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raise NotImplementedError
