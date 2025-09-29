from typing import Optional

from compas_fea2.base import Registry
from compas_fea2.base import from_data
from compas_fea2.units import GPa
from compas_fea2.units import MPa
from compas_fea2.units import kg_per_m3

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
    def C14(cls, **kwargs):
        """
        Softwood C14.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=14 * MPa,
            ft0k=8 * MPa,
            fc0k=16 * MPa,
            ft90k=0.4 * MPa,
            fc90k=2 * MPa,
            fvk=3 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=7 * GPa,
            E90mean=0.23 * GPa,
            Gmean=0.44 * GPa,
            densityk=290 * kg_per_m3,
            density=350 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C16(cls, **kwargs):
        """
        Softwood C16.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=16 * MPa,
            ft0k=10 * MPa,
            fc0k=17 * MPa,
            ft90k=0.4 * MPa,
            fc90k=2.2 * MPa,
            fvk=3.2 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=8 * GPa,
            E90mean=0.27 * GPa,
            Gmean=0.5 * GPa,
            densityk=310 * kg_per_m3,
            density=370 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C18(cls, **kwargs):
        """
        Softwood C18.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=18 * MPa,
            ft0k=11 * MPa,
            fc0k=18 * MPa,
            ft90k=0.4 * MPa,
            fc90k=2.2 * MPa,
            fvk=3.4 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=9 * GPa,
            E90mean=0.3 * GPa,
            Gmean=0.56 * GPa,
            densityk=320 * kg_per_m3,
            density=380 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C20(cls, **kwargs):
        """
        Softwood C20.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=20 * MPa,
            ft0k=12 * MPa,
            fc0k=19 * MPa,
            ft90k=0.4 * MPa,
            fc90k=2.3 * MPa,
            fvk=3.6 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=9.5 * GPa,
            E90mean=0.32 * GPa,
            Gmean=0.59 * GPa,
            densityk=330 * kg_per_m3,
            density=390 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C22(cls, **kwargs):
        """
        Softwood C22.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=22 * MPa,
            ft0k=13 * MPa,
            fc0k=20 * MPa,
            ft90k=0.4 * MPa,
            fc90k=2.4 * MPa,
            fvk=3.8 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=10 * GPa,
            E90mean=0.33 * GPa,
            Gmean=0.63 * GPa,
            densityk=340 * kg_per_m3,
            density=410 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C24(cls, **kwargs):
        """
        Softwood C24.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=24 * MPa,
            ft0k=14 * MPa,
            fc0k=21 * MPa,
            ft90k=0.4 * MPa,
            fc90k=2.5 * MPa,
            fvk=4 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=11 * GPa,
            E90mean=0.37 * GPa,
            Gmean=0.69 * GPa,
            densityk=350 * kg_per_m3,
            density=420 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C27(cls, **kwargs):
        """
        Softwood C27.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=27 * MPa,
            ft0k=16 * MPa,
            fc0k=22 * MPa,
            ft90k=0.4 * MPa,
            fc90k=2.6 * MPa,
            fvk=4 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=11.5 * GPa,
            E90mean=0.38 * GPa,
            Gmean=0.72 * GPa,
            densityk=370 * kg_per_m3,
            density=450 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C30(cls, **kwargs):
        """
        Softwood C30.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=30 * MPa,
            ft0k=18 * MPa,
            fc0k=23 * MPa,
            ft90k=0.4 * MPa,
            fc90k=2.7 * MPa,
            fvk=4 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=12 * GPa,
            E90mean=0.4 * GPa,
            Gmean=0.75 * GPa,
            densityk=380 * kg_per_m3,
            density=460 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C35(cls, **kwargs):
        """
        Softwood C35.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=35 * MPa,
            ft0k=21 * MPa,
            fc0k=25 * MPa,
            ft90k=0.4 * MPa,
            fc90k=2.8 * MPa,
            fvk=4 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=13 * GPa,
            E90mean=0.43 * GPa,
            Gmean=0.81 * GPa,
            densityk=400 * kg_per_m3,
            density=480 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C40(cls, **kwargs):
        """
        Softwood C40.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=40 * MPa,
            ft0k=24 * MPa,
            fc0k=26 * MPa,
            ft90k=0.4 * MPa,
            fc90k=2.9 * MPa,
            fvk=4 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=14 * GPa,
            E90mean=0.47 * GPa,
            Gmean=0.88 * GPa,
            densityk=420 * kg_per_m3,
            density=500 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C45(cls, **kwargs):
        """
        Softwood C45.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=45 * MPa,
            ft0k=27 * MPa,
            fc0k=27 * MPa,
            ft90k=0.4 * MPa,
            fc90k=3.1 * MPa,
            fvk=4 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=15 * GPa,
            E90mean=0.5 * GPa,
            Gmean=0.94 * GPa,
            densityk=440 * kg_per_m3,
            density=520 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def C50(cls, **kwargs):
        """
        Softwood C50.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled softwood material.
        """

        return cls(
            fmk=50 * MPa,
            ft0k=30 * MPa,
            fc0k=29 * MPa,
            ft90k=0.4 * MPa,
            fc90k=3.2 * MPa,
            fvk=4 * MPa,
            vLT=vLT_softwood,
            vTT=vTT_softwood,
            E0mean=16 * GPa,
            E90mean=0.53 * GPa,
            Gmean=1 * GPa,
            densityk=460 * kg_per_m3,
            density=550 * kg_per_m3,
            **kwargs,
        )

    # --- Hardwood Classes (D-classes) ---
    @classmethod
    def D18(cls, **kwargs):
        """
        Hardwood D18.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """

        return cls(
            fmk=18 * MPa,
            ft0k=11 * MPa,
            fc0k=18 * MPa,
            ft90k=0.6 * MPa,
            fc90k=7.5 * MPa,
            fvk=3.4 * MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=9.5 * GPa,
            E90mean=0.63 * GPa,
            Gmean=0.59 * GPa,
            densityk=475 * kg_per_m3,
            density=570 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def D24(cls, **kwargs):
        """
        Hardwood D24.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """

        return cls(
            fmk=24 * MPa,
            ft0k=14 * MPa,
            fc0k=21 * MPa,
            ft90k=0.6 * MPa,
            fc90k=7.8 * MPa,
            fvk=4 * MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=10 * GPa,
            E90mean=0.67 * GPa,
            Gmean=0.62 * GPa,
            densityk=485 * kg_per_m3,
            density=580 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def D30(cls, **kwargs):
        """
        Hardwood D30.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        return cls(
            fmk=30 * MPa,
            ft0k=18 * MPa,
            fc0k=23 * MPa,
            ft90k=0.6 * MPa,
            fc90k=8 * MPa,
            fvk=4 * MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=11 * GPa,
            E90mean=0.73 * GPa,
            Gmean=0.69 * GPa,
            densityk=530 * kg_per_m3,
            density=640 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def D35(cls, **kwargs):
        """
        Hardwood D35.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        return cls(
            fmk=35 * MPa,
            ft0k=21 * MPa,
            fc0k=25 * MPa,
            ft90k=0.6 * MPa,
            fc90k=8.1 * MPa,
            fvk=4 * MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=12 * GPa,
            E90mean=0.8 * GPa,
            Gmean=0.75 * GPa,
            densityk=540 * kg_per_m3,
            density=650 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def D40(cls, **kwargs):
        """
        Hardwood D40.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        return cls(
            fmk=40 * MPa,
            ft0k=24 * MPa,
            fc0k=26 * MPa,
            ft90k=0.6 * MPa,
            fc90k=8.3 * MPa,
            fvk=4 * MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=13 * GPa,
            E90mean=0.86 * GPa,
            Gmean=0.81 * GPa,
            densityk=550 * kg_per_m3,
            density=660 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def D50(cls, **kwargs):
        """
        Hardwood D50.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        return cls(
            fmk=50 * MPa,
            ft0k=30 * MPa,
            fc0k=29 * MPa,
            ft90k=0.6 * MPa,
            fc90k=9.3 * MPa,
            fvk=4 * MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=14 * GPa,
            E90mean=0.93 * GPa,
            Gmean=0.88 * GPa,
            densityk=620 * kg_per_m3,
            density=750 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def D60(cls, **kwargs):
        """
        Hardwood D60.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """

        return cls(
            fmk=60 * MPa,
            ft0k=36 * MPa,
            fc0k=32 * MPa,
            ft90k=0.6 * MPa,
            fc90k=10.5 * MPa,
            fvk=4.5 * MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=17 * GPa,
            E90mean=1.13 * GPa,
            Gmean=1.06 * GPa,
            densityk=700 * kg_per_m3,
            density=840 * kg_per_m3,
            **kwargs,
        )

    @classmethod
    def D70(cls, **kwargs):
        """
        Hardwood D70.

        Returns
        -------
        :class:`compas_fea2.model.material.ElasticTimber`
            The precompiled hardwood material.
        """
        return cls(
            fmk=70 * MPa,
            ft0k=42 * MPa,
            fc0k=34 * MPa,
            ft90k=0.6 * MPa,
            fc90k=13.5 * MPa,
            fvk=5 * MPa,
            vLT=vLT_hardwood,
            vTT=vTT_hardwood,
            E0mean=20 * GPa,
            E90mean=1.33 * GPa,
            Gmean=1.25 * GPa,
            densityk=900 * kg_per_m3,
            density=1080 * kg_per_m3,
            **kwargs,
        )
