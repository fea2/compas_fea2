import unittest
from compas.geometry import Frame, Vector
from compas_fea2.model.bcs import FixedBC, PinnedBC, RollerBCX, MechanicalBC


class TestBCs(unittest.TestCase):
    def test_fixed_bc(self):
        bc = FixedBC()
        self.assertTrue(bc.x)
        self.assertTrue(bc.y)
        self.assertTrue(bc.z)
        self.assertTrue(bc.xx)
        self.assertTrue(bc.yy)
        self.assertTrue(bc.zz)

    def test_pinned_bc(self):
        bc = PinnedBC()
        self.assertTrue(bc.x)
        self.assertTrue(bc.y)
        self.assertTrue(bc.z)
        self.assertFalse(bc.xx)
        self.assertFalse(bc.yy)
        self.assertFalse(bc.zz)

    def test_roller_bc_x(self):
        bc = RollerBCX()
        self.assertFalse(bc.x)
        self.assertTrue(bc.y)
        self.assertTrue(bc.z)
        self.assertFalse(bc.xx)
        self.assertFalse(bc.yy)
        self.assertFalse(bc.zz)

    def test_global_components_axis_aligned(self):
        bc = FixedBC()  # axis aligned (GLOBAL)
        self.assertTrue(bc.X)
        self.assertTrue(bc.Y)
        self.assertTrue(bc.Z)
        self.assertTrue(bc.XX)
        self.assertTrue(bc.YY)
        self.assertTrue(bc.ZZ)

    def test_rotated_frame_mapping_single_local(self):
        # 90 deg rotation about Z -> local x -> global Y, local y -> -global X
        frame = Frame([0,0,0], Vector(0,1,0), Vector(-1,0,0))
        bc = MechanicalBC(x=True, y=False, z=False, frame=frame)
        # Local x restrained means global Y restrained; global X not (needs local y)
        self.assertTrue(bc.X is False)  # global X requires local y restraint
        self.assertTrue(bc.Y is True)   # global Y aligns with local x
        self.assertTrue(bc.Z is False)
        # Rotations default False
        self.assertFalse(bc.XX)
        self.assertFalse(bc.YY)
        self.assertFalse(bc.ZZ)
        # Constraint equations: one equation for local x -> UX,UY,UZ coefficients = direction cosines of local x
        eqs = bc.global_constraint_equations()
        self.assertEqual(len(eqs), 1)
        coeffs, rhs = eqs[0]
        self.assertAlmostEqual(rhs, 0.0)
        # local x direction is (0,1,0)
        self.assertAlmostEqual(coeffs['UX'], 0.0)
        self.assertAlmostEqual(coeffs['UY'], 1.0)
        self.assertAlmostEqual(coeffs['UZ'], 0.0)

    def test_rotated_frame_mapping_combined(self):
        # 45 deg rotation about Z
        import math
        ang = math.radians(45)
        frame = Frame([0,0,0], Vector(math.cos(ang), math.sin(ang), 0), Vector(-math.sin(ang), math.cos(ang), 0))
        # Only restrain local x -> global DOFs partially constrained: both X and Y need both local x,y to be True to guarantee restraint
        bc = MechanicalBC(x=True, y=False, frame=frame)
        self.assertFalse(bc.X)  # because local y not restrained
        self.assertFalse(bc.Y)
        # Now restrain both
        bc2 = MechanicalBC(x=True, y=True, frame=frame)
        self.assertTrue(bc2.X)
        self.assertTrue(bc2.Y)
        # Equations: two for local x and y
        eqs = bc2.global_constraint_equations()
        self.assertEqual(len(eqs), 2)
        # Check orthogonality of coefficient vectors
        v1 = eqs[0][0]
        v2 = eqs[1][0]
        dot = v1['UX']*v2['UX'] + v1['UY']*v2['UY'] + v1['UZ']*v2['UZ']
        self.assertAlmostEqual(dot, 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
