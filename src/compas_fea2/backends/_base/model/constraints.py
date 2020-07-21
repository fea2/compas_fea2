
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


# Author(s): Andrew Liew (github.com/andrewliew), Francesco Ranaudo (github.com/franaudo)


__all__ = [
    'ConstraintBase',
    'TieConstraintBase',
]


class ConstraintBase(object):
    """Initialises base Constraint object.

    Parameters
    ----------
    name : str
        Name of the Constraint object.

    Returns
    -------
    None
    """

    def __init__(self, name):
        self.__name__ = 'ConstraintObject'
        self.name = name
        self.attr_list = ['name']

    def __str__(self):
        title = 'compas_fea2 {0} object'.format(self.__name__)
        separator = '-' * (len(self.__name__) + 19)
        l = []
        for attr in self.attr_list:
            l.append('{0:<10} : {1}'.format(attr, getattr(self, attr)))

        return """\n{}\n{}\n{}""".format(title, separator, '\n'.join(l))


class TieConstraintBase(ConstraintBase):
    """Tie constraint between two sets of nodes, elements or surfaces.

    Parameters
    ----------
    name : str
        TieConstraint name.
    master : str
        Master set name.
    slave : str
        Slave set name.
    tol : float
        Constraint tolerance, distance limit between master and slave.

    Returns
    -------
    None
    """

    def __init__(self, name, master, slave, tol):
        ConstraintBase.__init__(self, name=name)
        self.__name__ = 'TieConstraint'
        self.master = master
        self.slave = slave
        self.tol = tol
        self.attr_list.extend(['master', 'slave', 'tol'])