********************************************************************************
API Reference
********************************************************************************

model
-----

This package is the core of COMPAS FEA2. It provides the data structures and functionality to define and build finite element models, including parts, nodes, elements, materials, sections, boundary conditions, and groups.

.. toctree::
    :maxdepth: 1
    :titlesonly:

    compas_fea2.model


Problem
-------

This module allows you to define and configure analysis problems based on a finite element model. It supports various analysis steps (static, dynamic, modal, buckling, etc.), load patterns, boundary conditions, and output requests. Once configured, problems can be submitted to supported solvers for execution.

.. toctree::
    :maxdepth: 1
    :titlesonly:

    compas_fea2.problem


Results
-------

After running an analysis, the results module provides classes to access and query simulation outputs, such as displacements, stresses, forces, and reaction forces. You can extract field outputs, history outputs, and other result types for further post-processing or visualization.

.. toctree::
    :maxdepth: 1
    :titlesonly:

    compas_fea2.results


Utilities and Supporting Modules
--------------------------------

This section includes auxiliary modules for unit handling, job file generation, and general utilities that support the core functionalities but are not directly part of the finite element workflow.

.. toctree::
    :maxdepth: 1
    :titlesonly:

    compas_fea2.units
    compas_fea2.job
    compas_fea2.utilities

