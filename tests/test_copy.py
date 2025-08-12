import os
import json
import tempfile
import unittest
from compas.geometry import Translation  # type: ignore

from compas_fea2.model.model import Model  # explicit import
from compas_fea2.model.parts import Part  # type: ignore
from compas_fea2.model.materials.steel import Steel  # type: ignore
from compas_fea2.model.sections import GenericBeamSection  # type: ignore


class TestFEADataCopy(unittest.TestCase):
    
    def test_copy_guid_and_name(self):
        m1 = Model(name="orig")
        m2 = m1.copy()
        self.assertNotEqual(m1, m2)
        self.assertNotEqual(m1._uid, m2.uid)
        self.assertNotEqual(m1.name, m2.name)
        m3 = m1.copy(duplicate=True)  # type: ignore
        self.assertNotEqual(m1, m3)
        self.assertEqual(m1.name, m3.name)
        self.assertEqual(m1._uid, m3.uid)

    def test_copy_without_duplicate(self):
        m1 = Model(name="orig")
        m2 = m1.copy()  # type: ignore
        self.assertIsInstance(m2, Model)
        self.assertNotEqual(m1, m2)
        self.assertNotEqual(m1._uid, m2.uid)
        self.assertNotEqual(m1.name, m2.name)

    def test_copy_with_duplicate(self):
        m1 = Model(name="orig")
        m2 = m1.copy(duplicate=True)  # type: ignore
        self.assertIsInstance(m2, Model)
        self.assertNotEqual(m1, m2)
        self.assertEqual(m1._uid, m2.uid)
        self.assertEqual(m1.name, m2.name)
        

    def test_duplicate_nested_object(self):
        m = Model(name="test")
        part = m.add_part(Part(name="p1"))
        
        m2 = m.copy(duplicate=True)
        self.assertEqual(m2.parts[0].name, part.name)
        self.assertEqual(m2.parts[0].uid, part.uid)

    def test_copy_nested_object(self):
        m = Model(name="test")
        part = m.add_part(Part(name="p1"))
        m2 = m.copy()
        self.assertNotEqual(m2.parts[0].name, part.name)
        self.assertNotEqual(m2.parts[0].uid, part.uid)


class TestModelPartCopy(unittest.TestCase):
    def setUp(self):
        self.model = Model(name="test")
        self.part = self.model.add_part(Part(name="p1"))

    def test_copy_part(self):
        # translation by vector [1,1,1]
        t = Translation.from_vector([1, 1, 1])
        p2 = self.model.copy_part(self.part, t)
        self.assertIn(p2, self.model.parts)
        # ensure objects differ
        self.assertNotEqual(self.part, p2)


class TestModelMaterialsSections(unittest.TestCase):
    def setUp(self):
        self.model = Model()

    def test_add_materials(self):
        mat = Steel.S355()  # type: ignore
        returned = self.model.add_material(mat)  # type: ignore
        self.assertIn(mat, self.model.materials)  # type: ignore
        self.assertEqual(returned, mat)

    def test_add_sections(self):
        mat = Steel.S355()  # type: ignore
        sec = GenericBeamSection(
            material=mat,
            area=0.1,
            Ixx=0.01,
            Iyy=0.01,
            J=0.01,
            Ixy=0.0,
            Ixz=0.0,
            Iyz=0.0,
            shear_area_y=0.0,
            shear_area_z=0.0,
            torsional_constant=0.0,
            A=0.1,
            Avx=0.05,
            Avy=0.05,
            g0=0.0,
            gw=0.0,
            name="test_section",
        )
        returned = self.model.add_section(sec)  # type: ignore
        self.assertIn(sec, self.model.sections)  # type: ignore
        self.assertEqual(returned, sec)


class TestToJson(unittest.TestCase):
    def test_to_json_writes_file(self):
        m = Model(description="desc", author="auth")
        tmp = tempfile.mkdtemp()
        fpath = os.path.join(tmp, "model.json")
        m.to_json(fpath)  # type: ignore
        self.assertTrue(os.path.exists(fpath))
        data = json.load(open(fpath))
        # data keys should include 'description' and 'author'
        self.assertEqual(data.get("description"), "desc")
        self.assertEqual(data.get("author"), "auth")
