from typing import TYPE_CHECKING
from typing import Iterable
from typing import Optional
from typing import Any
from typing import List
from numbers import Number

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
    from compas_fea2.model.elements import _Element
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
    combination_rank : int, optional
        Rank of this field in a combination. 1=primary (leading), 2=secondary (accompanying),
        3=tertiary. Defaults to 1.
    **kwargs : dict, optional
        Additional keyword arguments forwarded to :class:`FEAData` (e.g. name).
    """
    def __init__(self, *, loads, distribution, load_case: str | None = None, combination_rank: int = 1, **kwargs):
        super().__init__(**kwargs)
        self._loads = loads if isinstance(loads, list) else [loads]
        self._distribution = distribution
        self._load_case = load_case
        self._registration: "_Step | None" = None
        self._loads: list[Any] = []
        self.combination_rank = combination_rank  # validates via setter

    # Removed value_kind & domain (now inferred downstream if needed)

    @property
    def load_case(self) -> str | None:
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
                "combination_rank": self._combination_rank,
                "distribution": getattr(self._distribution, "__data__", None),
                "loads": [L.__data__ if hasattr(L, "__data__") else L for L in self._loads],
            }
        )
        return data

    @property
    def combination_rank(self) -> int:
        """int: Rank in combinations (1=primary, 2=secondary, 3=tertiary)."""
        return self._combination_rank

    @combination_rank.setter
    def combination_rank(self, v: int) -> None:
        if not isinstance(v, int) or v not in (1, 2, 3):
            raise TypeError("combination_rank must be an int in {1, 2, 3}")
        self._combination_rank = v

    # Helper to combine two load-like values into a new value (no in-place mutation)
    @staticmethod
    def _combine_values(a: Any, b: Any) -> Any:
        if a is None:
            return b
        if b is None:
            return a

        # Numbers
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return float(a) + float(b)

        # ScalarLoad with number or ScalarLoad
        if isinstance(a, ScalarLoad) and isinstance(b, (int, float)):
            return ScalarLoad(a.scalar_load + float(b), amplitude=a.amplitude)
        if isinstance(b, ScalarLoad) and isinstance(a, (int, float)):
            return ScalarLoad(b.scalar_load + float(a), amplitude=b.amplitude)
        if isinstance(a, ScalarLoad) and isinstance(b, ScalarLoad):
            amp = a.amplitude if a.amplitude == b.amplitude else (a.amplitude or b.amplitude)
            return ScalarLoad(a.scalar_load + b.scalar_load, amplitude=amp)

        # VectorLoad: leverage in-place __add__ on a clone
        if isinstance(a, VectorLoad) and isinstance(b, VectorLoad):
            # Frames must be compatible
            a_frame = a._frame if getattr(a, "has_local_frame", False) and a.has_local_frame else None
            b_frame = b._frame if getattr(b, "has_local_frame", False) and b.has_local_frame else None
            if (a_frame is not None) and (b_frame is not None) and (a_frame != b_frame):
                raise ValueError("Cannot combine VectorLoads with different local frames.")
            # Clone 'a' with desired amplitude, then use __add__
            clone = _BaseLoadField._clone_vectorload(a, amplitude_override=a.amplitude or b.amplitude)
            clone += b
            return clone

        # GeneralDisplacement (or similar with __add__ semantics creating a new instance)
        try:
            res = a + b  # type: ignore
        except Exception:
            raise TypeError(f"Unsupported combination for values {type(a)} and {type(b)}")
        return res

    # Helper to scale a single load-like value by a numeric factor, returning a new value
    @staticmethod
    def _scale_value(v: Any, factor: float | int) -> Any:
        if v is None:
            return None
        f = float(factor)
        # Numbers
        if isinstance(v, (int, float)):
            return float(v) * f
        # ScalarLoad
        if isinstance(v, ScalarLoad):
            return ScalarLoad(v.scalar_load * f, amplitude=v.amplitude)
        # VectorLoad: leverage in-place __mul__ on a clone
        if isinstance(v, VectorLoad):
            clone = _BaseLoadField._clone_vectorload(v)
            clone *= f
            return clone
        # Fallback: try object's own __mul__
        try:
            return v * f  # type: ignore
        except Exception:
            raise TypeError(f"Unsupported scaling for value of type {type(v)}")

    @staticmethod
    def _clone_vectorload(src: VectorLoad, *, amplitude_override=None) -> VectorLoad:
        """Create a non-mutated copy of a VectorLoad, preserving local components/frame."""
        frame = src._frame if getattr(src, "has_local_frame", False) and src.has_local_frame else None
        return VectorLoad(
            x=src.x, y=src.y, z=src.z,
            xx=src.xx, yy=src.yy, zz=src.zz,
            frame=frame,
            amplitude=src.amplitude if amplitude_override is None else amplitude_override,
        )

    def find_load_at_location(self, location: "_Element | Node") -> Optional[Any]:
        for i, n in enumerate(self._distribution):
            if n == location:
                return self._loads[i]

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
    combination_rank : int, optional
        1=primary, 2=secondary, 3=tertiary. Defaults to 1.
    **kwargs : dict
        Extra keyword arguments forwarded to :class:`FEAData`.

    Raises
    ------
    ValueError
        If the number of provided loads is not 1 and does not match the number
        of nodes in the distribution.
    """

    def __init__(self, loads, nodes: "Node | Iterable[Node] | NodesGroup", *, load_case: str | None = None, **kwargs):
        super().__init__(loads=loads, distribution=nodes, load_case=load_case, **kwargs)
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

    def __add__(self, other: "_NodesLoadField") -> "_NodesLoadField":
        if type(self) is not type(other):
            return NotImplemented
        # Build mapping node -> load
        self_map = {n: L for n, L in zip(self._distribution, self._loads)}
        other_map = {n: L for n, L in zip(other._distribution, other._loads)}
        seen = set()
        combined_nodes = []
        # preserve order: self nodes first, then other's new ones
        for n in self._distribution:
            combined_nodes.append(n)
            seen.add(n)
        for n in other._distribution:
            if n not in seen:
                combined_nodes.append(n)
                seen.add(n)
        # combine loads per node
        combined_loads: list[Any] = []
        for n in combined_nodes:
            a = self_map.get(n)
            b = other_map.get(n)
            if a is None:
                combined_loads.append(b)
            elif b is None:
                combined_loads.append(a)
            else:
                combined_loads.append(self._combine_values(a, b))
        # resolve load_case: keep if identical, else None
        lc = self._load_case if self._load_case == other._load_case else None
        # preserve rank if equal, else default to 1 (primary)
        cr_other = getattr(other, "_combination_rank", 1)
        cr = self._combination_rank if self._combination_rank == cr_other else 1
        # instantiate same subclass with positional args (loads, nodes)
        return self.__class__(combined_loads, combined_nodes, load_case=lc, combination_rank=cr)

    def __mul__(self, factor: float | int):
        if not isinstance(factor, (int, float)):
            return NotImplemented
        scaled = [self._scale_value(L, factor) for L in self._loads]
        return self.__class__(scaled, self._distribution, load_case=self._load_case, combination_rank=self._combination_rank)

    def __rmul__(self, factor: float | int):
        return self.__mul__(factor)

    def __sub__(self, other: "_NodesLoadField") -> "_NodesLoadField":
        if type(self) is not type(other):
            return NotImplemented
        return self.__add__(other * -1)

    def __rsub__(self, other: "_NodesLoadField") -> "_NodesLoadField":
        if type(self) is not type(other):
            return NotImplemented
        return other.__add__(self * -1)


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
    combination_rank : int, optional
        1=primary, 2=secondary, 3=tertiary. Defaults to 1.
    **kwargs : dict
        Extra keyword arguments forwarded to :class:`FEAData`.

    Raises
    ------
    ValueError
        If the distribution is empty or if the number of provided loads is not
        1 and does not match the number of elements.
    """

    def __init__(self, loads, elements, *, load_case: str | None = None, **kwargs):
        super().__init__(loads=loads, distribution=elements,load_case=load_case, **kwargs)
        if isinstance(elements, NodesGroup):
            distribution = elements
        else:
            distribution = NodesGroup(elements)
        self._distribution = distribution

        if isinstance(loads, Iterable):
            loads_list = list(loads)
        else:
            loads_list = [loads] * len(distribution)
        if len(loads_list) != len(distribution):
            raise ValueError("Loads length must be 1 or match number of elements.")
        self._loads = loads_list

    @property
    def elements(self):
        """NodesGroup: The elements over which the loads are distributed."""
        return self._distribution

    def __add__(self, other: "_ElementsLoadField") -> "_ElementsLoadField":
        if type(self) is not type(other):
            return NotImplemented
        self_map = {e: L for e, L in zip(self._distribution, self._loads)}
        other_map = {e: L for e, L in zip(other._distribution, other._loads)}
        seen = set()
        combined_elems = []
        for e in self._distribution:
            combined_elems.append(e)
            seen.add(e)
        for e in other._distribution:
            if e not in seen:
                combined_elems.append(e)
                seen.add(e)
        combined_loads: list[Any] = []
        for e in combined_elems:
            a = self_map.get(e)
            b = other_map.get(e)
            if a is None:
                combined_loads.append(b)
            elif b is None:
                combined_loads.append(a)
            else:
                combined_loads.append(self._combine_values(a, b))
        lc = self._load_case if self._load_case == other._load_case else None
        cr_other = getattr(other, "_combination_rank", 1)
        cr = self._combination_rank if self._combination_rank == cr_other else 1
        return self.__class__(combined_loads, combined_elems, load_case=lc, combination_rank=cr)

    def __mul__(self, factor: float | int):
        if not isinstance(factor, (int, float)):
            return NotImplemented
        scaled = [self._scale_value(L, factor) for L in self._loads]
        return self.__class__(scaled, self._distribution, load_case=self._load_case, combination_rank=self._combination_rank)

    def __rmul__(self, factor: float | int):
        return self.__mul__(factor)

    def __sub__(self, other: "_ElementsLoadField") -> "_ElementsLoadField":
        if type(self) is not type(other):
            return NotImplemented
        return self.__add__(other * -1)

    def __rsub__(self, other: "_ElementsLoadField") -> "_ElementsLoadField":
        if type(self) is not type(other):
            return NotImplemented
        return other.__add__(self * -1)

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
    """Distribution of displacement boundary conditions over nodes.

    Parameters
    ----------
    displacements : Iterable[GeneralDisplacement]
    nodes : Iterable[Node]
    load_case : str | None, optional
    combination_rank : int, optional
        1=primary, 2=secondary, 3=tertiary. Defaults to 1.
    """
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
    """Distribution of concentrated (nodal) vector loads.

    Parameters
    ----------
    loads : Iterable[VectorLoad]
    nodes : Iterable[Node]
    load_case : str | None, optional
    combination_rank : int, optional
        1=primary, 2=secondary, 3=tertiary. Defaults to 1.
    """
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
    def from_points_and_loads(cls, loads: Iterable["VectorLoad"], points: Iterable["Point"], model, load_case: str | None = None, **kwargs):
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
    """Field distributing self‑weight (gravity) to nodes.

    Parameters
    ----------
    g : float
    direction : tuple[float, float, float]
    parts : Iterable[Any] | None
    nodes : Iterable[Node] | None
    load_case : str | None
    combination_rank : int, optional
        Typically 1 for permanent, unless you want to force a different rank.
    """
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
    """Thermal (nodal) temperature field.

    Parameters
    ----------
    temperature : float | Iterable[float]
    nodes : Iterable[Node]
    load_case : str | None
    combination_rank : int, optional
        1=primary, 2=secondary, 3=tertiary. Defaults to 1.
    """
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
