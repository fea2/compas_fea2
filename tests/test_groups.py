import unittest
from typing import List
from compas_fea2.model.groups import _Group, NodesGroup, ElementsGroup, FacesGroup, PartsGroup
from compas_fea2.model import Node, BeamElement, Part, ShellElement, ShellSection, Steel, RectangularSection
from compas.geometry import Point


class Dummy:
    key: int

    def __init__(self, key: int):
        self.key = key

    def __repr__(self):
        return f"Dummy({self.key})"

    def __eq__(self, other):
        return isinstance(other, Dummy) and self.key == other.key

    def __hash__(self):
        return hash(self.key)


class TestGroupBase(unittest.TestCase):
    members: List[Dummy]
    group: _Group

    def setUp(self):
        self.members = [Dummy(i) for i in range(5)]
        self.group = _Group(member_class=Dummy, members=self.members)

    def test_len_and_contains(self):
        self.assertEqual(len(self.group), 5)
        for m in self.members:
            self.assertIn(m, self.group)

    def test_add_and_remove_member(self):
        new = Dummy(99)
        self.group.add_member(new)
        self.assertIn(new, self.group)
        self.group.remove_member(new)
        self.assertNotIn(new, self.group)

    def test_add_and_remove_members(self):
        new_members = [Dummy(100), Dummy(101)]
        self.group.add_members(new_members)
        for m in new_members:
            self.assertIn(m, self.group)
        self.group.remove_members(new_members)
        for m in new_members:
            self.assertNotIn(m, self.group)

    def test_clear(self):
        self.group.clear()
        self.assertEqual(len(self.group), 0)

    def test_to_list_sorted_sorted_by(self):
        l = self.group.to_list()
        self.assertEqual(set(l), set(self.members))
        s = sorted(self.members, key=lambda x: x.key)
        self.assertEqual(self.group.sorted, s)
        s2 = sorted(self.members, key=lambda x: -x.key)
        self.assertEqual(self.group.sorted_by(lambda x: -x.key), s2)  # type: ignore[attr-defined]

    # def test_serialize_deserialize(self):
    #     data = self.group.serialize()
    #     g2 = _Group.deserialize(data)
    #     self.assertEqual(set(g2), set(self.group))

    def test_wrong_type(self):
        self._members_class = Dummy
        with self.assertRaises(TypeError):
            _Group(member_class=Dummy, members=[1, 2, 3])
        with self.assertRaises(TypeError):
            self.group.add_member(123)


class TestEmptyGroup(unittest.TestCase):
    def test_empty(self):
        g = _Group(member_class=Dummy)
        self.assertEqual(len(g), 0)
        self.assertEqual(list(g), [])
        self.assertEqual(g.to_list(), [])
        self.assertEqual(g.sorted, [])
        self.assertEqual(g.sorted_by(lambda x: x), [])
        self.assertEqual(g.__data__["members"], [])


class TestGroupDuplicates(unittest.TestCase):
    def test_duplicates(self):
        d = Dummy(1)
        g = _Group(member_class=Dummy, members=[d, d, d])
        self.assertEqual(len(g), 1)
        g.add_member(d)
        self.assertEqual(len(g), 1)


class TestNodesGroup(unittest.TestCase):
    def test_add_node(self):
        node = Node([0, 0, 0])
        group = NodesGroup(members=[node])
        self.assertIn(node, group.nodes)


class TestElementsGroup(unittest.TestCase):
    def test_add_element(self):
        node1 = Node([0, 0, 0])
        node2 = Node([1, 0, 0])
        mat = Steel.S355()
        section = RectangularSection(w=100, h=50, material=mat)
        element = BeamElement(nodes=[node1, node2], section=section, orientation=Point(0, 0, 1))
        group = ElementsGroup(members=[element])
        self.assertIn(element, group.elements)


class TestFacesGroup(unittest.TestCase):
    def test_add_face(self):
        node1 = Node([0, 0, 0])
        node2 = Node([1, 0, 0])
        node3 = Node([1, 1, 0])
        nodes = [node1, node2, node3]
        mat = Steel.S355()
        section = ShellSection(0.1, material=mat)
        element = ShellElement(nodes=nodes, section=section)
        # Ensure faces are generated if not already present
        if element.faces is None:
            raise AttributeError("Faces not generated")
        face = element.faces[0]
        group = FacesGroup(members=element.faces)
        self.assertIn(face, group.faces)


class TestPartsGroup(unittest.TestCase):
    def test_add_part(self):
        part = Part()
        group = PartsGroup(members=[part])
        self.assertIn(part, group.parts)


class TestGroupEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for _Group"""

    def test_empty_initialization(self):
        """Test initializing group with None members"""
        group = _Group(member_class=Dummy, members=None)
        self.assertEqual(len(group), 0)
        self.assertEqual(list(group), [])

    def test_type_validation_on_init(self):
        """Test type validation during initialization"""
        with self.assertRaises(TypeError):
            _Group(member_class=Dummy, members=[1, 2, "string"])

    def test_add_wrong_type(self):
        """Test adding wrong type to group"""
        group = _Group(member_class=Dummy)
        with self.assertRaises(TypeError):
            group.add_member("wrong_type")

    def test_remove_nonexistent_member(self):
        """Test removing member that doesn't exist"""
        group = _Group(member_class=Dummy, members=[Dummy(1)])
        result = group.remove_member(Dummy(999))
        self.assertFalse(result)

    def test_remove_members_partial_exists(self):
        """Test removing multiple members where some don't exist"""
        group = _Group(member_class=Dummy, members=[Dummy(1), Dummy(2)])
        removed = group.remove_members([Dummy(1), Dummy(999)])
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0], Dummy(1))


class TestGroupSerialization(unittest.TestCase):
    """Test serialization and deserialization of groups"""

    def test_serialize_empty_group(self):
        """Test serializing empty group"""
        group = _Group(member_class=Dummy)
        data = group.__data__
        self.assertEqual(type(data["uid"]), str)
        self.assertEqual(data["members"], [])
        self.assertEqual(data["member_class"], Dummy.__name__)


class TestSpecificGroupTypes(unittest.TestCase):
    """Test specific group type implementations"""

    def setUp(self):
        # Create test nodes
        n1 = Node([0, 0, 0])
        n1._key = 0
        n2 = Node([1, 1, 0])
        n2._key = 1
        n3 = Node([0, 1, 0])
        n3._key = 2
        self.nodes = [n1, n2, n3]

        # Create test material and section
        self.material = Steel.S355()
        self.shell_section = ShellSection(0.1, material=self.material)
        self.beam_section = RectangularSection(w=100, h=50, material=self.material)

        # Create test elements
        self.beam_element = BeamElement(nodes=[self.nodes[0], self.nodes[1]], section=self.beam_section, orientation=Point(0, 0, 1))

        self.shell_element = ShellElement(nodes=self.nodes, section=self.shell_section)

        # Create test part
        self.part = Part()

    def test_subgroup_and_group_by(self):
        group = NodesGroup(members=self.nodes[:2])
        even = group.subgroup(lambda x: x.key % 2 == 0)  # type: ignore[attr-defined]
        self.assertTrue(all(m.key % 2 == 0 for m in even))  # type: ignore[attr-defined]
        grouped = group.group_by(lambda x: x.key % 2)  # type: ignore[attr-defined]
        self.assertEqual(set(grouped.keys()), {0, 1})
        for k, g in grouped.items():
            for m in g:
                self.assertEqual(m.key % 2, k)  # type: ignore[attr-defined]

    # def test_set_operations(self):
    #     group = NodesGroup(members=self.nodes[:2])
    #     g2 = NodesGroup(members=self.nodes)
    #     union = group + g2
    #     self.assertEqual(len(union), 3)
    #     diff = group - g2
    #     self.assertEqual(set())
    #     inter = group.intersection(g2)
    #     self.assertEqual(set(inter), set())  # no overlap between [0,1,2,3,4] and [3,4,5] that are different objects

    #     # Test with actual overlapping elements
    #     g3 = _Group(member_class=Dummy, members=[self.members[3], self.members[4], Dummy(5)])
    #     union2 = group + g3
    #     self.assertEqual(len(union2), 6)  # 5 original + 1 new = 6 total
    #     inter2 = group.intersection(g3)
    #     self.assertEqual(set(inter2), {self.members[3], self.members[4]})

    #     self.assertEqual(set(self.group.union(g2)), set(union))
    #     self.assertEqual(set(self.group.difference(g2)), set(diff))

    def test_subgroup_with_empty_result(self):
        """Test subgroup that results in empty group"""
        group = NodesGroup(members=self.nodes[:2])
        empty_subgroup = group.subgroup(lambda x: x.x > 100)  # type: ignore
        self.assertEqual(len(empty_subgroup), 0)

    def test_nodes_group_properties(self):
        """Test NodesGroup specific properties and methods"""
        group = NodesGroup(members=self.nodes[:2])
        self.assertEqual(len(group.nodes), 2)

        # Test adding nodes
        new_node = Node([10, 0, 0])
        added = group.add_member(new_node)
        self.assertEqual(added, new_node)
        self.assertIn(new_node, group.nodes)

        # Test adding multiple nodes
        more_nodes = [Node([20, 0, 0]), Node([30, 0, 0])]
        added_list = group.add_members(more_nodes)
        self.assertEqual(len(added_list), 2)
        for node in more_nodes:
            self.assertIn(node, group.nodes)

    def test_elements_group_properties(self):
        """Test ElementsGroup specific properties and methods"""
        group = ElementsGroup(members=[self.beam_element])
        self.assertEqual(len(group.elements), 1)

        # Test adding element
        added = group.add_member(self.shell_element)
        self.assertEqual(added, self.shell_element)
        self.assertIn(self.shell_element, group.elements)

    def test_faces_group_properties(self):
        """Test FacesGroup specific properties and methods"""
        # Assuming shell element has faces
        if hasattr(self.shell_element, "faces") and self.shell_element.faces:
            faces = self.shell_element.faces
            group = FacesGroup(members=faces)

            # Test nodes property
            all_nodes = group.nodes
            self.assertIsInstance(all_nodes, set)

            # Test area property if faces have area
            if hasattr(faces[0], "area"):
                total_area = group.area
                self.assertIsInstance(total_area, (int, float))
                self.assertGreaterEqual(total_area, 0)

    def test_parts_group_properties(self):
        """Test PartsGroup specific properties and methods"""
        group = PartsGroup(members=[self.part])
        self.assertEqual(len(group.parts), 1)

        # Test adding part
        new_part = Part()
        added = group.add_member(new_part)
        self.assertEqual(added, new_part)
        self.assertIn(new_part, group.parts)


class TestGroupTypeValidation(unittest.TestCase):
    """Test type validation for specific group types"""

    def test_nodes_group_wrong_type(self):
        """Test NodesGroup with wrong member type"""
        with self.assertRaises(TypeError):
            NodesGroup(members=["not_a_node"])  # type: ignore

    def test_elements_group_wrong_type(self):
        """Test ElementsGroup with wrong member type"""
        with self.assertRaises(TypeError):
            ElementsGroup(members=["not_an_element"])  # type: ignore

    def test_parts_group_wrong_type(self):
        """Test PartsGroup with wrong member type"""
        with self.assertRaises(TypeError):
            PartsGroup(members=["not_a_part"])  # type: ignore


class TestGroupInheritance(unittest.TestCase):
    """Test that group inheritance works correctly"""

    def test_group_operations_preserve_type(self):
        """Test that group operations return the same type"""
        nodes = [Node([i, 0, 0]) for i in range(3)]
        group1 = NodesGroup(members=nodes[:2])
        group2 = NodesGroup(members=nodes[1:])

        # Test union preserves type
        union = group1 + group2
        self.assertIsInstance(union, NodesGroup)

        # # Test difference preserves type
        # diff = group1 - group2
        # self.assertIsInstance(diff, NodesGroup)

        # # Test intersection preserves type
        # inter = group1.intersection(group2)
        # self.assertIsInstance(inter, NodesGroup)

    def test_subgroup_preserves_type(self):
        """Test that subgroup returns the same type"""
        nodes = [Node([i, 0, 0]) for i in range(5)]
        group = NodesGroup(members=nodes)

        subgroup = group.subgroup(lambda n: n.xyz[0] < 3)  # type: ignore
        self.assertIsInstance(subgroup, NodesGroup)


class TestGroupDataOperations(unittest.TestCase):
    """Test data-related operations for specific group types"""

    def test_nodes_group_serialization(self):
        """Test NodesGroup serialization"""
        nodes = [Node([i, 0, 0]) for i in range(2)]
        group = NodesGroup(members=nodes)

        data = group.__data__
        self.assertIn("members", data)
        self.assertEqual(len(data["members"]), 2)

        # Test deserialization
        restored = NodesGroup.__from_data__(data)
        self.assertEqual(len(restored.nodes), 2)

    def test_elements_group_serialization(self):
        """Test ElementsGroup serialization"""
        nodes = [Node([0, 0, 0]), Node([1, 0, 0])]
        material = Steel.S355()
        section = RectangularSection(w=100, h=50, material=material)
        element = BeamElement(nodes=nodes, section=section, orientation=Point(0, 0, 1))

        group = ElementsGroup(members=[element])
        data = group.__data__
        self.assertIn("members", data)
        self.assertEqual(len(data["members"]), 1)


class TestGroupPerformance(unittest.TestCase):
    """Test group performance with large datasets"""

    def test_large_group_operations(self):
        """Test operations with large number of members"""

        large_members = [Node(xyz=[i, 2, i - 1]) for i in range(1000)]
        for c, n in enumerate(large_members):
            n._key = c
        group = NodesGroup(members=large_members)

        # Test basic operations work with large dataset
        self.assertEqual(len(group), 1000)
        self.assertIn(large_members[500], group)

        # Test sorting works
        sorted_members = group.sorted
        self.assertEqual(len(sorted_members), 1000)

        # Test subgroup works
        subgroup = group.subgroup(lambda x: x.key % 10 == 0)  # type: ignore
        self.assertEqual(len(subgroup), 100)


if __name__ == "__main__":
    unittest.main()
