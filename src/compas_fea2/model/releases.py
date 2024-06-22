from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import compas_fea2.model
from compas_fea2.base import FEAData


class _BeamEndRelease(FEAData):
    """Assign a general end release to a `compas_fea2.model.BeamElement`.

    Parameters
    ----------
    n : bool, optional
        Release displacements along the local axial direction, by default False
    v1 : bool, optional
        Release displacements along local 1 direction, by default False
    v2 : bool, optional
        Release displacements along local 2 direction, by default False
    m1 : bool, optional
        Release rotations about loacl 1 direction, by default False
    m2 : bool, optional
        Release rotations about local 2 direction, by default False
    t : bool, optional
        Release rotations about local axial direction (torsion), by default False

    Attributes
    ----------
    location : str
        'start' or 'end'
    element : :class:`compas_fea2.model.BeamElement`
        The element to release.
    n : bool, optional
        Release displacements along the local axial direction, by default False
    v1 : bool, optional
        Release displacements along local 1 direction, by default False
    v2 : bool, optional
        Release displacements along local 2 direction, by default False
    m1 : bool, optional
        Release rotations about loacl 1 direction, by default False
    m2 : bool, optional
        Release rotations about local 2 direction, by default False
    t : bool, optional
        Release rotations about local axial direction (torsion), by default False

    """

    @property
    def __data__(self):
        return {
            "n": self.n,
            "v1": self.v1,
            "v2": self.v2,
            "m1": self.m1,
            "m2": self.m2,
            "t": self.t,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            n=data["n"],
            v1=data["v1"],
            v2=data["v2"],
            m1=data["m1"],
            m2=data["m2"],
            t=data["t"],
        )

    def __init__(self, n=False, v1=False, v2=False, m1=False, m2=False, t=False, **kwargs):
        super(_BeamEndRelease, self).__init__(**kwargs)

        self._element = None
        self._location = None
        self.n = n
        self.v1 = v1
        self.v2 = v2
        self.m1 = m1
        self.m2 = m2
        self.t = t

    @property
    def element(self):
        return self._element

    @element.setter
    def element(self, value):
        if not isinstance(value, compas_fea2.model.BeamElement):
            raise TypeError("{!r} is not a beam element.".format(value))
        self._element = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if value not in ("start", "end"):
            raise TypeError("the location can be either `start` or `end`")
        self._location = value


class BeamEndPinRelease(_BeamEndRelease):
    """Assign a pin end release to a `compas_fea2.model.BeamElement`.

    Parameters
    ----------
    m1 : bool, optional
        Release rotations about loacl 1 direction, by default False
    m2 : bool, optional
        Release rotations about local 2 direction, by default False
    t : bool, optional
        Release rotations about local axial direction (torsion), by default False

    """

    @property
    def __data__(self):
        return {
            "m1": self.m1,
            "m2": self.m2,
            "t": self.t,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            m1=data["m1"],
            m2=data["m2"],
            t=data["t"],
        )

    def __init__(self, m1=False, m2=False, t=False, **kwargs):
        super(BeamEndPinRelease, self).__init__(n=False, v1=False, v2=False, m1=m1, m2=m2, t=t, **kwargs)


class BeamEndSliderRelease(_BeamEndRelease):
    """Assign a slider end release to a `compas_fea2.model.BeamElement`.

    Parameters
    ----------
    v1 : bool, optional
        Release displacements along local 1 direction, by default False
    v2 : bool, optional
        Release displacements along local 2 direction, by default False

    """

    @property
    def __data__(self):
        return {
            "v1": self.v1,
            "v2": self.v2,
            "t": self.t,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            n=data["n"],
            v1=data["v1"],
            v2=data["v2"],
            m1=data["m1"],
            m2=data["m2"],
            t=data["t"],
        )

    def __init__(self, v1=False, v2=False, **kwargs):
        super(BeamEndSliderRelease, self).__init__(v1=v1, v2=v2, n=False, m1=False, m2=False, t=False, **kwargs)
