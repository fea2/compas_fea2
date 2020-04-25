"""
********************************************************************************
structure
********************************************************************************

.. currentmodule:: compas_fea._core


structure
=========

.. autosummary::
    :toctree: generated/

    CoreStructure


constraints
===========

.. autosummary::
    :toctree: generated/

    Constraint
    TieConstraint


bcs
===

.. autosummary::
    :toctree: generated/

    GeneralDisplacement
    FixedDisplacement
    PinnedDisplacement
    FixedDisplacementXX
    FixedDisplacementYY
    FixedDisplacementZZ
    RollerDisplacementX
    RollerDisplacementY
    RollerDisplacementZ
    RollerDisplacementXY
    RollerDisplacementYZ
    RollerDisplacementXZ


elements
========

.. autosummary::
    :toctree: generated/

    Node
    Element
    MassElement
    BeamElement
    SpringElement
    TrussElement
    StrutElement
    TieElement
    ShellElement
    MembraneElement
    FaceElement
    SolidElement
    PentahedronElement
    TetrahedronElement
    HexahedronElement


properties
==========
.. autosummary::
    :toctree: generated/

    ElementProperties


loads
=====

.. autosummary::
    :toctree: generated/

    Load
    PrestressLoad
    PointLoad
    PointLoads
    LineLoad
    AreaLoad
    GravityLoad
    TributaryLoad
    HarmonicPointLoad


materials
=========

.. autosummary::
    :toctree: generated/

    Material
    Concrete
    ConcreteSmearedCrack
    ConcreteDamagedPlasticity
    Stiff
    ElasticIsotropic
    ElasticOrthotropic
    ElasticPlastic
    Steel


misc
====

.. autosummary::
    :toctree: generated/

    Misc
    Amplitude
    Temperatures


section
=======

.. autosummary::
    :toctree: generated/

    Section
    AngleSection
    BoxSection
    CircularSection
    GeneralSection
    ISection
    PipeSection
    RectangularSection
    ShellSection
    MembraneSection
    SolidSection
    TrapezoidalSection
    TrussSection
    StrutSection
    TieSection
    SpringSection


load_cases
==========

.. autosummary::
    :toctree: generated/

    Step
    GeneralStep
    ModalStep
    HarmonicStep
    BucklingStep


"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .structure import *
from .bcs import *
from .constraints import *
from .elements import *
from .load_cases import *
from .load_combos import *
from .loads import *
from .steps import *
from .materials import *
from .properties import *
from .sections import *
from .misc import *


__all__ = [name for name in dir() if not name.startswith('_')]