import csv
import logging
from itertools import groupby
from typing import TYPE_CHECKING
from typing import Iterable
from typing import Optional

from compas.geometry import Vector

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data

# Use the abstract DB interface to avoid hard-coupling to SQLite
from .database import ResultsDatabase

if TYPE_CHECKING:
    from compas_fea2.model import Model
    from compas_fea2.problem import Problem
    from compas_fea2.problem import _Step


logger = logging.getLogger(__name__)


class FieldResults(FEAData):
    """FieldResults object. This is a collection of Result objects that define a field.

    The objects use SQLite queries to efficiently retrieve the results from the results database.

    The field results are defined over multiple steps.

    You can use FieldResults to visualize a field over a part or the model, or to compute
    global quantities, such as maximum or minimum values.


    Notes
    -----
    FieldResults are registered to a :class:`compas_fea2.problem.Step`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def sqltable_schema(self):
        """Return the SQL table schema for the field results.
        The schema includes the table name and the columns with their types.

        Returns
        -------
        dict
            A dictionary with the table name and columns.

        Example
        -------
        >>> field_results = DisplacementFieldResults(step)
        >>> field_results.sqltable_schema
        {'table_name': 'u', 'columns': [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'), ('key', 'INTEGER'), ('step', 'TEXT'), ('part', 'TEXT'), ('x', 'REAL'), ('y', 'REAL'), ('z', 'REAL'), ('rx', 'REAL'), ('ry', 'REAL'), ('rz', 'REAL')]}
        """
        fields = []
        predefined_fields = [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("key", "INTEGER"),
            ("step", "TEXT"),
            ("part", "TEXT"),
        ]

        fields.extend(predefined_fields)

        for comp in self.components_names:
            fields.append((comp, "REAL"))
        return {
            "table_name": self.field_name,
            "columns": fields,
        }

    @property
    def step(self) -> "_Step | None":
        return self._registration

    @property
    def problem(self) -> "Problem":
        if not self.step:
            raise ValueError("The step is not registered to a problem.")
        return self.step.problem

    @property
    def model(self) -> "Model":
        if not self.problem.model:
            raise ValueError("The problem is not registered to a model.")
        return self.problem.model

    @property
    def components_names(self):
        """Names of the components of the field results."""
        raise NotImplementedError("This method should be implemented in the subclass.")

    @property
    def field_name(self) -> str:
        raise NotImplementedError("This method should be implemented in the subclass.")

    @property
    def results_func(self) -> str:
        raise NotImplementedError("This method should be implemented in the subclass.")

    @property
    def result_cls(self):
        """Return the class used to instantiate the results."""
        if not self._result_cls:
            raise ValueError("Result class is not set. Please set the result class in the subclass.")
        return self._result_cls

    @property
    def rdb(self) -> ResultsDatabase:
        return self.problem.rdb

    @property
    def results(self) -> list:
        data = self._get_results_from_db(columns=self.components_names)
        return data.get(self.step, [])

    @property
    def results_sorted(self) -> list:
        return sorted(self.results, key=lambda x: x.key)

    @property
    def locations(self) -> Iterable:
        """Return the locations where the field is defined.

        Yields
        ------
        :class:`compas.geometry.Point`
            The location where the field is defined.
        """
        for r in self.results:
            yield r.location

    def _get_results_from_db(self, members=None, columns=None, filters=None, func=None, **kwargs):
        """Get the results for the given members and steps.

        Parameters
        ----------
        members : list, optional
            List of members to filter results.
        columns : list, optional
            List of columns to retrieve.
        filters : dict, optional
            Dictionary of filters to apply.

        Returns
        -------
        dict
            Dictionary of results.
        """
        if not columns:
            columns = self.components_names

        if not filters:
            filters = {}

        filters["step"] = [self.step.name]

        if members:
            if not isinstance(members, Iterable):
                members = [members]
            # use lists for deterministic parameter binding order
            filters["key"] = [member.key for member in members]
            filters["part"] = [member.part.name for member in members]

        all_columns = ["step", "part", "key"] + columns

        try:
            results_set = self.rdb.get_rows(self.field_name, all_columns, filters, func)
        except Exception as e:
            # Gracefully handle missing/empty databases or tables
            logger.debug("Results fetch failed for table %s with error: %s", self.field_name, e)
            return {}

        results_set = [{k: v for k, v in zip(all_columns, row)} for row in results_set]

        return self.rdb.to_results(results_set, results_func=self.results_func, result_cls=self.result_cls, **kwargs)

    def get_result_at(self, location):
        """Get the result for a given location.

        Parameters
        ----------
        location : object
            The location to retrieve the result for.

        Returns
        -------
        object
            The result at the given location.
        """
        return self._get_results_from_db(members=location, columns=self.components_names)[self.step][0]

    def get_max_result(self, component):
        """Get the result where a component is maximum for a given step.

        Parameters
        ----------
        component : str
            The component to retrieve the maximum result for.

        Returns
        -------
        :class:`compas_fea2.results.Result`
            The appropriate Result object.
        """
        func = ["DESC", component]
        return self._get_results_from_db(columns=self.components_names, func=func)[self.step][0]

    def get_min_result(self, component):
        """Get the result where a component is minimum for a given step.

        Parameters
        ----------
        component : str
            The component to retrieve the minimum result for.

        Returns
        -------
        :class:`compas_fea2.results.Result`
            The appropriate Result object.
        """
        func = ["ASC", component]
        return self._get_results_from_db(columns=self.components_names, func=func)[self.step][0]

    def get_limits_component(self, component):
        """Get the result objects with the min and max value of a given component in a step.

        Parameters
        ----------
        component : int
            The index of the component to retrieve.

        Returns
        -------
        list
            A list containing the result objects with the minimum and maximum value of the given component in the step.
        """
        return [self.get_min_result(component), self.get_max_result(component)]

    def component_scalar(self, component):
        """Return the value of selected component."""
        for result in self.results:
            yield getattr(result, component, None)

    def filter_by_component(self, component, threshold=None):
        """Filter results by a specific component, optionally using a threshold.

        Parameters
        ----------
        componen : str
            The name of the component to filter by (e.g., "Fx_1").
        threshold : float, optional
            A threshold value to filter results. Only results above this value are included.

        Returns
        -------
        dict
            A dictionary of filtered elements and their results.
        """
        if component not in self.components_names:
            raise ValueError(f"Component '{component}' is not valid. Choose from {self.components_names}.")

        for result in self.results:
            component_value = getattr(result, component, None)
            if component_value is not None and (threshold is None or component_value >= threshold):
                yield result


# ------------------------------------------------------------------------------
# Node Field Results
# ------------------------------------------------------------------------------
class NodeFieldResults(FieldResults):
    """Node field results.

    This class handles the node field results from a finite element analysis.

    Parameters
    ----------
    step : :class:`compas_fea2.problem._Step`
        The analysis step where the results are defined.

    Attributes
    ----------
    components_names : list of str
        Names of the node components.
    invariants_names : list of str
        Names of the invariants of the node field.
    results_class : class
        The class used to instantiate the node results.
    results_func : str
        The function used to find nodes by key.
    """

    def __init__(self, *args, **kwargs):
        super(NodeFieldResults, self).__init__(*args, **kwargs)
        self._results_func = "find_node_by_key"
        self._field_name = None
        self._result_cls = None

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
        """Create a NodeFieldResults instance from data."""
        return cls()

    @property
    def components_names(self):
        return ["x", "y", "z", "xx", "yy", "zz"]

    @property
    def field_name(self):
        if not self._field_name:
            raise ValueError("Field name is not set. Please set the field name in the subclass.")
        return self._field_name

    @property
    def results_func(self):
        return self._results_func

    @property
    def vectors(self):
        """Return the vectors where the field is defined.

        Yields
        ------
        :class:`compas.geometry.Vector`
            The vector where the field is defined.
        """
        for r in self.results:
            yield r.vector

    @property
    def vectors_rotation(self):
        """Return the vectors where the field is defined.

        Yields
        ------
        :class:`compas.geometry.Vector`
            The vector where the field is defined.
        """
        for r in self.results:
            yield r.vector_rotation

    def compute_resultant(self, sub_set=None):
        """Compute the translation resultant, moment resultant, and location of the field.

        Parameters
        ----------
        sub_set : list, optional
            List of locations to filter the results. If None, all results are considered.

        Returns
        -------
        tuple
            The translation resultant as :class:`compas.geometry.Vector`,
            moment resultant as :class:`compas.geometry.Vector`,
            and location as a :class:`compas.geometry.Point`.
        """
        from compas.geometry import Point
        from compas.geometry import centroid_points_weighted
        from compas.geometry import cross_vectors
        from compas.geometry import sum_vectors

        results_subset = list(filter(lambda x: x.location in sub_set, self.results)) if sub_set else self.results
        vectors = [r.vector for r in results_subset]
        locations = [r.location.xyz for r in results_subset]
        resultant_location = Point(*centroid_points_weighted(locations, [v.length for v in vectors]))
        resultant_vector = sum_vectors(vectors)
        moment_vector = sum_vectors(cross_vectors(Vector(*loc) - resultant_location, vec) for loc, vec in zip(locations, vectors))

        return Vector(*resultant_vector), Vector(*moment_vector), resultant_location

    def components_vectors(self, components):
        """Return a vector representing the given components."""
        for vector in self.vectors:
            v_copy = vector.copy()
            for c in ["x", "y", "z"]:
                if c not in components:
                    setattr(v_copy, c, 0)
            yield v_copy

    def components_vectors_rotation(self, components):
        """Return a vector representing the given components."""
        for vector in self.vectors_rotation:
            v_copy = vector.copy()
            for c in ["x", "y", "z"]:
                if c not in components:
                    setattr(v_copy, c, 0)
            yield v_copy


class DisplacementFieldResults(NodeFieldResults):
    """Displacement field results.

    This class handles the displacement field results from a finite element analysis.

    Parameters
    ----------
    step : :class:`compas_fea2.problem._Step`
        The analysis step where the results are defined.

    Attributes
    ----------
    components_names : list of str
        Names of the displacement components.
    invariants_names : list of str
        Names of the invariants of the displacement field.
    results_class : class
        The class used to instantiate the displacement results.
    results_func : str
        The function used to find nodes by key.
    """

    def __init__(self, *args, **kwargs):
        super(DisplacementFieldResults, self).__init__(*args, **kwargs)
        self._field_name = "u"
        from compas_fea2.results.results import DisplacementResult

        self._result_cls = DisplacementResult


class AccelerationFieldResults(NodeFieldResults):
    """Acceleration field results.

    This class handles the acceleration field results from a finite element analysis.

    Parameters
    ----------
    step : :class:`compas_fea2.problem._Step`
        The analysis step where the results are defined.

    Attributes
    ----------
    components_names : list of str
        Names of the acceleration components.
    invariants_names : list of str
        Names of the invariants of the acceleration field.
    results_class : class
        The class used to instantiate the acceleration results.
    results_func : str
        The function used to find nodes by key.
    """

    def __init__(self, *args, **kwargs):
        super(AccelerationFieldResults, self).__init__(*args, **kwargs)
        self._field_name = "a"
        from compas_fea2.results.results import AccelerationResult

        self._result_cls = AccelerationResult


class VelocityFieldResults(NodeFieldResults):
    """Velocity field results.

    This class handles the velocity field results from a finite element analysis.

    Parameters
    ----------
    step : :class:`compas_fea2.problem._Step`
        The analysis step where the results are defined.

    Attributes
    ----------
    components_names : list of str
        Names of the velocity components.
    invariants_names : list of str
        Names of the invariants of the velocity field.
    results_class : class
        The class used to instantiate the velocity results.
    results_func : str
        The function used to find nodes by key.
    """

    def __init__(self, *args, **kwargs):
        super(VelocityFieldResults, self).__init__(*args, **kwargs)
        self._field_name = "v"
        from compas_fea2.results.results import VelocityResult

        self._result_cls = VelocityResult


class ReactionFieldResults(NodeFieldResults):
    """Reaction field results.

    This class handles the reaction field results from a finite element analysis.

    Parameters
    ----------
    step : :class:`compas_fea2.problem._Step`
        The analysis step where the results are defined.

    Attributes
    ----------
    components_names : list of str
        Names of the reaction components.
    invariants_names : list of str
        Names of the invariants of the reaction field.
    results_class : class
        The class used to instantiate the reaction results.
    results_func : str
        The function used to find nodes by key.
    """

    def __init__(self, *args, **kwargs):
        super(ReactionFieldResults, self).__init__(*args, **kwargs)
        self._field_name = "rf"
        from compas_fea2.results.results import ReactionResult

        self._result_cls = ReactionResult


class ContactForcesFieldResults(NodeFieldResults):
    """Reaction field results.

    This class handles the reaction field results from a finite element analysis.

    Parameters
    ----------
    step : :class:`compas_fea2.problem._Step`
        The analysis step where the results are defined.

    Attributes
    ----------
    components_names : list of str
        Names of the reaction components.
    invariants_names : list of str
        Names of the invariants of the reaction field.
    results_class : class
        The class used to instantiate the reaction results.
    results_func : str
        The function used to find nodes by key.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._field_name = "c"
        from compas_fea2.results.results import ContactForcesResult

        self._result_cls = ContactForcesResult


class TemperatureFieldResults(NodeFieldResults):
    """Reaction field results.

    This class handles the reaction field results from a finite element analysis.

    Parameters
    ----------
    step : :class:`compas_fea2.problem._Step`
        The analysis step where the results are defined.

    Attributes
    ----------
    components_names : list of str
        Names of the reaction components.
    invariants_names : list of str
        Names of the invariants of the reaction field.
    results_class : class
        The class used to instantiate the reaction results.
    results_func : str
        The function used to find nodes by key.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._field_name = "t"
        from compas_fea2.results.results import TemperatureResult

        self._result_cls = TemperatureResult

    @property
    def components_names(self):
        return ["temp"]


# ------------------------------------------------------------------------------
# Section Forces Field Results
# ------------------------------------------------------------------------------
class ElementFieldResults(FieldResults):
    """Element field results.

    This class handles the element field results from a finite element analysis.
    """

    def __init__(self, *args, **kwargs):
        super(ElementFieldResults, self).__init__(*args, **kwargs)
        self._results_func = "find_element_by_key"


class SectionForcesFieldResults(ElementFieldResults):
    """Section forces field results.

    This class handles the section forces field results from a finite element analysis.

    Parameters
    ----------
    step : :class:`compas_fea2.problem._Step`
        The analysis step where the results are defined.

    Attributes
    ----------
    components_names : list of str
        Names of the section forces components.
    invariants_names : list of str
        Names of the invariants of the section forces field.
    results_class : class
        The class used to instantiate the section forces results.
    results_func : str
        The function used to find elements by key.
    """

    def __init__(self, *args, **kwargs):
        super(SectionForcesFieldResults, self).__init__(*args, **kwargs)
        self._results_func = "find_element_by_key"
        self._field_name = "sf"
        from compas_fea2.results.results import SectionForcesResult

        self._result_cls = SectionForcesResult

    @property
    def field_name(self):
        return self._field_name

    @property
    def results_func(self):
        return self._results_func

    @property
    def components_names(self):
        # Typical beam section result components: axial (n1), shear (v2, v3), torsion (t), bending (m2, m3)
        return ["n1", "v2", "v3", "t", "m2", "m3"]

    def get_element_forces(self, element):
        """Get the section forces for a given element.

        Parameters
        ----------
        element : object
            The element to retrieve the section forces for.

        Returns
        -------
        object
            The section forces result for the specified element.
        """
        return self.get_result_at(element)

    def get_elements_forces(self, elements):
        """Get the section forces for a list of elements.

        Parameters
        ----------
        elements : list
            The elements to retrieve the section forces for.

        Yields
        ------
        object
            The section forces result for each element.
        """
        for e in elements:
            yield self.get_element_forces(e)

    def export_to_dict(self):
        """Export section forces for the current step to a list of dictionaries.

        Returns
        -------
        list[dict]
            Each dict includes keys: step, part, key, and all component names.
        """
        cols = ["step", "part", "key"] + self.components_names
        try:
            rows = self.rdb.get_rows(self.field_name, cols, {"step": [self.step.name]}, None)
        except Exception as e:
            logger.debug("Export to dict failed for table %s: %s", self.field_name, e)
            return []
        return [dict(zip(cols, row)) for row in rows]

    def export_to_csv(self, file_path):
        """Export section forces for the current step to CSV.

        Parameters
        ----------
        file_path : str | Path
            Path to the CSV file to write.
        """
        data = self.export_to_dict()
        if not data:
            logger.warning("No section forces data available to export for step '%s'", self.step.name)
            return
        fieldnames = list(data[0].keys())
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)


# ------------------------------------------------------------------------------
# Stress Field Results
# ------------------------------------------------------------------------------


class StressFieldResults(ElementFieldResults):
    """
    Generalized stress field results for both 2D and 3D elements.
    Stress results are computed in the global coordinate system.
    Operations on stress results are performed on the field level to improve efficiency.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._results_func = "find_element_by_key"
        self._field_name = "s"
        from compas_fea2.results.results import StressResult

        self._result_cls = StressResult

    @property
    def grouped_results(self):
        """Groups elements by their dimensionality (2D or 3D) correctly."""
        sorted_results = sorted(self.results, key=lambda r: r.element.ndim)  # Ensure sorting before grouping
        return {k: list(v) for k, v in groupby(sorted_results, key=lambda r: r.element.ndim)}

    @property
    def field_name(self):
        return self._field_name

    @property
    def results_func(self):
        return self._results_func

    @property
    def components_names(self):
        return ["s11", "s22", "s33", "s12", "s23", "s13"]

    @property
    def invariants_names(self):
        return ["von_mises_stress", "principal_stress_min", "principal_stress_mid", "principal_stress_max"]

    def get_component_value(self, component, **kwargs):
        """Return the value of the selected component."""
        if component not in self.components_names:
            raise ValueError(f"Component '{component}' is not valid. Choose from {self.components_names}.")
        for result in self.results:
            yield getattr(result, component, None)

    def get_invariant_value(self, invariant, **kwargs):
        """Return the value of the selected invariant."""
        if invariant not in self.invariants_names:
            raise ValueError(f"Invariant '{invariant}' is not valid. Choose from {self.invariants_names}.")
        for result in self.results:
            yield getattr(result, invariant, None)

    def global_stresses(self, plane="mid"):
        """Compute stress tensors in the global coordinate system.
        Note: Current implementation assumes stresses are already global.
        Returns a list of dicts keyed by component names per element.
        """
        data = []
        for r in self.results:
            data.append(
                {
                    "element": r.element,
                    **{c: getattr(r, c, None) for c in self.components_names},
                }
            )
        return data

    def average_stress_at_nodes(self, component="von_mises_stress"):
        """Average selected stress component at nodes.
        TODO: Implement nodal averaging using element-to-node mapping.
        """
        raise NotImplementedError("average_stress_at_nodes is not implemented yet.")
