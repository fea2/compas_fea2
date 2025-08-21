import unittest
from compas_fea2.problem.combinations import LoadFieldsCombination
from compas_fea2.problem import StaticStep, ForceField
from compas_fea2.model import Node
from compas_fea2.problem.loads import VectorLoad

class TestLoadFieldsCombination(unittest.TestCase):
    def setUp(self):
        self.n1 = Node(name="node1", xyz=[0.0, 0.0, 0.0])
        self.n2 = Node(name="node2", xyz=[1.0, 1.0, 1.0])
        self.v1 = VectorLoad(name="load1", x=1.0, y=2.0, z=0.0, amplitude=None)
        self.v2 = VectorLoad(name="load2", x=0.0, y=0.0, z=3.0, amplitude=None)

    def test_serialization_roundtrip(self):
        cdict = {
            "G": 1.35,
            "Q_IMP": {"primary": 1.5, "secondary": 1.05, "default": 0.0},
        }
        comb = LoadFieldsCombination(case_factor_dict=cdict)
        data = comb.__data__
        self.assertIn("case_factor_dict", data)
        comb2 = LoadFieldsCombination.__from_data__(data)  # type: ignore[misc]
        self.assertIsInstance(comb2, LoadFieldsCombination)
        self.assertEqual(comb2.case_factor_dict, comb.case_factor_dict)

    def test_combine_fields_scalar(self):
        ff1 = ForceField(name="force_field_1", loads=[self.v1], distribution=[self.n1], load_case="G")
        ff2 = ForceField(name="force_field_2", loads=[self.v2], distribution=[self.n2], load_case="Q_IMP")
        comb = LoadFieldsCombination(case_factor_dict={"G": 1.35, "Q_IMP": 1.5})
        group = comb.combine_fields([ff1, ff2])
        self.assertEqual(len(group), 2)
        found_g = found_qimp = False
        for field in group:
            if field.load_case == "G":
                self.assertAlmostEqual(field.loads[0].x, 1.0 * 1.35)
                found_g = True
            elif field.load_case == "Q_IMP":
                self.assertAlmostEqual(field.loads[0].z, 3.0 * 1.5)
                found_qimp = True
        self.assertTrue(found_g)
        self.assertTrue(found_qimp)

    def test_ec_scalar_factory(self):
        comb = LoadFieldsCombination.ec_uls_persistent()
        factors = comb.case_factor_dict
        self.assertIn("G", factors)
        self.assertIn("Q", factors)
        self.assertIn("Q_ROOF", factors)
        self.assertIn("S", factors)
        self.assertIn("W", factors)
        self.assertIn("T", factors)

    def test_ec_per_role_factory_values(self):
        comb = LoadFieldsCombination.ec_uls_persistent()
        f = comb.case_factor_dict
        self.assertIn("G", f)
        self.assertIsInstance(f["G"], dict)
        self.assertIn("Q", f)
        self.assertIsInstance(f["Q"], dict)
        lead_map = f["Q"]
        if isinstance(lead_map, dict):
            self.assertAlmostEqual(float(lead_map.get("primary", 0.0)), 1.5)
        if "W" in f:
            self.assertIsInstance(f["W"], dict)

    def test_combine_with_ec_case(self):
        ff = ForceField(name="force_field", loads=[self.v1], distribution=[self.n1], load_case="Q")
        # ff.combination_rank = 1
        comb = LoadFieldsCombination.ec_sls_characteristic()
        group = comb.combine_fields([ff])
        members = list(getattr(group, "members", []))
        self.assertEqual(len(members), 1)
        # Find by load_case
        found = False
        for field in members:
            if field.load_case == "Q":
                self.assertAlmostEqual(field.loads[0].x, 1.0 * 1.0)
                found = True
        self.assertTrue(found)

    def test_asce_factory_basic(self):
        comb = LoadFieldsCombination.asce7_lrfd_basic()
        f = comb.case_factor_dict
        self.assertEqual(f.get("LL"), {'primary': 1.6, 'secondary': 1.6, 'tertiary': 1.6, 'default': 1.6})
        self.assertEqual(f.get("Lr"), {'primary': 0.5, 'secondary': 0.5, 'tertiary': 0.5, 'default': 0.5})
        self.assertEqual(f.get("S"), {'primary': 0.5, 'secondary': 0.5, 'tertiary': 0.5, 'default': 0.5})
        self.assertEqual(f.get("R"), {'primary': 0.5, 'secondary': 0.5, 'tertiary': 0.5, 'default': 0.5})
        self.assertTrue(any(k in f for k in ("D", "DL", "SDL")))

    def test_combine_for_step(self):
        ff = ForceField(name="force_field", loads=[self.v1], distribution=[self.n1], load_case="X")
        step = StaticStep(name="static_step_1")
        step.add_field(ff)
        comb = LoadFieldsCombination(case_factor_dict={"X": 2.0})
        group = comb.combine_for_step(step)
        members = list(getattr(group, "members", []))
        self.assertEqual(len(members), 1)
        found = False
        for field in members:
            if field.load_case == "X":
                self.assertEqual(field.loads[0].x, 1.0 * 2.0)
                found = True
        self.assertTrue(found)

if __name__ == "__main__":
    unittest.main()
