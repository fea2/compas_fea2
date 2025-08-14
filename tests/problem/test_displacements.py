import unittest
from compas.geometry import Frame

from compas_fea2.problem.displacements import GeneralDisplacement


class TestGeneralDisplacement(unittest.TestCase):
    def test_general_displacement_global_mapping_rotated_frame(self):
        # Local x aligned to global +Y, local y aligned to global -X
        frame = Frame((0, 0, 0), (0, 1, 0), (-1, 0, 0))
        bc = GeneralDisplacement(x=True, y=False, z=False, frame=frame)
        self.assertFalse(bc.X)  # global X not fully restrained
        self.assertTrue(bc.Y)   # global Y aligned with local x
        self.assertFalse(bc.Z)

    def test_general_displacement_addition_and_frame_mismatch(self):
        frame = Frame((0, 0, 0), (1, 0, 0), (0, 1, 0))
        a = GeneralDisplacement(x=True, frame=frame)
        b = GeneralDisplacement(y=True, frame=frame)
        c = a + b
        self.assertTrue(c.x)
        self.assertTrue(c.y)
        self.assertFalse(c.z)

        frame2 = Frame((0, 0, 0), (0, 1, 0), (-1, 0, 0))
        d = GeneralDisplacement(z=True, frame=frame2)
        with self.assertRaises(ValueError):
            _ = a + d

    def test_general_displacement_global_constraint_equations(self):
        frame = Frame((0, 0, 0), (0, 1, 0), (-1, 0, 0))
        bc = GeneralDisplacement(x=True, frame=frame)
        eqs = bc.global_constraint_equations()
        # Only one equation from local x restraint; it aligns with global +Y
        self.assertEqual(len(eqs), 1)
        coeffs, rhs = eqs[0]
        self.assertEqual(rhs, 0.0)
        self.assertEqual(coeffs, {"UX": 0.0, "UY": 1.0, "UZ": 0.0})


if __name__ == "__main__":
    unittest.main()
