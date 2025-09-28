from typing import Optional

from compas_fea2.base import Registry
from compas_fea2.base import from_data

from .material import ElasticOrthotropic

vLT_softwood = 0.3
vTT_softwood = 0.4
vLT_hardwood = 0.4
vTT_hardwood = 0.5


class Timber(ElasticOrthotropic):
    """Base class for Timber material (elastic orthotropic behaviour).
    The longitudinal axis (along the grain) is defined along the y-axis.

    Additional Parameters
    ---------------------
    fmk : float
        Bending resistance.
    ft0k : float
        Characteristic tensile strength along the grain.
    fc0k : float
        Characteristic compressive strength along the grain.
    ft90k : float
        Characteristic tensile strength perpendicular to the grain.
    fc90k : float
        Characteristic tensile strength along the grain.
    fvk : float
        Shear resistance.
    vLT : float
        Value of Poisson ratio longitudinal/transverse.
    vTT : float
        Value of Poisson ratio transverse/transverse.
    E0mean : float
        Mean value of modulus of elasticity parallel.
    E90mean : float
        Mean value of modulus of elasticity perpendicular.
    Gmean : float
        Mean value of shear modulus.
    density : float
        Mean density of the timber material [kg/m^3].
    name : str, optional
        Name of the material.

    Additional Attributes
    ---------------------

    fmk : float
        Bending resistance.
    ft0k : float
        Characteristic tensile strength along the grain.
    fc0k : float
        Characteristic compressive strength along the grain.
    ft90k : float
        Characteristic tensile strength perpendicular to the grain.
    fc90k : float
        Characteristic tensile strength along the grain.
    fvk : float
        Shear resistance.
    Ex : float
        Young's modulus Ex in x direction (EN383 - E90 mean).
    Ey : float
        Young's modulus Ey in y direction (EN383 - E0 mean).
    Ez : float
        Young's modulus Ez in z direction (EN383 - E90 mean).
    vxy : float
        Poisson's ratio vxy in x-y directions.
    vyz : float
        Poisson's ratio vyz in y-z directions.
    vzx : float
        Poisson's ratio vzx in z-x directions.
    Gxy : float
        Shear modulus Gxy in x-y direction (EN383 - G mean).
    Gyz : float
        Shear modulus Gyz in y-z directions (EN383 - G mean).
    Gzx : float
        Shear modulus Gzx in z-x directions (EN383 - G mean).

    """

    __doc__ = __doc__ or ""
    __doc__ += ElasticOrthotropic.__doc__ or ""

    def __init__(self, fmk, ft0k, fc0k, ft90k, fc90k, fvk, vLT, vTT, E0mean, E90mean, Gmean, densityk, density, **kwargs):
        super().__init__(Ex=E90mean, Ey=E0mean, Ez=E90mean, vxy=vLT * E90mean / E0mean, vyz=vLT, vzx=vTT, Gxy=Gmean, Gyz=Gmean, Gzx=Gmean, density=density, **kwargs)
        self.fmk = fmk
        self.ft0k = ft0k
        self.fc0k = fc0k
        self.ft90k = ft90k
        self.fc90k = fc90k
        self.fvk = fvk
        self.densityk = densityk

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "fmk": self.fmk,
                "ft0k": self.ft0k,
                "fc0k": self.fc0k,
                "ft90k": self.ft90k,
                "fc90k": self.fc90k,
                "fvk": self.fvk,
                "vLT": self.vyz,
                "vTT": self.vxy,
                "E0mean": self.Ex,
                "E90mean": self.Ey,
                "Gmean": self.Gxy,
                "densityk": self.densityk,
                "density": self.density,
                "name": self.name,
            }
        )
        return data

    @from_data
    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None, duplicate: bool = True):
        material = cls(
            fmk=data.get("fmk"),
            ft0k=data.get("ft0k"),
            fc0k=data.get("fc0k"),
            ft90k=data.get("ft90k"),
            fc90k=data.get("fc90k"),
            fvk=data.get("fvk"),
            vLT=data.get("vLT"),
            vTT=data.get("vTT"),
            E0mean=data.get("E0mean"),
            E90mean=data.get("E90mean"),
            Gmean=data.get("Gmean"),
            densityk=data.get("densityk"),
            density=data.get("density"),
            name=data.get("name"),
        )
        return material

    # --- Softwood Classes (C-classes) ---
    @classmethod
    def C14(cls, units=None, **kwargs):
        """
        Softwood C14.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=14 * units.MPa,
            ft0k=8 * units.MPa,
            fc0k=16 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=2 * units.MPa,
            fvk=3 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=7 * units.GPa,
            E90mean=0.23 * units.GPa,
            Gmean=0.44 * units.GPa,
            densityk=290 * units("kg/m**3"),
            density=350 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C16(cls, units=None, **kwargs):
        """
        Softwood C16.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=16 * units.MPa,
            ft0k=10 * units.MPa,
            fc0k=17 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=2.2 * units.MPa,
            fvk=3.2 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=8 * units.GPa,
            E90mean=0.27 * units.GPa,
            Gmean=0.5 * units.GPa,
            densityk=310 * units("kg/m**3"),
            density=370 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C18(cls, units=None, **kwargs):
        """
        Softwood C18.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=18 * units.MPa,
            ft0k=11 * units.MPa,
            fc0k=18 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=2.2 * units.MPa,
            fvk=3.4 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=9 * units.GPa,
            E90mean=0.3 * units.GPa,
            Gmean=0.56 * units.GPa,
            densityk=320 * units("kg/m**3"),
            density=380 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C20(cls, units=None, **kwargs):
        """
        Softwood C20.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=20 * units.MPa,
            ft0k=12 * units.MPa,
            fc0k=19 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=2.3 * units.MPa,
            fvk=3.6 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=9.5 * units.GPa,
            E90mean=0.32 * units.GPa,
            Gmean=0.59 * units.GPa,
            densityk=330 * units("kg/m**3"),
            density=390 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C22(cls, units=None, **kwargs):
        """
        Softwood C22.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=22 * units.MPa,
            ft0k=13 * units.MPa,
            fc0k=20 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=2.4 * units.MPa,
            fvk=3.8 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=10 * units.GPa,
            E90mean=0.33 * units.GPa,
            Gmean=0.63 * units.GPa,
            densityk=340 * units("kg/m**3"),
            density=410 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C24(cls, units=None, **kwargs):
        """
        Softwood C24.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=24 * units.MPa,
            ft0k=14 * units.MPa,
            fc0k=21 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=2.5 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=11 * units.GPa,
            E90mean=0.37 * units.GPa,
            Gmean=0.69 * units.GPa,
            densityk=350 * units("kg/m**3"),
            density=420 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C27(cls, units=None, **kwargs):
        """
        Softwood C27.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=27 * units.MPa,
            ft0k=16 * units.MPa,
            fc0k=22 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=2.6 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=11.5 * units.GPa,
            E90mean=0.38 * units.GPa,
            Gmean=0.72 * units.GPa,
            densityk=370 * units("kg/m**3"),
            density=450 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C30(cls, units=None, **kwargs):
        """
        Softwood C30.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=30 * units.MPa,
            ft0k=18 * units.MPa,
            fc0k=23 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=2.7 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=12 * units.GPa,
            E90mean=0.4 * units.GPa,
            Gmean=0.75 * units.GPa,
            densityk=380 * units("kg/m**3"),
            density=460 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C35(cls, units=None, **kwargs):
        """
        Softwood C35.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=35 * units.MPa,
            ft0k=21 * units.MPa,
            fc0k=25 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=2.8 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=13 * units.GPa,
            E90mean=0.43 * units.GPa,
            Gmean=0.81 * units.GPa,
            densityk=400 * units("kg/m**3"),
            density=480 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C40(cls, units=None, **kwargs):
        """
        Softwood C40.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=40 * units.MPa,
            ft0k=24 * units.MPa,
            fc0k=26 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=2.9 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=14 * units.GPa,
            E90mean=0.47 * units.GPa,
            Gmean=0.88 * units.GPa,
            densityk=420 * units("kg/m**3"),
            density=500 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C45(cls, units=None, **kwargs):
        """
        Softwood C45.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=45 * units.MPa,
            ft0k=27 * units.MPa,
            fc0k=27 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=3.1 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=15 * units.GPa,
            E90mean=0.5 * units.GPa,
            Gmean=0.94 * units.GPa,
            densityk=440 * units("kg/m**3"),
            density=520 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def C50(cls, units=None, **kwargs):
        """
        Softwood C50.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=50 * units.MPa,
            ft0k=30 * units.MPa,
            fc0k=29 * units.MPa,
            ft90k=0.4 * units.MPa,
            fc90k=3.2 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=16 * units.GPa,
            E90mean=0.53 * units.GPa,
            Gmean=1 * units.GPa,
            densityk=460 * units("kg/m**3"),
            density=550 * units("kg/m**3"),
            **kwargs,
        )

    # --- Hardwood Classes (D-classes) ---
    @classmethod
    def D18(cls, units=None, **kwargs):
        """
        Hardwood D18.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=18 * units.MPa,
            ft0k=11 * units.MPa,
            fc0k=18 * units.MPa,
            ft90k=0.6 * units.MPa,
            fc90k=7.5 * units.MPa,
            fvk=3.4 * units.MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=9.5 * units.GPa,
            E90mean=0.63 * units.GPa,
            Gmean=0.59 * units.GPa,
            densityk=475 * units("kg/m**3"),
            density=570 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def D24(cls, units=None, **kwargs):
        """
        Hardwood D24.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=24 * units.MPa,
            ft0k=14 * units.MPa,
            fc0k=21 * units.MPa,
            ft90k=0.6 * units.MPa,
            fc90k=7.8 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=10 * units.GPa,
            E90mean=0.67 * units.GPa,
            Gmean=0.62 * units.GPa,
            densityk=485 * units("kg/m**3"),
            density=580 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def D30(cls, units=None, **kwargs):
        """
        Hardwood D30.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=30 * units.MPa,
            ft0k=18 * units.MPa,
            fc0k=23 * units.MPa,
            ft90k=0.6 * units.MPa,
            fc90k=8 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=11 * units.GPa,
            E90mean=0.73 * units.GPa,
            Gmean=0.69 * units.GPa,
            densityk=530 * units("kg/m**3"),
            density=640 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def D35(cls, units=None, **kwargs):
        """
        Hardwood D35.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=35 * units.MPa,
            ft0k=21 * units.MPa,
            fc0k=25 * units.MPa,
            ft90k=0.6 * units.MPa,
            fc90k=8.1 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=12 * units.GPa,
            E90mean=0.8 * units.GPa,
            Gmean=0.75 * units.GPa,
            densityk=540 * units("kg/m**3"),
            density=650 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def D40(cls, units=None, **kwargs):
        """
        Hardwood D40.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=40 * units.MPa,
            ft0k=24 * units.MPa,
            fc0k=26 * units.MPa,
            ft90k=0.6 * units.MPa,
            fc90k=8.3 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=13 * units.GPa,
            E90mean=0.86 * units.GPa,
            Gmean=0.81 * units.GPa,
            densityk=550 * units("kg/m**3"),
            density=660 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def D50(cls, units=None, **kwargs):
        """
        Hardwood D50.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=50 * units.MPa,
            ft0k=30 * units.MPa,
            fc0k=29 * units.MPa,
            ft90k=0.6 * units.MPa,
            fc90k=9.3 * units.MPa,
            fvk=4 * units.MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=14 * units.GPa,
            E90mean=0.93 * units.GPa,
            Gmean=0.88 * units.GPa,
            densityk=620 * units("kg/m**3"),
            density=750 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def D60(cls, units=None, **kwargs):
        """
        Hardwood D60.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=60 * units.MPa,
            ft0k=36 * units.MPa,
            fc0k=32 * units.MPa,
            ft90k=0.6 * units.MPa,
            fc90k=10.5 * units.MPa,
            fvk=4.5 * units.MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=17 * units.GPa,
            E90mean=1.13 * units.GPa,
            Gmean=1.06 * units.GPa,
            densityk=700 * units("kg/m**3"),
            density=840 * units("kg/m**3"),
            **kwargs,
        )

    @classmethod
    def D70(cls, units=None, **kwargs):
        """
        Hardwood D70.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        if not units:
            units = u(system="SI_mm")
        elif not isinstance(units, UnitRegistry):
            units = u(system=units)

        return cls(
            fmk=70 * units.MPa,
            ft0k=42 * units.MPa,
            fc0k=34 * units.MPa,
            ft90k=0.6 * units.MPa,
            fc90k=13.5 * units.MPa,
            fvk=5 * units.MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=20 * units.GPa,
            E90mean=1.33 * units.GPa,
            Gmean=1.25 * units.GPa,
            densityk=900 * units("kg/m**3"),
            density=1080 * units("kg/m**3"),
            **kwargs,
        )
