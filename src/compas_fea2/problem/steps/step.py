from typing import TYPE_CHECKING
from typing import Iterable
from typing import Set
from typing import Union

from compas_fea2.base import FEAData
from compas_fea2.base import from_data
from compas_fea2.model.groups import NodesGroup
from compas_fea2.problem.combinations import LoadFieldsCombination
from compas_fea2.problem.combinations import StepsCombination
from compas_fea2.problem.fields import DisplacementField
from compas_fea2.problem.fields import ForceField
from compas_fea2.problem.fields import GravityLoadField
from compas_fea2.problem.fields import TemperatureField
from compas_fea2.problem.groups import LoadsFieldGroup
from compas_fea2.results import DisplacementFieldResults
from compas_fea2.results import TemperatureFieldResults

if TYPE_CHECKING:
    from compas_fea2.model import Model
    from compas_fea2.model import NodesGroup
    from compas_fea2.problem import DisplacementField
    from compas_fea2.problem import ForceField
    from compas_fea2.problem import LoadFieldsCombination
    from compas_fea2.problem import Problem
    from compas_fea2.problem import StepsCombination
    from compas_fea2.problem import TemperatureField
    from compas_fea2.problem.groups import LoadsFieldGroup

FieldType = Union["DisplacementField", "ForceField"]
ComboType = Union["LoadFieldsCombination", "StepsCombination"]
OutputType = Union["DisplacementFieldResults", "TemperatureFieldResults"]

# ==============================================================================
#                                Base Steps
# ==============================================================================


class _Step(FEAData):
    """Initialises base Step object.


    Attributes
    ----------
    name : str
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    field_outputs: :class:`compas_fea2.problem.FieldOutput'
        Field outuputs requested for the step.
    history_outputs: :class:`compas_fea2.problem.HistoryOutput'
        History outuputs requested for the step.
    results : :class:`compas_fea2.results.StepResults`
        The results of the analysis at this step

    Notes
    -----
    Steps are registered to a :class:`compas_fea2.problem.Problem`.

    A ``compas_fea2`` analysis is based on the concept of ``steps``,
    which represent the sequence in which the state of the model is modified.
    Steps can be introduced for example to change loads, boundary conditions,
    analysis procedure, etc. There is no limit on the number of steps in an analysis.

    Developer-only class.
    """

    def __init__(self, **kwargs):
        super(_Step, self).__init__(**kwargs)
        self._field_outputs = set()
        self._history_outputs = set()

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "field_outputs": [output.__data__ for output in self._field_outputs],
                "history_outputs": [output.__data__ for output in self._history_outputs],
            }
        )
        return data

    @property
    def problem(self) -> "Problem":
        if not self._registration:
            raise AttributeError("Step is not registered to a Problem.")
        return self._registration

    @property
    def model(self) -> "Model | None":
        if self.problem:
            return self.problem.model

    @property
    def field_outputs(self):
        """Return the field outputs requested for the step."""
        return self._field_outputs

    @property
    def history_outputs(self):
        """Return the history outputs requested for the step."""
        return self._history_outputs

    # ==========================================================================
    #                             Field outputs
    # ==========================================================================

    def add_field_output(self, field_output):
        """Add a field output to the step.
        Parameters
        ----------
        field_output : :class:`compas_fea2.problem.fields.FieldType`
            The field output to add.
        Returns
        -------
        :class:`compas_fea2.problem.fields.FieldType`
        """
        self._field_outputs.add(field_output)
        field_output._registration = self
        return field_output

    # # ==========================================================================
    # #                             Results methods
    # # ==========================================================================

    # @property
    # def displacement_field(self):
    #     from compas_fea2.results.fields import DisplacementFieldResults

    #     return DisplacementFieldResults(self)

    # @property
    # def reaction_field(self):
    #     from compas_fea2.results.fields import ReactionFieldResults
    #     return ReactionFieldResults(self)

    # @property
    # def temperature_field(self):
    #     return TemperatureFieldResults(self)

    # @property
    # def stress_field(self):
    #     from compas_fea2.results.fields import StressFieldResults

    #     return StressFieldResults(self)

    # @property
    # def section_forces_field(self):
    #     from compas_fea2.results.fields import SectionForcesFieldResults

    #     return SectionForcesFieldResults(self)


# ==============================================================================
#                                General Steps
# ==============================================================================


class GeneralStep(_Step):
    """General Step object for use as a base class in a general static, dynamic
    or multiphysics analysis.

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
    time : float
        Total time of the case step. Note that this not actual 'time',
        but rather a proportionality factor. (By default is 1, meaning that the
        analysis is complete when all the increments sum up to 1)
    nlgeom : bool
        if ``True`` nonlinear geometry effects are considered.
    modify : bool
        if ``True`` the loads applied in a previous step are substituted by the
        ones defined in the present step, otherwise the loads are added.
    restart : float, optional
        Frequency at which saving the results for restarting the analysis,
        by default `False`.

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
    time : float
        Total time of the case step. Note that this not actual 'time',
        but rather a proportionality factor. (By default is 1, meaning that the
        analysis is complete when all the increments sum up to 1)
    nlgeom : bool
        if ``True`` nonlinear geometry effects are considered.
    modify : bool
        if ``True`` the loads applied in a previous step are substituted by the
        ones defined in the present step, otherwise the loads are added.
    restart : float
        Frequency at which saving the results for restarting the analysis.
    loads : dict
        Dictionary of the loads assigned to each part in the model in the step.
    fields : dict
        Dictionary of the prescribed fields assigned to each part in the model in the step.

    """

    def __init__(self, max_increments, initial_inc_size, min_inc_size, max_inc_size, time, nlgeom=False, modify=False, restart=False, **kwargs):
        super(GeneralStep, self).__init__(**kwargs)

        self._max_increments = max_increments
        self._initial_inc_size = initial_inc_size
        self._min_inc_size = min_inc_size
        self._max_inc_size = max_inc_size
        self._time = time
        self._nlgeom = nlgeom
        self._modify = modify
        self._restart = restart

        self._fields: "LoadsFieldGroup | None" = None
        self._combination: ComboType | None = None

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "fields": [field.__data__ for field in self._fields] if self._fields else None,
                "combination": self._combination.__data__ if self._combination else None,
                "max_increments": self._max_increments,
                "initial_inc_size": self._initial_inc_size,
                "min_inc_size": self._min_inc_size,
                "max_inc_size": self._max_inc_size,
                "time": self._time,
                "nlgeom": self._nlgeom,
                "modify": self._modify,
                "restart": self._restart,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry=None, duplicate=True):
        if not registry:
            raise ValueError("No registry provided for Step deserialization.")
        step = cls(
            max_increments=data.get("max_increments"),
            initial_inc_size=data.get("initial_inc_size"),
            min_inc_size=data.get("min_inc_size"),
            max_inc_size=data.get("max_inc_size"),
            time=data.get("time"),
            nlgeom=data.get("nlgeom", False),
            modify=data.get("modify", False),
            restart=data.get("restart", False),
            name=data.get("name"),
        )
        for field_data in data.get("fields", []):
            step.add_field(registry.add_from_data(field_data, duplicate=duplicate))
        for output_data in data.get("field_outputs", []):
            step.add_field_output(registry.add_from_data(output_data, duplicate=duplicate))
        for history_data in data.get("history_outputs", []):
            step._history_outputs.add(registry.add_from_data(history_data, duplicate=duplicate))
        step._combination = registry.add_from_data(data.get("combination"), duplicate=duplicate) if data.get("combination") else None
        return step

    @property
    def combination(self):
        """Return the combination associated with the step."""
        return self._combination

    @property
    def fields(self):
        """Return the fields associated with the step."""
        return self._fields

    @property
    def effective_fields(self) -> "LoadsFieldGroup | None":
        """Return the fields to use for analysis/export (combined if a combination is set)."""
        if not self._fields:
            return None
        if not self._combination:
            return self._fields
        if isinstance(self._combination, LoadFieldsCombination):
            return self._combination.combine_for_step(self)
        # For StepsCombination or other types, just return the fields
        return self._fields

    @property
    def combined_fields(self) -> dict | None:
        if not self.effective_fields:
            raise ValueError("No effective fields to combine.")
        subgroups = self.effective_fields.group_by(key=lambda f: type(f))
        combined_fields = {}
        for kind, group in subgroups.items():
            combined_fields[kind] = sum([field for field in group.fields], start=ForceField(name="combined_field", loads=[], distribution=[]))
        return combined_fields

    @property
    def load_cases(self) -> Set[str] | None:
        """Return the load cases associated with the step."""
        if self._fields:
            return set(field.load_case for field in self._fields if field.load_case)

    @property
    def amplitudes(self):
        """Return the amplitudes associated with the step."""
        amplitudes = set()
        if self.fields:
            for load_field in self.fields:
                for load in filter(lambda p: getattr(p, "amplitude"), load_field.loads):
                    amplitudes.add(load.amplitudes)
            return amplitudes

    @property
    def displacements(self):
        """Return the displacements associated with the step."""
        if self._fields:
            return list(filter(lambda p: isinstance(p, DisplacementField), self._fields))

    @property
    def loads(self):
        """Return the loads associated with the step."""
        if self._fields:
            loads_fields = [field for field in self._fields if isinstance(field, (ForceField, GravityLoadField))]
            return loads_fields

    @property
    def max_increments(self):
        """Return the maximum number of increments for the step."""
        return self._max_increments

    @property
    def initial_inc_size(self):
        """Return the initial increment size for the step."""
        return self._initial_inc_size

    @property
    def min_inc_size(self):
        """Return the minimum increment size for the step."""
        return self._min_inc_size

    @property
    def max_inc_size(self):
        """Return the maximum increment size for the step."""
        return self._max_inc_size

    @property
    def time(self):
        """Return the total time for the step."""
        return self._time

    @property
    def nlgeom(self):
        """Return whether nonlinear geometry effects are considered in the step."""
        return self._nlgeom

    @property
    def modify(self):
        """Return whether the loads are modified in the step."""
        return self._modify

    @property
    def restart(self):
        """Return the restart frequency for the step."""
        return self._restart

    @restart.setter
    def restart(self, value):
        self._restart = value

    # ==============================================================================
    #                               Load Fields
    # ==============================================================================

    def add_field(self, field: "ForceField | DisplacementField | TemperatureField") -> "ForceField | DisplacementField | TemperatureField":
        """Add a general :class:`compas_fea2.problem.patterns.Pattern` to the Step.

        Parameters
        ----------
        load_pattern : :class:`compas_fea2.problem.patterns.Pattern`
            The load pattern to add.

        Returns
        -------
        :class:`compas_fea2.problem.patterns.Pattern`

        """
        if not isinstance(field, (ForceField, DisplacementField, GravityLoadField, TemperatureField)):
            raise TypeError("{!r} is not a LoadField.".format(field))
        if not self._fields:
            self._fields = LoadsFieldGroup(members=[field])
        else:
            self._fields.add_member(field)
            self.model._groups.add(field.distribution)
        field._registration = self
        return field

    def add_load_fields(self, fields):
        """Add multiple :class:`compas_fea2.problem.patterns.Pattern` to the Problem.

        Parameters
        ----------
        patterns : list(:class:`compas_fea2.problem.patterns.Pattern`)
            The load patterns to add to the Problem.

        Returns
        -------
        list(:class:`compas_fea2.problem.patterns.Pattern`)

        """
        fields = fields if isinstance(fields, Iterable) else [fields]
        for field in fields:
            self.add_field(field)

    def add_uniform_forcefield(self, nodes, load_case=None, x=None, y=None, z=None, xx=None, yy=None, zz=None, amplitude=None, **kwargs):
        """Add a :class:`compas_fea2.problem.fields.NodeLoadField` where all the nodes
        have the same load.

        Parameters
        ----------
        name : str
            name of the point load
        x : float, optional
            x component (in global coordinates) of the point load, by default None
        y : float, optional
            y component (in global coordinates) of the point load, by default None
        z : float, optional
            z component (in global coordinates) of the point load, by default None
        xx : float, optional
            moment about the global x axis of the point load, by default None
        yy : float, optional
            moment about the global y axis of the point load, by default None
        zz : float, optional
            moment about the global z axis of the point load, by default None

        Returns
        -------
        :class:`compas_fea2.problem.PointLoad`

        Warnings
        --------
        local axes are not supported yet

        """
        from compas_fea2.problem import VectorLoad

        if not isinstance(nodes, (list, tuple, NodesGroup)):
            raise TypeError("nodes must be a list, tuple or NodesGroup, not {}".format(type(nodes)))
        nodes = NodesGroup(nodes) if not isinstance(nodes, NodesGroup) else nodes
        load = VectorLoad(x=x, y=y, z=z, xx=xx, yy=yy, zz=zz, amplitude=amplitude)
        field = ForceField(loads=load, distribution=nodes, load_case=load_case, **kwargs)

        return self.add_field(field)

    def add_uniform_line_field(self, polyline, load_case=None, discretization=10, x=None, y=None, z=None, xx=None, yy=None, zz=None, axes="global", tolerance=None, **kwargs):
        """Add a :class:`compas_fea2.problem.field.NodeLoadField` subclass object to the
        ``Step`` along a prescribed path.
        """
        raise NotImplementedError("This method is not implemented yet.")

    def add_uniform_forcefield_from_polygon(self, polygon, load_case=None, x=None, y=None, z=None, xx=None, yy=None, zz=None, axes="global", **kwargs):
        raise NotImplementedError("Uniform surface load fields from polygons are not implemented yet.")
        # from compas_fea2.problem.fields import UniformSurfaceLoadField
        # from compas_fea2.problem.loads import VectorLoad

        # if not self.model:
        #     raise AttributeError("Step is not registered to a Model.")
        # surface = self.model.find_faces_in_polygon(polygon)

        # load = VectorLoad(x=x, y=y, z=z, xx=xx, yy=yy, zz=zz, axes=axes)

        # field = UniformSurfaceLoadField(load=[load], surface=surface, load_case=load_case, **kwargs)

        # return self.add_field(field)

    def add_surface_field(self, surface, load_case=None, x=None, y=None, z=None, xx=None, yy=None, zz=None, axes="global", **kwargs):
        """Add a :class:`compas_fea2.problem.PointLoad` subclass object to the
        ``Step`` along a prescribed path.

        Parameters
        ----------
        name : str
            name of the point load
        part : str
            name of the :class:`compas_fea2.problem.Part` where the load is applied
        where : int or list(int), obj
            It can be either a key or a list of keys, or a NodesGroup of the nodes where the load is
            applied.
        x : float, optional
            x component (in global coordinates) of the point load, by default None
        y : float, optional
            y component (in global coordinates) of the point load, by default None
        z : float, optional
            z component (in global coordinates) of the point load, by default None
        xx : float, optional
            moment about the global x axis of the point load, by default None
        yy : float, optional
            moment about the global y axis of the point load, by default None
        zz : float, optional
            moment about the global z axis of the point load, by default None
        axes : str, optional
            'local' or 'global' axes, by default 'global'

        Returns
        -------
        :class:`compas_fea2.problem.PointLoad`

        Warnings
        --------
        local axes are not supported yet

        """
        raise NotImplementedError("This method is not implemented yet.")
        # from compas_fea2.problem import VectorLoad
        # from compas_fea2.problem.fields import UniformSurfaceLoadField

        # components = {"x": x or 0, "y": y or 0, "z": z or 0, "xx": xx or 0, "yy": yy or 0, "zz": zz or 0}
        # load = VectorLoad(**components, axes=axes)
        # field = UniformSurfaceLoadField(load=load, surface=surface, load_case=load_case, **kwargs)

        # return self.add_field(field)

    def add_gravity_fied(self, g=9810, x=0.0, y=0.0, z=-1.0, distribution=None, load_case=None, **kwargs):
        """Add a :class:`compas_fea2.problem.GravityLoad` load to the ``Step``

        Parameters
        ----------
        g : float, optional
            acceleration of gravity, by default 9.81
        x : float, optional
            x component of the gravity direction vector (in global coordinates), by default 0.
        y : [type], optional
            y component of the gravity direction vector (in global coordinates), by default 0.
        z : [type], optional
            z component of the gravity direction vector (in global coordinates), by default -1.
        distribution : [:class:`compas_fea2.model.PartsGroup`] | [:class:`compas_fea2.model.ElementsGroup`]
            Group of parts or elements affected by gravity.

        Notes
        -----
        The gravity field is applied to the whole model. To remove parts of the
        model from the calculation of the gravity force, you can assign to them
        a 0 mass material.

        Warnings
        --------
        Be careful to assign a value of *g* consistent with the units in your
        model!
        """
        from compas_fea2.problem.fields import GravityLoadField

        if not self.model and not distribution:
            raise AttributeError("Step is not registered to a Model.")
        distribution = distribution or self.model.elements
        gravity = GravityLoadField(g=g, distribution=distribution, direction=[x, y, z], load_case=load_case, **kwargs)
        self.add_field(gravity)
        return gravity

    def add_temperature_field(self, field, node):
        """Add a temperature field to the Step object.

        Parameters
        ----------
        field : :class:`compas_fea2.problem.fields.PrescribedTemperatureField`
            The temperature field to add.
        node : :class=`compas_fea2.model.Node`
            The node to which the temperature field is applied.

        Returns
        -------
        :class:`compas_fea2.problem.fields.PrescribedTemperatureField`
            The temperature field that was added.
        """
        raise NotImplementedError("This method is not implemented yet.")

    def add_uniform_displacement_field(self, nodes, x=None, y=None, z=None, xx=None, yy=None, zz=None, axes="global", **kwargs):
        """Add a uniform displacement field to the Step object.

        Parameters
        ----------
        nodes : list[:class=`compas_fea2.model.Node`] | :class=`compas_fea2.model.NodesGroup`
            Nodes where the displacement is applied.
        x, y, z : float, optional
            Translational displacements in the global x, y, z directions, by default None.
        xx, yy, zz : float, optional
            Rotational displacements about the global x, y, z axes, by default None.
        axes : str, optional
            Coordinate system for the displacements ('global' or 'local'), by default 'global'.

        Returns
        -------
        :class=`compas_fea2.problem.fields.DisplacementField`
            The displacement field that was added.

        Raises
        ------
        TypeError
            If `nodes` is not a list, tuple, or NodesGroup.
        """
        raise NotImplementedError("This method is not implemented yet.")
        # from compas_fea2.problem.fields import DisplacementField

        # if not isinstance(nodes, (list, tuple, NodesGroup)):
        #     raise TypeError(f"nodes must be a list, tuple, or NodesGroup, not {type(nodes)}")
        # nodes = NodesGroup(nodes) if not isinstance(nodes, NodesGroup) else nodes

        # displacement = GeneralDisplacement(x=x, y=y, z=z, xx=xx, yy=yy, zz=zz, axes=axes, **kwargs)
        # return self.add_field(DisplacementField(displacement, nodes))

    # ==============================================================================
    #                             Combinations
    # ==============================================================================

    def add_combination(self, combination: ComboType):
        """Add a combination to the Step.

        Parameters
        ----------
        combination : :class:`compas_fea2.problem.combinations.ComboType`
            The combination to add to the Step.
        Returns
        -------
        :class:`compas_fea2.problem.combinations.ComboType`
        """
        if not isinstance(combination, (LoadFieldsCombination, StepsCombination)):
            raise TypeError(f"{combination} is not a valid combination type.")
        if not self._combination:
            self._combination = combination
        else:
            raise ValueError("A combination is already assigned to this step.")
        combination._registration = self
        return combination

    # ==========================================================================
    #                         Results methods - fields

    # =========================================================================
    #                         Results methods - reactions
    # =========================================================================


#     def get_total_reaction(self, step=None):
#         """Compute the total reaction vector

#         Parameters
#         ----------
#         step : :class=`compas_fea2.problem._Step`, optional
#             The analysis step, by default the last step.

#         Returns
#         -------
#         :class=`compas.geometry.Vector`
#             The resultant vector.
#         :class=`compas.geometry.Point`
#             The application point.
#         """
#         if not step:
#             step = self.steps_order[-1]
#         reactions = self.reaction_field
#         locations, vectors, vectors_lengths = [], [], []
#         for reaction in reactions.results:
#             locations.append(reaction.location.xyz)
#             vectors.append(reaction.vector)
#             vectors_lengths.append(reaction.vector.length)
#         return Vector(*sum_vectors(vectors)), Point(*centroid_points_weighted(locations, vectors_lengths))

#     def get_min_max_reactions(self, step=None):
#         """Get the minimum and maximum reaction values for the last step.

#         Parameters
#         ----------
#         step : _type_, optional
#             _description_, by default None
#         """
#         if not step:
#             step = self.steps_order[-1]
#         reactions = self.reaction_field
#         return reactions.get_limits_absolute(step)

#     def get_min_max_reactions_component(self, component, step=None):
#         """Get the minimum and maximum reaction values for the last step.

#         Parameters
#         ----------
#         component : _type_
#             _description_
#         step : _type_, optional
#             _description_, by default None
#         """
#         if not step:
#             step = self.steps_order[-1]
#         reactions = self.reaction_field
#         return reactions.get_limits_component(component, step)

#     # def get_total_moment(self, step=None):
#     #     if not step:
#     #         step = self.steps_order[-1]
#     #     vector, location = self.get_total_reaction(step)

#     #     return sum_vectors([reaction.vector for reaction in reactions.results])

#     def check_force_equilibrium(self):
#         """Checks whether the equilibrium between reactions and applied loads is respected and
#         returns the total applied loads and total reaction forces.

#         Prints whether the equilibrium is found and the total loads and reactions.

#         Returns
#         -------
#         The two lists of total reaction and applied loads according to global x-, y- ans z-axis.

#         """

#         applied_load = [0, 0, 0]
#         reaction_vector = self.get_total_reaction(self)[0]
#         for load_field in self.loads:
#             for load in load_field.loads:
#                 applied_load[0], applied_load[1], applied_load[2] = applied_load[0] + load.x, applied_load[1] + load.y, applied_load[2] + load.z
#         equilibriumx = applied_load[0] + reaction_vector.x < (applied_load[0] / 1000 if applied_load[0] != 0 else 1e-3)
#         equilibriumy = applied_load[1] + reaction_vector.y < (applied_load[1] / 1000 if applied_load[1] != 0 else 1e-3)
#         equilibriumz = applied_load[2] + reaction_vector.z < (applied_load[2] / 1000 if applied_load[2] != 0 else 1e-3)
#         if equilibriumx and equilibriumy and equilibriumz:
#             print("The force equilibrium is respected.")
#         else:
#             print("The force equilibrium is not respected.")
#         print(
#             f""" Total reactions :
# X : {reaction_vector.x}
# Y : {reaction_vector.y}
# Z : {reaction_vector.z}

# Total applied loads :
# X : {applied_load[0]}
# Y : {applied_load[1]}
# Z : {applied_load[2]}
# """
#         )
#         return reaction_vector, applied_load

# # ==============================================================================
# # Visualisation
# # ==============================================================================

# def show_deformed(self, viewer, opacity=1, show_bcs=1, scale_results=1, scale_model=1, show_loads=0.1, show_original=False, **kwargs):
#     """Display the structure in its deformed configuration.

#     Parameters
#     ----------
#     opacity : float, optional
#         Opacity of the model, by default 1.
#     show_bcs : bool, optional
#         Whether to show boundary conditions, by default True.
#     scale_results : float, optional
#         Scale factor for results, by default 1.
#     scale_model : float, optional
#         Scale factor for the model, by default 1.
#     show_loads : bool, optional
#         Whether to show loads, by default True.
#     show_original : bool, optional
#         Whether to show the original model, by default False.

#     Returns
#     -------
#     None
#     """

#     if show_original:
#         viewer.add_model(self.model, fast=True, opacity=show_original, show_bcs=False, **kwargs)
#     # TODO create a copy of the model first
#     displacements = self.displacement_field
#     for displacement in displacements.results:
#         vector = displacement.vector.scaled(scale_results)
#         displacement.node.xyz = sum_vectors([Vector(*displacement.node.xyz), vector])
#     viewer.add_model(self.model, fast=True, opacity=opacity, show_bcs=bool(show_bcs), show_loads=bool(show_loads), **kwargs)
#     if show_loads:
#         viewer.add_step(self, show_loads=show_loads)
#     viewer.show()

# def show_displacements(self, viewer, fast=True, show_bcs=1, scale_model=1, show_loads=0.1, component=None, show_vectors=True, show_contour=True, **kwargs):
#     """Display the displacement field results for a given step.

#     Parameters
#     ----------
#     step : _type_, optional
#         _description_, by default None
#     scale_model : int, optional
#         _description_, by default 1
#     show_loads : bool, optional
#         _description_, by default True
#     component : _type_, optional
#         _description_, by default

#     """

#     if not self.displacement_field:
#         raise ValueError("No displacement field results available for this step")

#     viewer.add_model(self.model, fast=fast, show_parts=True, opacity=0.5, show_bcs=show_bcs, show_loads=show_loads, **kwargs)
#     viewer.add_displacement_field(self.displacement_field, fast=fast, model=self.model, component=component, show_vectors=show_vectors, show_contour=show_contour, **kwargs)
#     if show_loads:
#         viewer.add_step(self, show_loads=show_loads)
#     viewer.show()
#     viewer.scene.clear()

# def show_reactions(self, viewer, fast=True, show_bcs=1, scale_model=1, show_loads=0.1, component=None, show_vectors=1, show_contour=False, **kwargs):
#     """Display the reaction field results for a given step.

#     Parameters
#     ----------
#     fast : bool, optional
#         Whether to use fast rendering, by default True.
#     show_bcs : bool, optional
#         Whether to show boundary conditions, by default True.
#     scale_model : int, optional
#         Scale factor for the model, by default 1.
#     show_loads : bool, optional
#         Whether to show loads, by default True.
#     component : str, optional
#         Component of the reaction field to display, by default None.
#     show_vectors : bool, optional
#         Whether to show reaction vectors, by default True.
#     show_contour : bool, optional
#         Whether to show reaction contours, by default False.

#     Returns
#     -------
#     None
#     """
#     if not self.reaction_field:
#         raise ValueError("No reaction field results available for this step")

#     viewer.add_model(self.model, fast=fast, show_parts=True, opacity=0.5, show_bcs=bool(show_bcs), show_loads=bool(show_loads), **kwargs)
#     viewer.add_reaction_field(self.reaction_field, fast=fast, model=self.model, component=component, show_vectors=bool(show_vectors), show_contour=show_contour, **kwargs)

#     if show_loads:
#         viewer.add_step(self, show_loads=int(show_loads))
#     viewer.show()

# def show_stress(self, viewer, fast=True, show_bcs=1, scale_model=1, show_loads=0.1, component=None, show_vectors=1, show_contour=False, plane="mid", **kwargs):
#     if not self.stress_field:
#         raise ValueError("No reaction field results available for this step")

#     viewer.add_model(self.model, fast=fast, show_parts=True, opacity=0.5, show_bcs=show_bcs, show_loads=show_loads, **kwargs)
#     viewer.add_stress2D_field(self.stress_field, fast=fast, model=self.model, component=component, show_vectors=show_vectors, show_contour=show_contour, plane=plane, **kwargs)

#     if show_loads:
#         viewer.add_step(self, show_loads=show_loads)
#     viewer.show()
#     viewer.scene.clear()


# def plot_deflection_along_line(self, line, n_divide=1000):
#     """Plot the deflection along a compas line given as an input. This method can only be used on shell models.

#     Parameters
#     ----------
#     line : :class=`compas.geometry.Line`
#         Line along which the deflection is plotted.
#     n_divide : int, optional
#         Number of division of the input line.
#         If not indicated, a value of 1000 is implemented.

#     """
#     import matplotlib.pyplot as plt
#     from compas.geometry import Point
#     from scipy.spatial import KDTree

#     # -----------------------------------------------------------
#     # FIRST, the input line is discretized in n_divide points
#     # -----------------------------------------------------------
#     # TODO automatized the n_divide parameters with the mesh density

#     length = line.length / n_divide
#     l_discretized = line.divide_by_length(length)

#     # --------------------------------------------------------------------------------------------------------------------
#     # SECOND, looking for the closest points of mesh to input line, according to their projection on the horizontal plan
#     # --------------------------------------------------------------------------------------------------------------------
#     part = list(self.model.parts)[0]
#     nodes = part.nodes

#     # projection of the nodes of the mesh on the XY plan
#     element_XY_points = [Point(node.xyz[0], node.xyz[1], 0) for node in nodes]

#     # determination of the closest nodes of the projected mesh to the input line
#     l_closestpoints = []
#     for point_line in l_discretized:
#         tree = KDTree(element_XY_points)
#         _, closest_2D_point_index = tree.query(point_line, k=1)
#         closest_3D_point = list(nodes)[closest_2D_point_index]
#         l_closestpoints.append(closest_3D_point)

#     # Remove duplicate points
#     l_closestpoints = list(dict.fromkeys(l_closestpoints))

#     # --------------------------------------------------------------------------------------------------------------------
#     # THIRD, extraction of the deflection values of the nodes of the mesh
#     # --------------------------------------------------------------------------------------------------------------------
#     field_displacement = self.displacement_field

#     # Construction of plotting lists
#     plot_value = [field_displacement.get_result_at(point).z for point in l_closestpoints]
#     x_list = [point.x for point in l_closestpoints]
#     y_list = [point.y for point in l_closestpoints]

#     # --------------------------------------------------------------------------------------------------------------------
#     # FINAL, script for plot display.
#     # --------------------------------------------------------------------------------------------------------------------
#     fig, ax = plt.subplots()
#     ax.plot(x_list, plot_value, linestyle="dashed")
#     ax.set(xlabel="x", ylabel="Displacement (mm)", title="Displacement along line")

#     plt.show()
