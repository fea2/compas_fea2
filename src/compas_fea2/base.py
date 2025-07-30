import importlib
import json
import uuid
from abc import abstractmethod
from copy import deepcopy
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union
from typing import TYPE_CHECKING

import h5py
import numpy as np
from compas.data import Data

import compas_fea2

from .utilities._utils import to_dimensionless

# Type variable for FEAData subclasses
T = TypeVar('T', bound='FEAData')


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

    def __new__(cls, *args: Any, **kwargs: Any) -> 'FEAData':
        """Try to get the backend plug-in implementation, otherwise use the base
        one.
        """
        imp = compas_fea2._get_backend_implementation(cls)
        if not imp:
            return super(FEAData, cls).__new__(cls)
        return super(FEAData, imp).__new__(imp)

    def __init__(self, name: Optional[str] = None, **kwargs: Any) -> None:
        self.uid: uuid.UUID = uuid.uuid4()
        super().__init__()
        self._name: str = name or "".join([c for c in type(self).__name__ if c.isupper()]) + "_" + str(id(self))
        self._registration: Optional[Any] = None
        self._key: Optional[Any] = None

    @property
    def key(self) -> Optional[Any]:
        return self._key

    @property
    def name(self) -> str:
        return self._name

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
                        data_extended.append("{0:<15} : {1}".format(a, len(attr)))
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

    @classmethod
    def from_name(cls: Type[T], name: str, **kwargs: Any) -> T:
        """Create an instance of a class of the registered plugin from its name.

        Parameters
        ----------
        name : str
            The name of the class (without the `_` prefix)

        Returns
        -------
        obj
            The wanted object

        Notes
        -----
        By convention, only hidden class can be called by this method.

        """
        obj = cls(**kwargs)
        module_info = obj.__module__.split(".")
        obj = getattr(importlib.import_module(".".join([*module_info[:-1]])), "_" + name)
        return obj(**kwargs)

    # ==========================================================================
    # Copy and Serialization
    # ==========================================================================

    def copy(self, cls: Optional[Type[T]] = None, copy_guid: bool = False, copy_name: bool = False) -> T:
        """Make an independent copy of the data object.

        Parameters
        ----------
        cls : Type[:class:`compas.data.Data`], optional
            The type of data object to return.
            Defaults to the type of the current data object.
        copy_guid : bool, optional
            If True, the copy will have the same guid as the original.
        copy_name : bool, optional
            If True, the copy will have the same name as the original.

        Returns
        -------
        :class:`compas.data.Data`
            An independent copy of this object.

        """
        if cls is None:
            cls = type(self)  # type: ignore
        obj = cls.__from_data__(deepcopy(self.__data__))
        if copy_name and self._name is not None:
            obj._name = self.name
        if copy_guid:
            obj._guid = self.guid
        return obj  # type: ignore

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
