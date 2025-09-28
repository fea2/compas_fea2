from __future__ import annotations

import functools
import inspect
import contextvars
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple, Union, Iterable

import pint


# =============================================================================
# Unit registry (pretty formatting)
# =============================================================================

ureg = pint.UnitRegistry()
try:
    # Pint ≥ 0.23 (recommended)
    ureg.formatter.default_format = "~P"  # abbreviated units + SI prefixes (compact)
except Exception:
    # Older Pint compatibility
    try:
        ureg.default_format = "~P"
    except Exception:
        pass


# =============================================================================
# Built-in unit systems (type_key -> concrete unit)
# =============================================================================

UNIT_SYSTEMS: Dict[str, Dict[str, pint.Unit]] = {
    "SI": {
        "length":  ureg.meter,
        "time":    ureg.second,
        "mass":    ureg.kilogram,
        "force":   ureg.newton,
        "stress":  ureg.pascal,
        "density": ureg.kilogram / ureg.meter**3,
        "angle":   ureg.radian,
    },
    "SI-mm": {
        "length":  ureg.millimeter,
        "time":    ureg.second,
        "mass":    ureg.kilogram,
        "force":   ureg.newton,
        "stress":  ureg.megapascal,  # common with mm
        "density": ureg.kilogram / ureg.meter**3,
        "angle":   ureg.radian,
    },
    "Imperial": {
        "length":  ureg.inch,
        "time":    ureg.second,
        "mass":    ureg.slug,                # consistent with lbf
        "force":   ureg.pound_force,
        "stress":  ureg.psi,
        "density": ureg.slug / ureg.foot**3,
        "angle":   ureg.degree,
    },
}


# =============================================================================
# Context state: active unit system & display mode; call depth for internals
# =============================================================================

_CURRENT_SYSTEM: contextvars.ContextVar[Union[str, Dict[str, pint.Unit]]] = contextvars.ContextVar(
    "cfea2_unit_system", default="SI"
)
_DISPLAY_MODE: contextvars.ContextVar[str] = contextvars.ContextVar(
    "cfea2_display_mode", default="quantity"  # top-level returns Quantity by default
)
_CALL_DEPTH: contextvars.ContextVar[int] = contextvars.ContextVar(
    "cfea2_call_depth", default=0
)


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


def current_unit_for(type_key: str) -> pint.Unit:
    system = current_unit_system()
    try:
        return system[type_key]
    except KeyError:
        raise KeyError(f"Type '{type_key}' not defined in current unit system. Known: {list(system)}")


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

def _to_magnitude_in_system(val: Any, unit: pint.Unit, *, strict: bool) -> Any:
    """Convert Quantity to given unit and return magnitude; or accept numeric (strict=False)."""
    if _is_qty(val):
        return val.to(unit).m
    if strict:
        raise TypeError(f"Expected a Quantity compatible with '{unit}'.")
    return val

def _wrap_as_quantity(val: Any, unit: Union[pint.Unit, Tuple[pint.Unit, ...]]) -> Any:
    """Wrap numeric magnitudes as Quantity/Quantities, then to_compact() for pretty output."""
    if isinstance(val, tuple):
        if not isinstance(unit, tuple):
            raise TypeError("units_out is not a tuple but function returns a tuple.")
        if len(val) != len(unit):
            raise ValueError("Tuple length of return values and units_out must match.")
        return tuple(_wrap_as_quantity(v, u) for v, u in zip(val, unit))
    q = val * unit
    try:
        return q.to_compact()  # pretty prefixes (kN, MPa, mm, GPa, etc.)
    except Exception:
        return q

def _strip_magnitudes(val: Any) -> Any:
    """Return Quantity magnitudes; pass-through for numerics/objects; handle tuples."""
    if isinstance(val, tuple):
        return tuple(_strip_magnitudes(v) for v in val)
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
    types_in: Optional[Sequence[Optional[str]]],
    types_out: Optional[Union[str, Sequence[str]]],
    *,
    types_in_kw: Optional[Mapping[str, Optional[str]]] = None,
    strict: bool = False,
    sanitize_unknown_kwargs: bool = True,
):
    """
    Dimension-type-based I/O.

    - types_in: sequence of type keys aligned to the first positional-or-keyword params
      after self/cls; use None to skip a slot; may be shorter than the parameter list.
    - types_out: type key (scalar) or tuple of type keys (tuple return) or None.
    - types_in_kw: mapping {kwarg_name: type_key or None} for keyword-only parameters.
    - strict: require Quantities for typed positions/kwargs (else assume numerics are in system units).
    - sanitize_unknown_kwargs: strip any unknown-kwarg Quantity to magnitude before the call.
    """
    types_in_kw = dict(types_in_kw or {})

    def decorate(fn: Callable):
        sig = inspect.signature(fn)
        pos_names = _first_positional_params_after_self(fn)

        @functools.wraps(fn)
        def inner(*args, **kwargs):
            # Bind only what caller provided (no implicit defaults)
            ba = sig.bind_partial(*args, **kwargs)

            def conv(val: Any, type_key: Optional[str]) -> Any:
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

            return (
                _wrap_as_quantity(result, sys_unit_out)
                if _DISPLAY_MODE.get() == "quantity"
                else result
            )

        inner.__types_in__ = types_in
        inner.__types_in_kw__ = dict(types_in_kw)
        inner.__types_out__ = types_out
        return inner

    return decorate


# =============================================================================
# Method decorator: temporarily coerce ALL Quantity attributes to magnitudes
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
m    = ureg.meter
mm   = ureg.millimeter
cm   = ureg.centimeter
dm   = ureg.decimeter
km   = ureg.kilometer

# -- Imperial lengths
inch = ureg.inch
in_  = ureg.inch  # alt alias
ft   = ureg.foot
yd   = ureg.yard
mi   = ureg.mile

# -- Areas
m2   = m**2
cm2  = cm**2
mm2  = mm**2
dm2  = dm**2
km2  = km**2
ft2  = ft**2
in2  = inch**2
yd2  = yd**2
mi2  = mi**2

# -- Volumes
m3   = m**3
cm3  = cm**3
mm3  = mm**3
dm3  = dm**3
ft3  = ft**3
in3  = inch**3
yd3  = yd**3

# -- Mass
kg   = ureg.kilogram
g    = ureg.gram
mg   = ureg.milligram
ton  = 1000 * kg
lb   = ureg.pound         # avoirdupois (mass)
lbm  = ureg.pound         # alias
slug = ureg.slug

# -- Force / torque
N      = ureg.newton
kN     = 1e3 * N
MN     = 1e6 * N
GN     = 1e9 * N
lbf    = ureg.pound_force
kip    = 1000 * lbf
Nm     = N * m
kNm    = kN * m
MNm    = MN * m
lbf_ft = lbf * ft
lbf_in = lbf * inch

# -- Stress / pressure
Pa   = ureg.pascal
kPa  = ureg.kilopascal
MPa  = ureg.megapascal
GPa  = ureg.gigapascal
bar  = ureg.bar
mbar = ureg.millibar
psi  = ureg.psi
ksi  = 1000 * psi
psf  = lbf / ft2

# -- Density / specific weight
rho_m3       = kg / m3
rho_cm3      = g / cm3
rho_mm3      = mg / mm3
rho_ft3      = lb / ft3
rho_slug_ft3 = slug / ft3
gamma_N_m3    = N / m3        # specific weight (metric)
gamma_lbf_ft3 = lbf / ft3     # specific weight (imperial)

# -- Time
s    = ureg.second
ms   = ureg.millisecond
us   = ureg.microsecond
min_ = ureg.minute
h    = ureg.hour
day  = ureg.day

# -- Angle
rad  = ureg.radian
deg  = ureg.degree

# -- Temperature (absolute + deltas)
K     = ureg.kelvin
degC  = ureg.degC
degF  = ureg.degF
R     = ureg.degR              # Rankine (prefer degR for compatibility)
dK    = ureg.kelvin            # temperature difference in K
ddegC = ureg.delta_degC
ddegF = ureg.delta_degF

# -- Velocity
mps  = m / s
kmph = km / h
mph  = mi / h
fps  = ft / s

# -- Acceleration
mps2 = m / s**2
fps2 = ft / s**2
g0   = ureg.g0

# -- Energy / Power
J    = ureg.joule
kJ   = 1e3 * J
MJ   = 1e6 * J
W    = ureg.watt
kW   = 1e3 * W
MW   = 1e6 * W
Wh   = W * h
kWh  = 1e3 * Wh
hp   = ureg.horsepower
BTU  = ureg.Btu                # correct case for Pint
BTU_per_hr = BTU / h

# -- Stiffness / compliance
N_per_m      = N / m
kN_per_mm    = kN / mm
lbf_per_in   = lbf / inch
lbf_per_ft   = lbf / ft

# -- Line / surface / volumetric loads
N_per_m2     = N / m2           # = Pa
kN_per_m2    = kN / m2          # = kPa
N_per_m3     = N / m3
kN_per_m     = kN / m
lbf_per_ft2  = lbf / ft2        # = psf
lbf_per_ft   = lbf / ft

# -- Section properties
I_m4   = m**4         # second moment of area
I_cm4  = cm**4
I_mm4  = mm**4
I_in4  = inch**4
I_ft4  = ft**4

Z_m3   = m**3         # section modulus
Z_cm3  = cm**3
Z_mm3  = mm**3
Z_in3  = inch**3
Z_ft3  = ft**3

J_torsion_m4  = m**4  # torsional constant
J_torsion_in4 = inch**4

# -- Mass/area/length densities
kg_per_m   = kg / m
kg_per_m2  = kg / m2
kg_per_m3  = kg / m3
lb_per_ft  = lb / ft
lb_per_ft2 = lb / ft2
lb_per_ft3 = lb / ft3

# -- Thermal: conductivity, capacity, expansion, flux, HTC, diffusivity
k_W_mK            = W / (m * K)                        # thermal conductivity
k_BTU_hr_ft_degF  = BTU / (h * ft * ddegF)             # imperial conductivity
cp_J_kgK          = J / (kg * K)                       # specific heat capacity
cp_BTU_lb_degF    = BTU / (lb * ddegF)
alpha_1_K         = 1 / K                              # linear thermal expansion
alpha_1_degF      = 1 / ddegF
q_W_m2            = W / m2                             # heat flux
q_BTU_hr_ft2      = BTU / (h * ft2)
h_W_m2K           = W / (m2 * K)                       # heat transfer coefficient
h_BTU_hr_ft2_degF = BTU / (h * ft2 * ddegF)
thermal_diffusivity_m2_s  = m2 / s                     # α = k/(ρ c_p)
thermal_diffusivity_ft2_s = ft2 / s

# -- Viscosity
mu_Pa_s      = Pa * s                                   # dynamic viscosity
poise        = ureg.poise
centipoise   = ureg.centipoise                          # 1 cP = 1 mPa·s
nu_m2_s      = m2 / s                                   # kinematic viscosity
stokes       = ureg.stokes
centistokes  = ureg.centistokes

# -- Electrical
ohm_m   = ureg.ohm * m                                  # resistivity
S_m     = ureg.siemens / m                              # conductivity
A       = ureg.ampere
V       = ureg.volt
C       = ureg.coulomb
F       = ureg.farad
H       = ureg.henry
T       = ureg.tesla
Wb      = ureg.weber
ohm_sym = ureg.ohm     # ASCII alias for Ω

# -- Misc derived
J_per_kg   = J / kg
BTU_per_lb = BTU / lb
W_per_mK   = k_W_mK
Pa_s       = mu_Pa_s


__all__ = [
    # registry & systems
    "ureg",
    "UNIT_SYSTEMS", "list_unit_systems", "set_unit_system", "current_unit_system", "current_unit_for",
    # display & decorators
    "set_output_magnitudes", "output_magnitudes", "units_io", "magnitudes_during_call",

    # convenience aliases
    # lengths
    "m", "mm", "cm", "dm", "km", "inch", "in_", "ft", "yd", "mi",
    # areas
    "m2", "cm2", "mm2", "dm2", "km2", "ft2", "in2", "yd2", "mi2",
    # volumes
    "m3", "cm3", "mm3", "dm3", "ft3", "in3", "yd3",
    # mass
    "kg", "g", "mg", "ton", "lb", "lbm", "slug",
    # force / torque
    "N", "kN", "MN", "GN", "lbf", "kip", "Nm", "kNm", "MNm", "lbf_ft", "lbf_in",
    # stress / pressure
    "Pa", "kPa", "MPa", "GPa", "bar", "mbar", "psi", "ksi", "psf",
    # density / specific weight
    "rho_m3", "rho_cm3", "rho_mm3", "rho_ft3", "rho_slug_ft3", "gamma_N_m3", "gamma_lbf_ft3",
    # time
    "s", "ms", "us", "min_", "h", "day",
    # angle
    "rad", "deg",
    # temperature
    "K", "degC", "degF", "R", "dK", "ddegC", "ddegF",
    # velocity
    "mps", "kmph", "mph", "fps",
    # acceleration
    "mps2", "fps2", "g0",
    # energy / power
    "J", "kJ", "MJ", "W", "kW", "MW", "Wh", "kWh", "hp", "BTU", "BTU_per_hr",
    # stiffness / compliance
    "N_per_m", "kN_per_mm", "lbf_per_in", "lbf_per_ft",
    # loads
    "N_per_m2", "kN_per_m2", "N_per_m3", "kN_per_m", "lbf_per_ft2", "lbf_per_ft",
    # section properties
    "I_m4", "I_cm4", "I_mm4", "I_in4", "I_ft4",
    "Z_m3", "Z_cm3", "Z_mm3", "Z_in3", "Z_ft3",
    "J_torsion_m4", "J_torsion_in4",
    # mass/area/length densities
    "kg_per_m", "kg_per_m2", "kg_per_m3", "lb_per_ft", "lb_per_ft2", "lb_per_ft3",
    # thermal
    "k_W_mK", "k_BTU_hr_ft_degF", "cp_J_kgK", "cp_BTU_lb_degF",
    "alpha_1_K", "alpha_1_degF", "q_W_m2", "q_BTU_hr_ft2",
    "h_W_m2K", "h_BTU_hr_ft2_degF", "thermal_diffusivity_m2_s", "thermal_diffusivity_ft2_s",
    # viscosity
    "mu_Pa_s", "poise", "centipoise", "nu_m2_s", "stokes", "centistokes",
    # electrical
    "ohm_m", "S_m", "A", "V", "C", "F", "H", "T", "Wb", "ohm_sym",
    # misc
    "J_per_kg", "BTU_per_lb", "W_per_mK", "Pa_s",
]