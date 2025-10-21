from __future__ import annotations

import contextvars
import functools
import inspect
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

import pint

# =============================================================================
# Unit registry (pretty formatting)
# =============================================================================

ureg = pint.UnitRegistry()
# Pretty/compact units (abbrev + SI prefixes, e.g. 210 MPa, 12.3 kN, 25 mm)
# (In modern Pint, this is the recommended way to set the default)
ureg.formatter.default_format = "~P"


# =============================================================================
# Built-in unit systems (type_key -> concrete unit)
# =============================================================================

UNIT_SYSTEMS: Dict[str, Dict[str, pint.Unit]] = {
    # ========================================================================
    # SI (meters, newtons, pascals, kelvin)
    # ========================================================================
    "SI": {
        # --- Geometry & kinematics
        "length": ureg.meter,
        "area": ureg.meter**2,
        "volume": ureg.meter**3,
        "angle": ureg.radian,
        "time": ureg.second,
        "velocity": ureg.meter / ureg.second,
        "acceleration": ureg.meter / ureg.second**2,
        "angular_velocity": ureg.radian / ureg.second,
        "angular_acceleration": ureg.radian / ureg.second**2,
        # --- Forces & moments
        "mass": ureg.kilogram,
        "force": ureg.newton,
        "moment": ureg.newton * ureg.meter,  # torque
        # --- Loads
        "line_load": ureg.newton / ureg.meter,  # F/L
        "surface_load": ureg.newton / ureg.meter**2,  # = pressure
        "volumetric_load": ureg.newton / ureg.meter**3,
        # --- Stress/strain & material moduli
        "stress": ureg.pascal,
        "pressure": ureg.pascal,
        "strain": ureg.dimensionless,
        "youngs_modulus": ureg.pascal,
        "shear_modulus": ureg.pascal,  # G
        "bulk_modulus": ureg.pascal,  # K
        "lame_lambda": ureg.pascal,  # λ
        "lame_mu": ureg.pascal,  # μ (= G)
        "poisson_ratio": ureg.dimensionless,
        # --- Section properties (area inertia etc.)
        "area_moment": ureg.meter**4,  # I
        "polar_moment": ureg.meter**4,  # J_p
        "section_modulus": ureg.meter**3,  # Z
        "shear_area": ureg.meter**2,  # A_s (effective)
        "warping_constant": ureg.meter**6,  # C_w (thin-walled)
        "radius_of_gyration": ureg.meter,
        # --- Mass inertia (rigid-body)
        "mass_moment_inertia": ureg.kilogram * ureg.meter**2,
        "mass_polar_inertia": ureg.kilogram * ureg.meter**2,
        # --- Rigidities (EA/EI/GJ/kGA)
        "axial_rigidity": ureg.newton,  # EA
        "bending_rigidity": ureg.newton * ureg.meter**2,  # EI
        "torsional_rigidity": ureg.newton * ureg.meter**2,  # GJ
        "shear_rigidity": ureg.newton,  # kGA
        # --- Stiffness (springs/foundations)
        "translational_stiffness": ureg.newton / ureg.meter,  # k_t
        "rotational_stiffness": (ureg.newton * ureg.meter) / ureg.radian,  # k_r
        "foundation_modulus": ureg.newton / ureg.meter**3,  # Winkler k
        "shear_layer_modulus": ureg.newton / ureg.meter**2,  # Pasternak k_s
        "contact_penalty": ureg.newton / ureg.meter**3,
        # --- Damping
        "viscous_damping": ureg.newton * ureg.second / ureg.meter,  # c (transl.)
        "rotational_damping": (ureg.newton * ureg.meter) * ureg.second / ureg.radian,
        "damping_ratio": ureg.dimensionless,
        "loss_factor": ureg.dimensionless,
        # --- Densities & weights
        "density": ureg.kilogram / ureg.meter**3,  # ρ
        "specific_weight": ureg.newton / ureg.meter**3,  # γ
        # --- Flows
        "mass_flow": ureg.kilogram / ureg.second,
        "volumetric_flow": ureg.meter**3 / ureg.second,
        # --- Energy & power
        "energy": ureg.joule,
        "work": ureg.joule,
        "power": ureg.watt,
        "frequency": ureg.hertz,
        # --- Thermal
        "temperature": ureg.kelvin,  # absolute
        "temperature_diff": ureg.kelvin,  # ΔT
        "thermal_conductivity": ureg.watt / (ureg.meter * ureg.kelvin),
        "thermal_resistivity": (ureg.meter * ureg.kelvin) / ureg.watt,
        "thermal_resistance": ureg.kelvin / ureg.watt,
        "thermal_capacitance": ureg.joule / ureg.kelvin,
        "specific_heat": ureg.joule / (ureg.kilogram * ureg.kelvin),
        "thermal_expansion": 1 / ureg.kelvin,
        "heat_flux": ureg.watt / ureg.meter**2,
        "heat_rate": ureg.watt,
        "heat_source_vol": ureg.watt / ureg.meter**3,
        "heat_source_area": ureg.watt / ureg.meter**2,
        "heat_source_line": ureg.watt / ureg.meter,
        "htc": ureg.watt / (ureg.meter**2 * ureg.kelvin),
        "thermal_diffusivity": ureg.meter**2 / ureg.second,
        "emissivity": ureg.dimensionless,
        "absorptivity": ureg.dimensionless,
        "view_factor": ureg.dimensionless,
        "stefan_boltzmann": ureg.watt / (ureg.meter**2 * ureg.kelvin**4),
        # --- Fluids
        "viscosity_dynamic": ureg.pascal * ureg.second,  # μ
        "viscosity_kinematic": ureg.meter**2 / ureg.second,  # ν
        "pressure_head": ureg.meter,
        # --- Electromagnetics (basic)
        "voltage": ureg.volt,
        "current": ureg.ampere,
        "charge": ureg.coulomb,
        "resistance": ureg.ohm,
        "conductance": ureg.siemens,
        "capacitance": ureg.farad,
        "inductance": ureg.henry,
        "resistivity": ureg.ohm * ureg.meter,  # ρ_elec
        "conductivity": ureg.siemens / ureg.meter,  # σ
        "permittivity": ureg.farad / ureg.meter,  # ε
        "permeability": ureg.henry / ureg.meter,  # μ
        "electric_field": ureg.volt / ureg.meter,  # E
        "magnetic_field": ureg.ampere / ureg.meter,  # H
        "magnetic_flux": ureg.weber,  # Φ
        "magnetic_flux_density": ureg.tesla,  # B
        # --- Misc dimensionless
        "coefficient_of_friction": ureg.dimensionless,
    },
    # ========================================================================
    # SI-mm (millimeters, newtons, megapascal, kelvin)
    # ========================================================================
    "SI-mm": {
        # Geometry & kinematics
        "length": ureg.millimeter,
        "area": ureg.millimeter**2,
        "volume": ureg.millimeter**3,
        "angle": ureg.radian,
        "time": ureg.second,
        "velocity": ureg.millimeter / ureg.second,  # keep m/s
        "acceleration": ureg.millimeter / ureg.second**2,
        "angular_velocity": ureg.radian / ureg.second,
        "angular_acceleration": ureg.radian / ureg.second**2,
        # Forces & moments
        "mass": ureg.ton,
        "force": ureg.newton,
        "moment": ureg.newton * ureg.millimeter,  # N·mm
        # Loads
        "line_load": ureg.newton / ureg.millimeter,  
        "surface_load": ureg.newton / ureg.millimeter**2, 
        "volumetric_load": ureg.newton / ureg.millimeter**3,
        # Stress/strain & moduli
        "stress": ureg.megapascal,  # MPa with mm
        "pressure": ureg.megapascal,
        "strain": ureg.dimensionless,
        "youngs_modulus": ureg.megapascal,
        "shear_modulus": ureg.megapascal,
        "bulk_modulus": ureg.megapascal,
        "lame_lambda": ureg.megapascal,
        "lame_mu": ureg.megapascal,
        "poisson_ratio": ureg.dimensionless,
        # Section properties
        "area_moment": ureg.millimeter**4,
        "polar_moment": ureg.millimeter**4,
        "section_modulus": ureg.millimeter**3,
        "shear_area": ureg.millimeter**2,
        "warping_constant": ureg.millimeter**6,
        "radius_of_gyration": ureg.millimeter,
        # Mass inertia
        "mass_moment_inertia": ureg.ton * ureg.meter**2,  # keep SI base
        "mass_polar_inertia": ureg.ton * ureg.meter**2,
        # Rigidities
        "axial_rigidity": ureg.newton,
        "bending_rigidity": ureg.newton * ureg.millimeter**2,
        "torsional_rigidity": ureg.newton * ureg.millimeter**2,
        "shear_rigidity": ureg.newton,
        # Stiffness
        "translational_stiffness": ureg.newton / ureg.millimeter,
        "rotational_stiffness": (ureg.newton * ureg.millimeter) / ureg.radian,
        "foundation_modulus": ureg.newton / ureg.millimeter**3,
        "shear_layer_modulus": ureg.newton / ureg.millimeter**2,
        "contact_penalty": ureg.newton / ureg.millimeter**3,
        # Damping
        "viscous_damping": ureg.newton * ureg.second / ureg.millimeter,
        "rotational_damping": (ureg.newton * ureg.millimeter) * ureg.second / ureg.radian,
        "damping_ratio": ureg.dimensionless,
        "loss_factor": ureg.dimensionless,
        # Densities & weights
        "density": ureg.ton / ureg.millimeter**3,
        "specific_weight": ureg.newton / ureg.millimeter**3,
        # Flows
        "mass_flow": ureg.ton / ureg.second,
        "volumetric_flow": ureg.millimeter**3 / ureg.second,
        # Energy & power
        "energy": ureg.millijoule,
        "work": ureg.millijoule,
        "power": ureg.milliwatt,
        "frequency": ureg.hertz,
        # Thermal
        "temperature": ureg.kelvin,
        "temperature_diff": ureg.kelvin,
        "thermal_conductivity": ureg.milliwatt / (ureg.millimeter * ureg.kelvin),
        "thermal_resistivity": (ureg.millimeter * ureg.kelvin) / ureg.milliwatt,
        "thermal_resistance": ureg.kelvin / ureg.milliwatt,
        "thermal_capacitance": ureg.millijoule / ureg.kelvin,
        "specific_heat": ureg.joule / (ureg.ton * ureg.kelvin),
        "thermal_expansion": 1 / ureg.kelvin,
        "heat_flux": ureg.milliwatt / ureg.millimeter**2,
        "heat_rate": ureg.milliwatt,
        "heat_source_vol": ureg.milliwatt / ureg.millimeter**3,
        "heat_source_area": ureg.milliwatt / ureg.millimeter**2,
        "heat_source_line": ureg.milliwatt / ureg.millimeter,
        "htc": ureg.milliwatt / (ureg.millimeter**2 * ureg.kelvin),
        "thermal_diffusivity": ureg.millimeter**2 / ureg.second,
        "emissivity": ureg.dimensionless,
        "absorptivity": ureg.dimensionless,
        "view_factor": ureg.dimensionless,
        "stefan_boltzmann": ureg.milliwatt / (ureg.millimeter**2 * ureg.kelvin**4),
        # Fluids
        "viscosity_dynamic": ureg.megapascal * ureg.second,
        "viscosity_kinematic": ureg.millimeter**2 / ureg.second,
        "pressure_head": ureg.millimeter,
        # Electromagnetics
        "voltage": ureg.volt,
        "current": ureg.ampere,
        "charge": ureg.coulomb,
        "resistance": ureg.ohm,
        "conductance": ureg.siemens,
        "capacitance": ureg.farad,
        "inductance": ureg.henry,
        "resistivity": ureg.ohm * ureg.millimeter,
        "conductivity": ureg.siemens / ureg.millimeter,
        "permittivity": ureg.farad / ureg.millimeter,
        "permeability": ureg.henry / ureg.millimeter,
        "electric_field": ureg.volt / ureg.millimeter,
        "magnetic_field": ureg.ampere / ureg.millimeter,
        "magnetic_flux": ureg.weber,
        "magnetic_flux_density": ureg.tesla,
        # Dimensionless
        "coefficient_of_friction": ureg.dimensionless,
    },
    # ========================================================================
    # Imperial (inches, pound-force, psi, °F; ft/s for velocity)
    # ========================================================================
    "Imperial": {
        # Geometry & kinematics
        "length": ureg.inch,
        "area": ureg.inch**2,
        "volume": ureg.inch**3,
        "angle": ureg.radian,
        "time": ureg.second,
        "velocity": ureg.foot / ureg.second,  # ft/s
        "acceleration": ureg.foot / ureg.second**2,
        "angular_velocity": ureg.radian / ureg.second,
        "angular_acceleration": ureg.radian / ureg.second**2,
        # Forces & moments
        "mass": ureg.slug,
        "force": ureg.pound_force,  # lbf
        "moment": ureg.pound_force * ureg.inch,  # lbf·in
        # Loads
        "line_load": ureg.pound_force / ureg.foot,  # lbf/ft
        "surface_load": ureg.pound_force / ureg.foot**2,  # psf
        "volumetric_load": ureg.pound_force / ureg.foot**3,
        # Stress/strain & moduli
        "stress": ureg.psi,  # lbf/in²
        "pressure": ureg.psi,
        "strain": ureg.dimensionless,
        "youngs_modulus": ureg.psi,
        "shear_modulus": ureg.psi,
        "bulk_modulus": ureg.psi,
        "lame_lambda": ureg.psi,
        "lame_mu": ureg.psi,
        "poisson_ratio": ureg.dimensionless,
        # Section properties
        "area_moment": ureg.inch**4,
        "polar_moment": ureg.inch**4,
        "section_modulus": ureg.inch**3,
        "shear_area": ureg.inch**2,
        "warping_constant": ureg.inch**6,
        "radius_of_gyration": ureg.inch,
        # Mass inertia
        "mass_moment_inertia": ureg.slug * ureg.foot**2,
        "mass_polar_inertia": ureg.slug * ureg.foot**2,
        # Rigidities
        "axial_rigidity": ureg.pound_force,
        "bending_rigidity": ureg.pound_force * ureg.inch**2,
        "torsional_rigidity": ureg.pound_force * ureg.inch**2,
        "shear_rigidity": ureg.pound_force,
        # Stiffness
        "translational_stiffness": ureg.pound_force / ureg.inch,  # lbf/in
        "rotational_stiffness": (ureg.pound_force * ureg.inch) / ureg.radian,
        "foundation_modulus": ureg.pound_force / ureg.foot**3,
        "shear_layer_modulus": ureg.pound_force / ureg.foot**2,
        "contact_penalty": ureg.pound_force / ureg.inch**3,
        # Damping
        "viscous_damping": ureg.pound_force * ureg.second / ureg.inch,
        "rotational_damping": (ureg.pound_force * ureg.inch) * ureg.second / ureg.radian,
        "damping_ratio": ureg.dimensionless,
        "loss_factor": ureg.dimensionless,
        # Densities & weights
        "density": ureg.slug / ureg.foot**3,
        "specific_weight": ureg.pound_force / ureg.foot**3,
        # Flows
        "mass_flow": ureg.slug / ureg.second,
        "volumetric_flow": ureg.foot**3 / ureg.second,
        # Energy & power
        "energy": ureg.Btu,  # BTU (energy)
        "work": ureg.pound_force * ureg.foot,  # lbf·ft
        "power": ureg.horsepower,
        "frequency": ureg.hertz,
        # Thermal
        "temperature": ureg.degF,  # absolute (use degR if needed)
        "temperature_diff": ureg.delta_degF,  # differences
        "thermal_conductivity": ureg.Btu / (ureg.hour * ureg.foot * ureg.delta_degF),
        "thermal_resistivity": (ureg.foot * ureg.delta_degF) / (ureg.Btu / ureg.hour),
        "thermal_resistance": ureg.delta_degF / (ureg.Btu / ureg.hour),
        "thermal_capacitance": ureg.Btu / ureg.delta_degF,
        "specific_heat": ureg.Btu / (ureg.pound * ureg.delta_degF),
        "thermal_expansion": 1 / ureg.delta_degF,
        "heat_flux": ureg.Btu / (ureg.hour * ureg.foot**2),
        "heat_rate": ureg.Btu / ureg.hour,
        "heat_source_vol": (ureg.Btu / ureg.hour) / ureg.foot**3,
        "heat_source_area": (ureg.Btu / ureg.hour) / ureg.foot**2,
        "heat_source_line": (ureg.Btu / ureg.hour) / ureg.foot,
        "htc": ureg.Btu / (ureg.hour * ureg.foot**2 * ureg.delta_degF),
        "thermal_diffusivity": ureg.foot**2 / ureg.second,
        "emissivity": ureg.dimensionless,
        "absorptivity": ureg.dimensionless,
        "view_factor": ureg.dimensionless,
        # Keep canonical SI unit for σ in Stefan–Boltzmann; Pint converts as needed.
        "stefan_boltzmann": ureg.watt / (ureg.meter**2 * ureg.kelvin**4),
        # Fluids
        "viscosity_dynamic": ureg.pascal * ureg.second,  # SI base for μ (common in data)
        "viscosity_kinematic": ureg.foot**2 / ureg.second,
        "pressure_head": ureg.foot,
        # Electromagnetics
        "voltage": ureg.volt,
        "current": ureg.ampere,
        "charge": ureg.coulomb,
        "resistance": ureg.ohm,
        "conductance": ureg.siemens,
        "capacitance": ureg.farad,
        "inductance": ureg.henry,
        "resistivity": ureg.ohm * ureg.meter,  # canonical; Pint will convert
        "conductivity": ureg.siemens / ureg.meter,
        "permittivity": ureg.farad / ureg.meter,
        "permeability": ureg.henry / ureg.meter,
        "electric_field": ureg.volt / ureg.meter,
        "magnetic_field": ureg.ampere / ureg.meter,
        "magnetic_flux": ureg.weber,
        "magnetic_flux_density": ureg.tesla,
        # Dimensionless
        "coefficient_of_friction": ureg.dimensionless,
    },
}

# =============================================================================
# Context state: active unit system & display mode; call depth for internals
# =============================================================================

_CURRENT_SYSTEM: contextvars.ContextVar[Union[str, Dict[str, pint.Unit]]] = contextvars.ContextVar("cfea2_unit_system", default="SI")
_DISPLAY_MODE: contextvars.ContextVar[str] = contextvars.ContextVar(
    "cfea2_display_mode",
    default="quantity",  # top-level returns Quantity by default
)
_CALL_DEPTH: contextvars.ContextVar[int] = contextvars.ContextVar("cfea2_call_depth", default=0)


# =============================================================================
# Public helpers
# =============================================================================


def list_unit_systems() -> Sequence[str]:
    return list(UNIT_SYSTEMS.keys())


def set_unit_system(name_or_map: Union[str, Mapping[str, pint.Unit]]) -> None:
    """Select the active unit system by name (e.g. 'SI-mm') or pass a custom {type_key: unit} map."""
    if isinstance(name_or_map, str):
        if name_or_map not in UNIT_SYSTEMS:
            raise KeyError(f"Unknown unit system '{name_or_map}'. Available: {list_unit_systems()}")
        _CURRENT_SYSTEM.set(name_or_map)
    else:
        _CURRENT_SYSTEM.set(dict(name_or_map))


def current_unit_system() -> Mapping[str, pint.Unit]:
    sel = _CURRENT_SYSTEM.get()
    return UNIT_SYSTEMS[sel] if isinstance(sel, str) else sel


def current_unit_for(type_key: Union[str, Sequence[str]]) -> Union[pint.Unit, Tuple[pint.Unit, ...]]:
    """
    Return the concrete unit(s) for a given type key under the active system.

    Supports:
      - str -> unit (e.g. "length" -> meter)
      - tuple/list[str] -> tuple of units element-wise (e.g. ("length","length","length"))
    """
    system = current_unit_system()

    # Vectorized keys
    if isinstance(type_key, (tuple, list)):
        try:
            return tuple(system[k] for k in type_key)
        except KeyError as e:
            raise KeyError(f"Type '{type_key}' not defined in current unit system. Known: {list(system)}") from e

    # Scalar key
    try:
        return system[type_key]
    except KeyError as e:
        raise KeyError(f"Type '{type_key}' not defined in current unit system. Known: {list(system)}") from e


def set_output_magnitudes(enabled: bool) -> None:
    """Top-level display preference: True -> return magnitudes; False -> return Quantities (default)."""
    _DISPLAY_MODE.set("magnitude" if enabled else "quantity")


class output_magnitudes:
    """Context manager to temporarily switch top-level output to magnitudes (floats/arrays)."""

    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._token: Optional[contextvars.Token] = None

    def __enter__(self):
        self._token = _DISPLAY_MODE.set("magnitude" if self._enabled else "quantity")

    def __exit__(self, exc_type, exc, tb):
        if self._token is not None:
            _DISPLAY_MODE.reset(self._token)


def no_units(fn: Callable) -> Callable:
    """Decorator: for this call, force top-level returns to be magnitudes (no Quantities)."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        token = _DISPLAY_MODE.set("magnitude")
        try:
            return fn(*args, **kwargs)
        finally:
            _DISPLAY_MODE.reset(token)

    return wrapper


# =============================================================================
# Internal utilities
# =============================================================================


def _is_qty(x: Any) -> bool:
    # Pint Quantity has .to (convert) and .m (magnitude)
    return hasattr(x, "to") and hasattr(x, "m")


def _to_magnitude_in_system(
    val: Any,
    unit: Union[pint.Unit, Sequence[pint.Unit]],
    *,
    strict: bool,
) -> Any:
    """
    Convert Quantity or sequence of Quantities to magnitudes in the given unit(s).

    - If `unit` is a single unit:
        * Quantity -> convert to that unit and return .m
        * numeric -> if strict False, return as-is (assumed already in system units)
    - If `unit` is a tuple/list of units:
        * `val` must be a sequence of the same length; convert element-wise and
          preserve the original container type (list/tuple).
    """
    # Pass-through None (optional parameters)
    if val is None:
        return None

    # Collapse singleton unit sequences to scalar
    if isinstance(unit, (tuple, list)) and len(unit) == 1:
        unit = unit[0]

    # Vectorized branch
    if isinstance(unit, (tuple, list)):
        if not isinstance(val, (list, tuple)):
            raise TypeError(f"Expected a sequence value for units {unit}, got {type(val).__name__}")
        if len(val) != len(unit):
            raise ValueError(f"Value length {len(val)} does not match units length {len(unit)}")
        out = [_to_magnitude_in_system(v_i, u_i, strict=strict) for v_i, u_i in zip(val, unit)]
        return tuple(out) if isinstance(val, tuple) else out

    # Scalar branch
    if _is_qty(val):
        return val.to(unit).m
    if strict:
        raise TypeError(f"Expected a Quantity compatible with '{unit}'.")
    return val


def _wrap_as_quantity(
    val: Any,
    unit: Union[pint.Unit, Tuple[pint.Unit, ...]],
) -> Any:
    """
    Wrap magnitudes as Pint Quantity/Quantities in the provided unit(s) and apply to_compact()
    for pretty output. Preserves list/tuple container types.
    """
    # Pass-through None
    if val is None:
        return None

    # Collapse singleton unit sequences to scalar
    if isinstance(unit, (tuple, list)) and len(unit) == 1:
        unit = unit[0]

    # Vectorized return
    if isinstance(unit, (tuple, list)):
        if not isinstance(val, (list, tuple)):
            raise TypeError("Function returned a non-sequence, but units_out is a sequence.")
        if len(val) != len(unit):
            raise ValueError("Tuple/list length of return values and units_out must match.")
        out = [_wrap_as_quantity(v, u) for v, u in zip(val, unit)]
        return tuple(out) if isinstance(val, tuple) else out

    # Scalar return
    q = val * unit
    try:
        return q.to_compact()  # pretty prefixes (kN, MPa, mm, GPa, etc.)
    except Exception:
        return q


def _strip_magnitudes(val: Any) -> Any:
    """Return Quantity magnitudes; pass-through for numerics/objects; handle lists/tuples/dicts."""
    if isinstance(val, tuple):
        return tuple(_strip_magnitudes(v) for v in val)
    if isinstance(val, list):
        return [_strip_magnitudes(v) for v in val]
    if isinstance(val, dict):
        return {k: _strip_magnitudes(v) for k, v in val.items()}
    return getattr(val, "m", val)


def _first_positional_params_after_self(fn: Callable) -> Sequence[str]:
    """Names of positional-or-keyword params AFTER 'self'/'cls' (or all, if no self/cls)."""
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    start = 0
    if params:
        p0 = params[0]
        if p0.kind in (p0.POSITIONAL_ONLY, p0.POSITIONAL_OR_KEYWORD) and p0.name in ("self", "cls"):
            start = 1
    names: list[str] = []
    for p in params[start:]:
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD):
            names.append(p.name)
    return names


# =============================================================================
# Decorator: declare TYPES in/out; concrete units come from the active system
# =============================================================================


def units_io(
    types_in: Optional[Sequence[Optional[Union[str, Sequence[str]]]]],
    types_out: Optional[Union[str, Sequence[str]]],
    *,
    types_in_kw: Optional[Mapping[str, Optional[Union[str, Sequence[str]]]]] = None,
    strict: bool = False,
    sanitize_unknown_kwargs: bool = True,
):
    """
    Dimension-type-based I/O.

    Args
    ----
    types_in:
        Sequence aligned to the first positional-or-keyword params after self/cls.
        Use `None` to skip a slot. May be shorter than the parameter list.
        Items may be a `str` type key or a tuple/list of type keys for vector args.
    types_out:
        A single type key (str) for scalar returns, or a sequence of type keys
        for tuple/list returns, or None to return raw.
    types_in_kw:
        Mapping {kwarg_name: type_key or tuple/list of type keys or None} for keyword-only parameters.
    strict:
        If True, require Pint Quantities for typed inputs; if False (default), plain numerics
        are assumed to already be in the active unit system and are passed as-is.
    sanitize_unknown_kwargs:
        If True (default), any kwarg not declared in `types_in_kw` that is a Quantity
        will be stripped to its magnitude before calling the function.
    """
    types_in_kw = dict(types_in_kw or {})

    def decorate(fn: Callable):
        sig = inspect.signature(fn)
        pos_names = _first_positional_params_after_self(fn)

        @functools.wraps(fn)
        def inner(*args, **kwargs):
            # Bind only what caller provided (no implicit defaults)
            ba = sig.bind_partial(*args, **kwargs)

            def conv(val: Any, type_key: Optional[Union[str, Sequence[str]]]) -> Any:
                # Pass-through None for optional parameters
                if val is None:
                    return None
                if type_key is None:
                    return _strip_magnitudes(val) if (sanitize_unknown_kwargs and _is_qty(val)) else val
                return _to_magnitude_in_system(val, current_unit_for(type_key), strict=strict)

            # 1) Positional-or-keyword params by declared types_in
            if types_in:
                for type_key, name in zip(types_in, pos_names):
                    if name in ba.arguments:
                        ba.arguments[name] = conv(ba.arguments[name], type_key)

            # 2) Typed kwargs
            for k, t in types_in_kw.items():
                if k in ba.arguments:
                    ba.arguments[k] = conv(ba.arguments[k], t)

            # 3) Sanitize unknown kwargs (optional)
            if sanitize_unknown_kwargs and ba.kwargs:
                for k, v in list(ba.kwargs.items()):
                    if (k not in types_in_kw) and _is_qty(v):
                        ba.kwargs[k] = _strip_magnitudes(v)

            # 4) Depth-aware call: internals always numeric
            depth = _CALL_DEPTH.get()
            tok = _CALL_DEPTH.set(depth + 1)
            try:
                result = fn(*ba.args, **ba.kwargs)
            finally:
                _CALL_DEPTH.reset(tok)

            # 5) Format output
            if types_out is None:
                return result

            sys_unit_out: Union[pint.Unit, Tuple[pint.Unit, ...]]
            if isinstance(types_out, (tuple, list)):
                sys_unit_out = tuple(current_unit_for(t) for t in types_out)
            else:
                sys_unit_out = current_unit_for(types_out)

            if depth > 0:
                return result  # nested -> keep magnitudes internally

            return _wrap_as_quantity(result, sys_unit_out) if _DISPLAY_MODE.get() == "quantity" else result

        # Introspection aids
        inner.__types_in__ = types_in
        inner.__types_in_kw__ = dict(types_in_kw)
        inner.__types_out__ = types_out
        return inner

    return decorate


# =============================================================================
# Method decorator: temporarily coerce ALL Quantity attrs to magnitudes
# =============================================================================


def magnitudes_during_call(
    *,
    where: Optional[Callable[[str, Any], bool]] = None,
    include: Optional[Iterable[str]] = None,
    exclude: Optional[Iterable[str]] = None,
    deep: bool = False,
    touch_slots: bool = False,
) -> Callable:
    """
    Temporarily coerce selected self.<attr> from Pint Quantity -> magnitude for the duration
    of the method call, then restore original values.

    Args:
        where: predicate (name, value) -> bool selecting attrs (default: value is a Quantity)
        include: explicit attribute names to include (None -> all)
        exclude: attribute names to skip
        deep: if True, also convert Quantities inside lists/tuples/dicts
        touch_slots: if True, also consider names in __slots__ (default False)
    """
    include = set(include or ())
    exclude = set(exclude or ())
    predicate = where or (lambda n, v: _is_qty(v))

    def _to_mag(x: Any) -> Any:
        return x.m if _is_qty(x) else x

    def _coerce_container(x: Any, _deep: bool) -> Any:
        if not _deep:
            return _to_mag(x)
        if isinstance(x, dict):
            return {k: _coerce_container(v, True) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            conv = [_coerce_container(v, True) for v in x]
            return tuple(conv) if isinstance(x, tuple) else conv
        return _to_mag(x)

    def deco(fn: Callable):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            originals: dict[str, Any] = {}

            # Collect attribute names to consider
            names = set(getattr(self, "__dict__", {}).keys())
            if touch_slots:
                for s in getattr(self, "__slots__", ()) or ():
                    if isinstance(s, str):
                        names.add(s)

            # Coerce selected attributes, remember originals
            for name in names:
                if include and name not in include:
                    continue
                if name in exclude:
                    continue
                try:
                    val = getattr(self, name)
                except Exception:
                    continue
                if predicate(name, val):
                    originals[name] = val
                    try:
                        setattr(self, name, _coerce_container(val, deep))
                    except Exception:
                        originals.pop(name, None)  # not writable -> skip

            try:
                return fn(self, *args, **kwargs)
            finally:
                # Restore originals
                for name, val in originals.items():
                    try:
                        setattr(self, name, val)
                    except Exception:
                        pass

        return wrapper

    return deco


# =============================================================================
# Convenience unit aliases (Metric + Imperial), expanded
# =============================================================================
# -- Metric lengths
m = ureg.meter
mm = ureg.millimeter
cm = ureg.centimeter
dm = ureg.decimeter
km = ureg.kilometer

# -- Imperial lengths
inch = ureg.inch
in_ = ureg.inch  # alt alias
ft = ureg.foot
yd = ureg.yard
mi = ureg.mile

# -- Areas
m2 = m**2
cm2 = cm**2
mm2 = mm**2
dm2 = dm**2
km2 = km**2
ft2 = ft**2
in2 = inch**2
yd2 = yd**2
mi2 = mi**2

# -- Volumes
m3 = m**3
cm3 = cm**3
mm3 = mm**3
dm3 = dm**3
ft3 = ft**3
in3 = inch**3
yd3 = yd**3

# -- Mass
kg = ureg.kilogram
g = ureg.gram
mg = ureg.milligram
ton = 1000 * kg
lb = ureg.pound  # avoirdupois (mass)
lbm = ureg.pound  # alias
slug = ureg.slug

# -- Force / torque
N = ureg.newton
kN = 1e3 * N
MN = 1e6 * N
GN = 1e9 * N
lbf = ureg.pound_force
kip = 1000 * lbf
Nm = N * m
kNm = kN * m
MNm = MN * m
lbf_ft = lbf * ft
lbf_in = lbf * inch

# -- Stress / pressure
Pa = ureg.pascal
kPa = ureg.kilopascal
MPa = ureg.megapascal
GPa = ureg.gigapascal
bar = ureg.bar
mbar = ureg.millibar
psi = ureg.psi
ksi = 1000 * psi
psf = lbf / ft2

# -- Density / specific weight
rho_m3 = kg / m3
rho_cm3 = g / cm3
rho_mm3 = mg / mm3
rho_ft3 = lb / ft3
rho_slug_ft3 = slug / ft3
gamma_N_m3 = N / m3
gamma_lbf_ft3 = lbf / ft3

# -- Time
s = ureg.second
ms = ureg.millisecond
us = ureg.microsecond
min_ = ureg.minute
h = ureg.hour
day = ureg.day

# -- Angle
rad = ureg.radian
deg = ureg.degree

# -- Temperature (absolute + deltas)
K = ureg.kelvin
degC = ureg.degC
degF = ureg.degF
R = ureg.degR
dK = ureg.kelvin  # temperature difference in K
ddegC = ureg.delta_degC
ddegF = ureg.delta_degF

# -- Velocity
mps = m / s
kmph = km / h
mph = mi / h
fps = ft / s

# -- Acceleration
mps2 = m / s**2
fps2 = ft / s**2
g0 = ureg.g0

# -- Energy / Power
J = ureg.joule
kJ = 1e3 * J
MJ = 1e6 * J
W = ureg.watt
kW = 1e3 * W
MW = 1e6 * W
Wh = W * h
kWh = 1e3 * Wh
hp = ureg.horsepower
BTU = ureg.Btu
BTU_per_hr = BTU / h

# -- Stiffness / compliance
N_per_m = N / m
kN_per_mm = kN / mm
lbf_per_in = lbf / inch
lbf_per_ft = lbf / ft

# -- Line / surface / volumetric loads
N_per_m2 = N / m2  # = Pa
kN_per_m2 = kN / m2  # = kPa
N_per_m3 = N / m3
kN_per_m = kN / m
lbf_per_ft2 = lbf / ft2  # = psf
lbf_per_ft = lbf / ft

# -- Section properties
I_m4 = m**4
I_cm4 = cm**4
I_mm4 = mm**4
I_in4 = inch**4
I_ft4 = ft**4

Z_m3 = m**3
Z_cm3 = cm**3
Z_mm3 = mm**3
Z_in3 = inch**3
Z_ft3 = ft**3

J_torsion_m4 = m**4
J_torsion_in4 = inch**4

# -- Mass/area/length densities
kg_per_m = kg / m
kg_per_m2 = kg / m2
kg_per_m3 = kg / m3
lb_per_ft = lb / ft
lb_per_ft2 = lb / ft2
lb_per_ft3 = lb / ft3

# -- Thermal: conductivity, capacity, expansion, flux, HTC, diffusivity
k_W_mK = W / (m * K)
k_BTU_hr_ft_degF = BTU / (h * ft * ddegF)
cp_J_kgK = J / (kg * K)
cp_BTU_lb_degF = BTU / (lb * ddegF)
alpha_1_K = 1 / K
alpha_1_degF = 1 / ddegF
q_W_m2 = W / m2
q_BTU_hr_ft2 = BTU / (h * ft2)
h_W_m2K = W / (m2 * K)
h_BTU_hr_ft2_degF = BTU / (h * ft2 * ddegF)
thermal_diffusivity_m2_s = m2 / s
thermal_diffusivity_ft2_s = ft2 / s

# -- Viscosity
mu_Pa_s = Pa * s
poise = ureg.poise
centipoise = ureg.centipoise
nu_m2_s = m2 / s
stokes = ureg.stokes
centistokes = ureg.centistokes

# -- Electrical
ohm_m = ureg.ohm * m
S_m = ureg.siemens / m
A = ureg.ampere
V = ureg.volt
C = ureg.coulomb
F = ureg.farad
H = ureg.henry
T = ureg.tesla
Wb = ureg.weber
ohm_sym = ureg.ohm  # ASCII alias

# -- Misc derived
J_per_kg = J / kg
BTU_per_lb = BTU / lb
W_per_mK = k_W_mK
Pa_s = mu_Pa_s


__all__ = [
    # registry & systems
    "ureg",
    "UNIT_SYSTEMS",
    "list_unit_systems",
    "set_unit_system",
    "current_unit_system",
    "current_unit_for",
    # display & decorators
    "set_output_magnitudes",
    "output_magnitudes",
    "units_io",
    "magnitudes_during_call",
    "no_units",
    # convenience aliases
    # lengths
    "m",
    "mm",
    "cm",
    "dm",
    "km",
    "inch",
    "in_",
    "ft",
    "yd",
    "mi",
    # areas
    "m2",
    "cm2",
    "mm2",
    "dm2",
    "km2",
    "ft2",
    "in2",
    "yd2",
    "mi2",
    # volumes
    "m3",
    "cm3",
    "mm3",
    "dm3",
    "ft3",
    "in3",
    "yd3",
    # mass
    "kg",
    "g",
    "mg",
    "ton",
    "lb",
    "lbm",
    "slug",
    # force / torque
    "N",
    "kN",
    "MN",
    "GN",
    "lbf",
    "kip",
    "Nm",
    "kNm",
    "MNm",
    "lbf_ft",
    "lbf_in",
    # stress / pressure
    "Pa",
    "kPa",
    "MPa",
    "GPa",
    "bar",
    "mbar",
    "psi",
    "ksi",
    "psf",
    # density / specific weight
    "rho_m3",
    "rho_cm3",
    "rho_mm3",
    "rho_ft3",
    "rho_slug_ft3",
    "gamma_N_m3",
    "gamma_lbf_ft3",
    # time
    "s",
    "ms",
    "us",
    "min_",
    "h",
    "day",
    # angle
    "rad",
    "deg",
    # temperature
    "K",
    "degC",
    "degF",
    "R",
    "dK",
    "ddegC",
    "ddegF",
    # velocity
    "mps",
    "kmph",
    "mph",
    "fps",
    # acceleration
    "mps2",
    "fps2",
    "g0",
    # energy / power
    "J",
    "kJ",
    "MJ",
    "W",
    "kW",
    "MW",
    "Wh",
    "kWh",
    "hp",
    "BTU",
    "BTU_per_hr",
    # stiffness / compliance
    "N_per_m",
    "kN_per_mm",
    "lbf_per_in",
    "lbf_per_ft",
    # loads
    "N_per_m2",
    "kN_per_m2",
    "N_per_m3",
    "kN_per_m",
    "lbf_per_ft2",
    "lbf_per_ft",
    # section properties
    "I_m4",
    "I_cm4",
    "I_mm4",
    "I_in4",
    "I_ft4",
    "Z_m3",
    "Z_cm3",
    "Z_mm3",
    "Z_in3",
    "Z_ft3",
    "J_torsion_m4",
    "J_torsion_in4",
    # mass/area/length densities
    "kg_per_m",
    "kg_per_m2",
    "kg_per_m3",
    "lb_per_ft",
    "lb_per_ft2",
    "lb_per_ft3",
    # thermal
    "k_W_mK",
    "k_BTU_hr_ft_degF",
    "cp_J_kgK",
    "cp_BTU_lb_degF",
    "alpha_1_K",
    "alpha_1_degF",
    "q_W_m2",
    "q_BTU_hr_ft2",
    "h_W_m2K",
    "h_BTU_hr_ft2_degF",
    "thermal_diffusivity_m2_s",
    "thermal_diffusivity_ft2_s",
    # viscosity
    "mu_Pa_s",
    "poise",
    "centipoise",
    "nu_m2_s",
    "stokes",
    "centistokes",
    # electrical
    "ohm_m",
    "S_m",
    "A",
    "V",
    "C",
    "F",
    "H",
    "T",
    "Wb",
    "ohm_sym",
    # misc
    "J_per_kg",
    "BTU_per_lb",
    "W_per_mK",
    "Pa_s",
]
