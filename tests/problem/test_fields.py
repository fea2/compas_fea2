import unittest
from unittest.mock import patch
from typing import Any, cast

from compas_fea2.problem.fields import TemperatureField, ForceField, _ElementScalarField
from compas_fea2.problem.loads import VectorLoad


class DummyNode:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"DummyNode({self.name})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DummyNode):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


# Lightweight stand-in for NodesGroup to satisfy isinstance checks in fields.py
class DummyNodesGroup(list):
    def __init__(self, it):
        super().__init__(it)


def make_nodes(names):
    return [DummyNode(n) for n in names]


class TestProblemFields(unittest.TestCase):
    def test_temperature_field_addition_basic(self):
        # Patch NodesGroup to a simple list-like class to avoid model dependencies
        with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
            nodes = make_nodes(["n1", "n2"])
            f1 = TemperatureField([10.0, 20.0], cast(Any, nodes), load_case="LC1")
            f2 = TemperatureField([1.0, 2.5], cast(Any, nodes), load_case="LC1")
            f3 = f1 + f2

            self.assertIsInstance(f3, TemperatureField)
            self.assertEqual(f3.load_case, "LC1")
            dist = cast(Any, f3.distribution)
            self.assertEqual([n.name for n in dist], [n.name for n in nodes])
            self.assertEqual(list(f3.loads), [11.0, 22.5])

    def test_temperature_field_addition_different_nodes(self):
        with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
            nodes1 = make_nodes(["n1", "n2"])
            # Create a different list with a shared logical node name "n2"
            nodes2 = [DummyNode("n2"), DummyNode("n3")]
            f1 = TemperatureField([10.0, 20.0], cast(Any, nodes1), load_case="LC1")
            f2 = TemperatureField([2.5, 3.0], cast(Any, nodes2), load_case="LC1")
            f3 = f1 + f2

            dist = cast(Any, f3.distribution)
            self.assertEqual([n.name for n in dist], ["n1", "n2", "n3"])
            self.assertEqual(list(f3.loads), [10.0, 22.5, 3.0])

    def test_temperature_field_length_mismatch_raises(self):
        with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
            nodes = make_nodes(["n1", "n2", "n3"])
            with self.assertRaises(ValueError):
                TemperatureField([1.0, 2.0], cast(Any, nodes))

    def test_force_field_addition_vectors(self):
        with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
            nodes = make_nodes(["a", "b"])
            f1 = ForceField([VectorLoad(1, 2, 3), VectorLoad(0, 0, 1)], cast(Any, nodes), load_case="LC1")
            f2 = ForceField([VectorLoad(4, None, 6), VectorLoad(1, 1, None)], cast(Any, nodes), load_case="LC2")
            f3 = f1 + f2

            # different load_case -> None
            self.assertIsNone(f3.load_case)

            L0 = f3.loads[0]
            self.assertIsInstance(L0, VectorLoad)
            self.assertEqual((L0.x, L0.y, L0.z), (5, 2, 9))

            L1 = f3.loads[1]
            self.assertIsInstance(L1, VectorLoad)
            self.assertEqual((L1.x, L1.y, L1.z), (1, 1, 1))

    def test_add_different_field_types_returns_not_implemented(self):
        with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
            temp = TemperatureField([1.0], cast(Any, [DummyNode("n1")]))  # scalar over node
            force = ForceField([VectorLoad(1, 0, 0)], cast(Any, [DummyNode("n1")]))  # vector over node
            result = temp.__add__(force)
            self.assertIs(result, NotImplemented)

    def test_element_scalar_field_addition(self):
        with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
            elems1 = ["e1", "e2"]
            elems2 = ["e2", "e3"]
            f1 = _ElementScalarField([100.0, 200.0], elems1, load_case="LCX")
            f2 = _ElementScalarField([50.0, 30.0], elems2, load_case="LCX")
            f3 = f1 + f2

            dist = cast(Any, f3.distribution)
            self.assertEqual(list(dist), ["e1", "e2", "e3"])
            self.assertEqual(list(f3.loads), [100.0, 250.0, 30.0])
            self.assertEqual(f3.load_case, "LCX")

    def test_temperature_field_scalar_multiplication(self):
        with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
            nodes = make_nodes(["n1", "n2"])  # two nodes
            f = TemperatureField([10.0, 20.0], cast(Any, nodes), load_case="LCM")
            g = cast(Any, f) * 2
            self.assertIsInstance(g, TemperatureField)
            self.assertEqual(g.load_case, "LCM")
            self.assertEqual(list(g.loads), [20.0, 40.0])
            # right-mul
            h = 3 * cast(Any, f)
            self.assertEqual(list(h.loads), [30.0, 60.0])

    def test_force_field_scalar_multiplication(self):
        with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
            nodes = make_nodes(["a", "b"])  # two nodes
            loads = [
                VectorLoad(1, 2, 3, amplitude=2.0),
                VectorLoad(0, None, -1, amplitude=None),
            ]
            f = ForceField(loads, cast(Any, nodes), load_case="LCF")
            g = cast(Any, f) * 0.5
            self.assertIsInstance(g, ForceField)
            L0, L1 = g.loads
            self.assertEqual((L0.x, L0.y, L0.z), (0.5, 1.0, 1.5))
            self.assertEqual(L0.amplitude, 2.0)  # amplitude preserved
            self.assertEqual((L1.x, L1.y, L1.z), (0.0, None, -0.5))
            self.assertIsNone(L1.amplitude)

    def test_scalar_multiplication_non_numeric_returns_not_implemented(self):
        with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
            f = TemperatureField([10.0], cast(Any, [DummyNode("n")]))
            self.assertIs(f.__mul__(cast(Any, "a")), NotImplemented)
            self.assertIs(f.__rmul__(cast(Any, "a")), NotImplemented)

            # Python
            class TestAdditionalProblemFields(unittest.TestCase):
                def test_temperature_field_broadcast_single_value(self):
                    with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
                        nodes = make_nodes(["n1", "n2", "n3"])
                        f = TemperatureField(10.0, cast(Any, nodes), load_case="TB")
                        self.assertEqual(list(f.loads), [10.0, 10.0, 10.0])
                        self.assertEqual([n.name for n in cast(Any, f.distribution)], ["n1", "n2", "n3"])
                        # scaling a broadcasted field
                        g = cast(Any, f) * 3
                        self.assertEqual(list(g.loads), [30.0, 30.0, 30.0])

                def test_element_scalar_field_length_mismatch_raises(self):
                    with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
                        elems = ["e1", "e2", "e3"]
                        with self.assertRaises(ValueError):
                            _ElementScalarField([1.0, 2.0], elems)

                def test_element_scalar_field_broadcast_and_multiply(self):
                    with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
                        elems = ["e1", "e2", "e3"]
                        f = _ElementScalarField(7.0, elems, load_case="LCE")
                        self.assertEqual(list(f.loads), [7.0, 7.0, 7.0])
                        self.assertEqual(list(cast(Any, f.distribution)), elems)

                        g = cast(Any, f) * 2
                        self.assertIsInstance(g, _ElementScalarField)
                        self.assertEqual(g.load_case, "LCE")
                        self.assertEqual(list(g.loads), [14.0, 14.0, 14.0])

                        h = 0.5 * cast(Any, f)
                        self.assertEqual(list(h.loads), [3.5, 3.5, 3.5])

                def test_force_field_right_scalar_multiplication(self):
                    with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
                        nodes = make_nodes(["n1", "n2"])
                        f = ForceField([VectorLoad(1, 0, -1), VectorLoad(2, 2, 2)], cast(Any, nodes), load_case="LCF2")
                        h = 2 * cast(Any, f)
                        self.assertIsInstance(h, ForceField)
                        L0, L1 = h.loads
                        self.assertEqual((L0.x, L0.y, L0.z), (2, 0, -2))
                        self.assertEqual((L1.x, L1.y, L1.z), (4, 4, 4))
                        self.assertEqual(h.load_case, "LCF2")

                def test_force_field_addition_amplitude_selection(self):
                    with patch("compas_fea2.problem.fields.NodesGroup", new=DummyNodesGroup):
                        nodes = make_nodes(["n1"])
                        f1 = ForceField([VectorLoad(1, 0, 0, amplitude=5.0)], cast(Any, nodes), load_case="LCX")
                        f2 = ForceField([VectorLoad(2, 0, 0, amplitude=None)], cast(Any, nodes), load_case="LCX")
                        f3 = f1 + f2
                        self.assertIsInstance(f3, ForceField)
                        self.assertEqual(f3.load_case, "LCX")
                        L = f3.loads[0]
                        self.assertEqual((L.x, L.y, L.z), (3, 0, 0))
                        self.assertEqual(L.amplitude, 5.0)


if __name__ == "__main__":
    unittest.main()
