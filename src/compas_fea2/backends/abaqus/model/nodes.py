from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


from compas_fea2.backends._base.model import NodeBase

# Francesco Ranaudo (github.com/franaudo)

__all__ = [
    'Node',
]


# =============================================================================
# General
# =============================================================================

class Node(NodeBase):
    """ Node class

    Parameters
    ----------
    xyz : list
        [description]
    ex : [type], optional
        [description], by default None
    ey : [type], optional
        [description], by default None
    ez : [type], optional
        [description], by default None
    mass : [type], optional
        [description], by default None
    label : [type], optional
        [description], by default Non

    Attributes
    ----------
    xyz : list
        [description]
    ex : [type], optional
        [description], by default None
    ey : [type], optional
        [description], by default None
    ez : [type], optional
        [description], by default None
    mass : [type], optional
        [description], by default None
    label : [type], optional
        [description], by default None

    Example
    -------
    >>> n = Node([2,3,4])
    >>> n.key=300
    >>> print(n.key)

    Note
    ----
    The nodes key numbering in compas_fea2 starts from 0, while in Abaqus it starts
    from 1. The conversion in automatically resolved by compas_fea2.
    """

    def __init__(self, xyz, ex=None, ey=None, ez=None, mass=None, label=None):
        super(Node, self).__init__(xyz=xyz, ex=ex, ey=ey, ez=ez, mass=mass, label=label)

    def _generate_data(self):
        '''Generates the string information for the input file.

        Parameters
        ----------
        None

        Returns
        -------
        input file data line (str).
        '''
        x, y, z = self.xyz
        return ' {0},    {1:.3f},    {2:.3f},    {3:.3f}\n'.format(self.key+1, x, y, z)


# =============================================================================
# Debugging
# =============================================================================

if __name__ == "__main__":
    from compas_fea2.backends.abaqus import Node

    n = Node([2,3,4])
    n.key=300
    print(n.key)