from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import Set
from typing import TypeVar

from compas_fea2.model.groups import _Group


# Type-checking imports to avoid circular dependencies at runtime
if TYPE_CHECKING:
    from compas_fea2.problem.loads import _Load


# Define a generic type for members of _Group
_MemberType = TypeVar("_MemberType")

# Define a generic type for the _Group class itself, used for __add__, __sub__, etc.
G = TypeVar("G", bound="_Group[Any]")  # G must be a subclass of _Group

class LoadsGroup(_Group["_Load"]):
    """Base class for groups of loads.

    """

    def __init__(self, members: Iterable["_Load"] | "_Load", **kwargs) -> None:
        from compas_fea2.problem.loads import _Load

        if isinstance(members, _Load):
            members = [members]
        super().__init__(members=members, member_class=_Load, **kwargs)

    @property
    def loads(self) -> Set["_Load"]:
        return self._members


