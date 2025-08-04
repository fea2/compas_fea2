import unittest
from compas_fea2.model import Model
from compas_fea2.model import Part
from compas_fea2.model.nodes import Node
from compas_fea2.model.fields import RollerBCXField, FixedBCField, PinnedBCField, ThermalBCField


class TestBCFields(unittest.TestCase):
    def test_fixed_bc_field(self):
        node = Node(xyz = [0,0,0])
        bcf = FixedBCField(nodes=node)

        self.assertTrue(bcf.conditions[0].x)
        self.assertTrue(bcf.conditions[0].y)
        self.assertTrue(bcf.conditions[0].z)
        self.assertTrue(bcf.conditions[0].xx)
        self.assertTrue(bcf.conditions[0].yy)
        self.assertTrue(bcf.conditions[0].zz)

    def test_pinned_bc(self):
        node = Node(xyz = [0,0,0])
        bcf = PinnedBCField(nodes=node)
        self.assertTrue(bcf.conditions[0].x)
        self.assertTrue(bcf.conditions[0].y)
        self.assertTrue(bcf.conditions[0].z)
        self.assertFalse(bcf.conditions[0].xx)
        self.assertFalse(bcf.conditions[0].yy)
        self.assertFalse(bcf.conditions[0].zz)

    def test_roller_bc_x(self):
        node = Node(xyz = [0,0,0])
        bcf = RollerBCXField(nodes=node)
        self.assertFalse(bcf.conditions[0].x)
        self.assertTrue(bcf.conditions[0].y)
        self.assertTrue(bcf.conditions[0].z)
        self.assertFalse(bcf.conditions[0].xx)
        self.assertFalse(bcf.conditions[0].yy)
        self.assertFalse(bcf.conditions[0].zz)

    def test_node_removal(self):
        node1 = Node(xyz = [0,0,0])
        node2 = Node(xyz = [1,0,0])
        mdl = Model()
        prt = mdl.add_part(Part())
        prt.add_nodes([node1, node2])
        bcf = FixedBCField(nodes=[node1, node2])

        mdl.add_bcs_field(bcf)
        self.assertTrue(node2 in bcf.distribution)
        self.assertTrue(bcf.conditions[0] in node2.bcs)
        #dof is the dictionnary of the active degree of freedom of the node
        # False : the dof is blocked; True : the dof is free.
        self.assertFalse(node2.dof['x'])
        self.assertFalse(node2.dof['y'])
        self.assertFalse(node2.dof['z'])
        self.assertFalse(node2.dof['xx'])
        self.assertFalse(node2.dof['yy'])
        self.assertFalse(node2.dof['zz'])

        mdl.remove_bcs(node2)
        self.assertFalse(node2 in bcf.distribution)
        # self.assertFalse(bcf.conditions[0] in node2.bcs)
        self.assertTrue(node2.dof['x'])
        self.assertTrue(node2.dof['y'])
        self.assertTrue(node2.dof['z'])
        self.assertTrue(node2.dof['xx'])
        self.assertTrue(node2.dof['yy'])
        self.assertTrue(node2.dof['zz'])

    def test_bc_add(self):
        node = Node(xyz = [0,0,0])
        mdl = Model()
        prt = mdl.add_part(Part())
        prt.add_node(node)
        bcf1 = RollerBCXField(nodes=node)
        bcf2 = ThermalBCField(nodes=node, temperature=40)
        mdl.add_bcs_fields([bcf1, bcf2])
        self.assertTrue(all(bc in node.bcs for bc in bcf1.conditions))
        self.assertTrue(all(bc in node.bcs for bc in bcf2.conditions))
        self.assertTrue(node.dof['x'])
        self.assertFalse(node.dof['y'])
        self.assertFalse(node.dof['z'])
        self.assertTrue(node.dof['xx'])
        self.assertTrue(node.dof['yy'])
        self.assertTrue(node.dof['zz'])
        self.assertEqual(node.dof["temperature"], 40)

if __name__ == "__main__":
    unittest.main()
