import os
import json
import tempfile
import unittest
from compas.geometry import Transformation, Translation  # type: ignore

from compas_fea2.base import FEAData
from compas_fea2.model.model import Model  # explicit import
from compas_fea2.model.parts import Part  # type: ignore


class TestFEADataCopy(unittest.TestCase):

    def test_copy_guid_and_name(self):
        m1 = Model(name="orig")
        # default copy does not preserve guid or name
        m2 = m1.copy()  # type: ignore
        self.assertNotEqual(m1.uid, m2.uid)
        self.assertNotEqual(m1.name, m2.name)
        # preserve guid and name
        m3 = m1.copy(copy_guid=True, copy_name=True)  # type: ignore
        self.assertEqual(m1.uid, m3.uid)
        self.assertEqual(m1.name, m3.name)


class TestModelPartCopy(unittest.TestCase):

    def setUp(self):
        self.model = Model(name="test")
        self.part = self.model.add_part(Part(name="p1"))  # type: ignore

    def test_copy_part(self):
        # translation by vector [1,1,1]
        t = Transformation.from_translation([1, 1, 1])  # type: ignore
        p2 = self.model.copy_part(self.part, t)  # type: ignore
        self.assertIn(p2, self.model.parts)  # type: ignore
        # ensure objects differ
        self.assertNotEqual(self.part, p2)

    def test_array_parts(self):
        t = Transformation.from_translation([2, 0, 0])  # type: ignore
        arr = self.model.array_parts([self.part], 3, t)  # type: ignore
        self.assertEqual(len(arr), 3)
        # check they are distinct
        self.assertEqual(len(set(arr)), 3)


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
        sec = GenericBeamSection(material=mat, area=0.1, Ixx=0.01, Iyy=0.01, J=0.01)  # type: ignore
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