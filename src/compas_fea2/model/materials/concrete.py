import math
from typing import Optional
from uuid import UUID

from matplotlib import pyplot as plt
from compas_fea2.base import Registry

from .material import _Material


class Concrete(_Material):
    """Elastic and plastic-cracking Eurocode-based concrete material.

    Warning
    -------
    EXPERIMENTAL: THIS MATERIAL IS BASED ON THE EUROCODE 2 AND
    CAN BE USED ONLY IN A MODEL DEFINED INTHE SI UNIT SYSTEM!


    Parameters
    ----------
    fck : float
        Characteristic (5%) 28-day cylinder strength [MPa].
    v : float, optional
        Poisson's ratio v [-].
    fr : list, optional
        Failure ratios.
    density : float, optional
        Density of the concrete material [kg/m^3].
    name : str, optional
        Name of the material.

    Attributes
    ----------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    G : float
        Shear modulus G.
    fck : float
        Characteristic (5%) 28-day cylinder strength.
    fr : list
        Failure ratios.
    tension : dict
        Parameters for modeling the tension side of the stress-strain curve.
    compression : dict
        Parameters for modeling the compression side of the stress-strain curve.

    Notes
    -----
    The concrete model is based on Eurocode 2 up to fck=90 MPa.
    """

    def __init__(self, fck, density=None, **kwargs):
        super().__init__(density=density, **kwargs)
        self.v = 0.17

        # (Eurocode 2, Table 3.1) --- All calculations are done in MPa!
        fcm = fck + 8.0  # MPa
        self.fcm = fcm * 1e6  # Pa

        # Secant modulus of elasticity [MPa]
        Ecm_mpa = 22000 * (fcm / 10.0) ** 0.3
        self.E = Ecm_mpa * 1e6  # Store in Pa

        # Strain at peak compressive stress [-]
        ec1 = 0.001 * min(0.7 * fcm**0.31, 2.8)

        # Ultimate compressive strain [-]
        if fck <= 50:
            ecu1 = 0.0035
        else:
            ecu1 = 0.001 * (2.8 + 27 * ((98 - fcm) / 100.0) ** 4)

        # Mean tensile strength [MPa]
        if fck <= 50:
            fctm_mpa = 0.30 * fck ** (2 / 3)
        else:
            fctm_mpa = 2.12 * math.log(1 + fcm / 10.0)
        self.fctm = fctm_mpa * 1e6  # Store in Pa

        # Check: EN 1992-1-1, 3.1.5
        k = 1.05 * Ecm_mpa * ec1 / fcm

        num_points = 100  # Number of points on the curve
        strains_c = [i * ecu1 / num_points for i in range(num_points + 1)]
        stresses_c_mpa = []

        for e_c in strains_c:
            if e_c == 0:
                stresses_c_mpa.append(0.0)
                continue
            eta = e_c / ec1
            stress = fcm * (k * eta - eta**2) / (1 + (k - 2) * eta)
            stresses_c_mpa.append(stress)

        # Store compression curve in Pascals
        self.ec = strains_c
        self.fc = [s * 1e6 for s in stresses_c_mpa]

        e_t_peak = self.fctm / self.E
        e_t_ult = 2 * e_t_peak

        self.et = [0.0, e_t_peak, e_t_ult]
        self.ft = [0.0, self.fctm, 0.0]

        self.fck = fck * 1e6  # Store in Pa
        self.fr = [1.16, self.fctm / self.fcm]  # Failure ratios
        self.fcd = 0.85 * self.fck / 1.5  # Design compressive strength [Pa]

        self.tension = {"f": self.ft, "e": self.et}
        self.compression = {"f": self.fc, "e": self.ec}

        if len(self.fc) > 1 and self.fc[1] == 0:
            raise ValueError("fc[1] must be non-zero to calculate E.")
        if len(self.ec) > 1 and self.ec[1] == 0:
            raise ValueError("ec[1] must be non-zero for correct calculations.")

        self.tension = {"f": self.ft, "e": self.et}
        self.compression = {"f": self.fc[1:], "e": self.ec}

    @property
    def G(self):
        return 0.5 * self.E / (1 + self.v)

    def plot_stress_strain_curve(self):
        """
        Generates and displays a plot of the material's stress-strain curve.

        Requires the 'matplotlib' library to be installed.
        """
        # Convert stresses to MPa for plotting
        stresses_c_mpa = [s / 1e6 for s in self.fc]
        stresses_t_mpa = [s / 1e6 for s in self.ft]

        # Make compressive strains negative for conventional plotting
        strains_c_negative = [-e for e in self.ec]

        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot compression curve
        ax.plot(strains_c_negative, stresses_c_mpa, label="Compression", color="b")

        # Plot tension curve
        ax.plot(self.et, stresses_t_mpa, label="Tension", color="r")

        # Formatting
        ax.set_xlabel("Strain [-]")
        ax.set_ylabel("Stress [MPa]")
        ax.set_title(f"Stress-Strain Curve for {self.name} (fck={self.fck / 1e6:.0f} MPa)")
        ax.legend()
        ax.grid(True, which="both", linestyle="--", linewidth=0.5)
        ax.axhline(0, color="black", linewidth=0.75)
        ax.axvline(0, color="black", linewidth=0.75)

        plt.show()

    def __str__(self):
        return """
Concrete Material
-----------------
name    : {}
density : {}

E   : {}
v   : {}
G   : {}
fck : {}
fr  : {}
""".format(
            self.name, self.density, self.E, self.v, self.G, self.fck, self.fr
        )

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "fck": self.fck,
                "E": self.E,
                "v": self.v,
                "fr": self.fr,
                "tension": self.tension,
                "compression": self.compression,
            }
        )
        return data

    @classmethod
    def __from_data__(cls, data, registry: Optional[Registry] = None):
        if registry is None:
            registry = Registry()

        uid = data.get("uid")
        if uid and registry.get(uid):
            return registry.get(uid)

        material = cls(
            fck=data.get("fck"),
            density=data.get("density"),
            name=data.get("name"),
        )
        material._uid = UUID(uid) if uid else None

        if uid:
            registry.add(uid, material)

        return material

    @classmethod
    def C20_25(cls, **kwargs):
        return cls(fck=20, E=30_000, v=0.17, density=2400, name="C20/25", **kwargs)


class ConcreteSmearedCrack(_Material):
    """Elastic and plastic, cracking concrete material.

    Parameters
    ----------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    fc : list
        Plastic stress data in compression.
    ec : list
        Plastic strain data in compression.
    ft : list
        Plastic stress data in tension.
    et : list
        Plastic strain data in tension.
    fr : list, optional
        Failure ratios.
    density : float, optional
        Density of the concrete material [kg/m^3].
    name : str, optional
        Name of the material.

    Attributes
    ----------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    G : float
        Shear modulus G.
    fc : list
        Plastic stress data in compression.
    ec : list
        Plastic strain data in compression.
    ft : list
        Plastic stress data in tension.
    et : list
        Plastic strain data in tension.
    fr : list
        Failure ratios.
    tension : dict
        Parameters for modelling the tension side of the stress-strain curve.
    compression : dict
        Parameters for modelling the compression side of the stress-strain curve.
    """

    def __init__(self, *, E, v, density, fc, ec, ft, et, fr=[1.16, 0.0836], **kwargs):
        super().__init__(density=density, **kwargs)

        self.E = E
        self.v = v
        self.fc = fc
        self.ec = ec
        self.ft = ft
        self.et = et
        self.fr = fr
        # are these necessary if we have the above?
        self.tension = {"f": ft, "e": et}
        self.compression = {"f": fc, "e": ec}

    @property
    def G(self):
        return 0.5 * self.E / (1 + self.v)

    def __str__(self):
        return """
Concrete Material
-----------------
name    : {}
density : {}

E  : {}
v  : {}
G  : {}
fc : {}
ec : {}
ft : {}
et : {}
fr : {}
""".format(
            self.name, self.density, self.E, self.v, self.G, self.fc, self.ec, self.ft, self.et, self.fr
        )

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "class": self.__class__.__name__,
                "E": self.E,
                "v": self.v,
                "fc": self.fc,
                "ec": self.ec,
                "ft": self.ft,
                "et": self.et,
                "fr": self.fr,
                "tension": self.tension,
                "compression": self.compression,
            }
        )
        return data

    @classmethod
    def __from_data__(cls, data):
        return cls(
            E=data["E"],
            v=data["v"],
            density=data["density"],
            fc=data["fc"],
            ec=data["ec"],
            ft=data["ft"],
            et=data["et"],
            fr=data["fr"],
            name=data["name"],
        )


class ConcreteDamagedPlasticity(_Material):
    """Damaged plasticity isotropic and homogeneous material.

    Parameters
    ----------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    damage : list
        Damage parameters.
    hardening : list
        Compression hardening parameters.
    stiffening : list
        Tension stiffening parameters.
    density : float, optional
        Density of the concrete material [kg/m^3].
    name : str, optional
        Name of the material.

    Attributes
    ----------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    G : float
        Shear modulus G.
    damage : list
        Damage parameters.
    hardening : list
        Compression hardening parameters.
    stiffening : list
        Tension stiffening parameters.
    """

    def __init__(self, *, E, v, density, damage, hardening, stiffening, **kwargs):
        super().__init__(density=density, **kwargs)

        self.E = E
        self.v = v

        # TODO would make sense to validate these inputs
        self.damage = damage
        self.hardening = hardening
        self.stiffening = stiffening

    @property
    def G(self):
        return 0.5 * self.E / (1 + self.v)

    @property
    def __data__(self):
        data = super().__data__
        data.update(
            {
                "class": self.__class__.__name__,
                "E": self.E,
                "v": self.v,
                "damage": self.damage,
                "hardening": self.hardening,
                "stiffening": self.stiffening,
            }
        )
        return data

    @classmethod
    def __from_data__(cls, data):
        return cls(
            E=data["E"],
            v=data["v"],
            density=data["density"],
            damage=data["damage"],
            hardening=data["hardening"],
            stiffening=data["stiffening"],
            name=data["name"],
        )
