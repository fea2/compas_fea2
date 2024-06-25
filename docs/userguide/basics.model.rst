******************************************************************************
Model
******************************************************************************

At the heart of every COMPAS FEA2 analysis or simluation is a model.
A model consists of one or more parts, connected or constrainted.

>>> from compas_fea2.model import Model
>>> model = Model()


Parts
=====
Parts are the basic building blocks of a model.
The definition of a Part can be subjective.
Think about a brick wall: is it one part or many parts? Well, it depends on the context
and on the level of detail you want to include in your model and the purpose of the analysis.
You can think of it as a model with many parts, each part representing a brick; or as a model
with one part, representing the wall as a whole and the bricks as a finite elements.

A Part can be either Deformable or Rigid.

>>> from compas_fea2.model import DeformablePart
>>> prt = DeformablePart


Nodes
=====

Nodes are the basic building blocks of a model.
They define the locations in space that define all other entities.

>>> from compas_fea2.model import Node
>>> node = Node(xyz=[1.0, 2.0, 3.0])
>>> node.x
1.0
>>> node.y
2.0
>>> node.z
3.0
>>> node.xyz
[1.0, 2.0, 3.0]
>>> node.point
Point(x=1.0, y=2.0, z=3.0)

Besides coordinates, nodes have many other (optional) attributes.

>>> node.mass
(None, None, None)

>>> node.dof
{'x': True, 'y': True, 'z': True, 'xx': True, 'yy': True, 'zz': True}



Elements
========

Elements are defined by the nodes they connect to and a section.

>>>
