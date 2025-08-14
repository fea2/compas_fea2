from typing import TYPE_CHECKING

import compas_fea2
from compas_fea2.base import FEAData, from_data

if TYPE_CHECKING:
    from compas_fea2.model import Model
    from compas_fea2.problem import Problem
    from compas_fea2.problem import _Step


class LoadFieldsCombination(FEAData):
    """Load combination used to combine load fields together at each step.

    Parameters
    ----------
    factors : dict()
        Dictionary with the factors for each load case: {"load case": factor}
    """

    def __init__(self, factors, **kwargs):
        super(LoadFieldsCombination, self).__init__(**kwargs)
        self.factors = factors

    @property
    def load_cases(self):
        for k in self.factors.keys():
            yield k

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
        return cls(factors={"DL": 1.35, "SDL": 1.35, "LL": 1.35}, name="ULS")

    @classmethod
    def SLS(cls):
        return cls(factors={"DL": 1, "SDL": 1, "LL": 1}, name="SLS")

    @classmethod
    def Fire(cls):
        return cls(factors={"DL": 1, "SDL": 1, "LL": 0.3}, name="Fire")

    @property
    def __data__(self):
        base = super().__data__
        base.update({
            "factors": self.factors,
        })
        return base


    @from_data
    @classmethod
    def __from_data__(cls, data, registry=None, duplicate=True):
        return cls(factors=data["factors"])

    # BUG: Rewrite. this is not general and does not account for different loads types
    @property
    def node_load(self):
        """Generator returning each node and the corresponding total factored
        load of the combination.

        Returns
        -------
        zip obj
            :class:`compas_fea2.model.node.Node`, :class:`compas_fea2.problem.loads.NodeLoad`
        """
        nodes_loads = {}
        for load_field in self.step.fields:
            if isinstance(load_field, compas_fea2.problem._LoadField):
                if load_field.load_case in self.factors:
                    for node, load in load_field.node_load:
                        if node in nodes_loads:
                            nodes_loads[node] += load * self.factors[load_field.load_case]
                        else:
                            nodes_loads[node] = load * self.factors[load_field.load_case]
        return zip(list(nodes_loads.keys()), list(nodes_loads.values()))


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