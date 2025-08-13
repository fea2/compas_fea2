from typing import Optional

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data


class _Material(FEAData):
    """Basic Material

    Parameters
    ----------
    density : float
        Density of the material.
    expansion : float, optional
        Thermal expansion coefficient, by default None.

    Other Parameters
    ----------------
    **kwargs : dict
        Backend dependent keyword arguments.
        See the individual backends for more information.

    Attributes
    ----------
    density : float
        Density of the material.
    expansion : float
        Thermal expansion coefficient.
    key : int
        The key index of the material. It is automatically assigned to material
        once it is added to the model.
    model : :class:`compas_fea2.model.Model`
        The Model where the material is assigned.

    Notes
    -----
    Materials are registered to a :class:`compas_fea2.model.Model`. The same
    material can be assigned to multiple sections and in different elements and
    parts.

    """

    def __init__(self, density: Optional[float] = None, expansion: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)
        self.density = density
        self.expansion = expansion

    @property
    def model(self):
        return self._registration

    @property
    def __data__(self):
        data = super().__data__
        data.update({
            "density": self.density,
            "expansion": self.expansion,
        })
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate: bool = True):
        density = data.get("density", 0.0)
        expansion = data.get("expansion", None)
        material = cls(density=density, expansion=expansion)
        return material

    def __str__(self) -> str:
        return """
{}
{}
name        : {}
density     : {}
expansion   : {}
""".format(
            self.__class__.__name__, len(self.__class__.__name__) * "-", self.name, self.density, self.expansion
        )

    def __html__(self) -> str:
        return """<html>
<head></head>
<body><p>Hello World!</p></body>
</html>"""


# ==============================================================================
# linear elastic
# ==============================================================================
# @extend_docstring(_Material)
class ElasticOrthotropic(_Material):
    """Elastic, orthotropic and homogeneous material

    Parameters
    ----------
    Ex : float
        Young's modulus Ex in x direction.
    Ey : float
        Young's modulus Ey in y direction.
    Ez : float
        Young's modulus Ez in z direction.
    vxy : float
        Poisson's ratio vxy in x-y directions.
    vyz : float
        Poisson's ratio vyz in y-z directions.
    vzx : float
        Poisson's ratio vzx in z-x directions.
    Gxy : float
        Shear modulus Gxy in x-y directions.
    Gyz : float
        Shear modulus Gyz in y-z directions.
    Gzx : float
        Shear modulus Gzx in z-x directions.

    Attributes
    ----------
    Ex : float
        Young's modulus Ex in x direction.
    Ey : float
        Young's modulus Ey in y direction.
    Ez : float
        Young's modulus Ez in z direction.
    vxy : float
        Poisson's ratio vxy in x-y directions.
    vyz : float
        Poisson's ratio vyz in y-z directions.
    vzx : float
        Poisson's ratio vzx in z-x directions.
    Gxy : float
        Shear modulus Gxy in x-y directions.
    Gyz : float
        Shear modulus Gyz in y-z directions.
    Gzx : float
        Shear modulus Gzx in z-x directions.
    """

    def __init__(
        self,
        Ex: float,
        Ey: float,
        Ez: float,
        vxy: float,
        vyz: float,
        vzx: float,
        Gxy: float,
        Gyz: float,
        Gzx: float,
        density: float,
        expansion: Optional[float] = None,
        **kwargs,
    ):
        super().__init__(density=density, expansion=expansion, **kwargs)
        self.Ex = Ex
        self.Ey = Ey
        self.Ez = Ez
        self.vxy = vxy
        self.vyx = vxy * Ey / Ex
        self.vyz = vyz
        self.vzy = vyz * Ez / Ey
        self.vzx = vzx
        self.vxz = vzx * Ex / Ez
        self.Gxy = Gxy
        self.Gyz = Gyz
        self.Gzx = Gzx

        # the equations below must be verified by an orthotropic elactic material
        check_list = [
            self.Ex > 0,
            self.Ey > 0,
            self.Ez > 0,
            self.Gxy > 0,
            self.Gyz > 0,
            self.Gzx > 0,
            self.vxy < (Ex / Ey) ** 0.5,
            vzx < (Ez / Ex) ** 0.5,
            vyz < (Ey / Ez) ** 0.5,
            1 - self.vxy * self.vyx - self.vyz * self.vzy - self.vzx * self.vxz - 2 * self.vyx * self.vzy * self.vxz > 0,
        ]
        for check in check_list:
            if not (check):
                raise ValueError("The mechanical values do not respect the material stability criteria.")

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "Ex": self.Ex,
                "Ey": self.Ey,
                "Ez": self.Ez,
                "vxy": self.vxy,
                "vyz": self.vyz,
                "vzx": self.vzx,
                "Gxy": self.Gxy,
                "Gyz": self.Gyz,
                "Gzx": self.Gzx,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate: bool = True):
        material = cls(
            Ex=data.get("Ex"), Ey=data.get("Ey"), Ez=data.get("Ez"),
            vxy=data.get("vxy"), vyz=data.get("vyz"), vzx=data.get("vzx"),
            Gxy=data.get("Gxy"), Gyz=data.get("Gyz"), Gzx=data.get("Gzx"),
            density=data.get("density", 0.0), expansion=data.get("expansion", None),
        )
        return material

    def __str__(self) -> str:
        return """
{}
{}
name        : {}
density     : {}
expansion   : {}

Ex  : {}
Ey  : {}
Ez  : {}
vxy : {}
vyz : {}
vzx : {}
Gxy : {}
Gyz : {}
Gzx : {}
""".format(
            self.__class__.__name__,
            len(self.__class__.__name__) * "-",
            self.name,
            self.density,
            self.expansion,
            self.Ex,
            self.Ey,
            self.Ez,
            self.vxy,
            self.vyz,
            self.vzx,
            self.Gxy,
            self.Gyz,
            self.Gzx,
        )


# @extend_docstring(_Material)
class ElasticIsotropic(_Material):
    """Elastic, isotropic and homogeneous material

    Parameters
    ----------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.

    Attributes
    ----------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    G : float
        Shear modulus (automatically computed from E and v)

    """

    def __init__(self, E: float, v: float, density: float, expansion: Optional[float] = None, **kwargs):
        super().__init__(density=density, expansion=expansion, **kwargs)
        self.E = E
        self.v = v

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "E": self.E,
                "v": self.v,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate: bool = True):
        material = cls(E=data.get("E"), v=data.get("v"), density=data.get("density", 0.0), expansion=data.get("expansion", None))
        return material

    
    
    def __str__(self) -> str:
        return """
ElasticIsotropic Material
-------------------------
name        : {}
density     : {}
expansion   : {}

E : {}
v : {}
G : {}
""".format(
            self.name, self.density, self.expansion, self.E, self.v, self.G
        )

    @property
    def G(self) -> float:
        return 0.5 * self.E / (1 + self.v)


class Stiff(_Material):
    """Elastic, very stiff and massless material."""

    def __init__(self, *, density: float, expansion: Optional[float] = None, name: Optional[str] = None, **kwargs):
        raise NotImplementedError()


# ==============================================================================
# non-linear general
# ==============================================================================
class ElasticPlastic(ElasticIsotropic):
    """Elastic and plastic, isotropic and homogeneous material.

    Parameters
    ----------
    E : float
        Young's modulus.
    v : float
        Poisson's ratio.
    strain_stress : list[tuple[float, float]]
        Strain-stress data, including elastic and plastic behaviour,
        in the form of strain/stress value pairs.

    Attributes
    ----------
    E : float
        Young's modulus.
    v : float
        Poisson's ratio.
    G : float
        Shear modulus (automatically computed from E and v)
    strain_stress : list[tuple[float, float]]
        Strain-stress data, including elastic and plastic behaviour,
        in the form of strain/stress value pairs.
    """

    def __init__(self, E: float, v: float, density: float, strain_stress: list[tuple[float, float]], expansion: Optional[float] = None, **kwargs):
        super().__init__(E=E, v=v, density=density, expansion=expansion, **kwargs)
        self.strain_stress = strain_stress

    @property
    def __data__(self):
        data = super().__data__
        data.update({
            "strain_stress": self.strain_stress,
        })
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate: bool = True):
        material = cls(
            E=data.get("E"), v=data.get("v"), density=data.get("density", 0.0),
            strain_stress=data.get("strain_stress"), expansion=data.get("expansion", None)
        )
        return material

    def __str__(self) -> str:
        return """
ElasticPlastic Material
-----------------------
name        : {}
density     : {}
expansion   : {}

E  : {}
v  : {}
G  : {}

strain_stress : {}
""".format(
            self.name, self.density, self.expansion, self.E, self.v, self.G, self.strain_stress
        )


# ==============================================================================
# User-defined Materials
# ==============================================================================


class UserMaterial(FEAData):
    """User Defined Material. To implement this type of material, a
    separate subroutine is required

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raise NotImplementedError("This class is not available for the selected backend plugin")


# ==============================================================================
# Heat Material
# ==============================================================================


class ThermalElasticIsotropic(ElasticIsotropic):
    """Thermal isotropic material for heat analysis.

    Parameters
    ----------
    k : float
        Thermal conductivity.
    c : float
        Specific heat capacity.

    Attributes
    ----------
    k : float
        Thermal conductivity.
    c : float
        Specific heat capacity.

    """

    def __init__(self, k: float, c: float, E: float, v: float, density: float, expansion: Optional[float] = None, **kwargs):
        super().__init__(E=E, v=v, density=density, expansion=expansion, **kwargs)
        self._k = k
        self._c = c

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "k": self.k,
                "c": self.c,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate: bool = True):
        material = cls(
            k=data.get("k"), c=data.get("c"), E=data.get("E"), v=data.get("v"),
            density=data.get("density", 0.0), expansion=data.get("expansion", None)
        )
        return material

    def __str__(self) -> str:
        return """
Thermal ElasticIsotropic Material
-------------------------
name        : {}
density     : {}
expansion   : {}

E : {}
v : {}
G : {}

k : {}
c : {}
""".format(
            self.name, self.density, self.expansion, self.E, self.v, self.G, self.k, self.c
        )

    @property
    def k(self) -> float:
        return self._k

    @property
    def c(self) -> float:
        return self._c
