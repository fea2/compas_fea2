import unittest
from compas_fea2.model.ics import InitialTemperature, InitialStress


class TestInitialTemperature(unittest.TestCase):
    def test_initialization(self):
        ic = InitialTemperature(T0=100)
        self.assertEqual(ic.T0, 100)

    def test_temperature_setter(self):
        ic = InitialTemperature(T0=100)
        ic.T0 = 200
        self.assertEqual(ic.T0, 200)


class TestInitialStress(unittest.TestCase):
    def test_initialization(self):
        ic = InitialStress(stress=(10, 20, 30))
        self.assertEqual(ic.stress, (10, 20, 30))

    def test_stress_setter(self):
        ic = InitialStress(stress=(10, 20, 30))
        ic.stress = (40, 50, 60)
        self.assertEqual(ic.stress, (40, 50, 60))


if __name__ == "__main__":
    unittest.main()
