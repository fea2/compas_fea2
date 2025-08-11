import importlib
import json
import uuid
from abc import abstractmethod
from copy import deepcopy
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

import compas_fea2

from .utilities._utils import to_dimensionless

if TYPE_CHECKING:
    from pathlib import Path


class DimensionlessMeta(type):
    """Metaclass for converting pint Quantity objects to dimensionless."""

    def __new__(meta: Type[type], name: str, bases: tuple, class_dict: Dict[str, Any]) -> type:
        # Decorate each method
        for attributeName, attribute in class_dict.items():
            if callable(attribute) or isinstance(attribute, (classmethod, staticmethod)):
                # Unwrap classmethod/staticmethod to decorate the underlying function
                if isinstance(attribute, (classmethod, staticmethod)):
                    original_func = attribute.__func__
                    decorated_func = to_dimensionless(original_func)
                    # Re-wrap classmethod/staticmethod
                    attribute = type(attribute)(decorated_func)
                else:
                    attribute = to_dimensionless(attribute)
                class_dict[attributeName] = attribute
        return type.__new__(meta, name, bases, class_dict)


T = TypeVar("T", bound="FEAData")


class FEAData(Data, metaclass=DimensionlessMeta):
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
        imp = compas_fea2._get_backend_implementation(cls)
        if not imp:
            return super(FEAData, cls).__new__(cls)  # type: ignore
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
        self._name: str = name or "".join([c for c in type(self).__name__ if c.isupper()]) + "_" + str(id(self))
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
    def name(self, value: str) -> None:
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

    @abstractmethod
    def jobdata(self, *args: Any, **kwargs: Any) -> Any:
        """Generate the job data for the backend-specific input file."""
        raise NotImplementedError("This function is not available in the selected plugin.")

    @property
    def __data__(self) -> Dict[str, Union[Any, List[Any]]]:
        """Return the minimum data representation of the object."""
        registration = self._registration
        if registration:
            registration_data = [registration.__class__.__name__, registration._uid]
        else:
            registration_data = None
        return {
            "class": self.__class__.__name__,
            "name": self.name,
            "uid": str(self._uid),
            "key": self._key,
            "registration": registration_data
        }

    @classmethod
    def __from_data__(cls: Type[T], data: dict, registry: "Registry") -> T:
        """Construct an object of this type from the provided data.

        Parameters
        ----------
        data : dict
            The data to construct the object from.
        duplicate : bool, optional
            If True, the object will be created as a duplicate with the same UID.

        Returns
        -------
        T
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
        registry = Registry()
        return cls.__from_data__(compas.json_load(filepath), registry)

    # ==========================================================================
    # Copy and Serialization
    # ==========================================================================

    def copy(self, duplicate: bool = False):
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
        if not duplicate:
            data["uid"] = str(uuid.uuid4())  # Generate a new UID
            data["name"] = f"{self.name}_copy"  # Generate a new name
        try:
            obj = cls.__from_data__(data, registry)
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
            If True, format the output with newlines and indentation.
        compact : bool, optional
            If True, format the output without any whitespace.
        minimal : bool, optional
            If True, exclude the GUID from the JSON output.

        """
        json.dump(self.__data__, open(filepath, "w"), indent=4)


class Registry:
    """A centralized registry to track deserialized objects."""

    def __init__(self):
        self._registry = {}

    def get(self, key) -> Any:
        """Retrieve an object from the registry by its key."""
        return self._registry.get(key)

    def add_from_data(self, data, module_name) -> Any:
        """Add an object to the registry from its data representation."""
        uid = data.get("uid")
        if uid in self._registry:
            return self._registry[uid]

        cls = getattr(importlib.import_module(module_name), data["class"])
        if not issubclass(cls, FEAData):
            raise TypeError(f"Class {data['class']} is not a subclass of FEAData.")

        # Create a new object from the data
        obj = cls.__from_data__(data, registry=self)
        self._registry[uid] = obj
        return obj

    def add(self, key, obj):
        """Add an object to the registry."""
        if key in self._registry:
            raise ValueError(f"Key '{key}' already exists in the registry.")

        self._registry[key] = obj
        return obj

    def clear(self):
        """Clear the registry."""
        self._registry.clear()
