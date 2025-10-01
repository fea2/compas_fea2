import importlib
import json
import uuid
import warnings
from copy import deepcopy
from functools import wraps
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

import compas
from compas.data import Data
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Transformation
from compas.geometry import Vector

from compas_fea2.config import settings

from .registration import _IMPLS
from .utilities._devtools import normalize_string

if TYPE_CHECKING:
    from pathlib import Path


T = TypeVar("T", bound="FEAData")


def from_data(method=None, *, duplicate=True, register: bool = True):
    """Decorator to reduce boilerplate in __from_data__ implementations.

    Handles:
    - registry defaulting
    - short-circuit if uid already in registry
    - setting _uid and _name
    - registering the created instance

    Usage:
        @from_data
        def __from_data__(cls, data, registry=None):
            obj = cls(...)
            return obj

    Toggle behaviors with keyword-only args if a class needs a different behavior.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(cls: Type[T], data: dict, registry: Optional["Registry"] = None, duplicate=duplicate) -> T:
            # Ensure registry
            if registry is None:
                registry = Registry()
            # Reuse existing
            uid = data.get("uid")
            if uid:
                existing = registry.get(uid)
                if existing:
                    return existing  # type: ignore[return-value]
            # Build object with class-specific logic
            obj: T = func(cls, data, registry, duplicate)
            if obj is None:
                raise RuntimeError("__from_data__ did not return an object.")
            # Set base props
            if duplicate:
                setattr(obj, "_uid", uuid.UUID(uid) if uid else None)
                setattr(obj, "_name", data.get("name", None))
            else:
                name = data.get("name", None)
                if name:
                    setattr(obj, "_name", name + "_c")
            # Register
            if register and uid:
                registry.add(uid, obj)
            return obj

        # Ensure classmethod behavior
        return classmethod(wrapper)

    if method is None:
        return decorator
    # Tolerate accidental stacking like @from_data over @classmethod/@staticmethod
    if isinstance(method, (classmethod, staticmethod)):
        method = method.__func__
    return decorator(method)


class FEAData(Data):
    """Base class for all FEA model objects.

    This base class inherits the serialisation infrastructure
    from the base class for core COMPAS objects: :class:`compas.base.`.

    It adds the abstract functionality for the representation of FEA objects
    in a model and/or problem summary,
    and for their representation in software-specific calculation files.

    Parameters
    ----------
    name : str, optional
        The name of the object, by default None. If not provided, one is automatically
        generated.

    Attributes
    ----------
    name : str
        The name of the object.
    registration : compas_fea2 object
        The mother object where this object is registered to.

    """

    def __new__(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Try to get the backend plug-in implementation, otherwise use the base
        one.
        """
        imp = _IMPLS.get(cls)
        if not imp:
            return super(FEAData, cls).__new__(cls)
        return super(FEAData, imp).__new__(imp)  # type: ignore

    def __init__(self, name: Optional[str] = None, **kwargs: Any) -> None:
        # The uid of an object can be passed during the de-serialization process.
        if uid := kwargs.pop("uid", None):
            if isinstance(uid, str):
                self._uid = uuid.UUID(uid)
            elif isinstance(uid, uuid.UUID):
                self._uid = uid
            elif not isinstance(uid, uuid.UUID):
                raise TypeError("uid must be a string or a UUID object.")
        else:
            self._uid: uuid.UUID | None = uuid.uuid4()
        super().__init__()
        self._name: str = normalize_string(name or "".join([c for c in type(self).__name__ if c.isupper()]) + str(id(self)))
        self._registration: Any = None
        self._key: Optional[int] = None

    @property
    def uid(self) -> uuid.UUID | None:
        """Get the unique identifier of the object."""
        return self._uid

    @property
    def key(self) -> Optional[Any]:
        return self._key

    @property
    def name(self) -> str:
        return self._name

    @property
    def registration(self) -> Optional[Any]:
        """Get the object where this object is registered to."""
        return self._registration

    @registration.setter
    def registration(self, value: Any) -> None:
        """Set the object where this object is registered to."""
        self._registration = value

    @name.setter
    def name(self, value: str) -> None: # type: ignore
        self._name = value

    def __repr__(self) -> str:
        return "{0}({1})".format(self.__class__.__name__, id(self))

    def __str__(self) -> str:
        title = "compas_fea2 {0} object".format(self.__class__.__name__)
        separator = "-" * (len(title))
        data_extended = []
        for a in list(filter(lambda a: not a.startswith("__") and not a.startswith("_") and a != "jsondefinitions", dir(self))):
            try:
                attr = getattr(self, a)
                if not callable(attr):
                    if not isinstance(attr, Iterable):
                        data_extended.append("{0:<15} : {1}".format(a, attr.__repr__()))
                    else:
                        from collections.abc import Sized

                        if isinstance(attr, Sized):
                            data_extended.append("{0:<15} : {1}".format(a, len(attr)))
                        else:
                            data_extended.append("{0:<15} : (non-sized iterable)".format(a))
            except Exception:
                pass
        return """\n{}\n{}\n{}\n""".format(title, separator, "\n".join(data_extended))

    def __getstate__(self) -> Dict[str, Any]:
        return self.__dict__

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)

    @property
    def jobdata(self) -> Any:
        """Generate the job data for the backend-specific input file."""
        raise NotImplementedError("This function is not available in the selected plugin.")

    # ==========================================================================
    # Copy and Serialization
    # ==========================================================================

    @property
    def __data__(self) -> Dict[str, Union[Any, List[Any]]]:
        """Return the minimum data representation of the object."""
        registration = self._registration
        if registration:
            registration_data = [registration.__class__.__name__, str(registration._uid)]
        else:
            registration_data = None
        base = {
            "class": self.__class__.__name__,
            "name": self._name,
            "uid": str(self._uid),
            "key": self._key,
            "registration": registration_data,
            "module": self.__class__.__module__,
        }
        return base

    @from_data
    def __from_data__(cls: Type[T], data: dict, registry: Optional["Registry"] = None) -> T:  # type: ignore[override]
        """Construct an object of this type from the provided data.

        Parameters
        ----------
        data : dict
            The data to construct the object from.
        duplicate : bool, optional
            If True, the object will be created as a duplicate with the same UID.

        Returns
        -------
        FEAData
            An instance of the class with the provided data.

        Notes
        -----
        This method is used internally to create objects from JSON or other data formats.
        If `duplicate` is True, the UID will be copied from the data, otherwise a new UID will be generated.
        """
        raise NotImplementedError("This function must be implemented in the subclass.")

    @classmethod
    def from_json(cls: Type[T], filepath: "Path | str ") -> T:
        """Construct an object of this type from a JSON file.

        Parameters
        ----------
        filepath : str
            The path to the JSON file.

        Returns
        -------
        :class:`compas.data.Data`
            An instance of this object type if the data contained in the file has the correct schema.

        Raises
        ------
        TypeError
            If the data in the file is not a :class:`compas.data.Data`.

        """
        print(f"Loading {cls.__name__} from {filepath}")
        return cls.__from_data__(compas.json_load(filepath))  # type: ignore[return-value, no-any-return]

    def copy(self, duplicate: bool = False):  # type: ignore
        """
        Make an independent copy of the data object.

        Parameters
        ----------
        duplicate : bool, optional
            If True, the copy will have the same name and UID as the original.
            Defaults to False, which means the copy will have a new name and UID.

        Returns
        -------
        :class:`compas.data.Data`
            An independent copy of this object.

        Notes
        -----
        - If `duplicate` is False, the new object will have a unique UID and a name
          derived from the original name (e.g., "original_copy").
        - The copy is independent of the original object. Changes to one will not affect the other.
        """
        cls = type(self)
        registry = Registry()
        data = deepcopy(self.__data__)
        try:
            obj = cls.__from_data__(data, registry, duplicate=duplicate)  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Failed to copy object: {e}")
        return obj

    def to_json(self, filepath: str, pretty: bool = False, compact: bool = False, minimal: bool = False) -> None:
        """Convert an object to its native data representation and save it to a JSON file.

        Parameters
        ----------
        filepath : str
            The path to the JSON file.
        pretty : bool, optional
            If True, output will be pretty-printed.
        compact : bool, optional
            If True, output will be compact.
        minimal : bool, optional
            If True, output will be minimal.

        """
        print(f"Saving {self.__class__.__name__} to {filepath}")
        indent = 4 if pretty else None
        separators = (",", ":") if compact else None
        data = self.__data__
        if minimal:
            # Optionally remove keys for minimal output
            data = {k: v for k, v in data.items() if v is not None}
        with open(filepath, "w") as f:
            json.dump(data, f, indent=indent, separators=separators)


class Registry:
    """A centralized registry to track deserialized objects."""

    def __init__(self):
        self._registry = {}

    def __contains__(self, key) -> bool:
        return key in self._registry

    def get(self, key) -> Any:
        """Retrieve an object from the registry by its key."""
        return self._registry.get(key)

    def add_from_data(self, data, module_name: Optional[str] = None, duplicate=True) -> Any:
        """Instantiate object described by data.

        If module_name is None, the function will look for 'module' and 'class'
        keys inside data (written by FEAData.__data__).
        """
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")

        cls_name = data.get("class")
        mod_name = module_name or data.get("module")
        if not mod_name or not cls_name:
            raise ValueError("module_name or data['module'] and data['class'] must be provided")

        module = importlib.import_module(mod_name)
        cls = getattr(module, cls_name)

        if hasattr(cls, "__from_data__"):
            return cls.__from_data__(data, registry=self, duplicate=duplicate)
        # fallback: try to instantiate directly
        return cls(**data)

    def add(self, key, obj):
        """Add an object to the registry."""
        if key in self._registry:
            raise ValueError(f"Key '{key}' already exists in the registry.")

        self._registry[key] = obj
        return obj

    def clear(self):
        """Clear the registry."""
        self._registry.clear()


### -------------------------------------------------------------------
# Mixins
### -------------------------------------------------------------------


class Frameable:
    """Opt-in mixin giving an object an optional local reference frame.

    If no local frame is set, GLOBAL_FRAME is used transparently.

    Provides helpers to convert points/vectors between global and local,
    plus geometric utilities (axis alignment and direction cosines).
    """

    __slots__ = ("_frame",)

    def __init__(self, frame: Frame | None = None):
        self._frame: Frame | None = frame

    @property
    def frame(self) -> Frame:
        """Get the local frame of the object."""
        return self._frame or settings.GLOBAL_FRAME

    @frame.setter
    def frame(self, value: Frame | None):
        self._frame = value

    @property
    def has_local_frame(self) -> bool:
        """Check if the object has a local frame set."""
        return self._frame is not None

    def clear_frame(self):
        """Clear the local frame, reverting to GLOBAL_FRAME."""
        self._frame = None

    # --- geometric helpers -------------------------------------------------
    def is_axis_aligned(self, tol: float = 1e-9) -> bool:
        """Return True if local frame coincides with GLOBAL frame within tolerance."""
        if not self.has_local_frame:
            return True
        from compas.geometry import Transformation  # local import

        T = Transformation.from_frame_to_frame(self.frame, settings.GLOBAL_FRAME)
        # Extract rotation part and compare to identity.
        for i in range(3):
            for j in range(3):
                target = 1.0 if i == j else 0.0
                if abs(T.matrix[i][j] - target) > tol:
                    return False
        return True

    def direction_cosines(self) -> tuple[Vector, Vector, Vector]:
        """Return local axes expressed as global vectors (x, y, z)."""
        return self.frame.xaxis, self.frame.yaxis, self.frame.zaxis

    # --- transformations ----------------------------------------------------
    def _T_local_to_global(self) -> Transformation:
        """Get the transformation from local frame to global frame."""

        return Transformation.from_frame_to_frame(self.frame, settings.GLOBAL_FRAME)

    def _T_global_to_local(self) -> Transformation:
        """Get the transformation from global frame to local frame."""

        return Transformation.from_frame_to_frame(settings.GLOBAL_FRAME, self.frame)

    def to_local_point(self, pt: Point) -> Point:
        """Convert a global point to the local frame."""
        return pt.transformed(self._T_global_to_local())

    def to_global_point(self, pt: Point) -> Point:
        """Convert a local point to the global frame."""
        return pt.transformed(self._T_local_to_global())

    def to_local_vector(self, vec: Vector) -> Vector:
        """Convert a global vector to the local frame."""
        return vec.transformed(self._T_global_to_local())

    def to_global_vector(self, vec: Vector) -> Vector:
        """Convert a local vector to the global frame."""
        return vec.transformed(self._T_local_to_global())

    def transform_to(self, other: Frame) -> Transformation:
        """Get the transformation from this object's local frame to another frame."""
        return Transformation.from_frame_to_frame(self.frame, other)

    # --- serialization helper (optional usage) ------------------------------
    def _frame_data(self):
        """Return the frame data for serialization."""
        return self._frame.__data__ if self._frame else None
