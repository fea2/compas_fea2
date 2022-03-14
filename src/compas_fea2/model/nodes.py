from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import compas

from compas.utilities.maps import geometric_key
from compas_fea2.base import FEABase


class Node(FEABase):
    """Initialises base Node object.

    Parameters
    ----------
    xyz : list[float]
        The location of the node in the global coordinate system.
    name : str, optional
        Node's label. If no label is specified, it is automatically generated
        when a node is added. The label does not need to be unique.

    Attributes
    ----------
    key : str, read-only
        The identifier of the node.
    xyz : list[float]
        The location of the node in the global coordinate system.
    x : float
        The X coordinate.
    y : float
        The Y coordinate.
    z : float
        The Z coordinate.
    gkey : str, read-only
        The geometric key.

    Examples
    --------
    >>> node = Node(1.0, 2.0, 3.0)

    """

    def __init__(self, xyz, **kwargs):
        super(Node, self).__init__(**kwargs)
        self._key = None
        self._x = None
        self._y = None
        self._z = None
        self.xyz = xyz

    @property
    def key(self):
        return self._key

    @property
    def xyz(self):
        return [self.x, self.y, self.z]

    @xyz.setter
    def xyz(self, value):
        self.x = value[0]
        self.y = value[1]
        self.z = value[2]

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = float(value)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = float(value)

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, value):
        self._z = float(value)

    @property
    def gkey(self):
        return geometric_key(self.xyz, precision=compas.PRECISION, sanitize=False)
