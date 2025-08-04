from typing import Optional
from uuid import UUID

from compas_fea2.base import FEAData
from compas_fea2.base import Registry


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

    @property
    def __data__(self):
        data = super().__data__
        data.update({
            "master": self._master.__data__,
            "slave": self._slave.__data__,
            "behavior": self._behavior.__data__,
        })
        return data

    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)
        
        master = registry.add_from_data(data.get("master"), "compas_fea2.model.elements")
        slave = registry.add_from_data(data.get("slave"), "compas_fea2.model.elements")
        behavior = registry.add_from_data(data.get("behavior"), "compas_fea2.model.interactions")
        interface = cls(master, slave, behavior)
        
        # Add base properties
        interface._uid = UUID(uid) if uid else None
        # interface._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interface._name = data.get("name", "")

        if uid:
            registry.add(uid, interface)
        return interface


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

    @property
    def __data__(self):
        data = super().__data__
        data.update({
            "master": self._master.__data__,
            "behavior": self._behavior.__data__,
        })
        return data

    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)
        
        master = registry.add_from_data(data.get("master"), "compas_fea2.model.elements")
        behavior = registry.add_from_data(data.get("behavior"), "compas_fea2.model.interactions")
        interface = cls(master, behavior)
        
        # Add base properties
        interface._uid = UUID(uid) if uid else None
        # interface._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interface._name = data.get("name", "")

        if uid:
            registry.add(uid, interface)
        return interface