from compas_fea2.base import FEAData


class _Interface(FEAData):
    """An interface is defined as a pair of master and slave surfaces
    with a behavior property between them.

    Note
    ----
    Interfaces are registered to a :class:`compas_fea2.model.Model`.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    master : :class:`compas_fea2.model.FacesGroup`
        Group of element faces determining the Master surface.
    slave : :class:`compas_fea2.model.FacesGroup`
        Group of element faces determining the Slave surface.
    behavior : :class:`compas_fea2.model._Interaction`
        behavior type between master and slave.

    Attributes
    ----------
    name : str
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    master : :class:`compas_fea2.model.FacesGroup`
        Group of element faces determining the Master surface.
    slave : :class:`compas_fea2.model.FacesGroup`
        Group of element faces determining the Slave surface.
    behavior : :class:`compas_fea2.model._Interaction` | :class:`compas_fea2.model._Constraint`
        behavior type between master and slave.

    """

    def __init__(self, master, slave, behavior, name=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self._master = master
        self._slave = slave
        self._behavior = behavior

    @property
    def master(self):
        return self._master

    @property
    def slave(self):
        return self._slave

    @property
    def behavior(self):
        return self._behavior


class PartPartInterface(_Interface):
    """A surface interface is defined as a pair of master and slave surfaces
    with a behavior property between them.

    Note
    ----
    Surface interfaces are registered to a :class:`compas_fea2.model.Model`.

    Parameters
    ----------
    master : :class:`compas_fea2.model.FacesGroup`
        Group of element faces determining the Master surface.
    slave : :class:`compas_fea2.model.FacesGroup`
        Group of element faces determining the Slave surface.
    behavior : :class:`compas_fea2.model._Interaction`
        behavior type between master and slave.
        
    """
    
    def __init__(self, master, slave, behavior, **kwargs):
        super().__init__(master=master, slave=slave, behavior=behavior, **kwargs)
        

class BoundaryInterface(_Interface):
    """A boundary interface is defined as a pair of master and slave surfaces
    with a behavior property between them.

    Note
    ----
    Boundary interfaces are registered to a :class:`compas_fea2.model.Model`.

    Parameters
    ----------
    master : :class:`compas_fea2.model.FacesGroup`
        Group of element faces determining the Master surface.
    slave : :class:`compas_fea2.model.FacesGroup`
        Group of element faces determining the Slave surface.
    behavior : :class:`compas_fea2.model._Interaction`
        behavior type between master and slave.
        
    """
    
    def __init__(self, master, behavior, **kwargs):
        super().__init__(master=master, slave=None, behavior=behavior, **kwargs)