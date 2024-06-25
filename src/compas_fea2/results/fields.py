from itertools import groupby
from typing import List, Dict, Set, Any, Tuple, Iterable
import numpy as np

from compas_fea2.base import FEAData
from compas_fea2.model import _Element2D
from compas_fea2.model import _Element3D
from compas.geometry import Vector, Point

from .results import DisplacementResult
from .results import ReactionResult
from .results import ShellStressResult
from .results import SolidStressResult

from compas.geometry import Transformation, Frame


class FieldResults(FEAData):
    """FieldResults object. This is a collection of Result objects that define a field.

    The objects uses SQLite queries to efficiently retrieve the results from the results database.

    The field results are defined over multiple steps

    You can use FieldResults to visualise a field over a part or the model, or to compute
    global quantiies, such as maximum or minimum values.

    Parameters
    ----------
    field_name : str
        Name of the field.
    step : :class:`compas_fea2.problem._Step`
        The analysis step where the results are defined.

    Attributes
    ----------
    field_name : str
        Name of the field.
    step : :class:`compas_fea2.problem._Step`
        The analysis step where the results are defined.
    problem : :class:`compas_fea2.problem.Problem`
        The Problem where the Step is registered.
    model : :class:`compas_fea2.problem.Model
        The Model where the Step is registered.
    db_connection : :class:`sqlite3.Connection` | None
        Connection object or None
    components : dict
        A dictionary with {"component name": component value} for each component of the result.
    invariants : dict
        A dictionary with {"invariant name": invariant value} for each invariant of the result.

    Notes
    -----
    FieldResults are registered to a :class:`compas_fea2.problem.Problem`.

    """

    def __init__(self, problem, field_name, *args, **kwargs):
        super(FieldResults, self).__init__(*args, **kwargs)
        self._registration = problem
        self._field_name = field_name
        self._table = self.problem.results_db.get_table_from_name(field_name)
        self._results_class = None
        self._results_func = None

    @property
    def field_name(self):
        return self._field_name

    @property
    def problem(self):
        return self._registration

    @property
    def model(self):
        return self.problem.model

    @property
    def rdb(self):
        return self.problem.results_db

    @property
    def components_names(self):
        return self._table._components_names

    @property
    def invariants_names(self):
        return self._table._invariants_names

    @property
    def all_components(self):
        return self._table.all_components

    @property
    def results_columns(self):
        return

    def results(self, filters=None):
        results_set = self._table.get_rows(columns_names=self._table.all_columns, filters=filters)
        return self.to_fea2_results(results_set)

    def locations(self, step=None, point=False):
        """Return the locations where the field is defined.

        Parameters
        ----------
        step : :class:`compas_fea2.problem.steps.Step`, optional
            The analysis step, by default None

        Yields
        ------
        :class:`compas.geometry.Point`
            The location where the field is defined.
        """
        step = step or self.problem.steps_order[-1]
        for r in self.results(filters={'step': step.name}):
            if point:
                yield r.node.point
            else:
                yield r.node

    def vectors(self, step=None):
        """Return the locations where the field is defined.

        Parameters
        ----------
        step : :class:`compas_fea2.problem.steps.Step`, optional
            The analysis step, by default None

        Yields
        ------
        :class:`compas.geometry.Point`
            The location where the field is defined.
        """
        step = step or self.problem.steps_order[-1]
        for r in self.results(step):
            yield r.vector


    def vector_field(self, step=None, component=None, point=False):
        """Return the locations where the field is defined.

        Parameters
        ----------
        step : :class:`compas_fea2.problem.steps.Step`, optional
            The analysis step, by default None

        Yields
        ------
        :class:`compas.geometry.Point`
            The location where the field is defined.
        """
        step = step or self.problem.steps_order[-1]
        for l, r in zip(self.locations(step, point), self.results(filters={'step': step.name})):
            if component:
                vector_components = {c: r.vector[component] if component==n else 0. for n, c in enumerate(["x", "y", "z"], 1)}
                yield (l, Vector(**vector_components))
            else:
                yield (l, r.vector)

    def max_component(self, component, **kwargs):
        """Get the result where a component is maximum for a given step.

        Parameters
        ----------
        component : _type_
            _description_
        step : _type_
            _description_

        Returns
        -------
        :class:`compas_fea2.results.Result`
            The appriate Result object.
        """
        results_set = self._table.get_func_row(self.field_name + str(component), "MAX", kwargs, self._table.all_columns)
        return self.to_fea2_results(results_set)[0]

    def min_component(self, component, **kwargs):
        """Get the result where a component is minimum for a given step.

        Parameters
        ----------
        component : _type_
            _description_
        step : _type_
            _description_

        Returns
        -------
        :class:`compas_fea2.results.Result`
            The appriate Result object.
        """
        results_set = self._table.get_func_row(self.field_name + str(component), "MIN", kwargs, self._table.all_columns)
        return self.to_fea2_results(results_set)[0]

    def to_fea2_results(self, results_set: List[Dict[str, Any]]) -> Dict[Any, List[Any]]:
        """
        Convert a set of results in database format to the appropriate result object.

        Parameters
        ----------
        results_set : List[Dict[str, Any]]
            The result set from the database.

        Returns
        -------
        Dict[Any, List[Any]]
            Dictionary grouping the results per Step.
        """
        if not isinstance(results_set, List):
            results_set = [results_set]
        results = []
        for r in results_set:

            step = self.problem.find_step_by_name(r["step"]) or self.problem.find_step_by_name(r["step"], casefold=True)
            if not step:
                raise ValueError(f"Result {r['key']} is invalid. Step {r['step']} not found")

            part = self.model.find_part_by_name(r["part"]) or self.model.find_part_by_name(r["part"], casefold=True)
            if not part:
                raise ValueError(f"Result {r['key']} is invalid. Part {r['part']} not found")

            m = getattr(part, self._results_func)(r["key"] - self.model._starting_key)
            if not m:
                raise ValueError(f"Result {r['key']} is invalid. No Node/Element found.")

            result = self._results_class(m, *[r[c] for c in self._table._components_names])
            result._step = step

            results.append(result)
        return results


class _NodeFieldResults(FieldResults):
    """_summary_

    Parameters
    ----------
    FieldResults : _type_
        _description_
    """

    def __init__(self, problem, field_name, *args, **kwargs):
        super(_NodeFieldResults, self).__init__(problem=problem, field_name=field_name, *args, **kwargs)
        self._results_func = "find_node_by_key"


    def get_results_at_node(self, node, steps=None):
        """"""
        if not node:
            print(f"WARNING: No node found")
        else:
            steps = steps or self.problem.steps
            return self._get_results_from_db([node], steps)[0]

    def get_results_at_nodes(self, nodes, steps=None):
        """"""
        if not nodes:
            print(f"WARNING: No nodes found")
        else:
            steps = steps or self.problem.steps
            return self._get_results_from_db(nodes, steps)

    def get_results_at_point(self, point, distance, plane=None, steps=None):
        """Get the displacement of the model around a location (point).

        Parameters
        ----------
        point : [float]
            The coordinates of the point.
        steps : _type_, optional
            _description_, by default None

        Returns
        -------
        dict
            Dictionary with {step: result}

        """
        nodes = self.model.find_nodes_around_point(point, distance, plane)
        if not nodes:
            print(f"WARNING: No nodes found at {point} within {distance}")
        else:
            steps = steps or self.problem.steps
            results = self._get_results_from_db(nodes, steps)
            return results


class DisplacementFieldResults(_NodeFieldResults):
    """Displacement field.

    Parameters
    ----------
    FieldResults : _type_
        _description_
    """

    def __init__(self, problem, *args, **kwargs):
        super(DisplacementFieldResults, self).__init__(problem=problem, field_name="U", *args, **kwargs)
        self._results_class = DisplacementResult



class ReactionFieldResults(_NodeFieldResults):
    """Reaction field.

    Parameters
    ----------
    FieldResults : _type_
        _description_
    """

    def __init__(self, problem, *args, **kwargs):
        super(ReactionFieldResults, self).__init__(problem=problem, field_name="RF", *args, **kwargs)
        self._results_class = ReactionResult



class StressFieldResults(FEAData):
    """_summary_

    Parameters
    ----------
    FieldResults : _type_
        _description_
    """

    def __init__(self, problem, *args, **kwargs):
        super(StressFieldResults, self).__init__(*args, **kwargs)
        self._registration = problem
        self._components_names_2d = ["S11", "S22", "S12", "M11", "M22", "M12"]
        self._components_names_3d = ["S11", "S22", "S23", "S12", "S13", "S33"]
        self._field_name_2d = "S2D"
        self._field_name_3d = "S3D"
        self._results_class_2d = ShellStressResult
        self._results_class_3d = SolidStressResult
        self._results_func = "find_element_by_key"

    @property
    def field_name(self):
        return self._field_name

    @property
    def problem(self):
        return self._registration

    @property
    def model(self):
        return self.problem.model

    @property
    def rdb(self):
        return self.problem.results_db

    @property
    def components_names(self):
        return self._components_names

    @property
    def invariants_names(self):
        return self._invariants_names

    # def _get_results_from_db(self, members, steps):
    #     """Get the results for the given members and steps in the database
    #     format.

    #     Parameters
    #     ----------
    #     members : _type_
    #         _description_
    #     steps : _type_
    #         _description_

    #     Returns
    #     -------
    #     _type_
    #         _description_
    #     """
    #     if not isinstance(members, Iterable):
    #         members = [members]
    #     if not isinstance(steps, Iterable):
    #         steps = [steps]

    #     members_keys = {}
    #     parts_names = {}
    #     for member in members:
    #         members_keys[member.input_key] = member
    #         parts_names[member.part.name] = member.part
    #     steps_names = {step.name: step for step in steps}

    #     if isinstance(members[0], _Element3D):
    #         columns = ["step", "part", "key"] + self._components_names_3d
    #         field_name = self._field_name_3d
    #     elif isinstance(members[0], _Element2D):
    #         columns = ["step", "part", "key"] + self._components_names_2d
    #         field_name = self._field_name_2d
    #     else:
    #         raise ValueError("Not an element")

    #     results_set = self.rdb.get_rows(field_name, columns, {"key": members_keys, "part": parts_names, "step": steps_names})
    #     return self._to_fea2_results(results_set, members_keys, steps_names)


    def get_results_at_point(self, point, distance, plane=None, steps=None):
        """Get the displacement of the model around a location (point).

        Parameters
        ----------
        point : [float]
            The coordinates of the point.
        steps : _type_, optional
            _description_, by default None

        Returns
        -------
        dict
            Dictionary with {'part':..; 'node':..; 'vector':...}

        """
        nodes = self.model.find_nodes_around_point(point, distance, plane)
        results = []
        for step in steps:
            results.append(self.get_results(nodes, steps)[step])


    def locations(self, step=None, point=False):
        """Return the locations where the field is defined.

        Parameters
        ----------
        step : :class:`compas_fea2.problem.steps.Step`, optional
            The analysis step, by default None

        Yields
        ------
        :class:`compas.geometry.Point`
            The location where the field is defined.
        """
        step = step or self.problem.steps_order[-1]
        for s in self.results(step):
            if point:
                yield Point(*s.reference_point)
            else:
                yield s.reference_point

    def global_stresses(self, step=None):
        """Stress field in global coordinates

        Parameters
        ----------
        step : :class:`compas_fea2.problem.steps.Step`, optional
            The analysis step, by default None


        Returns
        -------
        numpy array
            The stress tensor defined at each location of the field in
            global coordinates.
        """
        step = step or self.problem.steps_order[-1]
        results = self.results(step)
        n_locations = len(results)
        new_frame = Frame.worldXY()

        # Initialize tensors and rotation_matrices arrays
        tensors = np.zeros((n_locations, 3, 3))
        rotation_matrices = np.zeros((n_locations, 3, 3))

        from_change_of_basis = Transformation.from_change_of_basis
        np_array = np.array

        for i, r in enumerate(results):
            tensors[i] = r.local_stress
            rotation_matrices[i] = np_array(from_change_of_basis(r.element.frame, new_frame).matrix)[:3, :3]

        # Perform the tensor transformation using numpy's batch matrix multiplication
        transformed_tensors = rotation_matrices @ tensors @ rotation_matrices.transpose(0, 2, 1)

        return transformed_tensors

    def principal_components(self, step=None):
        """Compute the eigenvalues and eigenvetors of the stress field at each location.

        Parameters
        ----------
        step : :class:`compas_fea2.problem.steps.Step`, optional
            The analysis step in which the stress filed is defined. If not
            provided, the last analysis step is used.

        Returns
        -------
        touple(np.array, np.array)
            The eigenvalues and the eigenvectors, not ordered.
        """
        step = step or self.problem.steps_order[-1]
        return np.linalg.eig(self.global_stresses(step))

    def principal_components_vectors(self, step=None):
        """Compute the principal components of the stress field at each location
        as vectors.

        Parameters
        ----------
        step : :class:`compas_fea2.problem.steps.Step`, optional
            The analysis step in which the stress filed is defined. If not
            provided, the last analysis step is used.


        Yields
        ------
        list(:class:`compas.geometry.Vector)
            list with the vectors corresponding to max, mid and min principal componets.
        """
        step = step or self.problem.steps_order[-1]
        eigenvalues, eigenvectors = self.principal_components(step)
        sorted_indices = np.argsort(eigenvalues, axis=1)
        sorted_eigenvalues = np.take_along_axis(eigenvalues, sorted_indices, axis=1)
        sorted_eigenvectors = np.take_along_axis(eigenvectors, sorted_indices[:, np.newaxis, :], axis=2)
        for i in range(eigenvalues.shape[0]):
            yield [Vector(*sorted_eigenvectors[i, :, j]) * sorted_eigenvalues[i, j] for j in range(eigenvalues.shape[1])]

    def vonmieses(self, step=None):
        """Compute the principal components of the stress field at each location
        as vectors.

        Parameters
        ----------
        step : :class:`compas_fea2.problem.steps.Step`, optional
            The analysis step in which the stress filed is defined. If not
            provided, the last analysis step is used.


        Yields
        ------
        list(:class:`compas.geometry.Vector)
            list with the vectors corresponding to max, mid and min principal componets.
        """
        step = step or self.problem.steps_order[-1]
        for r in self.results(step):
            yield r.von_mises_stress
