import unittest
from compas_fea2.model.sections import RectangularSection, CircularSection, ISection
from compas_fea2.model.materials.steel import Steel


class TestSections(unittest.TestCase):
    def setUp(self):
        self.material = Steel.S355()

    def test_rectangular_section(self):
        section = RectangularSection(w=100, h=50, material=self.material)
        self.assertIsNotNone(section.shape)
        self.assertEqual(getattr(section.shape, 'w', None), 100)
        self.assertEqual(getattr(section.shape, 'h', None), 50)
        self.assertAlmostEqual(section.A, 5000)
        self.assertAlmostEqual(section.Ixx, (100 * 50 ** 3) / 12)
        self.assertAlmostEqual(section.Iyy, (50 * 100 ** 3) / 12)
        self.assertEqual(section.Ixy, 0)
        self.assertEqual(section.material, self.material)

    def test_circular_section(self):
        section = CircularSection(r=10, material=self.material)
        self.assertIsNotNone(section.shape)
        self.assertEqual(getattr(section.shape, 'radius', None), 10)
        self.assertAlmostEqual(section.A, 314.159265, places=1)
        self.assertAlmostEqual(section.Ixx, (3.14 * 10 ** 4) / 4, delta=5)
        self.assertAlmostEqual(section.Iyy, (3.14 * 10 ** 4) / 4, delta=5)
        self.assertAlmostEqual(section.Ixy, 0, delta=5)
        self.assertEqual(section.material, self.material)

    def test_isection(self):
        section = ISection(w=100, h=200, tw=10, ttf=20, tbf=20, material=self.material)
        self.assertIsNotNone(section.shape)
        self.assertEqual(getattr(section.shape, 'w', None), 100)
        self.assertEqual(getattr(section.shape, 'h', None), 200)
        self.assertEqual(getattr(section.shape, 'tw', None), 10)
        self.assertEqual(getattr(section.shape, 'tbf', None), 20)
        self.assertEqual(getattr(section.shape, 'ttf', None), 20)
        # For a symmetric I-section, check area and Ixx/Iyy with known values
        flange_area = 100 * 20
        web_area = (200 - 2 * 20) * 10
        expected_A = 2 * flange_area + web_area
        self.assertAlmostEqual(section.A, expected_A)
        self.assertTrue(section.Ixx > 0)
        self.assertTrue(section.Iyy > 0)
        self.assertEqual(section.Ixy, 0)
        self.assertEqual(section.material, self.material)


if __name__ == "__main__":
    unittest.main()
