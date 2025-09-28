from typing import Optional

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.problem.loads import ScalarLoad
from compas_fea2.units import units_io


class _Interaction(FEAData):
    """Base class for all interactions.

    Notes
    -----
    Interactions are registered to a :class:`compas_fea2.model.Model`.
    All physical parameters (friction, stiffness, tolerance, heat transfer, etc.)
    are expressed in the active unit system. See :mod:`compas_fea2.units`.
    """

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
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update(
            {
                "normal": self._normal,
                "tangent": self._tangent,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, set_uid: Optional[bool] = False, set_name: Optional[bool] = True):
        normal = data.get("normal")
        tangent = data.get("tangent")
        interaction = cls(normal, tangent)
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
    tol : float
        Slippage tollerance during contact, expressed as a length in active units.

    Attributes
    ----------
    name : str
        Automatically generated id. You can change the name if you want a more
        human readable input file.
    tol : float
        Slippage tollerance during contact, expressed as a length in active units.
    """

    @units_io(types_in=("length",), types_out=None)
    def __init__(self, tol, **kwargs) -> None:
        super().__init__(normal="HARD", tangent=None, **kwargs)
        self._tol = tol

    @property
    @units_io(types_in=(), types_out="length")
    def tol(self):
        return self._tol

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update(
            {
                "tol": self._tol,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, set_uid: Optional[bool] = False, set_name: Optional[bool] = True):
        tol = data.get("tol")
        interaction = cls(tol)
        return interaction


class HardContactFrictionPenalty(Contact):
    """Hard contact interaction property with friction using a penalty
    formulation.

    Parameters
    ----------
    mu : float
        Friction coefficient for tangential behaviour (dimensionless).
    tol : float
        Slippage tollerance during contact, expressed as a length in active units.

    Attributes
    ----------
    name : str
        Automatically generated id. You can change the name if you want a more
        human readable input file.
    mu : float
        Friction coefficient for tangential behaviour (dimensionless).
    tol : float
        Slippage tollerance during contact, expressed as a length in active units.
    """

    @units_io(types_in=("coefficient_of_friction", "length"), types_out=None)
    def __init__(self, mu, tol, **kwargs) -> None:
        super().__init__(normal="HARD", tangent=mu, **kwargs)
        self._tol = tol

    @property
    @units_io(types_in=(), types_out="coefficient_of_friction")
    def mu(self):
        return self._tangent

    @property
    @units_io(types_in=(), types_out="length")
    def tol(self):
        return self._tol

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update(
            {
                "mu": self._tangent,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, set_uid: Optional[bool] = False, set_name: Optional[bool] = True):
        tol = data.get("tolerance")
        mu = data.get("mu")
        interaction = cls(mu, tol)
        return interaction


class LinearContactFrictionPenalty(Contact):
    """Contact interaction property with linear softnening and friction using a
    penalty formulation.

    Parameters
    ----------
    stiffness : float
        Stiffness of the the contact in the normal direction (translational_stiffness).
    mu : float
        Friction coefficient for tangential behaviour (dimensionless).
    tolerance : float
        Slippage tollerance during contact, expressed as a length in active units.

    Attributes
    ----------
    name : str
        Automatically generated id. You can change the name if you want a more
        human readable input file.
    mu : float
        Friction coefficient for tangential behaviour (dimensionless).
    tolerance : float
        Slippage tollerance during contact, expressed as a length in active units.
    """

    @units_io(types_in=("translational_stiffness", "coefficient_of_friction", "length"), types_out=None)
    def __init__(self, stiffness, mu, tolerance, **kwargs) -> None:
        super().__init__(normal="Linear", tangent=mu, **kwargs)
        self._tolerance = tolerance
        self._stiffness = stiffness

    @property
    @units_io(types_in=(), types_out="translational_stiffness")
    def stiffness(self):
        return self._stiffness

    @stiffness.setter
    def stiffness(self, value):
        self._stiffness = value

    @property
    @units_io(types_in=(), types_out="length")
    def tolerance(self):
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value):
        self._tolerance = value

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update(
            {
                "stiffness": self._stiffness,
                "mu": self._tangent,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, set_uid: Optional[bool] = False, set_name: Optional[bool] = True):
        tol = data.get("tolerance")
        mu = data.get("mu")
        stiffness = data.get("stiffness")
        interaction = cls(stiffness, mu, tol)
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
    This interaction has infinite friction and no numeric parameters.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(normal="HARD", tangent="ROUGH", **kwargs)

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, set_uid: Optional[bool] = False, set_name: Optional[bool] = True):
        interaction = cls()
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

    @units_io(types_in=("temperature", None), types_out=None)
    def __init__(self, temperature_value, temperature_amplitude=None, **kwargs):
        super(_Interaction, self).__init__(**kwargs)
        self._temperature = ScalarLoad(scalar_load=temperature_value, amplitude=temperature_amplitude)

    @property
    @units_io(types_in=(), types_out="temperature")
    def temperature(self):
        return self._temperature

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update(
            {
                "temperature": self._temperature,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        temperature = data.get("temperature")
        interaction = cls(temperature)
        return interaction


class Convection(ThermalInteraction):
    """Convection.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    h : float
        Heat transfer coefficient.
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
        Heat transfer coefficient.
    temperature : ScalarLoad
        Constant temperature load or transient temperature load.

    """

    @units_io(types_in=("heat_transfer_coefficient", "temperature", None), types_out=None)
    def __init__(self, h, temperature_value, temperature_amplitude, **kwargs):
        super().__init__(temperature_value=temperature_value, temperature_amplitude=temperature_amplitude, **kwargs)
        self._h = h

    @property
    @units_io(types_in=(), types_out="heat_transfer_coefficient")
    def h(self):
        return self._h

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update(
            {
                "h": self._h,
                "temperature": self._temperature,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        temperature = data.get("temperature")
        h = data.get("h")
        surface = registry.add_from_data(data.get("surface"), "compas_fea2.model.groups", duplicate=duplicate)  # type: ignore[no-any-return]
        interaction = cls(surface, h, temperature)
        return interaction


class Radiation(ThermalInteraction):
    """Radiation.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    eps : float
        Emissivity coefficient (dimensionless).
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
        Emissivity coefficient (dimensionless).
    temperature : ScalarLoad
        Constant temperature load or transient temperature load.

    """

    @units_io(types_in=("emissivity", "temperature", None), types_out=None)
    def __init__(self, eps, temperature_value, temperature_amplitude, **kwargs):
        super().__init__(temperature_value=temperature_value, temperature_amplitude=temperature_amplitude, **kwargs)
        self._eps = eps

    @property
    @units_io(types_in=(), types_out="emissivity")
    def eps(self):
        return self._eps

    @property
    def __data__(self):
        """Return the data representation of the interaction."""
        data = super().__data__
        data.update(
            {
                "eps": self._eps,
                "temperature": self._temperature,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        temperature = data.get("temperature")
        eps = data.get("eps")
        surface = registry.add_from_data(data.get("surface"), "compas_fea2.model.groups", duplicate=duplicate)  # type: ignore[no-any-return]
        interaction = cls(surface, eps, temperature)
        return interaction
