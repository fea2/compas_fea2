from typing import Optional

from compas_fea2.base import FEAData
from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.units import units_io


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

    @units_io(types_in=("density", "thermal_expansion"), types_out=None)
    def __init__(self, density: Optional[float] = None, expansion: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)
        self._density = density
        self._expansion = expansion

    @property
    @units_io(types_in=(), types_out="density")
    def density(self) -> Optional[float]: #type: ignore[override]
        """float: Density of the material."""
        return self._density

    @density.setter
    @units_io(types_in=("density",), types_out=None)
    def density(self, value: Optional[float]):
        self._density = value

    @property
    @units_io(types_in=(), types_out="thermal_expansion")
    def expansion(self) -> Optional[float]: #type: ignore[override]
        """float: Thermal expansion coefficient."""
        return self._expansion

    @expansion.setter
    @units_io(types_in=("thermal_expansion",), types_out=None)
    def expansion(self, value: Optional[float]):
        """Set the thermal expansion coefficient."""
        self._expansion = value

    @property
    def model(self):
        return self._registration

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "density": self._density,
                "expansion": self._expansion,
            }
        )
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
            self.__class__.__name__, len(self.__class__.__name__) * "-", self.name, self._density, self._expansion
        )


# ==============================================================================
# linear elastic
# ==============================================================================
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

    @units_io(
        types_in=(
            "stress",
            "stress",
            "stress",  # Ex, Ey, Ez
            None,
            None,
            None,  # vxy, vyz, vzx (dimensionless)
            "stress",
            "stress",
            "stress",  # Gxy, Gyz, Gzx
            "density",  # density
            "thermal_expansion",  # expansion
        ),
        types_out=None,
    )
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
            Ex=data.get("Ex"),
            Ey=data.get("Ey"),
            Ez=data.get("Ez"),
            vxy=data.get("vxy"),
            vyz=data.get("vyz"),
            vzx=data.get("vzx"),
            Gxy=data.get("Gxy"),
            Gyz=data.get("Gyz"),
            Gzx=data.get("Gzx"),
            density=data.get("density", 0.0),
            expansion=data.get("expansion", None),
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
            self._density,
            self._expansion,
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

    @units_io(types_in=("stress", None, "density", "thermal_expansion"), types_out=None)
    def __init__(self, E: float, v: float, density: float, expansion: Optional[float] = None, **kwargs):
        super().__init__(density=density, expansion=expansion, **kwargs)
        self._E = E
        self._v = v

    @property
    @units_io(types_in=(), types_out="stress")
    def E(self) -> float: # type: ignore[override]
        """float: Young's modulus E."""
        return self._E

    @E.setter
    @units_io(types_in=("stress", None), types_out=None)
    def E(self, value: float):
        self._E = value

    @property
    def v(self) -> float:
        """float: Poisson's ratio v."""
        return self._v

    @v.setter
    def v(self, value: float):
        self._v = value

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "E": self._E,
                "v": self._v,
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
            self.name, self._density, self._expansion, self._E, self._v, self.G
        )

    @property
    @units_io(types_in=(), types_out=("stress"))
    def G(self) -> float:
        return 0.5 * self._E / (1 + self._v)


class Stiff(_Material):
    """Elastic, very stiff and massless material."""


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

    @units_io(types_in=("stress", None, "density", None, "thermal_expansion"), types_out=None)
    def __init__(self, E: float, v: float, density: float, strain_stress: list[tuple[float, float]], expansion: Optional[float] = None, **kwargs):
        super().__init__(E=E, v=v, density=density, expansion=expansion, **kwargs)
        self.strain_stress = strain_stress

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "strain_stress": self.strain_stress,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate: bool = True):
        material = cls(E=data.get("E"), v=data.get("v"), density=data.get("density", 0.0), strain_stress=data.get("strain_stress"), expansion=data.get("expansion", None))
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
            self.name, self._density, self._expansion, self._E, self._v, self.G, self.strain_stress
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

    @units_io(types_in=("thermal_conductivity", "specific_heat", "stress", None, "density", "thermal_expansion"), types_out=None)
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
        material = cls(k=data.get("k"), c=data.get("c"), E=data.get("E"), v=data.get("v"), density=data.get("density", 0.0), expansion=data.get("expansion", None))
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
            self.name, self._density, self._expansion, self._E, self._v, self.G, self.k, self.c
        )

    @property
    @units_io(types_in=(), types_out=("thermal_conductivity"))
    def k(self) -> float:
        return self._k

    @property
    @units_io(types_in=(), types_out=("specific_heat"))
    def c(self) -> float:
        return self._c
