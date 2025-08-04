from compas_fea2.problem.fields import TemperatureField

from .step import _Step


class HeatTransferStep(_Step):
    """HeatTransfer for use in a heat transfer analysis.
    Specific for now to a transient heat transfer analysis as defined in Abaqus.

    Parameters
    ----------
    max_increments : int
        Max number of increments to perform during the case step.
        (Typically 100 but you might have to increase it in highly non-linear
        problems. This might increase the analysis time.).
    initial_inc_size : float
        Sets the the size of the increment for the first iteration.
        (By default is equal to the total time, meaning that the software decrease
        the size automatically.)
    min_inc_size : float
        Minimum increment size before stopping the analysis.
        (By default is 1e-5, but you can set a smaller size for highly non-linear
        problems. This might increase the analysis time.)
    max_temp_delta : float
        Maximum allowable temperature change per increment.
        (By default is 10.)
    max_emiss_delta : float
        Maximum allowable emissivity change per increment.
    time : float
        Total time of the case step. Note that this not actual 'time',
        but rather a proportionality factor. (By default is 1, meaning that the
        analysis is complete when all the increments sum up to 1)
    nlgeom : bool
        if ``True`` nonlinear geometry effects are considered.
    modify : bool
        if ``True`` the loads applied in a previous step are substituted by the
        ones defined in the present step, otherwise the loads are added.

    Attributes
    ----------
    name : str
        Automatically generated id. You can change the name if you want a more
        human readable input file.
    max_increments : int
        Max number of increments to perform during the case step.
        (Typically 100 but you might have to increase it in highly non-linear
        problems. This might increase the analysis time.).
    initial_inc_size : float
        Sets the the size of the increment for the first iteration.
        (By default is equal to the total time, meaning that the software decrease
        the size automatically.)
    min_inc_size : float
        Minimum increment size before stopping the analysis.
        (By default is 1e-5, but you can set a smaller size for highly non-linear
        problems. This might increase the analysis time.)
    max_temp_delta : float
        Maximum allowable temperature change per increment.
        (By default is 10.)
    max_emiss_delta : float
        Maximum allowable emissivity change per increment.
    time : float
        Total time of the case step. Note that this not actual 'time',
        but rather a proportionality factor. (By default is 1, meaning that the
        analysis is complete when all the increments sum up to 1)
    nlgeom : bool
        if ``True`` nonlinear geometry effects are considered.
    modify : bool
        if ``True`` the loads applied in a previous step are substituted by the
        ones defined in the present step, otherwise the loads are added.
    loads : dict
        Dictionary of the loads assigned to each part in the model in the step.
    displacements : dict
        Dictionary of the displacements assigned to each part in the model in the step.

    """

    def __init__(
        self,
        max_increments=100,
        initial_inc_size=1,
        min_inc_size=0.00001,
        max_inc_size=1,
        time=1,
        max_temp_delta=10,
        max_emiss_change=0.1,
        nlgeom=False,
        modify=True,
        **kwargs,
    ):
        super().__init__(
            **kwargs,
        )

        self._max_increments = max_increments
        self._initial_inc_size = initial_inc_size
        self._min_inc_size = min_inc_size
        self._max_inc_size = max_inc_size
        self._time = time
        self.max_temp_delta = max_temp_delta
        self.max_emiss_change = max_emiss_change
        self._nlgeom = nlgeom
        self._modify = modify

    def __data__(self):
        return {
            "max_increments": self.max_increments,
            "initial_inc_size": self.initial_inc_size,
            "min_inc_size": self.min_inc_size,
            "time": self.time,
            "max_temp_delta": self.max_temp_delta,
            "max_emiss_change": self.max_emiss_change,
            "nlgeom": self.nlgeom,
            "modify": self.modify,
            # Add other attributes as needed
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            max_increments=data["max_increments"],
            initial_inc_size=data["initial_inc_size"],
            min_inc_size=data["min_inc_size"],
            max_temp_delta=data["max_temp_delta"],
            max_emiss_change=data["max_emiss_change"],
            time=data["time"],
            nlgeom=data["nlgeom"],
            modify=data["modify"],
            # Add other attributes as needed
        )

    def add_load_field(self, field):
        """Add a general :class:`compas_fea2.problem.patterns.Pattern` to the Step.

        Parameters
        ----------
        load_pattern : :class:`compas_fea2.problem.patterns.Pattern`
            The load pattern to add.

        Returns
        -------
        :class:`compas_fea2.problem.patterns.Pattern`

        """
        from compas_fea2.problem.fields import _LoadField

        if not isinstance(field, _LoadField):
            raise TypeError("{!r} is not a LoadPattern.".format(field))
        
        if not(isinstance(field, (TemperatureField))):
            raise ValueError("A non-thermal load can not be implemented in a heat analysis step.")

        self._load_fields.add(field)
        self._load_cases.add(field.load_case)
        field._registration = self
        self.model.add_group(field.distribution)
        for amplitude in field.amplitudes:
            self.model.amplitudes.add(amplitude)
        return field
