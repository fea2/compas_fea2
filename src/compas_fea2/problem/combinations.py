from typing import TYPE_CHECKING

from compas_fea2.base import FEAData, from_data
from compas_fea2.model.groups import NodesGroup
from compas_fea2.problem.fields import ForceField, DisplacementField, TemperatureField
from compas_fea2.problem.groups import LoadsFieldGroup
from compas_fea2.problem.loads import VectorLoad, ScalarLoad

if TYPE_CHECKING:
    from compas_fea2.model import Model
    from compas_fea2.problem import Problem
    from compas_fea2.problem import _Step
    from compas_fea2.model.nodes import Node


class LoadFieldsCombination(FEAData):
    """Load combination used to combine load fields together at each step.

    Parameters
    ----------
    factors : dict()
        Dictionary with the factors for each load case: {"load case": factor}
    """

    def __init__(self, case_factor_dict, **kwargs):
        super(LoadFieldsCombination, self).__init__(**kwargs)
        self._case_factor_dict = case_factor_dict

    @property
    def __data__(self):
        base = super().__data__
        base.update({
            "case_factor_dict": self._case_factor_dict,
        })
        return base


    @from_data
    @classmethod
    def __from_data__(cls, data, registry=None, duplicate=True):
        return cls(case_factor_dict=data["case_factor_dict"])

    @property
    def load_cases(self):
        for k in self._case_factor_dict.keys():
            yield k

    @property
    def load_factors(self):
        for v in self._case_factor_dict.values():
            yield v

    @property
    def case_factor_dict(self):
        # FIX: return backing field
        return self._case_factor_dict
    
    @case_factor_dict.setter
    def case_factor_dict(self, value):
        if not isinstance(value, dict):
            raise TypeError("case_factor_dict must be a dictionary.")
        self._case_factor_dict = value
    
    @property
    def step(self) -> "_Step | None":
        if self._registration:
            return self._registration

    @property
    def problem(self) -> "Problem | None":
        if self.step:
            return self.step.problem

    @property
    def model(self) -> "Model | None":
        if self.problem:
            return self.problem.model

    @classmethod
    def ULS(cls):
        return cls(case_factor_dict={"DL": 1.35, "SDL": 1.35, "LL": 1.5}, name="ULS")

    @classmethod
    def SLS(cls):
        return cls(case_factor_dict={"DL": 1, "SDL": 1, "LL": 1}, name="SLS")

    @classmethod
    def Fire(cls):
        return cls(case_factor_dict={"DL": 1, "SDL": 1, "LL": 0.3}, name="Fire")

    # --- combination logic ----------------------------------------------------
    # def _clone_and_scale_load(self, load, factor):
    #     """Return a NEW scaled load/value, without mutating inputs."""
    #     f = float(factor)
    #     if isinstance(load, ScalarLoad):
    #         # explicit non-mutating scale
    #         return ScalarLoad(getattr(load, "scalar_load", None) * f, amplitude=load.amplitude)
    #     if isinstance(load, VectorLoad):
    #         # clone via __data__/__from_data__ to preserve frame/amplitude
    #         data = load.__data__
    #         clone = VectorLoad.__from_data__(data, duplicate=False)
    #         clone *= f  # mutates the clone
    #         return clone
    #     if isinstance(load, (int, float)):
    #         return float(load) * f
    #     # Fallback to type's own __mul__
    #     return load * f

    # def _accumulate_node_field(self, accum: dict["Node", object], loads_iter, nodes_iter, factor):
    #     """Accumulate scaled loads by node using loads' arithmetic."""
    #     for node, value in zip(nodes_iter, loads_iter):
    #         scaled = self._clone_and_scale_load(value, factor)
    #         current = accum.get(node)
    #         if current is None:
    #             accum[node] = scaled
    #         else:
    #             # VectorLoad __add__ mutates LHS; others typically return a new instance
    #             if isinstance(current, VectorLoad):
    #                 current += scaled
    #                 accum[node] = current
    #             else:
    #                 accum[node] = current + scaled
    #     return accum

    # Combine any iterable/group of fields (no Step required)
    def combine_fields(self, fields) -> LoadsFieldGroup:
        """Build a new LoadsFieldGroup representing the linear combination for the given fields.

        fields can be an iterable of fields or a LoadsFieldGroup.
        """
        # fields_iter = getattr(fields, "fields", getattr(fields, "members", fields))
        # if not fields_iter:
        #     return LoadsFieldGroup(fields=[])

        # factors = self._case_factor_dict or {}

        node_vector_accum: dict["Node", object] = {}
        node_scalar_accum: dict["Node", object] = {}
        passthrough_fields = []
        scaled_fields = []

        for field in fields:
            lcase = getattr(field, "load_case", None)
            if lcase not in self.case_factor_dict:
                passthrough_fields.append(field)
                continue

            factor = self.case_factor_dict[lcase]
            scaled_field = factor * field if factor != 1 else field
            scaled_fields.append(scaled_field)

        return LoadsFieldGroup(members=scaled_fields)

    def combine_for_step(self, step: "_Step") -> LoadsFieldGroup:
        """Build a new LoadsFieldGroup representing the linear combination for this step."""
        fields = getattr(step, "fields", [])
        return self.combine_fields(fields)


class StepsCombination(FEAData):
    """A StepsCombination `sums` the analysis results of given steps
    (:class:`compas_fea2.problem.LoadPattern`).

    Parameters
    ----------
    FEAData : _type_
        _description_

    Notes
    -----
    By default every analysis in `compas_fea2` is meant to be `non-linear`, in
    the sense that the effects of a load pattern (:class:`compas_fea2.problem.Pattern`)
    in a given steps are used as a starting point for the application of the load
    patterns in the next step. Therefore, the sequence of the steps can affect
    the results (if the response is actully non-linear).

    """

    def __init__(self, **kwargs):
        raise NotImplementedError()