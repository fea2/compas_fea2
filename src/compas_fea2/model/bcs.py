from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas.geometry import Frame
from compas_fea2.base import FEAData

docs = """
Note
----
BoundaryConditions are registered to a :class:`compas_fea2.model.Model`.

Warning
-------
The `frame` parameter is WIP. Currently only WorldXY can be used.

Parameters
----------
nodes : List[`class:compas_fea2.elements.Node`]
    The nodes to which the boundary condition is applied.
frame : `class:compas.geotmery.Frame`, optional
    The refernce frame.

Attributes
----------
nodes : List[`class:compas_fea2.elements.Node`]
    The nodes to which the boundary condition is applied.
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
components : dict
    Dictionary with component-value pairs summarizing the boundary condition.
frame : str
    The refernce frame.
"""


class _BoundaryCondition(FEAData):
    """Base class for all zero-valued boundary conditions."""

    __doc__ += docs

    @property
    def __data__(self):
        return {
            "nodes": self.nodes,
            "axes": self.frame,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            nodes=data["nodes"],
            axes=data["axes"],
        )

    def __init__(self, nodes, frame=Frame.worldXY(), **kwargs):
        super(_BoundaryCondition, self).__init__(**kwargs)
        self.nodes = nodes
        self._frame = frame
        self._x = False
        self._y = False
        self._z = False
        self._xx = False
        self._yy = False
        self._zz = False

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def z(self):
        return self._z

    @property
    def xx(self):
        return self._xx

    @property
    def yy(self):
        return self._yy

    @property
    def zz(self):
        return self._zz

    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, value):
        self._frame = value

    @property
    def components(self):
        return {c: getattr(self, c) for c in ["x", "y", "z", "xx", "yy", "zz"]}


class GeneralBC(_BoundaryCondition):
    """Costumized boundary condition."""

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

    def __init__(self, nodes, x=False, y=False, z=False, xx=False, yy=False, zz=False, **kwargs):
        super(GeneralBC, self).__init__(nodes, **kwargs)
        self._x = x
        self._y = y
        self._z = z
        self._xx = xx
        self._yy = yy
        self._zz = zz


class FixedBC(_BoundaryCondition):
    """A fixed nodal displacement boundary condition."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(FixedBC, self).__init__(nodes, **kwargs)
        self._x = True
        self._y = True
        self._z = True
        self._xx = True
        self._yy = True
        self._zz = True


class FixedBCX(_BoundaryCondition):
    """A fixed nodal displacement boundary condition  along and around Z"""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(FixedBC, self).__init__(nodes, **kwargs)
        self._x = True
        self._xx = True


class FixedBCY(_BoundaryCondition):
    """A fixed nodal displacement boundary condition along and around Y"""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(FixedBC, self).__init__(nodes, **kwargs)
        self._y = True
        self._yy = True


class FixedBCZ(_BoundaryCondition):
    """A fixed nodal displacement boundary condition along and around Z"""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(FixedBC, self).__init__(nodes, **kwargs)
        self._z = True
        self._z = True


class PinnedBC(_BoundaryCondition):
    """A pinned nodal displacement boundary condition."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(PinnedBC, self).__init__(nodes, **kwargs)
        self._x = True
        self._y = True
        self._z = True


class ClampBCXX(PinnedBC):
    """A pinned nodal displacement boundary condition clamped in XX."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(ClampBCXX, self).__init__(nodes, **kwargs)
        self._xx = True


class ClampBCYY(PinnedBC):
    """A pinned nodal displacement boundary condition clamped in YY."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(ClampBCYY, self).__init__(nodes, **kwargs)
        self._yy = True


class ClampBCZZ(PinnedBC):
    """A pinned nodal displacement boundary condition clamped in ZZ."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(ClampBCZZ, self).__init__(nodes, **kwargs)
        self._zz = True


class RollerBCX(PinnedBC):
    """A pinned nodal displacement boundary condition released in X."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(RollerBCX, self).__init__(nodes, **kwargs)
        self._x = False


class RollerBCY(PinnedBC):
    """A pinned nodal displacement boundary condition released in Y."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(RollerBCY, self).__init__(nodes, **kwargs)
        self._y = False


class RollerBCZ(PinnedBC):
    """A pinned nodal displacement boundary condition released in Z."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(RollerBCZ, self).__init__(nodes, **kwargs)
        self._z = False


class RollerBCXY(PinnedBC):
    """A pinned nodal displacement boundary condition released in X and Y."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(RollerBCXY, self).__init__(nodes, **kwargs)
        self._x = False
        self._y = False


class RollerBCYZ(PinnedBC):
    """A pinned nodal displacement boundary condition released in Y and Z."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(RollerBCYZ, self).__init__(nodes, **kwargs)
        self._y = False
        self._z = False


class RollerBCXZ(PinnedBC):
    """A pinned nodal displacement boundary condition released in X and Z."""

    __doc__ += docs

    def __init__(self, nodes, **kwargs):
        super(RollerBCXZ, self).__init__(nodes, **kwargs)
        self._x = False
        self._z = False
