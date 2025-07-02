from typing import TYPE_CHECKING

import compas_fea2
from compas_fea2.base import FEAData

if TYPE_CHECKING:
    from compas_fea2.problem import Step
    from compas_fea2.problem import Problem



class LoadCombination(FEAData):
    """Load combination used to combine load fields together at each step.

    Parameters
    ----------
    factors : dict()
        Dictionary with the factors for each load case: {"load case": factor}
    """

    def __init__(self, factors, **kwargs):
        super(LoadCombination, self).__init__(**kwargs)
        self.factors = factors

    @property
    def load_cases(self):
        for k in self.factors.keys():
            yield k

    @property
    def step(self) -> "Step":
        if self._registration:
            return self._registration
        else:
            raise ValueError("Register the LoadCombination to a Step first.")

    @property
    def problem(self) -> "Problem":
        return self.step.problem

    @property
    def model(self):
        self.problem.model

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
        return {
            "factors": self.factors,
            "name": self.name,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(factors=data["factors"], name=data.get("name"))

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
        for load_field in self.step.load_fields:
            if isinstance(load_field, compas_fea2.problem.LoadField):
                if load_field.load_case in self.factors:
                    for node, load in load_field.node_load :
                            if node in nodes_loads:
                                nodes_loads[node] += load * self.factors[load_field.load_case]
                            else:
                                nodes_loads[node] = load * self.factors[load_field.load_case]
        return zip(list(nodes_loads.keys()), list(nodes_loads.values()))
