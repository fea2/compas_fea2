********************************************************************************
model
********************************************************************************

.. currentmodule:: compas_fea2.model

.. rst-class:: lead

This package provides the core data structures of COMPAS FEA2, enabling the definition and construction of finite element models. It includes classes for models, parts, nodes, elements, materials, sections, boundary conditions, loads, constraints, releases, and groups.

Model
=====

.. autosummary::
    :toctree: generated/

    Model


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

    BeamElement
    HexahedronElement
    MassElement
    MembraneElement
    ShellElement
    SpringElement
    StrutElement
    TieElement
    TetrahedronElement
    TrussElement

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

    BeamMPC
    TieConstraint
    TieMPC

Materials
=========

.. autosummary::
    :toctree: generated/

    Concrete
    ConcreteDamagedPlasticity
    ConcreteSmearedCrack
    ElasticIsotropic
    ElasticOrthotropic
    ElasticPlastic
    Steel
    Stiff
    Timber
    UserMaterial

Sections
========

.. autosummary::
    :toctree: generated/

    AngleSection
    BeamSection
    BoxSection
    CircularSection
    HexSection
    ISection
    MembraneSection
    PipeSection
    RectangularSection
    ShellSection
    SolidSection
    SpringSection
    StrutSection
    TieSection
    TrapezoidalSection
    TrussSection

Boundary Conditions
===================

.. autosummary::
    :toctree: generated/

    ClampBCXX
    ClampBCYY
    ClampBCZZ
    FixedBC
    GeneralBC
    PinnedBC
    RollerBCX
    RollerBCXY
    RollerBCXZ
    RollerBCY
    RollerBCYZ
    RollerBCZ

Initial Conditions
==================

.. autosummary::
    :toctree: generated/

    InitialStressField
    InitialTemperatureField

Groups
======

.. autosummary::
    :toctree: generated/

    ElementsGroup
    FacesGroup
    NodesGroup
    PartsGroup


Base Classes
============

As user, you never interact with the following classes. They define the basic
behavior of each component in FEA2.

.. autosummary::
    :toctree: generated/

    _BeamEndRelease
    _BoundaryCondition
    _Connector
    _Constraint
    _Element
    _Element1D
    _Element2D
    _Element3D
    _Group
    _InitialCondition
    _Interaction
    _Material
    _Part
    _Section
    _Section1D
    _Section2D
    _Section3D

