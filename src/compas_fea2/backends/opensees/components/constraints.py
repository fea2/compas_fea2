from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


from compas_fea2.backends._core import ConstraintBase
from compas_fea2.backends._core import TieConstraintBase


# Author(s): Francesco Ranaudo (github.com/franaudo)

__all__ = [
    'Constraint',
    'TieConstraint',
]


class Constraint(ConstraintBase):
    """Initialises base Constraint object.

    Parameters
    ----------
    name : str
        Name of the Constraint object.

    Returns
    -------
    None

    """
    pass
    # def __init__(self, name):
    #     super(Constraint, self).__init__(name)


class TieConstraint(TieConstraintBase):
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
    pass
    # def __init__(self, name, master, slave, tol):
    #     super(TieConstraint, self).__init__(name, master, slave, tol)
