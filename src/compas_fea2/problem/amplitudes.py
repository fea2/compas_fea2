from compas_fea2.base import FEAData


class Amplitude(FEAData):
    """Amplitude object for creating a time-varying fonction that defines
     how the magnitude of a load, boundary condition, or predifined field
     changes throughout a step or the analysis.

    Parameters
    ----------
    multipliers : list[float]
        Multipliers list of values.

    times : list[float]
        Corresponding time to the multipliers.

    Attributes
    ----------
    q : float
        Heat flux value of the load.

    amplitude :  :class:`compas_fea2.problem.Amplitude`
        Amplitude associated to the load, optionnal."""

    def __init__(self, multipliers, times, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self._multipliers = multipliers
        self._times = times
        if len(self._multipliers) != len(self._times):
            raise ValueError("The lists of values and times must have the same length.")

    @property
    def multipliers(self):
        return self._multipliers

    @property
    def times(self):
        return self._times

    @property
    def multipliers_times(self):
        """Return a list of tuples with the values and the assigned time."""
        return zip(self.multipliers, self.times)

    @classmethod
    def equally_spaced(cls, multipliers, first_value, fixed_interval, **kwargs):
        times = [first_value + fixed_interval * i for i in range(len(fixed_interval))]
        return cls(multipliers=multipliers, times=times, **kwargs)
