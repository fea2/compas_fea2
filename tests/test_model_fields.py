import unittest
from compas_fea2.model import Model
from compas_fea2.model import Part
from compas_fea2.model import FixedBC, PinnedBC, RollerBCX
from compas_fea2.model.nodes import Node
from compas_fea2.model.fields import BoundaryConditionsField


class TestBCFields(unittest.TestCase):
    def test_fixed_bc_field(self):
        node = Node(xyz=[0, 0, 0])
        bc = FixedBC()
        bcf = BoundaryConditionsField(distribution=node, condition=bc)

        self.assertTrue(bcf.condition.x)
        self.assertTrue(bcf.condition.y)
        self.assertTrue(bcf.condition.z)
        self.assertTrue(bcf.condition.xx)
        self.assertTrue(bcf.condition.yy)
        self.assertTrue(bcf.condition.zz)

    def test_pinned_bc(self):
        node = Node(xyz=[0, 0, 0])
        bc = PinnedBC()
        bcf = BoundaryConditionsField(condition=bc, distribution=node)
        self.assertTrue(bcf.bc.x)
        self.assertTrue(bcf.bc.y)
        self.assertTrue(bcf.bc.z)
        self.assertFalse(bcf.bc.xx)
        self.assertFalse(bcf.bc.yy)
        self.assertFalse(bcf.bc.zz)

    def test_roller_bc_x(self):
        node = Node(xyz=[0, 0, 0])
        bc = RollerBCX()
        bcf = BoundaryConditionsField(condition=bc, distribution=node)
        self.assertFalse(bcf.condition.x)
        self.assertTrue(bcf.condition.y)
        self.assertTrue(bcf.condition.z)
        self.assertFalse(bcf.condition.xx)
        self.assertFalse(bcf.condition.yy)
        self.assertFalse(bcf.condition.zz)

    #TODO  complete
    def test_node_removal(self):
        node1 = Node(xyz=[0, 0, 0])
        node2 = Node(xyz=[1, 0, 0])
        mdl = Model()
        prt = mdl.add_part(Part())
        prt.add_nodes([node1, node2])
        bc = RollerBCX()
        bcf = BoundaryConditionsField(condition=bc, distribution=[node1, node2])

        mdl.add_bcs(bcf)
        self.assertTrue(node2 in bcf.distribution)
        # self.assertTrue(bcf.condition in node2.bcs)
        # dof is the dictionnary of the active degree of freedom of the node
        # False : the dof is blocked; True : the dof is free.
        # self.assertFalse(node2.dof["x"])
        # self.assertFalse(node2.dof["y"])
        # self.assertFalse(node2.dof["z"])
        # self.assertFalse(node2.dof["xx"])
        # self.assertFalse(node2.dof["yy"])
        # self.assertFalse(node2.dof["zz"])

        # mdl.remove_bcs(node2)
        # self.assertFalse(node2 in bcf.distribution)
        # self.assertFalse(bcf.conditions[0] in node2.bcs)
        # self.assertTrue(node2.dof["x"])
        # self.assertTrue(node2.dof["y"])
        # self.assertTrue(node2.dof["z"])
        # self.assertTrue(node2.dof["xx"])
        # self.assertTrue(node2.dof["yy"])
        # self.assertTrue(node2.dof["zz"])

    # def test_bc_add(self):
    #     node = Node(xyz=[0, 0, 0])
    #     mdl = Model()
    #     prt = mdl.add_part(Part())
    #     prt.add_node(node)
    #     bcf1 = BoundaryConditionsField(distribution=node, condition=FixedBC())
    #     bcf2 = BoundaryConditionsField(distribution=node, condition =ImposedTemperature(temperature=40))
    #     mdl.add_bcs([bcf1, bcf2])
    #     self.assertTrue(all(bc in node.bc_fields for bc in bcf1.condition))
    #     self.assertTrue(all(bc in node.bc_fields for bc in bcf2.condition))
    #     self.assertTrue(node.dof["x"])
    #     self.assertFalse(node.dof["y"])
    #     self.assertFalse(node.dof["z"])
    #     self.assertTrue(node.dof["xx"])
    #     self.assertTrue(node.dof["yy"])
    #     self.assertTrue(node.dof["zz"])
    #     self.assertEqual(node.dof["temperature"], 40)


if __name__ == "__main__":
    unittest.main()
