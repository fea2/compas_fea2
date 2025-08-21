from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import Mapping
from typing import Optional
from typing import Union

from compas_fea2.base import FEAData
from compas_fea2.base import from_data
from compas_fea2.problem.groups import LoadsFieldGroup

if TYPE_CHECKING:
    from compas_fea2.model import Model
    from compas_fea2.problem import Problem
    from compas_fea2.problem import _Step

# Eurocode default combination factors (typical for buildings; override for your project as needed).
_EC_PSI0_DEFAULT: Dict[str, float] = {
    "Q": 0.7,  # Imposed (floors)
    "Q_ROOF": 0.7,  # Roof imposed
    "S": 0.5,  # Snow
    "W": 0.6,  # Wind
    "T": 0.6,  # Temperature
}
_EC_PSI1_DEFAULT: Dict[str, float] = {
    "Q": 0.5,
    "Q_ROOF": 0.5,
    "S": 0.2,
    "W": 0.2,
    "T": 0.5,
}
_EC_PSI2_DEFAULT: Dict[str, float] = {
    "Q": 0.3,
    "Q_ROOF": 0.3,
    "S": 0.2,
    "W": 0.0,
    "T": 0.0,
}

# EC/ASCE load-case name defaults (keep them separate to avoid mixing)
_EC_DEAD_CASES_DEFAULT: Iterable[str] = ("G", "G1", "G2")
_ASCE_DEAD_CASES_DEFAULT: Iterable[str] = ("D", "DL", "SDL")

# Allow factors per load case to be a single float or a mapping by role (primary/secondary/...).
FactorByRole = Mapping[str, float]
FactorSpec = Union[float, FactorByRole]


class LoadFieldsCombination(FEAData):
    """
    Represents a linear combination of load fields for a structural analysis step.

    This class allows you to define how different load cases (dead, imposed, wind, snow, etc.)
    are combined for analysis according to design codes (Eurocode, ASCE 7, etc.).
    Each load case is assigned a factor, which can be a single value or a mapping by "role"
    (primary, secondary, tertiary, default) to support code-specific combination rules.

    The combination is typically attached to an analysis step, and is used to scale
    the loads applied in that step. The class provides factory methods for standard
    Eurocode and ASCE 7 combinations, which return ready-to-use objects with the
    correct factors for each load case.

    Parameters
    ----------
    case_factor_dict : Mapping[str, float] | Mapping[str, Mapping[str, float]]
        Dictionary mapping load case names to factors. Each value can be:
        - a single float (applied to all fields of that case), or
        - a mapping with keys 'primary', 'secondary', 'tertiary', and/or 'default'
          to scale fields according to their combination_rank.
    name : str, optional
        Optional name for the combination (e.g. "EC-ULS-PERS", "ASCE7-LRFD-WIND").

    Usage
    -----
    Use the provided classmethods to create combinations for standard codes:

        combo = LoadFieldsCombination.ec_uls_persistent()
        combo = LoadFieldsCombination.asce7_lrfd_basic()

    Attach the combination to a step, or use `combine_fields` to apply it directly
    to a set of load fields.

    Notes
    -----
    - All combinations are "per-role": factors are chosen according to the field's
      `combination_rank` attribute.
    - Load case names must match the standard for the chosen code (e.g. "G", "Q", "W" for Eurocode).
    """

    def __init__(self, case_factor_dict: Mapping[str, FactorSpec], **kwargs: Any):
        super(LoadFieldsCombination, self).__init__(**kwargs)
        self.case_factor_dict = dict(case_factor_dict)  # validates

    # ---------------------------
    # Serialization
    # ---------------------------

    @property
    def __data__(self) -> Dict[str, Any]:
        """Serialized representation used by compas_fea2."""
        base = super().__data__
        base.update(
            {
                "case_factor_dict": self._case_factor_dict,
            }
        )
        return base

    @from_data
    @classmethod
    def __from_data__(cls, data: Mapping[str, Any], registry=None, duplicate: bool = True) -> "LoadFieldsCombination":
        """Reconstruct from serialized data."""
        return cls(case_factor_dict=data["case_factor_dict"])

    # ---------------------------
    # Helpers
    # ---------------------------

    @staticmethod
    def _role_map(*, primary: float | None = None, secondary: float | None = None, tertiary: float | None = None, default: float | None = None) -> FactorByRole:
        """Build a compact role map including only provided entries."""
        m: Dict[str, float] = {}
        if primary is not None:
            m["primary"] = float(primary)
        if secondary is not None:
            m["secondary"] = float(secondary)
        if tertiary is not None:
            m["tertiary"] = float(tertiary)
        if default is not None:
            m["default"] = float(default)
        return m

    @staticmethod
    def _uniform_roles(v: float) -> FactorByRole:
        """Role map with the same factor for all roles."""
        return LoadFieldsCombination._role_map(primary=v, secondary=v, tertiary=v, default=v)

    # ---------------------------
    # Properties
    # ---------------------------

    @property
    def load_cases(self) -> Iterator[str]:
        """Iterate over the names of the load cases in this combination."""
        for k in self._case_factor_dict.keys():
            yield k

    @property
    def load_factors(self) -> Iterator[Union[float, FactorByRole]]:
        """Iterate over the factors in this combination (float or per-role mapping)."""
        for v in self._case_factor_dict.values():
            yield v

    # ---------------------------
    # Validation
    # ---------------------------

    @property
    def case_factor_dict(self) -> Dict[str, FactorSpec]:
        """Return the mapping of load case to factor or per-role factor mapping."""
        return self._case_factor_dict

    @case_factor_dict.setter
    def case_factor_dict(self, value: Mapping[str, FactorSpec]) -> None:
        if not isinstance(value, Mapping):
            raise TypeError("case_factor_dict must be a mapping of {str: float | {role: float}}.")
        normalized: Dict[str, FactorSpec] = {}
        for k, v in value.items():
            if not isinstance(k, str):
                raise TypeError(f"Load case names must be str, got {type(k)!r}.")
            if isinstance(v, Mapping):
                role_map: Dict[str, float] = {}
                for rk, rv in v.items():
                    if not isinstance(rk, str):
                        raise TypeError(f"Role keys must be str, got {type(rk)!r} for case '{k}'.")
                    try:
                        role_map[rk] = float(rv)
                    except (TypeError, ValueError):
                        raise TypeError(f"Role factor for case '{k}'[{rk!r}] must be a real number, got {rv!r}.")
                normalized[k] = role_map
            else:
                try:
                    normalized[k] = float(v)
                except (TypeError, ValueError):
                    raise TypeError(f"Load factor for case '{k}' must be a real number, got {v!r}.")
        self._case_factor_dict = normalized

    # ---------------------------
    # Associations
    # ---------------------------

    @property
    def step(self) -> Optional["_Step"]:
        """The registered step, if this combination is attached to a step."""
        if getattr(self, "_registration", None):
            return self._registration
        return None

    @property
    def problem(self) -> Optional["Problem"]:
        """The problem this combination belongs to, if any."""
        if self.step:
            return self.step.problem
        return None

    @property
    def model(self) -> Optional["Model"]:
        """The model this combination belongs to, if any."""
        if self.problem:
            return self.problem.model
        return None

    # ---------------------------
    # Combination of fields
    # ---------------------------

    def combine_fields(self, fields: Union[Iterable[Any], LoadsFieldGroup]) -> LoadsFieldGroup:
        """Build a LoadsFieldGroup for the linear combination applied to the given fields.

        If a per-role mapping was provided for a load case, the factor is chosen
        using the field's combination_rank:
        - rank 1 -> 'primary'
        - rank 2 -> 'secondary'
        - rank >=3 -> 'tertiary'
        """
        iterable = fields.members if isinstance(fields, LoadsFieldGroup) else fields

        def select_factor(spec: FactorSpec, rank: int) -> float:
            if not isinstance(spec, Mapping):
                return float(spec)
            role_key = "primary" if rank == 1 else ("secondary" if rank == 2 else ("tertiary" if rank >= 3 else "default"))
            if role_key in spec:
                return float(spec[role_key])  # type: ignore[index]
            # sensible fallbacks
            for key in ("default", "secondary", "primary", "tertiary"):
                if key in spec:
                    return float(spec[key])  # type: ignore[index]
            return 0.0  # not specified -> ignore

        scaled_fields = []
        for field in iterable:
            lcase = getattr(field, "load_case", None)
            if lcase not in self.case_factor_dict:
                continue
            # default to 1 (primary) when not specified
            rank = int(getattr(field, "combination_rank", 1) or 1)
            spec = self.case_factor_dict[lcase]
            factor = select_factor(spec, rank)
            if factor == 0.0:
                continue
            scaled_field = field if factor == 1.0 else factor * field
            scaled_fields.append(scaled_field)
        return LoadsFieldGroup(members=scaled_fields)

    def combine_for_step(self, step: "_Step") -> LoadsFieldGroup:
        """Build a LoadsFieldGroup representing the linear combination for this step."""
        fields = getattr(step, "fields", [])
        return self.combine_fields(fields)

    # ----------------------------------------------------
    # Eurocode EN 1990 factories (per-role, parameterless)
    # ----------------------------------------------------

    @classmethod
    def ec_uls_persistent(cls) -> "LoadFieldsCombination":
        """EN 1990 ULS persistent/transient (per-role).
        - G: 1.35
        - Variables: primary=1.5, others=1.5*psi0
        """
        gamma_g = 1.35
        gamma_q = 1.5
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(gamma_g) for d in _EC_DEAD_CASES_DEFAULT}
        for case, p in _EC_PSI0_DEFAULT.items():
            factors[case] = cls._role_map(primary=gamma_q, secondary=gamma_q * p, tertiary=gamma_q * p, default=gamma_q * p)
        return cls(case_factor_dict=factors, name="EC-ULS-PERS")

    @classmethod
    def ec_uls_accidental(cls) -> "LoadFieldsCombination":
        """EN 1990 ULS accidental (per-role).
        - G: 1.0
        - A: 1.0
        - Other variables: psi1 (all roles)
        """
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.0) for d in _EC_DEAD_CASES_DEFAULT}
        factors["A"] = cls._uniform_roles(1.0)
        for case, p in _EC_PSI1_DEFAULT.items():
            if case == "A":
                continue
            factors[case] = cls._uniform_roles(p)
        return cls(case_factor_dict=factors, name="EC-ULS-ACC")

    @classmethod
    def ec_sls_characteristic(cls) -> "LoadFieldsCombination":
        """EN 1990 SLS characteristic (per-role).
        - G: 1.0
        - Variables: primary=1.0, others=psi0
        """
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.0) for d in _EC_DEAD_CASES_DEFAULT}
        for case, p in _EC_PSI0_DEFAULT.items():
            factors[case] = cls._role_map(primary=1.0, secondary=p, tertiary=p, default=p)
        return cls(case_factor_dict=factors, name="EC-SLS-CHAR")

    @classmethod
    def ec_sls_frequent(cls) -> "LoadFieldsCombination":
        """EN 1990 SLS frequent (per-role).
        - G: 1.0
        - Variables: primary=psi1, others=psi2
        """
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.0) for d in _EC_DEAD_CASES_DEFAULT}
        cases = set(_EC_PSI1_DEFAULT) | set(_EC_PSI2_DEFAULT)
        for case in cases:
            p1 = _EC_PSI1_DEFAULT.get(case, 0.0)
            p2 = _EC_PSI2_DEFAULT.get(case, 0.0)
            factors[case] = cls._role_map(primary=p1, secondary=p2, tertiary=p2, default=p2)
        return cls(case_factor_dict=factors, name="EC-SLS-FREQ")

    @classmethod
    def ec_sls_quasi_permanent(cls) -> "LoadFieldsCombination":
        """EN 1990 SLS quasi-permanent (per-role).
        - G: 1.0
        - Variables: psi2 (all roles)
        """
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.0) for d in _EC_DEAD_CASES_DEFAULT}
        for case, p in _EC_PSI2_DEFAULT.items():
            factors[case] = cls._uniform_roles(p)
        return cls(case_factor_dict=factors, name="EC-SLS-QP")

    # ---------------------------
    # ASCE 7 (LRFD/ASD) factories
    # ---------------------------

    @classmethod
    def asce7_lrfd_1_4D(cls) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 1.4D (per-role)."""
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.4) for d in _ASCE_DEAD_CASES_DEFAULT}
        return cls(case_factor_dict=factors, name="ASCE7-LRFD-1.4D")

    @classmethod
    def asce7_lrfd_basic(cls) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 1.2D + 1.6L + 0.5(Lr + S + R) (per-role)."""
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.2) for d in _ASCE_DEAD_CASES_DEFAULT}
        factors.update({"LL": cls._uniform_roles(1.6), "Lr": cls._uniform_roles(0.5), "S": cls._uniform_roles(0.5), "R": cls._uniform_roles(0.5)})
        return cls(case_factor_dict=factors, name="ASCE7-LRFD-BASIC")

    @classmethod
    def asce7_lrfd_wind(cls) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 1.2D + 1.0W + 1.6L + 0.5(Lr + S + R) (per-role)."""
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.2) for d in _ASCE_DEAD_CASES_DEFAULT}
        factors.update({"W": cls._uniform_roles(1.0), "LL": cls._uniform_roles(1.6), "Lr": cls._uniform_roles(0.5), "S": cls._uniform_roles(0.5), "R": cls._uniform_roles(0.5)})
        return cls(case_factor_dict=factors, name="ASCE7-LRFD-WIND")

    @classmethod
    def asce7_lrfd_seismic(cls) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 1.2D + 1.0E + 1.6L + 0.2S (per-role)."""
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.2) for d in _ASCE_DEAD_CASES_DEFAULT}
        factors.update({"E": cls._uniform_roles(1.0), "LL": cls._uniform_roles(1.6), "S": cls._uniform_roles(0.2)})
        return cls(case_factor_dict=factors, name="ASCE7-LRFD-SEISMIC")

    @classmethod
    def asce7_lrfd_wind_uplift(cls) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 0.9D + 1.0W (per-role)."""
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(0.9) for d in _ASCE_DEAD_CASES_DEFAULT}
        factors.update({"W": cls._uniform_roles(1.0)})
        return cls(case_factor_dict=factors, name="ASCE7-LRFD-0.9D+W")

    @classmethod
    def asce7_lrfd_seismic_uplift(cls) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 0.9D + 1.0E (per-role)."""
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(0.9) for d in _ASCE_DEAD_CASES_DEFAULT}
        factors.update({"E": cls._uniform_roles(1.0)})
        return cls(case_factor_dict=factors, name="ASCE7-LRFD-0.9D+E")

    @classmethod
    def asce7_asd_basic(cls) -> "LoadFieldsCombination":
        """ASCE 7 ASD: D + L + (Lr + S + R) (per-role)."""
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.0) for d in _ASCE_DEAD_CASES_DEFAULT}
        factors.update({"LL": cls._uniform_roles(1.0), "Lr": cls._uniform_roles(1.0), "S": cls._uniform_roles(1.0), "R": cls._uniform_roles(1.0)})
        return cls(case_factor_dict=factors, name="ASCE7-ASD-BASIC")

    @classmethod
    def asce7_asd_wind(cls) -> "LoadFieldsCombination":
        """ASCE 7 ASD: D + 0.75L + 0.75(Lr + S + R) + 0.6W (per-role)."""
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.0) for d in _ASCE_DEAD_CASES_DEFAULT}
        factors.update({"LL": cls._uniform_roles(0.75), "Lr": cls._uniform_roles(0.75), "S": cls._uniform_roles(0.75), "R": cls._uniform_roles(0.75), "W": cls._uniform_roles(0.6)})
        return cls(case_factor_dict=factors, name="ASCE7-ASD-WIND")

    @classmethod
    def asce7_asd_seismic(cls) -> "LoadFieldsCombination":
        """ASCE 7 ASD: D + 0.75L + 0.2S + 0.7E (per-role)."""
        factors: Dict[str, FactorSpec] = {d: cls._uniform_roles(1.0) for d in _ASCE_DEAD_CASES_DEFAULT}
        factors.update({"LL": cls._uniform_roles(0.75), "S": cls._uniform_roles(0.2), "E": cls._uniform_roles(0.7)})
        return cls(case_factor_dict=factors, name="ASCE7-ASD-SEISMIC")


class StepsCombination(FEAData):
    """
    Represents a combination of results from multiple analysis steps.

    This class is intended for post-processing, where results from several steps
    (e.g., different load scenarios or time increments) are summed or otherwise
    combined to produce a final result. This is useful for envelope calculations,
    staged construction, or other advanced analysis workflows.

    Usage
    -----
    Not implemented yet. Intended usage:

        steps_comb = StepsCombination(...)
        result = steps_comb.combine_results([step1, step2, ...])

    Notes
    -----
    - By default, compas_fea2 analyses are non-linear: the response of previous steps
      is used as the starting point for subsequent steps.
    - The sequence of steps can affect the results.
    - This class is a placeholder for future development.
    """

    def __init__(self, **kwargs: Any):
        """Not implemented yet."""
        raise NotImplementedError()
