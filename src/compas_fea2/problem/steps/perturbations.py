from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .step import Step


class _Perturbation(Step):
    """A perturbation is a change of the state of the structure after an analysis
    step. Differently from Steps, perturbations' changes are not carried over to
    the next step.

    Parameters
    ----------
    Step : _type_
        _description_
    """

    @property
    def __data__(self):
        return {
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
        )

    def __init__(self, **kwargs):
        super(_Perturbation, self).__init__(**kwargs)


class ModalAnalysis(_Perturbation):
    """Perform a modal analysis of the Model from the resulting state after an
    analysis Step.

    Parameters
    ----------
    name : str
        Name of the ModalStep.
    modes : int
        Number of modes to analyse.

    """

    @property
    def __data__(self):
        return {
            "modes": self.modes,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            modes=data["modes"],
        )

    def __init__(self, modes=1, **kwargs):
        super(ModalAnalysis, self).__init__( **kwargs)
        self.modes = modes


class ComplexEigenValue(_Perturbation):
    """"""

    @property
    def __data__(self):
        return {
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raise NotImplementedError


class BucklingAnalysis(_Perturbation):
    """"""

    @property
    def __data__(self):
        return {
            "modes": self.modes,
            "vectors": self.vectors,
            "iterations": self.iterations,
            "algorithm": self.algorithm,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            modes=data["modes"],
            vectors=data["vectors"],
            iterations=data["iterations"],
            algorithm=data["algorithm"],
        )

    def __init__(self, modes, vectors=None, iterations=30, algorithm=None, **kwargs):
        super().__init__(**kwargs)
        self._modes = modes
        self._vectors = vectors or self._compute_vectors(modes)
        self._iterations = iterations
        self._algorithm = algorithm

    def _compute_vectors(self, modes):
        self._vectors = modes * 2
        if modes > 9:
            self._vectors += modes

    @staticmethod
    def Lanczos(modes, name=None):
        return BucklingAnalysis(modes=modes, vectors=None, algorithhm="Lanczos", name=name)

    @staticmethod
    def Subspace(modes, iterations, vectors=None, name=None):
        return BucklingAnalysis(modes=modes, vectors=vectors, iterations=iterations, algorithhm="Subspace", name=name)


class LinearStaticPerturbation(_Perturbation):
    """"""

    @property
    def __data__(self):
        return {
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raise NotImplementedError


class StedyStateDynamic(_Perturbation):
    """"""

    @property
    def __data__(self):
        return {
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raise NotImplementedError


class SubstructureGeneration(_Perturbation):
    """"""

    @property
    def __data__(self):
        return {
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raise NotImplementedError
