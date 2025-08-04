from .model import Model
from .parts import (
    Part,
    RigidPart,
)
from .nodes import Node
from .elements import (
    _Element,
    MassElement,
    _Element0D,
    SpringElement,
    LinkElement,
    _Element1D,
    BeamElement,
    TrussElement,
    StrutElement,
    TieElement,
    _Element2D,
    ShellElement,
    MembraneElement,
    _Element3D,
    TetrahedronElement,
    HexahedronElement,
    Face,
)
from .materials.material import (
    _Material,
    ElasticIsotropic,
    ThermalElasticIsotropic,
    ElasticOrthotropic,
    ElasticPlastic,
    Stiff,
    UserMaterial,
)
from .materials.concrete import (
    Concrete,
    ConcreteDamagedPlasticity,
    ConcreteSmearedCrack,
)
from .materials.steel import Steel
from .materials.timber import Timber
from .sections import (
    _Section,
    _Section1D,
    _Section2D,
    _Section3D,
    SpringSection,
    ConnectorSection,
    GenericBeamSection,
    AngleSection,
    BoxSection,
    CircularSection,
    HexSection,
    ISection,
    PipeSection,
    RectangularSection,
    ShellSection,
    MembraneSection,
    SolidSection,
    TrapezoidalSection,
    TrussSection,
    StrutSection,
    TieSection,
)
from .constraints import (
    _Constraint,
    _MultiPointConstraint,
    TieMPC,
    BeamMPC,
    TieConstraint,
)
from .connectors import (
    _Connector,
    LinearConnector,
    RigidLinkConnector,
    SpringConnector,
    ZeroLengthConnector,
    ZeroLengthSpringConnector,
    ZeroLengthContactConnector,
)
from .groups import (
    _Group,
    NodesGroup,
    ElementsGroup,
    FacesGroup,
    PartsGroup,
)
from .releases import (
    _BeamEndRelease,
    BeamEndPinRelease,
    BeamEndSliderRelease,
)
from .bcs import (
    _BoundaryCondition,
    GeneralBC,
    FixedBC,
    FixedBCX,
    FixedBCY,
    FixedBCZ,
    PinnedBC,
    ClampBCXX,
    ClampBCYY,
    ClampBCZZ,
    RollerBCX,
    RollerBCY,
    RollerBCZ,
    RollerBCXY,
    RollerBCYZ,
    RollerBCXZ,
)

from .ics import (
    _InitialCondition,
    InitialTemperature,
    InitialStress,
)

from .fields import (
    InitialTemperatureField,
    InitialStressField,
    _BoundaryConditionsField,
    _MechanicalBoundaryCondition,
    GeneralBCField,
    FixedBCField,
    FixedBCXField,
    FixedBCYField,
    FixedBCZField,
    PinnedBCField,
    ClampedBCXXField,
    ClampedBCYYField,
    ClampedBCZZField,
    RollerBCXField,
    RollerBCYField,
    RollerBCZField,
    RollerBCXYField,
    RollerBCYZField,
    RollerBCXZField,
    ThermalBCField
    
)

from .interfaces import (
    _Interface,
)

from .interactions import (
    _Interaction,
    Contact,
    HardContactFrictionPenalty,
    HardContactNoFriction,
    LinearContactFrictionPenalty,
    HardContactRough,
    Convection,
    Radiation,
)

__all__ = [  # type: ignore[reportUnsupportedDunderAll]
    name for name, obj in globals().items() if not name.startswith(" _") and not name.startswith("__") and not callable(name) and not name.startswith("_") and name.isidentifier()
]
