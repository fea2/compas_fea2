from typing import TYPE_CHECKING, Any, Dict, Iterable, Iterator, Mapping, Optional, Union

from compas_fea2.base import FEAData, from_data
from compas_fea2.problem.groups import LoadsFieldGroup

if TYPE_CHECKING:
    from compas_fea2.model import Model
    from compas_fea2.problem import Problem
    from compas_fea2.problem import _Step
    from compas_fea2.model.nodes import Node

# Eurocode default combination factors (typical for buildings; override for your project as needed).
_EC_PSI0_DEFAULT: Dict[str, float] = {
    "Q_IMP": 0.7,  # Imposed (floors)
    "Q_ROOF": 0.7, # Roof imposed
    "S": 0.5,      # Snow
    "W": 0.6,      # Wind
    "T": 0.6,      # Temperature
}
_EC_PSI1_DEFAULT: Dict[str, float] = {
    "Q_IMP": 0.5,
    "Q_ROOF": 0.5,
    "S": 0.2,
    "W": 0.2,
    "T": 0.5,
}
_EC_PSI2_DEFAULT: Dict[str, float] = {
    "Q_IMP": 0.3,
    "Q_ROOF": 0.3,
    "S": 0.2,
    "W": 0.0,
    "T": 0.0,
}

# EC/ASCE load-case name defaults (keep them separate to avoid mixing)
_EC_DEAD_CASES_DEFAULT: Iterable[str] = ("G", "G1", "G2")
_ASCE_DEAD_CASES_DEFAULT: Iterable[str] = ("D", "DL", "SDL")

# Aliases to bridge common US names to EC action symbols (used by EC factories).
# If a factor is defined for the canonical EC name, we duplicate it to the alias.
_EC_ALIASES: Dict[str, str] = {
    "DL": "G",
    "SDL": "G2",
    "LL": "Q_IMP",
    "Lr": "Q_ROOF",
}

# Allow factors per load case to be a single float or a mapping by role (primary/secondary/...).
FactorByRole = Mapping[str, float]
FactorSpec = Union[float, FactorByRole]


class LoadFieldsCombination(FEAData):
    """Represents a linear combination of load fields, typically applied per analysis step.

    Parameters
    ----------
    case_factor_dict : Mapping[str, float] | Mapping[str, Mapping[str, float]]
        Factors per load case. Each value can be:
        - a single float (applied to all fields of that case), or
        - a mapping with keys 'primary', 'secondary', 'tertiary', and/or 'default'
          to scale fields according to their combination_rank.
    name : str, optional
        Optional name for the combination (e.g. "EC-ULS-PERS[Q_IMP]", "ASCE7-LRFD-WIND").
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
        base.update({
            "case_factor_dict": self._case_factor_dict,
        })
        return base

    @from_data
    @classmethod
    def __from_data__(
        cls,
        data: Mapping[str, Any],
        registry=None,
        duplicate: bool = True
    ) -> "LoadFieldsCombination":
        """Reconstruct from serialized data."""
        return cls(case_factor_dict=data["case_factor_dict"])

    # ---------------------------
    # Helpers
    # ---------------------------

    @staticmethod
    def _role_map(
        *,
        primary: float | None = None,
        secondary: float | None = None,
        tertiary: float | None = None,
        default: float | None = None
    ) -> FactorByRole:
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
    def _apply_aliases(factors: Mapping[str, FactorSpec], aliases: Mapping[str, str]) -> Dict[str, FactorSpec]:
        """Duplicate canonical entries to their alias names if not already present."""
        out = dict(factors)
        for alias, canon in aliases.items():
            if canon in out and alias not in out:
                out[alias] = out[canon]
        return out

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
                        raise TypeError(
                            f"Role factor for case '{k}'[{rk!r}] must be a real number, got {rv!r}."
                        )
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
        - otherwise -> 'default' (fallbacks apply)
        """
        iterable = fields.members if isinstance(fields, LoadsFieldGroup) else fields

        def select_factor(spec: FactorSpec, rank: int) -> float:
            if not isinstance(spec, Mapping):
                return float(spec)
            role_key = (
                "primary" if rank == 1
                else ("secondary" if rank == 2 else ("tertiary" if rank >= 3 else "default"))
            )
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
            rank = int(getattr(field, "combination_rank", 0) or 0)
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

    # ---------------------------
    # Eurocode EN 1990 factories (scalar factors)
    # ---------------------------

    @classmethod
    def ec_uls_persistent(
        cls,
        leading: str = "Q_IMP",
        *,
        gamma_g: float = 1.35,
        gamma_q: float = 1.5,
        dead_cases: Iterable[str] = _EC_DEAD_CASES_DEFAULT,
        psi0: Optional[Mapping[str, float]] = None,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ULS persistent/transient (EN 1990):
        sum(gamma_G*Gk) + gamma_Q*Qk,leading + sum(gamma_Q*psi0,i*Qk,i)
        """
        psi0_map = dict(_EC_PSI0_DEFAULT)
        if psi0:
            psi0_map.update(psi0)
        lead = _EC_ALIASES.get(leading, leading)
        factors: Dict[str, FactorSpec] = {d: gamma_g for d in dead_cases}
        factors[lead] = gamma_q
        for case, p in psi0_map.items():
            if case == lead:
                continue
            factors[case] = gamma_q * p
        factors = cls._apply_aliases(factors, _EC_ALIASES)
        return cls(case_factor_dict=factors, name=name or f"EC-ULS-PERS[{lead}]")

    @classmethod
    def ec_uls_accidental(
        cls,
        accidental: str,
        *,
        gamma_g: float = 1.0,
        gamma_q_acc: float = 1.0,
        dead_cases: Iterable[str] = _EC_DEAD_CASES_DEFAULT,
        psi1: Optional[Mapping[str, float]] = None,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ULS accidental (EN 1990):
        sum(1.0*Gk) + 1.0*Qk,acc + sum(1.0*psi1,i*Qk,i)
        """
        psi1_map = dict(_EC_PSI1_DEFAULT)
        if psi1:
            psi1_map.update(psi1)
        factors: Dict[str, FactorSpec] = {d: gamma_g for d in dead_cases}
        acc = _EC_ALIASES.get(accidental, accidental)
        factors[acc] = gamma_q_acc
        for case, p in psi1_map.items():
            if case == acc:
                continue
            factors[case] = 1.0 * p
        factors = cls._apply_aliases(factors, _EC_ALIASES)
        return cls(case_factor_dict=factors, name=name or f"EC-ULS-ACC[{acc}]")

    @classmethod
    def ec_sls_characteristic(
        cls,
        leading: str = "Q_IMP",
        *,
        dead_cases: Iterable[str] = _EC_DEAD_CASES_DEFAULT,
        psi0: Optional[Mapping[str, float]] = None,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """SLS characteristic (EN 1990):
        sum(1.0*Gk) + 1.0*Qk,leading + sum(psi0,i*Qk,i)
        """
        psi0_map = dict(_EC_PSI0_DEFAULT)
        if psi0:
            psi0_map.update(psi0)
        lead = _EC_ALIASES.get(leading, leading)
        factors: Dict[str, FactorSpec] = {d: 1.0 for d in dead_cases}
        factors[lead] = 1.0
        for case, p in psi0_map.items():
            if case == lead:
                continue
            factors[case] = p
        factors = cls._apply_aliases(factors, _EC_ALIASES)
        return cls(case_factor_dict=factors, name=name or f"EC-SLS-CHAR[{lead}]")

    @classmethod
    def ec_sls_frequent(
        cls,
        leading: str = "Q_IMP",
        *,
        dead_cases: Iterable[str] = _EC_DEAD_CASES_DEFAULT,
        psi1: Optional[Mapping[str, float]] = None,
        psi2: Optional[Mapping[str, float]] = None,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """SLS frequent (EN 1990):
        sum(1.0*Gk) + psi1,leading*Qk,leading + sum(psi2,i*Qk,i)
        """
        psi1_map = dict(_EC_PSI1_DEFAULT)
        if psi1:
            psi1_map.update(psi1)
        psi2_map = dict(_EC_PSI2_DEFAULT)
        if psi2:
            psi2_map.update(psi2)
        lead = _EC_ALIASES.get(leading, leading)
        factors: Dict[str, FactorSpec] = {d: 1.0 for d in dead_cases}
        factors[lead] = psi1_map.get(lead, 0.0)
        for case, p in psi2_map.items():
            if case == lead:
                continue
            factors[case] = p
        factors = cls._apply_aliases(factors, _EC_ALIASES)
        return cls(case_factor_dict=factors, name=name or f"EC-SLS-FREQ[{lead}]")

    @classmethod
    def ec_sls_quasi_permanent(
        cls,
        *,
        dead_cases: Iterable[str] = _EC_DEAD_CASES_DEFAULT,
        psi2: Optional[Mapping[str, float]] = None,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """SLS quasi-permanent (EN 1990):
        sum(1.0*Gk) + sum(psi2,i*Qk,i)
        """
        psi2_map = dict(_EC_PSI2_DEFAULT)
        if psi2:
            psi2_map.update(psi2)
        factors: Dict[str, FactorSpec] = {d: 1.0 for d in dead_cases}
        for case, p in psi2_map.items():
            factors[case] = p
        factors = cls._apply_aliases(factors, _EC_ALIASES)
        return cls(case_factor_dict=factors, name=name or "EC-SLS-QP")

    @classmethod
    def ec_uls_persistent_roles(
        cls,
        leading: str = "Q_IMP",
        *,
        gamma_g: float = 1.35,
        gamma_q: float = 1.5,
        dead_cases: Iterable[str] = _EC_DEAD_CASES_DEFAULT,
        psi0: Optional[Mapping[str, float]] = None,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """EC EN 1990, ULS persistent/transient (per-role)."""
        psi0_map = dict(_EC_PSI0_DEFAULT)
        if psi0:
            psi0_map.update(psi0)

        factors: Dict[str, FactorSpec] = {d: float(gamma_g) for d in dead_cases}

        psi_lead = psi0_map.get(leading, 0.0)
        factors[leading] = cls._role_map(
            primary=gamma_q,
            secondary=gamma_q * psi_lead,
            tertiary=gamma_q * psi_lead,
            default=gamma_q * psi_lead,
        )

        for case, p in psi0_map.items():
            if case == leading:
                continue
            val = gamma_q * p
            factors[case] = cls._role_map(primary=val, secondary=val, tertiary=val, default=val)
        factors = cls._apply_aliases(factors, _EC_ALIASES)
        return cls(case_factor_dict=factors, name=name or f"EC-ULS-PERS-ROLES[{leading}]")

    @classmethod
    def ec_uls_accidental_roles(
        cls,
        accidental: str,
        *,
        gamma_g: float = 1.0,
        gamma_q_acc: float = 1.0,
        dead_cases: Iterable[str] = _EC_DEAD_CASES_DEFAULT,
        psi1: Optional[Mapping[str, float]] = None,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """EC EN 1990, ULS accidental (per-role)."""
        psi1_map = dict(_EC_PSI1_DEFAULT)
        if psi1:
            psi1_map.update(psi1)

        factors: Dict[str, FactorSpec] = {d: float(gamma_g) for d in dead_cases}
        factors[accidental] = cls._role_map(
            primary=gamma_q_acc, secondary=gamma_q_acc, tertiary=gamma_q_acc, default=gamma_q_acc
        )

        for case, p in psi1_map.items():
            if case == accidental:
                continue
            val = 1.0 * p
            factors[case] = cls._role_map(primary=val, secondary=val, tertiary=val, default=val)
        factors = cls._apply_aliases(factors, _EC_ALIASES)
        return cls(case_factor_dict=factors, name=name or f"EC-ULS-ACC-ROLES[{accidental}]")

    @classmethod
    def ec_sls_characteristic_roles(
        cls,
        leading: str = "Q_IMP",
        *,
        dead_cases: Iterable[str] = _EC_DEAD_CASES_DEFAULT,
        psi0: Optional[Mapping[str, float]] = None,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """EC EN 1990, SLS characteristic (per-role)."""
        psi0_map = dict(_EC_PSI0_DEFAULT)
        if psi0:
            psi0_map.update(psi0)

        factors: Dict[str, FactorSpec] = {d: 1.0 for d in dead_cases}

        psi_lead = psi0_map.get(leading, 0.0)
        factors[leading] = cls._role_map(primary=1.0, secondary=psi_lead, tertiary=psi_lead, default=psi_lead)

        for case, p in psi0_map.items():
            if case == leading:
                continue
            factors[case] = cls._role_map(primary=p, secondary=p, tertiary=p, default=p)
        factors = cls._apply_aliases(factors, _EC_ALIASES)
        return cls(case_factor_dict=factors, name=name or f"EC-SLS-CHAR-ROLES[{leading}]")

    @classmethod
    def ec_sls_frequent_roles(
        cls,
        leading: str = "Q_IMP",
        *,
        dead_cases: Iterable[str] = _EC_DEAD_CASES_DEFAULT,
        psi1: Optional[Mapping[str, float]] = None,
        psi2: Optional[Mapping[str, float]] = None,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """EC EN 1990, SLS frequent (per-role)."""
        psi1_map = dict(_EC_PSI1_DEFAULT)
        if psi1:
            psi1_map.update(psi1)
        psi2_map = dict(_EC_PSI2_DEFAULT)
        if psi2:
            psi2_map.update(psi2)

        factors: Dict[str, FactorSpec] = {d: 1.0 for d in dead_cases}

        p1 = psi1_map.get(leading, 0.0)
        p2 = psi2_map.get(leading, 0.0)
        factors[leading] = cls._role_map(primary=p1, secondary=p2, tertiary=p2, default=p2)

        for case, p in psi2_map.items():
            if case == leading:
                continue
            factors[case] = cls._role_map(primary=p, secondary=p, tertiary=p, default=p)
        factors = cls._apply_aliases(factors, _EC_ALIASES)
        return cls(case_factor_dict=factors, name=name or f"EC-SLS-FREQ-ROLES[{leading}]")

    @classmethod
    def ec_sls_quasi_permanent_roles(
        cls,
        *,
        dead_cases: Iterable[str] = _EC_DEAD_CASES_DEFAULT,
        psi2: Optional[Mapping[str, float]] = None,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """EC EN 1990, SLS quasi-permanent (per-role)."""
        psi2_map = dict(_EC_PSI2_DEFAULT)
        if psi2:
            psi2_map.update(psi2)

        factors: Dict[str, FactorSpec] = {d: 1.0 for d in dead_cases}
        for case, p in psi2_map.items():
            factors[case] = cls._role_map(primary=p, secondary=p, tertiary=p, default=p)
        factors = cls._apply_aliases(factors, _EC_ALIASES)
        return cls(case_factor_dict=factors, name=name or "EC-SLS-QP-ROLES")

    # -----------------------
    # ASCE 7 (LRFD/ASD) sets
    # -----------------------

    @classmethod
    def asce7_lrfd_1_4D(
        cls,
        *,
        dead_cases: Iterable[str] = _ASCE_DEAD_CASES_DEFAULT,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 1.4D"""
        factors: Dict[str, FactorSpec] = {d: 1.4 for d in dead_cases}
        return cls(case_factor_dict=factors, name=name or "ASCE7-LRFD-1.4D")

    @classmethod
    def asce7_lrfd_basic(
        cls,
        *,
        dead_cases: Iterable[str] = _ASCE_DEAD_CASES_DEFAULT,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 1.2D + 1.6L + 0.5(Lr + S + R)"""
        factors: Dict[str, FactorSpec] = {d: 1.2 for d in dead_cases}
        factors.update({"LL": 1.6, "Lr": 0.5, "S": 0.5, "R": 0.5})
        return cls(case_factor_dict=factors, name=name or "ASCE7-LRFD-BASIC")

    @classmethod
    def asce7_lrfd_wind(
        cls,
        *,
        dead_cases: Iterable[str] = _ASCE_DEAD_CASES_DEFAULT,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 1.2D + 1.0W + 1.6L + 0.5(Lr + S + R)"""
        factors: Dict[str, FactorSpec] = {d: 1.2 for d in dead_cases}
        factors.update({"W": 1.0, "LL": 1.6, "Lr": 0.5, "S": 0.5, "R": 0.5})
        return cls(case_factor_dict=factors, name=name or "ASCE7-LRFD-WIND")

    @classmethod
    def asce7_lrfd_seismic(
        cls,
        *,
        dead_cases: Iterable[str] = _ASCE_DEAD_CASES_DEFAULT,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 1.2D + 1.0E + 1.6L + 0.2S"""
        factors: Dict[str, FactorSpec] = {d: 1.2 for d in dead_cases}
        factors.update({"E": 1.0, "LL": 1.6, "S": 0.2})
        return cls(case_factor_dict=factors, name=name or "ASCE7-LRFD-SEISMIC")

    @classmethod
    def asce7_lrfd_wind_uplift(
        cls,
        *,
        dead_cases: Iterable[str] = _ASCE_DEAD_CASES_DEFAULT,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 0.9D + 1.0W"""
        factors: Dict[str, FactorSpec] = {d: 0.9 for d in dead_cases}
        factors.update({"W": 1.0})
        return cls(case_factor_dict=factors, name=name or "ASCE7-LRFD-0.9D+W")

    @classmethod
    def asce7_lrfd_seismic_uplift(
        cls,
        *,
        dead_cases: Iterable[str] = _ASCE_DEAD_CASES_DEFAULT,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ASCE 7 LRFD: 0.9D + 1.0E"""
        factors: Dict[str, FactorSpec] = {d: 0.9 for d in dead_cases}
        factors.update({"E": 1.0})
        return cls(case_factor_dict=factors, name=name or "ASCE7-LRFD-0.9D+E")

    @classmethod
    def asce7_asd_basic(
        cls,
        *,
        dead_cases: Iterable[str] = _ASCE_DEAD_CASES_DEFAULT,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ASCE 7 ASD: D + L + (Lr + S + R)"""
        factors: Dict[str, FactorSpec] = {d: 1.0 for d in dead_cases}
        factors.update({"LL": 1.0, "Lr": 1.0, "S": 1.0, "R": 1.0})
        return cls(case_factor_dict=factors, name=name or "ASCE7-ASD-BASIC")

    @classmethod
    def asce7_asd_wind(
        cls,
        *,
        dead_cases: Iterable[str] = _ASCE_DEAD_CASES_DEFAULT,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ASCE 7 ASD: D + 0.75L + 0.75(Lr + S + R) + 0.6W"""
        factors: Dict[str, FactorSpec] = {d: 1.0 for d in dead_cases}
        factors.update({"LL": 0.75, "Lr": 0.75, "S": 0.75, "R": 0.75, "W": 0.6})
        return cls(case_factor_dict=factors, name=name or "ASCE7-ASD-WIND")

    @classmethod
    def asce7_asd_seismic(
        cls,
        *,
        dead_cases: Iterable[str] = _ASCE_DEAD_CASES_DEFAULT,
        name: Optional[str] = None,
    ) -> "LoadFieldsCombination":
        """ASCE 7 ASD: D + 0.75L + 0.2S + 0.7E"""
        factors: Dict[str, FactorSpec] = {d: 1.0 for d in dead_cases}
        factors.update({"LL": 0.75, "S": 0.2, "E": 0.7})
        return cls(case_factor_dict=factors, name=name or "ASCE7-ASD-SEISMIC")


class StepsCombination(FEAData):
    """A StepsCombination sums the analysis results of given steps.

    Notes
    -----
    By default every analysis in compas_fea2 is meant to be non-linear:
    the response of previous steps is used as the starting point for subsequent
    steps. Therefore, the sequence of steps can affect the results.
    """

    def __init__(self, **kwargs: Any):
        """Not implemented yet."""
        raise NotImplementedError()