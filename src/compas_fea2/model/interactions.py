from compas_fea2.base import FEAData


class _Interaction(FEAData):
    """Base class for all interactions.

    Note
    ----
    Interactions are registered to a :class:`compas_fea2.model.Model` and can be
    assigned to multiple interfaces."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
    temperature : float or [float]
        Constant temperature value or temperature evolution.


    Attributes
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    temperature : float or [float]
        Constant temperature value or temperature evolution.

    """

    def __init__(self, temperature, **kwargs):
        super(_Interaction, self).__init__(**kwargs)
        self._temperature = temperature

    @property
    def temperature(self):
        return self._temperature


class SurfaceConvection(ThermalInteraction):
    """Convection.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    h : float
        Convection coefficient.
    surface : FaceGroup
        Convection surface.
    temperature : float or [float]
        Constant temperature value or temperature evolution.

    Attributes
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    temperature : float or [float]
        Constant temperature value or temperature evolution.

    """

    def __init__(self, surface, h, temperature, **kwargs):
        super().__init__(temperature=temperature, **kwargs)
        self._h = h
        self._surface = surface

    @property
    def h(self):
        return self._h

    @property
    def surface(self):
        return self._surface


class SurfaceRadiation(ThermalInteraction):
    """Radiation.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    eps : float
        Radiation coefficient.
    surface : FaceGroup
        Convection surface.
    temperature : float or [float]
        Constant temperature value or temperature evolution.

    Attributes
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    temperature : float or [float]
        Constant temperature value or temperature evolution.

    """

    def __init__(self, surface, eps, temperature, **kwargs):
        super().__init__(temperature=temperature, **kwargs)
        self._eps = eps
        self._surface = surface

    @property
    def eps(self):
        return self._eps

    @property
    def surface(self):
        return self._surface
