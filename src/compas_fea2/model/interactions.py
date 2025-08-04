from typing import Optional

from uuid import UUID

from compas_fea2.base import FEAData
from compas_fea2.problem.loads import ScalarLoad
from compas_fea2.base import Registry



class _Interaction(FEAData):
    """Base class for all interactions.

    Note
    ----
    Interactions are registered to a :class:`compas_fea2.model.Model` and can be
    assigned to multiple interfaces."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        return data
    
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)

        interaction = cls()
        # Add base properties
        interaction._uid = UUID(uid) if uid else None
        # interaction._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interaction._name = data.get("name", "")

        if uid:
            registry.add(uid, interaction)
        return interaction
        
   
    @property
    def model(self):
        """Get the model to which this interaction belongs."""
        return self._registration


# ------------------------------------------------------------------------------
# SURFACE TO SURFACE INTERACTION
# ------------------------------------------------------------------------------
class Contact(_Interaction):
    """General contact interaction between two parts.

    Note
    ----
    Interactions are registered to a :class:`compas_fea2.model.Model` and can be
    assigned to multiple interfaces.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    normal : str
        Behaviour of the contact along the direction normal to the interaction
        surface. For faceted surfaces, this is the behavior along the direction
        normal to each face.
    tangent :
        Behaviour of the contact along the directions tangent to the interaction
        surface. For faceted surfaces, this is the behavior along the directions
        tangent to each face.

    Attributes
    ----------
    name : str
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    normal : str
        Behaviour of the contact along the direction normal to the interaction
        surface. For faceted surfaces, this is the behavior along the direction
        normal to each face.
    tangent :
        Behaviour of the contact along the directions tangent to the interaction
        surface. For faceted surfaces, this is the behavior along the directions
        tangent to each face.
    """

    def __init__(self, normal, tangent, **kwargs):
        super().__init__(**kwargs)
        self._tangent = tangent
        self._normal = normal

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update({
            "normal": self._normal,
            "tangent": self._tangent,
        })
        return data
    
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)
        
        normal = data.get("normal")
        tangent = data.get("tangent")
        interaction = cls(normal, tangent)
        
        # Add base properties
        interaction._uid = UUID(uid) if uid else None
        # interaction._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interaction._name = data.get("name", "")

        if uid:
            registry.add(uid, interaction)
        return interaction

    @property
    def tangent(self):
        return self._tangent

    @property
    def normal(self):
        return self._normal


class HardContactNoFriction(Contact):
    """Hard contact interaction property with friction using a penalty
    formulation.

    Parameters
    ----------
    mu : float
        Friction coefficient for tangential behaviour.
    tollerance : float
        Slippage tollerance during contact.

    Attributes
    ----------
    name : str
        Automatically generated id. You can change the name if you want a more
        human readable input file.
    mu : float
        Friction coefficient for tangential behaviour.
    tollerance : float
        Slippage tollerance during contact.
    """

    def __init__(self, tol, **kwargs) -> None:
        super().__init__(normal="HARD", tangent=None, **kwargs)
        self._tol = tol

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update({
            "tol": self._tol,
        })
        return data
    
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)
        
        tol = data.get("tol")
        interaction = cls(tol)
        
        # Add base properties
        interaction._uid = UUID(uid) if uid else None
        # interaction._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interaction._name = data.get("name", "")

        if uid:
            registry.add(uid, interaction)
        return interaction

class HardContactFrictionPenalty(Contact):
    """Hard contact interaction property with friction using a penalty
    formulation.

    Parameters
    ----------
    mu : float
        Friction coefficient for tangential behaviour.
    tollerance : float
        Slippage tollerance during contact.

    Attributes
    ----------
    name : str
        Automatically generated id. You can change the name if you want a more
        human readable input file.
    mu : float
        Friction coefficient for tangential behaviour.
    tollerance : float
        Slippage tollerance during contact.
    """

    def __init__(self, mu, tol, **kwargs) -> None:
        super().__init__(normal="HARD", tangent=mu, **kwargs)
        self._tol = tol

    @property
    def mu(self):
        return self._tangent

    @property
    def tol(self):
        return self._tol

    @tol.setter
    def tol(self, value):
        self._tol = value

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update({
            "mu": self._tangent,
        })
        return data
    
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)
        
        tol = data.get("tol")
        mu = data.get("tangent")
        interaction = cls(mu, tol)
        
        # Add base properties
        interaction._uid = UUID(uid) if uid else None
        # interaction._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interaction._name = data.get("name", "")

        if uid:
            registry.add(uid, interaction)
        return interaction


class LinearContactFrictionPenalty(Contact):
    """Contact interaction property with linear softnening and friction using a
    penalty formulation.

    Parameters
    ----------
    stiffness : float
        Stiffness of the the contact in the normal direction.
    mu : float
        Friction coefficient for tangential behaviour.
    tollerance : float
        Slippage tollerance during contact.

    Attributes
    ----------
    name : str
        Automatically generated id. You can change the name if you want a more
        human readable input file.
    mu : float
        Friction coefficient for tangential behaviour.
    tollerance : float
        Slippage tollerance during contact.
    """

    def __init__(self, stiffness, mu, tolerance, **kwargs) -> None:
        super().__init__(normal="Linear", tangent=mu, **kwargs)
        self._tolerance = tolerance
        self._stiffness = stiffness

    @property
    def stiffness(self):
        return self._stiffness

    @stiffness.setter
    def stiffness(self, value):
        self._stiffness = value

    @property
    def tolerance(self):
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value):
        self._tolerance = value

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update({
            "stiffness": self._stiffness,
            "mu": self._tangent,
        })
        return data
    
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)
        
        tol = data.get("tolerance")
        mu = data.get("mu")
        stiffness = data.get("stiffness")
        interaction = cls(stiffness, mu, tol)
        
        # Add base properties
        interaction._uid = UUID(uid) if uid else None
        # interaction._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interaction._name = data.get("name", "")

        if uid:
            registry.add(uid, interaction)
        return interaction


class HardContactRough(Contact):
    """Hard contact interaction property with indefinite friction (rough surfaces).

    Parameters
    ----------
    name : str, optional
        You can change the name if you want a more human readable input file.

    Attributes
    ----------
    name : str
        Automatically generated id. You can change the name if you want a more
        human readable input file.
    mu : float
        Friction coefficient for tangential behaviour.
    tollerance : float
        Slippage tollerance during contact.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(normal="HARD", tangent="ROUGH", **kwargs)


    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        return data
    
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)
        
        interaction = cls()
        
        # Add base properties
        interaction._uid = UUID(uid) if uid else None
        # interaction._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interaction._name = data.get("name", "")

        if uid:
            registry.add(uid, interaction)
        return interaction

# ------------------------------------------------------------------------------
# THERMAL INTERACTION
# ------------------------------------------------------------------------------


class ThermalInteraction(_Interaction):
    """General thermal interaction of a part with the exterior.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    temperature_value : float
        Temperature value.
    temperature_amplitude : Amplitude, optionnal
        Associated amplitude to the temperature.

    Attributes
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    temperature : ScalarLoad
        Constant temperature load or transient temperature load. 

    """

    def __init__(self, temperature_value, temperature_amplitude=None, **kwargs):
        super(_Interaction, self).__init__(**kwargs)
        self._temperature = ScalarLoad(scalar_load=temperature_value, amplitude=temperature_amplitude)

    @property
    def temperature(self):
        return self._temperature


    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update({
            "temperature": self._temperature,
        })
        return data
    
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)
        
        temperature = data.get("temperature")
        interaction = cls(temperature)
        
        # Add base properties
        interaction._uid = UUID(uid) if uid else None
        # interaction._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interaction._name = data.get("name", "")

        if uid:
            registry.add(uid, interaction)
        return interaction


class Convection(ThermalInteraction):
    """Convection.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    h : float
        Convection coefficient.
    temperature_value : float
        Temperature value.
    temperature_amplitude : Amplitude, optionnal
        Associated amplitude to the temperature.

    Attributes
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    h : float
        Convection coefficient.
    temperature : ScalarLoad
        Constant temperature load or transient temperature load. 

    """

    def __init__(self, h, temperature_value, temperature_amplitude, **kwargs):
        super().__init__(temperature_value=temperature_value, temperature_amplitude=temperature_amplitude, **kwargs)
        self._h = h

    @property
    def h(self):
        return self._h
    

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update({
            "h": self._h,
            "temperature": self._temperature,
        })
        return data
    
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)
        
        temperature = data.get("temperature")
        h = data.get("h")
        surface = registry.add_from_data(data.get("surface"), "compas_fea2.model.groups")
        interaction = cls(surface, h, temperature)
        
        # Add base properties
        interaction._uid = UUID(uid) if uid else None
        # interaction._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interaction._name = data.get("name", "")

        if uid:
            registry.add(uid, interaction)
        return interaction



class Radiation(ThermalInteraction):
    """Radiation.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    eps : float
        Radiation coefficient.
    temperature_value : float
        Temperature value.
    temperature_amplitude : Amplitude, optionnal
        Associated amplitude to the temperature.

    Attributes
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    eps : float
        Radiation coefficient.
    temperature : ScalarLoad
        Constant temperature load or transient temperature load. 

    """

    def __init__(self, eps, temperature_value, temperature_amplitude, **kwargs):
        super().__init__(temperature_value=temperature_value, temperature_amplitude=temperature_amplitude, **kwargs)
        self._eps = eps

    @property
    def eps(self):
        return self._eps

    @property
    def surface(self):
        return self._surface

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update({
            "eps": self._eps,
            "temperature": self._temperature,
        })
        return data
    
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)
        
        temperature = data.get("temperature")
        eps = data.get("eps")
        surface = registry.add_from_data(data.get("surface"), "compas_fea2.model.groups")
        interaction = cls(surface, eps, temperature)
        
        # Add base properties
        interaction._uid = UUID(uid) if uid else None
        # interaction._registration = registry.add_from_data(data.get("registration"), "compas_fea2.model.model") if data.get("registration") else None
        interaction._name = data.get("name", "")

        if uid:
            registry.add(uid, interaction)
        return interaction