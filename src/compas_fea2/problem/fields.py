from typing import TYPE_CHECKING
from typing import Iterable
from typing import Optional
from typing import Any
from typing import List

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.model.groups import NodesGroup
from compas_fea2.problem.loads import ScalarLoad
from compas_fea2.problem.loads import VectorLoad

if TYPE_CHECKING:
    from compas.geometry import Point

    from compas_fea2.model import Model
    from compas_fea2.model.groups import FacesGroup
    from compas_fea2.model.nodes import Node
    from compas_fea2.problem import Problem
    from compas_fea2.problem.displacements import GeneralDisplacement
    from compas_fea2.problem.loads import _Load
    from compas_fea2.problem.steps import _Step

# TODO implement __*__ magic method for combination


# --- Base Field classes----------------------------------------------
class _BaseLoadField(FEAData):
    """Abstract base class for load / boundary condition fields.

    Provides common storage and (de)serialisation logic for all concrete field
    types. Subclasses normalise *loads* into their distribution containers.

    Parameters
    ----------
    load_case : str, optional
        Identifier of the load case this field belongs to.
    **kwargs : dict, optional
        Additional keyword arguments forwarded to :class:`FEAData` (e.g. name).

    Attributes
    ----------
    _load_case : str | None
        Associated load case.
    _distribution : Any
        The normalised distribution object (nodes, elements, faces, ...).
    _loads : list[Any]
        List of load objects / numerical values aligned with the distribution.
    """

    def __init__(self, *, load_case: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self._load_case = load_case
        self._registration: "_Step | None" = None
        self._distribution = None
        self._loads: list[Any] = []

    # Removed value_kind & domain (now inferred downstream if needed)

    @property
    def load_case(self):
        """str | None: Load case identifier to which this field belongs."""
        return self._load_case

    @load_case.setter
    def load_case(self, v):
        if v is not None and not isinstance(v, str):
            raise TypeError("load_case must be str or None")
        self._load_case = v

    @property
    def loads(self):
        """list: Sequence of loads / numeric values mapped one‑to‑one to the distribution."""
        return self._loads

    @property
    def distribution(self):
        """Any: Normalised distribution object (e.g. NodesGroup or list of elements)."""
        return self._distribution

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "dtype": self.__class__.__name__,
                "load_case": self._load_case,
                "distribution": getattr(self._distribution, "__data__", None),
                "loads": [L.__data__ if hasattr(L, "__data__") else L for L in self._loads],
            }
        )
        return data


# def _rebuild_loads(loads_data, registry):  # helper
#     rebuilt = []
#     for Ld in loads_data:
#         if isinstance(Ld, dict) and "dtype" in Ld:
#             cls_name = Ld.get("dtype")
#             if isinstance(cls_name, str):
#                 load_cls = globals().get(cls_name)
#                 if load_cls and hasattr(load_cls, "__from_data__"):
#                     try:
#                         rebuilt.append(load_cls.__from_data__(Ld, registry=registry))  # type: ignore
#                         continue
#                     except Exception:
#                         pass
#         rebuilt.append(Ld)
#     return rebuilt


class _NodesLoadField(_BaseLoadField):
    """Field with a node-based distribution.

    Parameters
    ----------
    loads : Iterable | Any
        Iterable of load objects / numeric values or a single value to broadcast.
    distribution : Node | Iterable[Node] | NodesGroup
        Node(s) over which the loads are distributed (auto-wrapped in NodesGroup).
    load_case : str, optional
        Load case identifier.
    **kwargs : dict
        Extra keyword arguments forwarded to :class:`FEAData`.

    Raises
    ------
    ValueError
        If the number of provided loads is not 1 and does not match the number
        of nodes in the distribution.
    """

    def __init__(self, loads, nodes: "Node | Iterable[Node] | NodesGroup", *, load_case: str | None = None, **kwargs):
        super().__init__(load_case=load_case, **kwargs)
        if not isinstance(nodes, NodesGroup):
            nodes = NodesGroup(nodes)
        self._distribution = nodes

        if isinstance(loads, Iterable):
            loads_list = list(loads)
        else:
            loads_list = [loads] * len(nodes)
        if len(loads_list) != len(nodes):
            raise ValueError("Loads length must be 1 or match number of nodes.")
        self._loads = loads_list

    @property
    def nodes(self):
        """NodesGroup: The nodes over which the loads are distributed."""
        return self._distribution


class _ElementsLoadField(_BaseLoadField):
    """Field with an element-based distribution.

    Parameters
    ----------
    loads : Iterable | Any
        Iterable of load objects / numeric values or a single value to broadcast.
    elements : Iterable | Any
        Elements over which the loads are applied.
    load_case : str, optional
        Load case identifier.
    **kwargs : dict
        Extra keyword arguments forwarded to :class:`FEAData`.

    Raises
    ------
    ValueError
        If the distribution is empty or if the number of provided loads is not
        1 and does not match the number of elements.
    """

    def __init__(self, loads, elements, *, load_case: str | None = None, **kwargs):
        super().__init__(load_case=load_case, **kwargs)
        if not isinstance(elements, NodesGroup):
            distribution = NodesGroup(elements)
        self._distribution = distribution

        if isinstance(loads, Iterable):
            loads_list = list(loads)
        else:
            loads_list = [loads] * len(distribution)
        if len(loads_list) != len(distribution):
            raise ValueError("Loads length must be 1 or match number of nodes.")
        self._loads = loads_list

    @property
    def elements(self):
        """NodesGroup: The elements over which the loads are distributed."""
        return self._distribution

    # @from_data
    # @classmethod
    # def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
    #     obj = super(_ElementsLoadField, cls).__from_data__(data, registry=registry, duplicate=duplicate)  # type: ignore
    #     if registry:
    #         elements = [registry.get(uid) for uid in data.get("element_uids", []) if registry.get(uid)]  # type: ignore
    #         obj._distribution = elements
    #     obj._loads = _rebuild_loads(data.get("loads", []), registry)
    #     return obj


# --- Node Scalar / Vector -----------------------------------------------------
class _NodeScalarField(_NodesLoadField):
    """Scalar load field over nodes."""

    def __init__(self, scalars, nodes, load_case: str | None = None, *, wrap: bool = False, amplitude=None, **kwargs):
        if not isinstance(scalars, Iterable):
            scalars = [scalars]
        scalars_list = list(scalars)
        if wrap:
            wrapped = []
            for s in scalars_list:
                if isinstance(s, ScalarLoad):
                    wrapped.append(s)
                else:
                    wrapped.append(ScalarLoad(scalar_load=s, amplitude=amplitude))
            scalars_list = wrapped
        super().__init__(loads=scalars_list, nodes=nodes, load_case=load_case, **kwargs)

    # @from_data
    # @classmethod
    # def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
    #     obj = super(_NodeScalarField, cls).__from_data__(data, registry=registry, duplicate=duplicate)  # type: ignore
    #     return obj


class _NodeVectorField(_NodesLoadField):
    """Vector load field over nodes."""

    def __init__(self, vectors, distribution, load_case: str | None = None, **kwargs):
        if not isinstance(vectors, Iterable):
            vectors = [vectors]
        super().__init__(loads=list(vectors), nodes=distribution, load_case=load_case, **kwargs)

    # @from_data
    # @classmethod
    # def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
    #     obj = super(_NodeVectorField, cls).__from_data__(data, registry=registry, duplicate=duplicate)  # type: ignore
    #     return obj


# --- Element Scalar / Vector --------------------------------------------------
class _ElementScalarField(_ElementsLoadField):
    """Scalar load field over elements."""

    def __init__(self, scalars, elements, load_case: str | None = None, **kwargs):
        if not isinstance(scalars, Iterable):
            scalars = [scalars]
        super().__init__(loads=list(scalars), elements=elements, load_case=load_case, **kwargs)

    # @from_data
    # @classmethod
    # def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
    #     obj = super(_ElementScalarField, cls).__from_data__(data, registry=registry, duplicate=duplicate)  # type: ignore
    #     return obj


class _ElementVectorField(_ElementsLoadField):
    """Vector load field over elements."""

    def __init__(self, vectors, elements, load_case: str | None = None, **kwargs):
        if not isinstance(vectors, Iterable) or isinstance(vectors, (str, bytes)):
            vectors = [vectors]
        super().__init__(loads=list(vectors), elements=elements, load_case=load_case, **kwargs)

    # @from_data
    # @classmethod
    # def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
    #     obj = super(_ElementVectorField, cls).__from_data__(data, registry=registry, duplicate=duplicate)  # type: ignore
    #     return obj


# --- Users Fields -------------------------------------------------
class DisplacementField(_NodeVectorField):
    """Distribution of displacement boundary conditions over nodes."""

    def __init__(self, displacements: Iterable["GeneralDisplacement"], nodes: Iterable["Node"], load_case=None, **kwargs):
        super().__init__(vectors=displacements, distribution=nodes, load_case=load_case, **kwargs)

    # @from_data
    # @classmethod
    # def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
    #     obj = super(DisplacementField, cls).__from_data__(data, registry=registry, duplicate=duplicate)  # type: ignore
    #     return obj

    @property
    def displacements(self):
        return self._loads

    @property
    def node_displacement(self):
        return zip(self._distribution, self._loads)


class ForceField(_NodeVectorField):
    """Distribution of concentrated (nodal) vector loads."""

    def __init__(self, loads: Iterable["VectorLoad"], nodes: Iterable["Node"], load_case: str | None = None, **kwargs):
        super().__init__(vectors=loads, distribution=nodes, load_case=load_case, **kwargs)

    # @from_data
    # @classmethod
    # def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
    #     obj = super(ForceField, cls).__from_data__(data, registry=registry, duplicate=duplicate)  # type: ignore
    #     return obj

    @property
    def node_load(self):
        return zip(self._distribution, self._loads)

    @classmethod
    def from_points_field(cls, loads: Iterable["VectorLoad"], points: Iterable["Point"], model, load_case: str | None = None, **kwargs):
        nodes = []
        for pt in points:
            n = model.find_closest_node_to_point(pt, single=True)
            nodes.append(n)
        return cls(loads=loads, nodes=nodes, load_case=load_case, **kwargs)


class UniformSurfaceLoadField(_NodeVectorField):
    def __init__(self, load: float, surface: "FacesGroup", direction: list[float] | None = None, **kwargs):
        from compas_fea2.problem.loads import VectorLoad

        distribution = surface.nodes
        area = surface.area
        direction = direction or surface.normal
        amplitude = kwargs.pop("amplitude", None)
        share = area / len(distribution) if distribution else 0.0
        components = [i * load * share for i in direction]
        loads = [VectorLoad(*components, amplitude=amplitude) for _ in distribution]
        super().__init__(loads=loads, nodes=distribution, **kwargs)
        self._surface = surface
        self._direction = direction
        self._load_value = load

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "surface": self.surface.__data__,
                "direction": list(self._direction) if self._direction else None,
                "load_value": self._load_value,
            }
        )
        return data

    # @from_data
    # @classmethod
    # def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):

    #     return obj

    @property
    def surface(self):
        return self._surface

    @property
    def direction(self):
        return self._direction

    @property
    def load_value(self):
        return self._load_value


class GravityLoadField(_NodeVectorField):
    """Field distributing self‑weight (gravity) to nodes."""

    def __init__(self, g=9.81, direction=(0, 0, -1), parts=None, nodes=None, load_case=None, **kwargs):
        from compas_fea2.problem.loads import VectorLoad

        self._g = g
        self._direction = direction
        if parts:
            nodes_list = []
            for part in parts:
                nodes_list.extend(part.nodes)
        else:
            if nodes is None:
                raise ValueError("Provide either parts or nodes for GravityLoadField.")
            nodes_list = list(nodes)
        components: List[float] = [g * v for v in direction]
        loads = []
        for n in nodes_list:
            force_components = [n.mass[i] * components[i] for i in range(len(components))]
            loads.append(VectorLoad(*force_components, name="gravity_load", load_case=load_case))
        super().__init__(loads=loads, nodes=nodes_list, load_case=load_case, **kwargs)

    @property
    def __data__(self):
        data = super().__data__
        data.update({"g": self._g, "direction": list(self._direction)})
        return data

    # @from_data
    # @classmethod
    # def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
    #     obj = super(GravityLoadField, cls).__from_data__(data, registry=registry, duplicate=duplicate)  # type: ignore
    #     obj._g = data.get("g", 9.81)
    #     obj._direction = tuple(data.get("direction", (0, 0, -1)))
    #     # Recompute loads if distribution present & nodes available
    #     if obj._distribution and all(hasattr(n, 'mass') for n in obj._distribution):
    #         components = [obj._g * v for v in obj._direction]
    #         new_loads = []
    #         for n in obj._distribution:
    #             try:
    #                 force_components = [n.mass[i] * components[i] for i in range(len(components))]
    #                 new_loads.append(VectorLoad(*force_components, name='gravity_load', load_case=obj._load_case))
    #             except Exception:
    #                 new_loads.append(0.0)
    #         obj._loads = new_loads
    #     return obj


class TemperatureField(_NodeScalarField):
    """Thermal (nodal) temperature field."""

    def __init__(self, temperature: float | Iterable[float], nodes: Iterable["Node"], **kwargs):
        super().__init__(scalars=temperature, nodes=nodes, wrap=False, **kwargs)

    # @from_data
    # @classmethod
    # def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate=True):
    #     obj = super(TemperatureField, cls).__from_data__(data, registry=registry, duplicate=duplicate)  # type: ignore
    #     return obj

    @property
    def temperatures(self):
        return self._loads

    @property
    def node_temperature(self):
        return zip(self._distribution, self._loads)
