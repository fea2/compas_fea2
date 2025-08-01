import unittest
from compas_fea2.model import Concrete
from compas_fea2.units import units

u = units("SI")

# Concrete properties based on Eurocode 2 (EN 1992-1-1:2004)
concrete_properties = {
    "C12/15": {"fck": 12 * u.MPa, "fck_cube": 15 * u.MPa, "fcm": 20 * u.MPa, "fctm": 1.57 * u.MPa, "Ecm": 27.085 * u.GPa},
    "C16/20": {"fck": 16 * u.MPa, "fck_cube": 20 * u.MPa, "fcm": 24 * u.MPa, "fctm": 1.90 * u.MPa, "Ecm": 28.608 * u.GPa},
    "C20/25": {"fck": 20 * u.MPa, "fck_cube": 25 * u.MPa, "fcm": 28 * u.MPa, "fctm": 2.21 * u.MPa, "Ecm": 29.962 * u.GPa},
    "C25/30": {"fck": 25 * u.MPa, "fck_cube": 30 * u.MPa, "fcm": 33 * u.MPa, "fctm": 2.56 * u.MPa, "Ecm": 31.476 * u.GPa},
    "C30/37": {"fck": 30 * u.MPa, "fck_cube": 37 * u.MPa, "fcm": 38 * u.MPa, "fctm": 2.90 * u.MPa, "Ecm": 32.837 * u.GPa},
    "C35/45": {"fck": 35 * u.MPa, "fck_cube": 45 * u.MPa, "fcm": 43 * u.MPa, "fctm": 3.21 * u.MPa, "Ecm": 34.077 * u.GPa},
    "C40/50": {"fck": 40 * u.MPa, "fck_cube": 50 * u.MPa, "fcm": 48 * u.MPa, "fctm": 3.51 * u.MPa, "Ecm": 35.220 * u.GPa},
    "C45/55": {"fck": 45 * u.MPa, "fck_cube": 55 * u.MPa, "fcm": 53 * u.MPa, "fctm": 3.80 * u.MPa, "Ecm": 36.283 * u.GPa},
    "C50/60": {"fck": 50 * u.MPa, "fck_cube": 60 * u.MPa, "fcm": 58 * u.MPa, "fctm": 4.07 * u.MPa, "Ecm": 37.278 * u.GPa},
    "C55/67": {"fck": 55 * u.MPa, "fck_cube": 67 * u.MPa, "fcm": 63 * u.MPa, "fctm": 4.21 * u.MPa, "Ecm": 38.214 * u.GPa},
    "C60/75": {"fck": 60 * u.MPa, "fck_cube": 75 * u.MPa, "fcm": 68 * u.MPa, "fctm": 4.35 * u.MPa, "Ecm": 39.100 * u.GPa},
    "C70/85": {"fck": 70 * u.MPa, "fck_cube": 85 * u.MPa, "fcm": 78 * u.MPa, "fctm": 4.61 * u.MPa, "Ecm": 40.743 * u.GPa},
    "C80/95": {"fck": 80 * u.MPa, "fck_cube": 95 * u.MPa, "fcm": 88 * u.MPa, "fctm": 4.84 * u.MPa, "Ecm": 42.244 * u.GPa},
    "C90/105": {"fck": 90 * u.MPa, "fck_cube": 105 * u.MPa, "fcm": 98 * u.MPa, "fctm": 5.04 * u.MPa, "Ecm": 43.631 * u.GPa},
}


class TestConcrete(unittest.TestCase):
    def test_C20_25(self):
        properties = concrete_properties["C20/25"]
        c20 = Concrete.C20_25()
        self.assertEqual(c20.fck, properties["fck"].to_base_units().magnitude)
        self.assertEqual(c20.fcm, properties["fcm"].to_base_units().magnitude)
        self.assertAlmostEqual(c20.E / 10**9, properties["Ecm"].to_base_units().magnitude / 10**9, places=2)
