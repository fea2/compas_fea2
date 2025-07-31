********************************************************************************
model
********************************************************************************

.. currentmodule:: compas_fea2.model

.. rst-class:: lead

This package defines the core data structures of COMPAS FEA2. It is data 
structure of the package and lets your build your FEA model. 

Model
=====

.. toctree::
    :maxdepth: 1
    :titlesonly:

    compas_fea2.model.model

Parts
=====

.. autosummary::
    :toctree: generated/

    Part
    RigidPart

Nodes
=====

.. autosummary::
    :toctree: generated/

    Node

Elements
========

.. autosummary::
    :toctree: generated/

    MassElement
    BeamElement
    SpringElement
    TrussElement
    StrutElement
    TieElement
    ShellElement
    MembraneElement
    TetrahedronElement
    HexahedronElement

Releases
========

.. autosummary::
    :toctree: generated/

    BeamEndPinRelease
    BeamEndSliderRelease

Constraints
===========

.. autosummary::
    :toctree: generated/

    TieMPC
    BeamMPC
    TieConstraint

Materials
=========

.. autosummary::
    :toctree: generated/

    UserMaterial
    Stiff
    ElasticIsotropic
    ElasticOrthotropic
    ElasticPlastic
    Concrete
    ConcreteSmearedCrack
    ConcreteDamagedPlasticity
    Steel
    Timber

Sections
========

.. autosummary::
    :toctree: generated/

    BeamSection
    SpringSection
    AngleSection
    BoxSection
    CircularSection
    HexSection
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
    MassSection

Boundary Conditions
===================

.. autosummary::
    :toctree: generated/

    GeneralBC
    FixedBC
    PinnedBC
    ClampBCXX
    ClampBCYY
    ClampBCZZ
    RollerBCX
    RollerBCY
    RollerBCZ
    RollerBCXY
    RollerBCYZ
    RollerBCXZ

Initial Conditions
==================

.. autosummary::
    :toctree: generated/

    InitialTemperatureField
    InitialStressField

Groups
======

.. autosummary::
    :toctree: generated/

    NodesGroup
    ElementsGroup
    FacesGroup
    PartsGroup


Base Classes
============

As user, you never interact with the following classes. They define the basic
behavior of each component in FEA2.

.. autosummary::
    :toctree: generated/

    _Part
    _BoundaryCondition
    _Material
    _Section
    _Section1D
    _Section2D
    _Section3D
    _Element
    _Element1D
    _Element2D
    _Element3D
    _Group
    _Connector
    _Constraint
    _InitialCondition
    _Interaction
    _BeamEndRelease

    