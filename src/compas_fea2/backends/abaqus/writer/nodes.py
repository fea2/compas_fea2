from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


# Author(s): Andrew Liew (github.com/andrewliew), Francesco Ranaudo (github.com/franaudo)


__all__ = [
    'Nodes',
]

class Nodes(object):

    def __init__(self):
        pass

    def write_nodes(self):
        self.write_section('Nodes')
        self.write_line('**\n*NODE, NSET=nset_all\n**')

        for key in sorted(self.structure.nodes, key=int):

            self.write_node(key)

        self.blank_line()
        self.blank_line()

    def write_node(self, key):
        prefix  = ''
        spacer  = self.spacer
        x, y, z = self.structure.node_xyz(key)

        line    = '{0}{1}{2}{3:.3f}{2}{4:.3f}{2}{5:.3f}'.format(prefix, key + 1, spacer, x, y, z)
        self.write_line(line)

    def write_mass(self, key):
        mr = '' if self.ndof == 3 else '0 0 0'
        line = 'mass {0} {1} {1} {1} {2}'.format(key + 1, self.structure.nodes[key].mass, mr)
        self.write_line(line)
