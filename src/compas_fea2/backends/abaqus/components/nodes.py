from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


from compas_fea2.backends._core import NodeBase

# Francesco Ranaudo (github.com/franaudo)

# TODO add the property class here

__all__ = [
    'Node',
]


# ==============================================================================
# General
# ==============================================================================

class Node(NodeBase):
    """Initialises base Node object.

    Parameters
    ----------
    key : int
        Node key number.
    xyz : list
        [x, y, z] co-ordinates of the node.
    ex : list
        Node's local x axis.
    ey : list
        Node's local y axis.
    ez : list
        Node's local z axis.
    mass : float
        Mass in kg associated with the node.

    Attributes
    ----------
    key : int
        Node key number.
    x : float
        x co-ordinates of the node.
    y : float
        y co-ordinates of the node.
    z : float
        z co-ordinates of the node.
    ex : list
        Node's local x axis.
    ey : list
        Node's local y axis.
    ez : list
        Node's local z axis.
    mass : float
        Mass in kg associated with the node.

    """

    def __init__(self, key, xyz, ex, ey, ez, mass, part):
        super(Node, self).__init__(key, xyz, ex, ey, ez, mass)

    def write_header(self, f):
        line = '*Node'
        f.write(line)

    def write_to_input_file(self, f):
        prefix  = ''
        spacer  = self.spacer
        x, y, z = self.xyz

        line    = '{0}{1}{2}{3:.3f}{4:.3f}{2}{5:.3f}'.format(prefix, self.key + 1, spacer, x, y, z)

        f.write(line)