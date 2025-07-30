import unittest
from typing import List
from unittest.mock import Mock, patch
from compas_fea2.model.groups import (_Group, NodesGroup, ElementsGroup, FacesGroup, PartsGroup, 
                                      EdgesGroup, SectionsGroup, MaterialsGroup, InterfacesGroup,
                                      BCsGroup, ConnectorsGroup, ConstraintsGroup, ICsGroup, ReleasesGroup)
from compas_fea2.model import Node, BeamElement, Part, ShellElement, ShellSection, Steel


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
        self.group._add_member(new)
        self.assertIn(new, self.group)
        self.group._remove_member(new)
        self.assertNotIn(new, self.group)

    def test_add_and_remove_members(self):
        new_members = [Dummy(100), Dummy(101)]
        self.group._add_members(new_members)
        for m in new_members:
            self.assertIn(m, self.group)
        self.group._remove_members(new_members)
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

    def test_subgroup_and_group_by(self):
        even = self.group.subgroup(lambda x: x.key % 2 == 0)  # type: ignore[attr-defined]
        self.assertTrue(all(m.key % 2 == 0 for m in even))  # type: ignore[attr-defined]
        grouped = self.group.group_by(lambda x: x.key % 2)  # type: ignore[attr-defined]
        self.assertEqual(set(grouped.keys()), {0, 1})
        for k, g in grouped.items():
            for m in g:
                self.assertEqual(m.key % 2, k)  # type: ignore[attr-defined]

    def test_set_operations(self):
        g2 = _Group(member_class=Dummy, members=[Dummy(3), Dummy(4), Dummy(5)])
        union = self.group + g2
        self.assertEqual(len(union), 8)  # 5 original + 3 new = 8 total
        diff = self.group - g2
        self.assertEqual(set(diff), {Dummy(0), Dummy(1), Dummy(2), Dummy(3), Dummy(4)})  # only Dummy(5) removed
        inter = self.group.intersection(g2)
        self.assertEqual(set(inter), set())  # no overlap between [0,1,2,3,4] and [3,4,5] that are different objects
        
        # Test with actual overlapping elements
        g3 = _Group(member_class=Dummy, members=[self.members[3], self.members[4], Dummy(5)])
        union2 = self.group + g3
        self.assertEqual(len(union2), 6)  # 5 original + 1 new = 6 total
        inter2 = self.group.intersection(g3)
        self.assertEqual(set(inter2), {self.members[3], self.members[4]})
        
        self.assertEqual(set(self.group.union(g2)), set(union))
        self.assertEqual(set(self.group.difference(g2)), set(diff))

    def test_serialize_deserialize(self):
        data = self.group.serialize()
        g2 = _Group.deserialize(data)
        self.assertEqual(set(g2), set(self.group))

    def test_wrong_type(self):
        with self.assertRaises(TypeError):
            _Group(member_class=Dummy, members=[1, 2, 3])
        with self.assertRaises(TypeError):
            self.group._add_member(123)


class TestEmptyGroup(unittest.TestCase):
    def test_empty(self):
        g = _Group(member_class=Dummy)
        self.assertEqual(len(g), 0)
        self.assertEqual(list(g), [])
        self.assertEqual(g.to_list(), [])
        self.assertEqual(g.sorted, [])
        self.assertEqual(g.sorted_by(lambda x: x), [])
        self.assertEqual(g.serialize(), {"members": []})


class TestGroupDuplicates(unittest.TestCase):
    def test_duplicates(self):
        d = Dummy(1)
        g = _Group(member_class=Dummy, members=[d, d, d])
        self.assertEqual(len(g), 1)
        g._add_member(d)
        self.assertEqual(len(g), 1)


class TestNodesGroup(unittest.TestCase):
    def test_add_node(self):
        node = Node([0, 0, 0])
        group = NodesGroup(nodes=[node])
        self.assertIn(node, group.nodes)


class TestElementsGroup(unittest.TestCase):
    def test_add_element(self):
        node1 = Node([0, 0, 0])
        node2 = Node([1, 0, 0])
        mat = Steel.S355()
        section = ShellSection(0.1, material=mat)
        element = BeamElement(nodes=[node1, node2], section=section, frame=[0, 0, 1])
        group = ElementsGroup(elements=[element])
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
        group = FacesGroup(faces=element.faces)
        self.assertIn(face, group.faces)


class TestPartsGroup(unittest.TestCase):
    def test_add_part(self):
        part = Part()
        group = PartsGroup(parts=[part])
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
            group._add_member("wrong_type")
    
    def test_remove_nonexistent_member(self):
        """Test removing member that doesn't exist"""
        group = _Group(member_class=Dummy, members=[Dummy(1)])
        result = group._remove_member(Dummy(999))
        self.assertFalse(result)
    
    def test_remove_members_partial_exists(self):
        """Test removing multiple members where some don't exist"""
        group = _Group(member_class=Dummy, members=[Dummy(1), Dummy(2)])
        removed = group._remove_members([Dummy(1), Dummy(999)])
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0], Dummy(1))
    
    def test_operations_with_different_types(self):
        """Test set operations with incompatible group types"""
        group1 = _Group(member_class=Dummy, members=[Dummy(1)])
        
        class OtherGroup(_Group):
            pass
        
        group2 = OtherGroup(member_class=Dummy, members=[Dummy(2)])
        
        with self.assertRaises(TypeError):
            _ = group1 + group2
        
        with self.assertRaises(TypeError):
            _ = group1 - group2


class TestGroupAdvancedOperations(unittest.TestCase):
    """Test advanced group operations and methods"""
    
    def setUp(self):
        self.members = [Dummy(i) for i in range(10)]
        self.group = _Group(member_class=Dummy, members=self.members)
    
    def test_subgroup_with_empty_result(self):
        """Test subgroup that results in empty group"""
        empty_subgroup = self.group.subgroup(lambda x: x.key > 100)  # type: ignore
        self.assertEqual(len(empty_subgroup), 0)
    
    def test_subgroup_with_all_members(self):
        """Test subgroup that includes all members"""
        all_subgroup = self.group.subgroup(lambda x: x.key >= 0)  # type: ignore
        self.assertEqual(len(all_subgroup), len(self.group))
    
    def test_group_by_single_group(self):
        """Test group_by that results in single group"""
        grouped = self.group.group_by(lambda x: "all")
        self.assertEqual(len(grouped), 1)
        self.assertIn("all", grouped)
        self.assertEqual(len(grouped["all"]), len(self.group))
    
    def test_group_by_multiple_groups(self):
        """Test group_by with multiple resulting groups"""
        grouped = self.group.group_by(lambda x: x.key // 3)  # type: ignore
        expected_keys = {0, 1, 2, 3}
        self.assertEqual(set(grouped.keys()), expected_keys)
    
    def test_sorted_by_reverse(self):
        """Test sorted_by with reverse order"""
        sorted_desc = self.group.sorted_by(lambda x: x.key, reverse=True)  # type: ignore
        expected = sorted(self.members, key=lambda x: x.key, reverse=True)
        self.assertEqual(sorted_desc, expected)
    
    def test_complex_key_function(self):
        """Test sorting with complex key function"""
        # Sort by key modulo 3, then by key itself
        sorted_complex = self.group.sorted_by(lambda x: (x.key % 3, x.key))  # type: ignore
        # Verify that items with same modulo are in ascending order
        for i in range(len(sorted_complex) - 1):
            curr_mod = sorted_complex[i].key % 3  # type: ignore
            next_mod = sorted_complex[i + 1].key % 3  # type: ignore
            if curr_mod == next_mod:
                self.assertLessEqual(sorted_complex[i].key, sorted_complex[i + 1].key)  # type: ignore


class TestGroupSerialization(unittest.TestCase):
    """Test serialization and deserialization of groups"""
    
    def test_serialize_empty_group(self):
        """Test serializing empty group"""
        group = _Group(member_class=Dummy)
        data = group.serialize()
        self.assertEqual(data, {"members": []})
    
    def test_deserialize_empty_group(self):
        """Test deserializing empty group"""
        data = {"members": []}
        group = _Group.deserialize(data)
        self.assertEqual(len(group), 0)
    
    def test_serialize_deserialize_roundtrip(self):
        """Test full roundtrip serialization"""
        original = _Group(member_class=Dummy, members=[Dummy(1), Dummy(2)])
        data = original.serialize()
        restored = _Group.deserialize(data)
        self.assertEqual(set(original), set(restored))


class TestSpecificGroupTypes(unittest.TestCase):
    """Test specific group type implementations"""
    
    def setUp(self):
        # Create test nodes
        self.nodes = [Node([i, 0, 0]) for i in range(3)]
        
        # Create test material and section
        self.material = Steel.S355()
        self.section = ShellSection(0.1, material=self.material)
        
        # Create test elements
        self.beam_element = BeamElement(
            nodes=[self.nodes[0], self.nodes[1]], 
            section=self.section, 
            frame=[0, 0, 1]
        )
        
        self.shell_element = ShellElement(
            nodes=self.nodes, 
            section=self.section
        )
        
        # Create test part
        self.part = Part()
    
    def test_nodes_group_properties(self):
        """Test NodesGroup specific properties and methods"""
        group = NodesGroup(nodes=self.nodes[:2])
        self.assertEqual(len(group.nodes), 2)
        
        # Test adding nodes
        new_node = Node([10, 0, 0])
        added = group.add_node(new_node)
        self.assertEqual(added, new_node)
        self.assertIn(new_node, group.nodes)
        
        # Test adding multiple nodes
        more_nodes = [Node([20, 0, 0]), Node([30, 0, 0])]
        added_list = group.add_nodes(more_nodes)
        self.assertEqual(len(added_list), 2)
        for node in more_nodes:
            self.assertIn(node, group.nodes)
    
    def test_elements_group_properties(self):
        """Test ElementsGroup specific properties and methods"""
        group = ElementsGroup(elements=[self.beam_element])
        self.assertEqual(len(group.elements), 1)
        
        # Test adding element
        added = group.add_element(self.shell_element)
        self.assertEqual(added, self.shell_element)
        self.assertIn(self.shell_element, group.elements)
    
    def test_faces_group_properties(self):
        """Test FacesGroup specific properties and methods"""
        # Assuming shell element has faces
        if hasattr(self.shell_element, 'faces') and self.shell_element.faces:
            faces = self.shell_element.faces
            group = FacesGroup(faces=faces)
            
            # Test nodes property
            all_nodes = group.nodes
            self.assertIsInstance(all_nodes, set)
            
            # Test area property if faces have area
            if hasattr(faces[0], 'area'):
                total_area = group.area
                self.assertIsInstance(total_area, (int, float))
                self.assertGreaterEqual(total_area, 0)
    
    def test_parts_group_properties(self):
        """Test PartsGroup specific properties and methods"""
        group = PartsGroup(parts=[self.part])
        self.assertEqual(len(group.parts), 1)
        
        # Test adding part
        new_part = Part()
        added = group.add_part(new_part)
        self.assertEqual(added, new_part)
        self.assertIn(new_part, group.parts)


class TestGroupTypeValidation(unittest.TestCase):
    """Test type validation for specific group types"""
    
    def test_nodes_group_wrong_type(self):
        """Test NodesGroup with wrong member type"""
        with self.assertRaises(TypeError):
            NodesGroup(nodes=["not_a_node"])
    
    def test_elements_group_wrong_type(self):
        """Test ElementsGroup with wrong member type"""
        with self.assertRaises(TypeError):
            ElementsGroup(elements=["not_an_element"])
    
    def test_parts_group_wrong_type(self):
        """Test PartsGroup with wrong member type"""
        with self.assertRaises(TypeError):
            PartsGroup(parts=["not_a_part"])


class TestGroupInheritance(unittest.TestCase):
    """Test that group inheritance works correctly"""
    
    def test_group_operations_preserve_type(self):
        """Test that group operations return the same type"""
        nodes = [Node([i, 0, 0]) for i in range(3)]
        group1 = NodesGroup(nodes=nodes[:2])
        group2 = NodesGroup(nodes=nodes[1:])
        
        # Test union preserves type
        union = group1 + group2
        self.assertIsInstance(union, NodesGroup)
        
        # Test difference preserves type
        diff = group1 - group2
        self.assertIsInstance(diff, NodesGroup)
        
        # Test intersection preserves type
        inter = group1.intersection(group2)
        self.assertIsInstance(inter, NodesGroup)
    
    def test_subgroup_preserves_type(self):
        """Test that subgroup returns the same type"""
        nodes = [Node([i, 0, 0]) for i in range(5)]
        group = NodesGroup(nodes=nodes)
        
        subgroup = group.subgroup(lambda n: n.xyz[0] < 3)  # type: ignore
        self.assertIsInstance(subgroup, NodesGroup)


class TestGroupDataOperations(unittest.TestCase):
    """Test data-related operations for specific group types"""
    
    def test_nodes_group_serialization(self):
        """Test NodesGroup serialization"""
        nodes = [Node([i, 0, 0]) for i in range(2)]
        group = NodesGroup(nodes=nodes)
        
        data = group.__data__
        self.assertIn("nodes", data)
        self.assertEqual(len(data["nodes"]), 2)
        
        # Test deserialization
        restored = NodesGroup.__from_data__(data)
        self.assertEqual(len(restored.nodes), 2)
    
    def test_elements_group_serialization(self):
        """Test ElementsGroup serialization"""
        nodes = [Node([0, 0, 0]), Node([1, 0, 0])]
        material = Steel.S355()
        section = ShellSection(0.1, material=material)
        element = BeamElement(nodes=nodes, section=section, frame=[0, 0, 1])
        
        group = ElementsGroup(elements=[element])
        data = group.__data__
        self.assertIn("elements", data)
        self.assertEqual(len(data["elements"]), 1)


class TestGroupPerformance(unittest.TestCase):
    """Test group performance with large datasets"""
    
    def test_large_group_operations(self):
        """Test operations with large number of members"""
        large_members = [Dummy(i) for i in range(1000)]
        group = _Group(member_class=Dummy, members=large_members)
        
        # Test basic operations work with large dataset
        self.assertEqual(len(group), 1000)
        self.assertIn(Dummy(500), group)
        
        # Test sorting works
        sorted_members = group.sorted
        self.assertEqual(len(sorted_members), 1000)
        
        # Test subgroup works
        subgroup = group.subgroup(lambda x: x.key % 10 == 0)  # type: ignore
        self.assertEqual(len(subgroup), 100)


class TestAllGroupTypesInstantiation(unittest.TestCase):
    """Test that all group types can be instantiated without errors"""
    
    def test_instantiate_all_group_types(self):
        """Test instantiating all group types with empty members"""
        group_types = [
            (NodesGroup, []),
            (ElementsGroup, []),
            (FacesGroup, []),
            (EdgesGroup, []),
            (PartsGroup, []),
            (SectionsGroup, []),
            (MaterialsGroup, []),
            (InterfacesGroup, []),
            (BCsGroup, []),
            (ConnectorsGroup, []),
            (ConstraintsGroup, []),
            (ICsGroup, []),
            (ReleasesGroup, [])
        ]
        
        for group_class, members in group_types:
            with self.subTest(group_class=group_class):
                # Get the parameter name from the constructor
                if group_class == NodesGroup:
                    group = group_class(nodes=members)
                elif group_class == ElementsGroup:
                    group = group_class(elements=members)
                elif group_class == FacesGroup:
                    group = group_class(faces=members)
                elif group_class == EdgesGroup:
                    group = group_class(edges=members)
                elif group_class == PartsGroup:
                    group = group_class(parts=members)
                elif group_class == SectionsGroup:
                    group = group_class(sections=members)
                elif group_class == MaterialsGroup:
                    group = group_class(materials=members)
                elif group_class == InterfacesGroup:
                    group = group_class(interfaces=members)
                elif group_class == BCsGroup:
                    group = group_class(bcs=members)
                elif group_class == ConnectorsGroup:
                    group = group_class(connectors=members)
                elif group_class == ConstraintsGroup:
                    group = group_class(constraints=members)
                elif group_class == ICsGroup:
                    group = group_class(ics=members)
                elif group_class == ReleasesGroup:
                    group = group_class(releases=members)
                
                self.assertIsInstance(group, group_class)
                self.assertEqual(len(group), 0)


if __name__ == "__main__":
    unittest.main()
