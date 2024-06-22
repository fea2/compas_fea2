from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import itertools
from typing import Iterable

from compas_fea2.base import FEAData
from compas_fea2.problem.loads import NodeLoad, GravityLoad


class Pattern(FEAData):
    """A pattern is the spatial distribution of a specific set of forces,
    displacements, temperatures, and other effects which act on a structure.
    Any combination of nodes and elements may be subjected to loading and
    kinematic conditions.

    Parameters
    ----------
    distribution : list
        list of :class:`compas_fea2.model.Node` or :class:`compas_fea2.model._Element`

    Attributes
    ----------
    distribution : list
        list of :class:`compas_fea2.model.Node` or :class:`compas_fea2.model._Element`

    """


    @property
    def __data__(self):
        return {
            "distribution": self._distribution,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "xx": self.xx,
            "yy": self.yy,
            "zz": self.zz,
            "load_case": self.load_case,
            "axes": self.axes,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            distribution=data["distribution"],
            x=data["x"],
            y=data["y"],
            z=data["z"],
            xx=data["xx"],
            yy=data["yy"],
            zz=data["zz"],
            load_case=data["load_case"],
            axes=data["axes"],
        )

    def __init__(self, distribution, x=None, y=None, z=None, xx=None, yy=None, zz=None, load_case=None, axes="global", **kwargs):
        super(Pattern, self).__init__(**kwargs)
        self._distribution = distribution if isinstance(distribution, Iterable) else [distribution]
        self._nodes = None
        self.x = x
        self.y = y
        self.z = z
        self.xx = xx
        self.yy = yy
        self.zz = zz
        self.load_case = load_case
        self.axes = axes
        if axes != "global":
            raise NotImplementedError("local axes are not supported yet")
        self._registration = None

    @property
    def components(self):
        return {i: getattr(self, i) for i in ["x", "y", "z", "xx", "yy", "zz"]}

    @property
    def n_nodes(self):
        return len(self.nodes)

    @property
    def step(self):
        return self._registration

    @property
    def problem(self):
        return self.step._registration

    @property
    def model(self):
        return self.problem._registration

    @property
    def distribution(self):
        return self._distribution



class NodeLoadPattern(Pattern):
    """Nodal distribution of a load case.

    Parameters
    ----------
    Pattern : _type_
        _description_
    """

    def __init__(self, nodes, x=None, y=None, z=None, xx=None, yy=None, zz=None, load_case=None, axes="global", **kwargs):
        super(NodeLoadPattern, self).__init__(nodes, x, y, z, xx, yy, zz, load_case, axes, **kwargs)

    @property
    def nodes(self):
        return self._distribution

    @property
    def load(self):
        return NodeLoad(**{k: v if v else v for k, v in self.components.items()}, axes=self.axes)

    @property
    def node_load(self):
        n_nodes = len(self.nodes)
        # FIXME change to tributary load for each node
        return zip(self.nodes, [self.load] * n_nodes)



class PointLoadPattern(NodeLoadPattern):
    """Point distribution of a load case.

    Parameters
    ----------
    Pattern : _type_
        _description_
    """


    @property
    def __data__(self):
        data = super(PointLoadPattern, self).__data__
        data.update({
            "tolerance": self.tolerance,
        })
        return data

    @classmethod
    def __from_data__(cls, data):
        return cls(
            points=data["distribution"],
            x=data["x"],
            y=data["y"],
            z=data["z"],
            xx=data["xx"],
            yy=data["yy"],
            zz=data["zz"],
            load_case=data["load_case"],
            axes=data["axes"],
            tolerance=data["tolerance"],
        )

    def __init__(self, points, x=None, y=None, z=None, xx=None, yy=None, zz=None, load_case=None, axes="global", tolerance=1, **kwargs):
        super(PointLoadPattern, self).__init__(points, x, y, z, xx, yy, zz, load_case, axes, **kwargs)
        self.tolerance = tolerance

    @property
    def points(self):
        return self._distribution

    @property
    def nodes(self):
        return [self.model.find_closest_nodes_to_point(point, distance=self.tolerance)[0] for point in self.points]


class LineLoadPattern(Pattern):
    """Line distribution of a load case.

    Parameters
    ----------
    Pattern : _type_
        _description_
    """

    def __init__(self, polyline, x=None, y=None, z=None, xx=None, yy=None, zz=None, load_case=None, axes="global", tolerance=1, discretization=10, **kwargs):
        super(LineLoadPattern, self).__init__(polyline, x, y, z, xx, yy, zz, load_case, axes, **kwargs)
        self.tolerance = tolerance
        self.discretization = discretization


    @property
    def __data__(self):
        data = super(LineLoadPattern, self).__data__
        data.update({
            "tolerance": self.tolerance,
            "discretization": self.discretization,
        })
        return data

    @classmethod
    def __from_data__(cls, data):
        return cls(
            polyline=data["distribution"],
            x=data["x"],
            y=data["y"],
            z=data["z"],
            xx=data["xx"],
            yy=data["yy"],
            zz=data["zz"],
            load_case=data["load_case"],
            axes=data["axes"],
            tolerance=data["tolerance"],
            discretization=data["discretization"],
        )

    @property
    def load(self):
        return NodeLoad(**{k: v if v else v for k, v in self.components.items()}, axes=self.axes)

    @property
    def polyline(self):
        return self._distribution

    @property
    def nodes(self):
        return [self.model.find_closest_nodes_to_point(point, distance=self.distance)[0] for point in self.polyline.divide_polyline(self.discretization)]

    @property
    def node_load(self):
        n_nodes = len(self.nodes)
        length = self.polyline.length
        # FIXME change to tributary load for each node
        return zip(self.nodes, [NodeLoad(**{k: v * length / n_nodes if v else v for k, v in self.components.items()}, axes=self.axes)] * n_nodes)



class AreaLoadPattern(Pattern):
    """Area distribution of a load case.

    Parameters
    ----------
    Pattern : _type_
        _description_
    """


    @property
    def __data__(self):
        data = super(AreaLoadPattern, self).__data__
        data.update({
            "tolerance": self.tolerance,
        })
        return data

    @classmethod
    def __from_data__(cls, data):
        return cls(
            polygon=data["distribution"],
            x=data["x"],
            y=data["y"],
            z=data["z"],
            xx=data["xx"],
            yy=data["yy"],
            zz=data["zz"],
            load_case=data["load_case"],
            axes=data["axes"],
            tolerance=data["tolerance"],
        )

    def __init__(self, polygon, x=None, y=None, z=None, xx=None, yy=None, zz=None, load_case=None, axes="global", tolerance=1.05, **kwargs):
        super(AreaLoadPattern, self).__init__(distribution=polygon, x=x, y=y, z=z, xx=xx, yy=yy, zz=zz, load_case=load_case, axes=axes, **kwargs)
        self.tolerance = tolerance

    @property
    def polygon(self):
        return self._distribution

    @property
    def nodes(self):
        return self.model.find_nodes_in_polygon(self.polygon, tolerance=self.tolerance)

    @property
    def load(self):
        return NodeLoad(**{k: v if v else v for k, v in self.components.items()}, axes=self.axes)

    @property
    def node_load(self):
        n_nodes = len(self.nodes)
        area = self.polygon.area
        return zip(self.nodes, [NodeLoad(**{k: v * area / n_nodes if v else v for k, v in self.components.items()}, axes=self.axes)] * n_nodes)



class VolumeLoadPattern(Pattern):
    """Volume distribution of a load case (e.g., gravity load).

    Parameters
    ----------
    Pattern : _type_
        _description_
    """

    def __init__(self, parts, x=None, y=None, z=None, xx=None, yy=None, zz=None, load_case=None, axes="global", **kwargs):
        super(VolumeLoadPattern, self).__init__(parts, x, y, z, xx, yy, zz, load_case, axes, **kwargs)

    @property
    def parts(self):
        return self._distribution

    @property
    def nodes(self):
        return list(set(itertools.chain.from_iterable(self.parts)))

    @property
    def load(self):
        return NodeLoad(**{k: v if v else v for k, v in self.components.items()}, axes=self.axes)

    @property
    def node_load(self):
        nodes_loads = {}
        for part in self.parts:
            for element in part.elements:
                vol = element.volume
                den = element.section.material.density
                n_nodes = len(element.nodes)
                load = NodeLoad(**{k: v * vol * den / n_nodes if v else v for k, v in self.components.items()}, axes=self.axes)
                for node in element.nodes:
                    if node in nodes_loads:
                        nodes_loads[node] += load
                    else:
                        nodes_loads[node] = load
        return zip(list(nodes_loads.keys()), list(nodes_loads.values()))


class GravityLoadPattern(Pattern):
    """Volume distribution of a load case (e.g., gravity load).

    Parameters
    ----------
    Pattern : _type_
        _description_
    """

    @property
    def __data__(self):
        return {
            "parts": self.parts,
            "g": self.g,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "load_case": self.load_case,
            "axes": self.axes,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            parts=data["distribution"],
            g=data["g"],
            x=data["x"],
            y=data["y"],
            z=data["z"],
            load_case=data["load_case"],
            axes=data["axes"],
        )

    def __init__(self, parts=None, g=9810, x=0, y=0, z=-1, load_case=None, axes="global", **kwargs):
        super(GravityLoadPattern, self).__init__(parts, x, y, z, xx=None, yy=None, zz=None, load_case=load_case, axes=axes, **kwargs)
        self._g = g

    @property
    def g(self):
        return self._g

    @property
    def parts(self):
        return self._distribution

    @property
    def nodes(self):
        return list(set(itertools.chain.from_iterable(self.parts)))

    @property
    def load(self):
        return GravityLoad(self.g, self.x, self.y, self.z)

    @property
    def node_load(self):
        return zip([None], [self.load])
