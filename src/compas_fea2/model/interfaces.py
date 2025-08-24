from typing import Optional

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data


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
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "master": self._master.__data__,
                "slave": self._slave.__data__,
                "behavior": self._behavior.__data__,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        master = registry.add_from_data(data.get("master"), "compas_fea2.model.elements")  # type: ignore
        slave = registry.add_from_data(data.get("slave"), "compas_fea2.model.elements")  # type: ignore
        behavior = registry.add_from_data(data.get("behavior"), "compas_fea2.model.interactions")  # type: ignore
        interface = cls(master, slave, behavior)
        return interface

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
        
    @classmethod
    def from_parts_and_plane(cls, part_master, part_slave, plane, behavior, **kwargs):
        """Create a PartPartInterface from two parts and a plane that separates them.

        Parameters
        ----------
        part_master : :class:`compas_fea2.model.Part`
            The part that will be assigned as master.
        part_slave : :class:`compas_fea2.model.Part`
            The part that will be assigned as slave.
        plane : :class:`compas.geometry.Plane`
            The plane that separates the two parts. The normal of the plane
            should point from the master to the slave.
        behavior : :class:`compas_fea2.model._Interaction`
            behavior type between master and slave.
        """
        from compas_fea2.model import FacesGroup

        tol = 1e-3
        master_faces = part_master.find_faces_on_plane(plane, tol=tol)
        slave_faces = part_slave.find_faces_on_plane(plane, tol=tol)

        if not master_faces:
            raise ValueError(f"No faces found on master part '{part_master.name}' for the given plane.")
        if not slave_faces:
            raise ValueError(f"No faces found on slave part '{part_slave.name}' for the given plane.")

        master_fg = FacesGroup(master_faces, name=f"{part_master.name}_to_{part_slave.name}_master", part=part_master)
        slave_fg = FacesGroup(slave_faces, name=f"{part_master.name}_to_{part_slave.name}_slave", part=part_slave)

        return cls(master=master_fg, slave=slave_fg, behavior=behavior, **kwargs)


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
        data.update(
            {
                "master": self._master.__data__,
                "behavior": self._behavior.__data__,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        master = registry.add_from_data(data.get("master"), "compas_fea2.model.elements", duplicate=duplicate)  # type: ignore
        behavior = registry.add_from_data(data.get("behavior"), "compas_fea2.model.interactions", duplicate=duplicate)  # type: ignore
        interface = cls(master, behavior)
        return interface
