from typing import TYPE_CHECKING
from typing import Iterable

from compas.geometry import Point
from compas.geometry import Vector
from compas.geometry import centroid_points_weighted
from compas.geometry import sum_vectors

from compas_fea2.base import FEAData
from compas_fea2.model.groups import NodesGroup
from compas_fea2.model.nodes import Node
from compas_fea2.problem.displacements import GeneralDisplacement
from compas_fea2.problem.fields import DisplacementField
from compas_fea2.problem.fields import NodeLoadField
from compas_fea2.problem.fields import _PrescribedField
from compas_fea2.results import TemperatureFieldResults

if TYPE_CHECKING:
    from compas_fea2.model import Model
    from compas_fea2.model import NodesGroup
    from compas_fea2.problem import Problem

# ==============================================================================
#                                Base Steps
# ==============================================================================


class _Step(FEAData):
    """Initialises base Step object.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.

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

    def __init__(self, replace=False, **kwargs):
        super(_Step, self).__init__(**kwargs)
        self.replace = replace
        self._field_outputs = set()
        self._history_outputs = set()
        self._results = None
        self._key = None

        self._load_fields = set()
        self._load_cases = set()
        self._combination = None
        self._prescribed_fields = dict()

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
        return self._field_outputs

    @property
    def load_cases(self):
        return self._load_cases

    @property
    def load_fields(self):
        return self._load_fields

    @property
    def combination(self):
        return self._combination

    @property
    def prescribed_fields(self):
        return self._prescribed_fields
        
    @property
    def amplitudes(self):
        amplitudes=set()
        for load_field in self.load_fields:
            for load in filter(lambda p: getattr(p, "amplitude"), load_field.loads):
                amplitudes.add(load.amplitudes)
        return amplitudes

    @combination.setter
    def combination(self, combination):
        """Combine the load patterns according to their load case.

        Parameters
        ----------
        combination : :class:`compas_fea2.problem.combinations.LoadCombination`
            _description_

        Raises
        ------
        ValueError
            _description_
        """
        combination._registration = self
        self._combination = combination
        # for case in combination.load_cases:
        #     if case not in self._load_cases:
        #         raise ValueError(f"{case} is not a valid load case.")
        for field in self.load_fields:
            if field.load_case in combination.load_cases:
                factor = combination.factors[field.load_case]
                for node, load in field.node_load:
                    factored_load = factor * load

                    node.loads.setdefault(self, {}).setdefault(combination, {})[field] = factored_load
                    if node._total_load:
                        node._total_load += factored_load
                    else:
                        node._total_load = factored_load

    @property
    def history_outputs(self):
        return self._history_outputs

    @property
    def results(self):
        return self._results

    # ==========================================================================
    #                             Field outputs
    # ==========================================================================
    def add_output(self, output):
        """Request a field or history output.

        Parameters
        ----------
        output : :class:`compas_fea2.Results.FieldResults`
            The requested output.

        Returns
        -------
        :class:`compas_fea2.problem._Output`
            The requested output.

        Raises
        ------
        TypeError
            if the output is not an instance of an :class:`compas_fea2.problem._Output`.
        """
        # output._registration = self
        self._field_outputs.add(output(self))
        return output

    def add_outputs(self, outputs):
        """Request multiple field or history outputs.

        Parameters
        ----------
        outputs : list(:class:`compas_fea2.problem._Output`)
            The requested outputs.

        Returns
        -------
        list(:class:`compas_fea2.problem._Output`)
            The requested outputs.

        Raises
        ------
        TypeError
            if the output is not an instance of an :class:`compas_fea2.problem._Output`.
        """
        for output in outputs:
            self.add_output(output)

    # ==========================================================================
    #                             Results methods
    # ==========================================================================

    @property
    def displacement_field(self):
        from compas_fea2.results.fields import DisplacementFieldResults

        return DisplacementFieldResults(self)

    @property
    def reaction_field(self):
        from compas_fea2.results.fields import ReactionFieldResults

        return ReactionFieldResults(self)

    @property
    def temperature_field(self):
        return TemperatureFieldResults(self)

    @property
    def stress_field(self):
        from compas_fea2.results.fields import StressFieldResults

        return StressFieldResults(self)

    @property
    def section_forces_field(self):
        from compas_fea2.results.fields import SectionForcesFieldResults

        return SectionForcesFieldResults(self)

    @property
    def __data__(self):
        return {
            "name": self.name,
            "field_outputs": list(self._field_outputs),
            "history_outputs": list(self._history_outputs),
            "results": self._results,
            "key": self._key,
            "patterns": list(self._load_fields),
            "load_cases": list(self._load_cases),
            "combination": self._combination,
        }

    @classmethod
    def __from_data__(cls, data):
        obj = cls()
        obj.name = data["name"]
        obj._field_outputs = set(data["field_outputs"])
        obj._history_outputs = set(data["history_outputs"])
        obj._results = data["results"]
        obj._key = data["key"]
        obj._load_fields = set(data["load_fields"])
        obj._load_cases = set(data["load_cases"])
        obj._combination = data["combination"]
        return obj


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

    @property
    def displacements(self):
        return list(filter(lambda p: isinstance(p, DisplacementField), self._load_fields))

    @property
    def loads(self):
        return list(filter(lambda p: not isinstance(p, DisplacementField), self._load_fields))

    @property
    def max_increments(self):
        return self._max_increments

    @property
    def initial_inc_size(self):
        return self._initial_inc_size

    @property
    def min_inc_size(self):
        return self._min_inc_size

    @property
    def max_inc_size(self):
        return self._max_inc_size

    @property
    def time(self):
        return self._time

    @property
    def nlgeom(self):
        return self._nlgeom

    @property
    def modify(self):
        return self._modify

    @property
    def restart(self):
        return self._restart

    @restart.setter
    def restart(self, value):
        self._restart = value

    # ==============================================================================
    #                               Load Fields
    # ==============================================================================

    def add_load_field(self, field: NodeLoadField | DisplacementField):
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
            raise TypeError("{!r} is not a LoadField.".format(field))
        self._load_fields.add(field)
        self._load_cases.add(field.load_case)
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
            self.add_load_field(field)

    def add_uniform_vector_field(self, nodes, load_case=None, x=None, y=None, z=None, xx=None, yy=None, zz=None, amplitude=None, **kwargs):
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
        field = NodeLoadField(loads=[load], nodes=nodes, load_case=load_case, **kwargs)

        return self.add_load_field(field)

    def add_uniform_scalar_field(self, nodes, load_case=None, value=None, amplitude=None, **kwargs):
        """Add a :class:`compas_fea2.problem.fields.NodeLoadField` where all the nodes
        have the same scalar load.
        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`] | :class:`compas_fea2.model.NodesGroup`
            Nodes where the load is applied.
        load_case : str, optional
            Load case name, by default None
        value : float, optional
            Value of the scalar load, by default None
        amplitude : str, optional
            Name of the amplitude to be used, by default None
        **kwargs : dict
            Additional keyword arguments to be passed to the NodeLoadField constructor.

        Returns
        -------
        :class:`compas_fea2.problem.fields.NodeLoadField`
        """
        from compas_fea2.problem.loads import ScalarLoad

        if not isinstance(nodes, (list, tuple, NodesGroup)):
            raise TypeError("nodes must be a list, tuple or NodesGroup, not {}".format(type(nodes)))
        nodes = NodesGroup(nodes) if not isinstance(nodes, NodesGroup) else nodes
        load = ScalarLoad(scalar_load=value, amplitude=amplitude)
        field = NodeLoadField(loads=[load], nodes=nodes, load_case=load_case, **kwargs)

        return self.add_load_field(field)

    def add_uniform_line_field(self, polyline, load_case=None, discretization=10, x=None, y=None, z=None, xx=None, yy=None, zz=None, axes="global", tolerance=None, **kwargs):
        """Add a :class:`compas_fea2.problem.field.NodeLoadField` subclass object to the
        ``Step`` along a prescribed path.
        """
        raise NotImplementedError("This method is not implemented yet.")

    def add_surface_field_from_polygon(self, polygon, load_case=None, x=None, y=None, z=None, xx=None, yy=None, zz=None, axes="global", **kwargs):
        from compas_fea2.problem.fields import UniformSurfaceLoadField
        from compas_fea2.problem.loads import VectorLoad

        if not self.model:
            raise AttributeError("Step is not registered to a Model.")
        surface = self.model.find_faces_in_polygon(polygon)

        load = VectorLoad(x=x, y=y, z=z, xx=xx, yy=yy, zz=zz, axes=axes)

        field = UniformSurfaceLoadField(load=[load], surface=surface, load_case=load_case, **kwargs)

        return self.add_load_field(field)

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
        from compas_fea2.problem import VectorLoad
        from compas_fea2.problem.fields import UniformSurfaceLoadField

        components = {"x": x or 0, "y": y or 0, "z": z or 0, "xx": xx or 0, "yy": yy or 0, "zz": zz or 0}
        load = VectorLoad(**components, axes=axes)
        field = UniformSurfaceLoadField(load=load, surface=surface, load_case=load_case, **kwargs)

        return self.add_load_field(field)

    def add_gravity_fied(self, parts=None, g=9.81, x=0.0, y=0.0, z=-1.0, load_case=None, **kwargs):
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

        gravity = GravityLoadField(g=g, parts=parts, direction=[x, y, z], load_case=load_case, **kwargs)
        self.add_load_field(gravity)

    def add_temperature_field(self, field, node):
        """Add a temperature field to the Step object.

        Parameters
        ----------
        field : :class:`compas_fea2.problem.fields.PrescribedTemperatureField`
            The temperature field to add.
        node : :class:`compas_fea2.model.Node`
            The node to which the temperature field is applied.

        Returns
        -------
        :class:`compas_fea2.problem.fields.PrescribedTemperatureField`
            The temperature field that was added.
        """
        raise NotImplementedError()

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
        from compas_fea2.problem.fields import DisplacementField

        if not isinstance(nodes, (list, tuple, NodesGroup)):
            raise TypeError(f"nodes must be a list, tuple, or NodesGroup, not {type(nodes)}")
        nodes = NodesGroup(nodes) if not isinstance(nodes, NodesGroup) else nodes

        displacement = GeneralDisplacement(x=x, y=y, z=z, xx=xx, yy=yy, zz=zz, axes=axes, **kwargs)
        return self.add_load_field(DisplacementField(displacement, nodes))

    # ==============================================================================
    #                             Prescribed Fields
    # ==============================================================================
    def _add_prescribed_field(self, prescribed_field, group):
        """Add a prescribed field to the model.

        Parameters
        ----------
        prescribed_field : :class=`compas_fea2.problem.fields._PrescribedField`
            The prescribed field to add.
        group : :class=`compas_fea2.model.NodesGroup`
            Group of nodes where the field is applied.

        Returns
        -------
        :class=`compas_fea2.problem.fields._PrescribedField`
        """
        if not isinstance(prescribed_field, _PrescribedField):
            raise TypeError(f"{prescribed_field!r} is not a _PrescribedField.")

        if not isinstance(group, NodesGroup):
            raise TypeError(f"{group!r} is not a NodesGroup.")

        for member in group.members:
            if not isinstance(member, Node):
                raise TypeError(f"{member!r} is not a Node.")

        prescribed_field._registration = self  # Ensure this attribute is valid
        self._prescribed_fields[prescribed_field] = group.members
        return prescribed_field

    def add_nodes_prescribed_field(self, prescribed_field, nodes):
        """Add a :class:`compas_fea2.model._InitialCondition` to the model.

        Parameters
        ----------
        ic : :class:`compas_fea2.model._InitialCondition`
        nodes : list[:class:`compas_fea2.model.Node`] or :class:`compas_fea2.model.NodesGroup`

        Returns
        -------
        :class:`compas_fea2.model._InitialCondition`

        """
        if not isinstance(nodes, NodesGroup):
            raise TypeError("{} is not a group of nodes".format(nodes))
        self._add_prescribed_field(prescribed_field, nodes)
        return prescribed_field

    def add_prescribed_field(self, field, *kwargs):
        """Add a general :class:`compas_fea2.problem.patterns.Pattern` to the Step.

        Parameters
        ----------

        Returns
        -------
        :class:`compas_fea2.problem.patterns.Pattern`

        """

        if not isinstance(field, _PrescribedField):
            raise TypeError("{!r} is not a _PrescribedField.".format(field))

        self._prescribed_fields.add(field)
        field._registration = self
        return field

    # ==============================================================================
    #                             Combinations
    # ==============================================================================

    # =========================================================================
    #                         Results methods - reactions
    # =========================================================================

    def get_total_reaction(self, step=None):
        """Compute the total reaction vector

        Parameters
        ----------
        step : :class=`compas_fea2.problem._Step`, optional
            The analysis step, by default the last step.

        Returns
        -------
        :class=`compas.geometry.Vector`
            The resultant vector.
        :class=`compas.geometry.Point`
            The application point.
        """
        if not step:
            step = self.steps_order[-1]
        reactions = self.reaction_field
        locations, vectors, vectors_lengths = [], [], []
        for reaction in reactions.results:
            locations.append(reaction.location.xyz)
            vectors.append(reaction.vector)
            vectors_lengths.append(reaction.vector.length)
        return Vector(*sum_vectors(vectors)), Point(*centroid_points_weighted(locations, vectors_lengths))

    def get_min_max_reactions(self, step=None):
        """Get the minimum and maximum reaction values for the last step.

        Parameters
        ----------
        step : _type_, optional
            _description_, by default None
        """
        if not step:
            step = self.steps_order[-1]
        reactions = self.reaction_field
        return reactions.get_limits_absolute(step)

    def get_min_max_reactions_component(self, component, step=None):
        """Get the minimum and maximum reaction values for the last step.

        Parameters
        ----------
        component : _type_
            _description_
        step : _type_, optional
            _description_, by default None
        """
        if not step:
            step = self.steps_order[-1]
        reactions = self.reaction_field
        return reactions.get_limits_component(component, step)

    # def get_total_moment(self, step=None):
    #     if not step:
    #         step = self.steps_order[-1]
    #     vector, location = self.get_total_reaction(step)

    #     return sum_vectors([reaction.vector for reaction in reactions.results])

    def check_force_equilibrium(self):
        """Checks whether the equilibrium between reactions and applied loads is respected and
        returns the total applied loads and total reaction forces.

        Prints whether the equilibrium is found and the total loads and reactions.

        Returns
        -------
        The two lists of total reaction and applied loads according to global x-, y- ans z-axis.

        """

        applied_load = [0, 0, 0]
        reaction_vector = self.get_total_reaction(self)[0]
        for load_field in self.loads:
            for load in load_field.loads:
                applied_load[0], applied_load[1], applied_load[2] = applied_load[0] + load.x, applied_load[1] + load.y, applied_load[2] + load.z
        equilibriumx = applied_load[0] + reaction_vector.x < (applied_load[0] / 1000 if applied_load[0] != 0 else 1e-3)
        equilibriumy = applied_load[1] + reaction_vector.y < (applied_load[1] / 1000 if applied_load[1] != 0 else 1e-3)
        equilibriumz = applied_load[2] + reaction_vector.z < (applied_load[2] / 1000 if applied_load[2] != 0 else 1e-3)
        if equilibriumx and equilibriumy and equilibriumz:
            print("The force equilibrium is respected.")
        else:
            print("The force equilibrium is not respected.")
        print(
            f""" Total reactions :
X : {reaction_vector.x}
Y : {reaction_vector.y}
Z : {reaction_vector.z}

Total applied loads :
X : {applied_load[0]}
Y : {applied_load[1]}
Z : {applied_load[2]}
"""
        )
        return reaction_vector, applied_load

    # ==============================================================================
    # Visualisation
    # ==============================================================================

    def show_deformed(self, viewer, opacity=1, show_bcs=1, scale_results=1, scale_model=1, show_loads=0.1, show_original=False, **kwargs):
        """Display the structure in its deformed configuration.

        Parameters
        ----------
        opacity : float, optional
            Opacity of the model, by default 1.
        show_bcs : bool, optional
            Whether to show boundary conditions, by default True.
        scale_results : float, optional
            Scale factor for results, by default 1.
        scale_model : float, optional
            Scale factor for the model, by default 1.
        show_loads : bool, optional
            Whether to show loads, by default True.
        show_original : bool, optional
            Whether to show the original model, by default False.

        Returns
        -------
        None
        """

        if show_original:
            viewer.add_model(self.model, fast=True, opacity=show_original, show_bcs=False, **kwargs)
        # TODO create a copy of the model first
        displacements = self.displacement_field
        for displacement in displacements.results:
            vector = displacement.vector.scaled(scale_results)
            displacement.node.xyz = sum_vectors([Vector(*displacement.node.xyz), vector])
        viewer.add_model(self.model, fast=True, opacity=opacity, show_bcs=bool(show_bcs), show_loads=bool(show_loads), **kwargs)
        if show_loads:
            viewer.add_step(self, show_loads=show_loads)
        viewer.show()

    def show_displacements(self, viewer, fast=True, show_bcs=1, scale_model=1, show_loads=0.1, component=None, show_vectors=True, show_contour=True, **kwargs):
        """Display the displacement field results for a given step.

        Parameters
        ----------
        step : _type_, optional
            _description_, by default None
        scale_model : int, optional
            _description_, by default 1
        show_loads : bool, optional
            _description_, by default True
        component : _type_, optional
            _description_, by default

        """

        if not self.displacement_field:
            raise ValueError("No displacement field results available for this step")

        viewer.add_model(self.model, fast=fast, show_parts=True, opacity=0.5, show_bcs=show_bcs, show_loads=show_loads, **kwargs)
        viewer.add_displacement_field(self.displacement_field, fast=fast, model=self.model, component=component, show_vectors=show_vectors, show_contour=show_contour, **kwargs)
        if show_loads:
            viewer.add_step(self, show_loads=show_loads)
        viewer.show()
        viewer.scene.clear()

    def show_reactions(self, viewer, fast=True, show_bcs=1, scale_model=1, show_loads=0.1, component=None, show_vectors=1, show_contour=False, **kwargs):
        """Display the reaction field results for a given step.

        Parameters
        ----------
        fast : bool, optional
            Whether to use fast rendering, by default True.
        show_bcs : bool, optional
            Whether to show boundary conditions, by default True.
        scale_model : int, optional
            Scale factor for the model, by default 1.
        show_loads : bool, optional
            Whether to show loads, by default True.
        component : str, optional
            Component of the reaction field to display, by default None.
        show_vectors : bool, optional
            Whether to show reaction vectors, by default True.
        show_contour : bool, optional
            Whether to show reaction contours, by default False.

        Returns
        -------
        None
        """
        if not self.reaction_field:
            raise ValueError("No reaction field results available for this step")

        viewer.add_model(self.model, fast=fast, show_parts=True, opacity=0.5, show_bcs=bool(show_bcs), show_loads=bool(show_loads), **kwargs)
        viewer.add_reaction_field(self.reaction_field, fast=fast, model=self.model, component=component, show_vectors=bool(show_vectors), show_contour=show_contour, **kwargs)

        if show_loads:
            viewer.add_step(self, show_loads=int(show_loads))
        viewer.show()

    def show_stress(self, viewer, fast=True, show_bcs=1, scale_model=1, show_loads=0.1, component=None, show_vectors=1, show_contour=False, plane="mid", **kwargs):
        if not self.stress_field:
            raise ValueError("No reaction field results available for this step")

        viewer.add_model(self.model, fast=fast, show_parts=True, opacity=0.5, show_bcs=show_bcs, show_loads=show_loads, **kwargs)
        viewer.add_stress2D_field(self.stress_field, fast=fast, model=self.model, component=component, show_vectors=show_vectors, show_contour=show_contour, plane=plane, **kwargs)

        if show_loads:
            viewer.add_step(self, show_loads=show_loads)
        viewer.show()
        viewer.scene.clear()

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "max_increments": self._max_increments,
                "initial_inc_size": self._initial_inc_size,
                "min_inc_size": self._min_inc_size,
                "time": self._time,
                "nlgeom": self._nlgeom,
                "modify": self._modify,
                "restart": self._restart,
            }
        )
        return data

    def plot_deflection_along_line(self, line, n_divide=1000):
        """Plot the deflection along a compas line given as an input. This method can only be used on shell models.

        Parameters
        ----------
        line : :class=`compas.geometry.Line`
            Line along which the deflection is plotted.
        n_divide : int, optional
            Number of division of the input line.
            If not indicated, a value of 1000 is implemented.

        """
        import matplotlib.pyplot as plt
        from compas.geometry import Point
        from scipy.spatial import KDTree

        # -----------------------------------------------------------
        # FIRST, the input line is discretized in n_divide points
        # -----------------------------------------------------------
        # TODO automatized the n_divide parameters with the mesh density

        length = line.length / n_divide
        l_discretized = line.divide_by_length(length)

        # --------------------------------------------------------------------------------------------------------------------
        # SECOND, looking for the closest points of mesh to input line, according to their projection on the horizontal plan
        # --------------------------------------------------------------------------------------------------------------------
        part = list(self.model.parts)[0]
        nodes = part.nodes

        # projection of the nodes of the mesh on the XY plan
        element_XY_points = [Point(node.xyz[0], node.xyz[1], 0) for node in nodes]

        # determination of the closest nodes of the projected mesh to the input line
        l_closestpoints = []
        for point_line in l_discretized:
            tree = KDTree(element_XY_points)
            _, closest_2D_point_index = tree.query(point_line, k=1)
            closest_3D_point = list(nodes)[closest_2D_point_index]
            l_closestpoints.append(closest_3D_point)

        # Remove duplicate points
        l_closestpoints = list(dict.fromkeys(l_closestpoints))

        # --------------------------------------------------------------------------------------------------------------------
        # THIRD, extraction of the deflection values of the nodes of the mesh
        # --------------------------------------------------------------------------------------------------------------------
        field_displacement = self.displacement_field

        # Construction of plotting lists
        plot_value = [field_displacement.get_result_at(point).z for point in l_closestpoints]
        x_list = [point.x for point in l_closestpoints]
        y_list = [point.y for point in l_closestpoints]

        # --------------------------------------------------------------------------------------------------------------------
        # FINAL, script for plot display.
        # --------------------------------------------------------------------------------------------------------------------
        fig, ax = plt.subplots()
        ax.plot(x_list, plot_value, linestyle="dashed")
        ax.set(xlabel="x", ylabel="Displacement (mm)", title="Displacement along line")

        plt.show()

    @classmethod
    def __from_data__(cls, data):
        obj = cls(
            max_increments=data["max_increments"],
            initial_inc_size=data["initial_inc_size"],
            min_inc_size=data["min_inc_size"],
            time=data["time"],
            nlgeom=data["nlgeom"],
            modify=data["modify"],
            restart=data["restart"],
        )
        obj._field_outputs = set(data["field_outputs"])
        obj._history_outputs = set(data["history_outputs"])
        obj._results = data["results"]
        obj._key = data["key"]
        obj._load_fields = set(data["patterns"])
        obj._load_cases = set(data["load_cases"])
        obj._combination = data["combination"]
        return obj
