from compas_fea2.cad import rhino

from compas_fea2.backends.abaqus import ElasticIsotropic
from compas_fea2.backends.abaqus import ElementProperties as Properties
from compas_fea2.backends.abaqus import GeneralStep
from compas_fea2.backends.abaqus import ModalStep
from compas_fea2.backends.abaqus import PinnedDisplacement
from compas_fea2.backends.abaqus import ShellSection
from compas_fea2.backends.abaqus import Structure


# Author(s): Andrew Liew (github.com/andrewliew)


# Structure

mdl = Structure(name='mesh_modal', path='C:/Temp/')

# Elements

rhino.add_nodes_elements_from_layers(mdl, mesh_type='ShellElement', layers='elset_concrete', pA=600)

# Sets

rhino.add_sets_from_layers(mdl, layers='nset_pins')

# Materials

mdl.add(ElasticIsotropic(name='mat_concrete', E=40*10**9, v=0.2, p=2400))

# Sections

mdl.add(ShellSection(name='sec_concrete', t=0.250))

# Properties

mdl.add(Properties(name='ep_concrete', material='mat_concrete', section='sec_concrete', elset='elset_concrete'))

# Displacements

mdl.add(PinnedDisplacement(name='disp_pinned', nodes='nset_pins'))

# Steps

mdl.add([
    GeneralStep(name='step_bc', displacements=['disp_pinned']),
    ModalStep(name='step_modal', modes=5),
])
mdl.steps_order = ['step_bc', 'step_modal']

# Summary

mdl.summary()

# Run

mdl.analyse_and_extract(fields=['u'])

rhino.plot_mode_shapes(mdl, step='step_modal', layer='mode-')

print(mdl.results['step_modal']['frequencies'])
print(mdl.results['step_modal']['masses'])