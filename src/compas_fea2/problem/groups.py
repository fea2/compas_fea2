from typing import TYPE_CHECKING
from typing import Iterable
from typing import Set

from compas_fea2.model.groups import _Group

# Type-checking imports to avoid circular dependencies at runtime
if TYPE_CHECKING:
    from compas_fea2.problem.displacements import GeneralDisplacement
    from compas_fea2.problem.fields import DisplacementField
    from compas_fea2.problem.fields import ForceField
    from compas_fea2.problem.loads import _Load


class LoadsGroup(_Group["_Load"]):
    """Base class for groups of loads."""

    def __init__(self, members: Iterable["_Load"] | "_Load", **kwargs) -> None:
        from compas_fea2.problem.loads import _Load

        if isinstance(members, _Load):
            members = [members]
        super().__init__(members=members, member_class=_Load, **kwargs)

    @property
    def loads(self) -> Set["_Load"]:
        return self._members


class DisplacementsGroup(_Group["GeneralDisplacement"]):
    """Base class for groups of displacements."""

    def __init__(self, members: Iterable["GeneralDisplacement"] | "GeneralDisplacement", **kwargs) -> None:
        from compas_fea2.problem.displacements import GeneralDisplacement

        if isinstance(members, "GeneralDisplacement"):
            members = [members]
        super().__init__(members=members, member_class=GeneralDisplacement, **kwargs)

    @property
    def displacements(self) -> Set["GeneralDisplacement"]:
        return self._members


class LoadsFieldGroup(_Group["DisplacementField | ForceField"]):
    """Base class for groups of loads that can be applied to a field."""

    def __init__(self, members: "Iterable[DisplacementField | ForceField] | DisplacementField | ForceField", **kwargs) -> None:
        from compas_fea2.problem.fields import _BaseLoadField

        if not isinstance(members, Iterable):
            members = [members]
        super().__init__(members=members, member_class=_BaseLoadField, **kwargs)

    @property
    def fields(self) -> "Iterable[DisplacementField | ForceField]":
        return self._members
