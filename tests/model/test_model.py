import unittest
from compas_fea2.model.model import Model
from compas_fea2.model.parts import Part
from compas_fea2.problem import Problem


class TestModel(unittest.TestCase):
    def test_add_part(self):
        model = Model()
        part = Part()
        model.add_part(part)
        self.assertIn(part, model.parts)

    def test_find_part_by_name(self):
        model = Model()
        part = Part(name="test_part")
        model.add_part(part)
        found_part = model.find_part_by_name("test_part")
        self.assertEqual(found_part, part)

    def test_add_problem(self):
        model = Model()
        problem = Problem()  # Replace with actual problem class
        model.add_problem(problem)
        self.assertIn(problem, model.problems)

    def test_model_serialization(self):
        model = Model(description="Test Model", author="Author")
        data = model.__data__
        self.assertEqual(data["description"], "Test Model")
        self.assertEqual(data["author"], "Author")

    def test_model_deserialization(self):
        data = {
            "class": "Model",
            "description": "Test Model",
            "author": "Author",
            "parts": [],
            "materials": [],
            "sections": [],
            "interfaces": [],
            "interactions": [],
            "constraints": [],
            "connectors": [],
            "problems": [],
            "path": None,
            "constants": {"g": 9.81},
            "name": "TestModel",
        }
        model = Model.__from_data__(data)
        self.assertEqual(model.description, "Test Model")
        self.assertEqual(model.author, "Author")


if __name__ == "__main__":
    unittest.main()
