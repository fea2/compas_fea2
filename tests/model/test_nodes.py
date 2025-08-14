import unittest
from compas_fea2.model.nodes import Node
from compas.geometry import Point


class TestNode(unittest.TestCase):
    def test_initialization(self):
        node = Node([1, 2, 3])
        self.assertEqual(node.xyz, [1, 2, 3])
        self.assertEqual(node.mass, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.assertIsNone(node.t0)

    def test_mass_setter(self):
        node = Node([1, 2, 3], mass=[10, 10, 10, 10, 10, 10])
        self.assertEqual(node.mass, [10, 10, 10, 10, 10, 10])
        node.mass = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
        self.assertEqual(node.mass, [5, 5, 5, 5, 5, 5])

    def test_temperature_setter(self):
        node = Node([1, 2, 3], temperature=100)
        self.assertEqual(node.t0, 100)
        node.t0 = 200
        self.assertEqual(node.t0, 200)

    def test_gkey(self):
        node = Node([1, 2, 3])
        self.assertIsNotNone(node.gkey)

    def test_from_compas_point(self):
        point = Point(1, 2, 3)
        node = Node.from_compas_point(point)
        self.assertEqual(node.xyz, [1, 2, 3])

    def test_copy_node(self):
        node = Node([1, 2, 3], mass=[10, 10, 10], temperature=100)
        node_copy = node.copy()

        # Ensure the copied node is independent of the original
        self.assertNotEqual(node.uid, node_copy.uid)  # Different UID
        self.assertNotEqual(node.name, node_copy.name)  # Different name
        self.assertEqual(node.xyz, node_copy.xyz)  # Same coordinates
        self.assertEqual(node.mass, node_copy.mass)  # Same mass
        self.assertEqual(node.t0, node_copy.t0)  # Same temperature

        # Test with duplicate=True
        node_duplicate = node.copy(duplicate=True)
        self.assertEqual(node.uid, node_duplicate.uid)  # Same UID
        self.assertEqual(node.name, node_duplicate.name)  # Same name
        self.assertEqual(node.xyz, node_duplicate.xyz)  # Same coordinates
        self.assertEqual(node.mass, node_duplicate.mass)  # Same mass
        self.assertEqual(node.t0, node_duplicate.t0)  # Same temperature


if __name__ == "__main__":
    unittest.main()
