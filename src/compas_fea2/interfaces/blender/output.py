from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    from compas_blender.geometry import BlenderMesh
    from compas_blender.utilities import create_layer
    from compas_blender.utilities import clear_layer
    from compas_blender.utilities import draw_cylinder
    from compas_blender.utilities import draw_plane
    from compas_blender.utilities import draw_line
    from compas_blender.utilities import get_meshes
    from compas_blender.utilities import get_objects
    from compas_blender.utilities import get_points
    from compas_blender.utilities import mesh_from_bmesh
    from compas_blender.utilities import set_deselect
    from compas_blender.utilities import set_select
    from compas_blender.utilities import set_objects_coordinates
    from compas_blender.utilities import get_object_property
    from compas_blender.utilities import set_object_property
    from compas_blender.utilities import draw_text
    from compas_blender.utilities import xdraw_mesh
except:
    pass

try:
    import bpy
except:
    pass

from compas.geometry import cross_vectors
from compas.geometry import subtract_vectors

from compas_fea.structure import Structure

from compas_fea.utilities import colorbar
from compas_fea.utilities import extrude_mesh
from compas_fea.utilities import discretise_faces
from compas_fea.utilities import postprocess
from compas_fea.utilities import tets_from_vertices_faces
from compas_fea.utilities import plotvoxels

try:
    from numpy import array
    from numpy import hstack
    from numpy import max
    from numpy import newaxis
    from numpy import where
    from numpy.linalg import norm
except:
    pass

# Author(s): Andrew Liew (github.com/andrewliew), Francesco Ranaudo (github.com/franaudo)


__all__ = [
    'mesh_extrude',
    'plot_concentrated_forces',
    'plot_data',
    'plot_reaction_forces',
    'plot_voxels',
    'weld_meshes_from_layer',
]

class ProblemSolver():
    """Initialises the ProblemSolver object. This object uses a `compas_fea2`
    Problem object to display results in Blender.
    """
    def __init__(self, problem):
        self.problem = problem

    def mesh_extrude(structure, mesh, layers, thickness, mesh_name='', links_name='', blocks_name='', points_name='',
                    plot_mesh=False, plot_links=False, plot_blocks=False, plot_points=False):
        """
        Extrudes a Blender mesh and adds/creates elements.

        Parameters
        ----------
        structure : obj
            Structure object to update.
        mesh : obj
            Blender mesh object.
        layers : int
            Number of layers.
        thickness : float
            Layer thickness.
        mesh_name : str
            Name of set for mesh on final surface.
        links_name : str
            Name of set for adding links along extrusion.
        blocks_name : str
            Name of set for solid elements.
        points_name : str
            Name of aded points.
        plot_mesh : bool
            Plot outer mesh.
        plot_links : bool
            Plot links.
        plot_blocks : bool
            Plot blocks.
        plot_points : bool
            Plot end points.

        Returns
        -------
        None

        Notes
        -----
        - Extrusion is along the vertex normals.

        """

        mesh = mesh_from_bmesh(mesh)
        extrude_mesh(structure=structure, mesh=mesh, layers=layers, thickness=thickness, mesh_name=mesh_name,
                    links_name=links_name, blocks_name=blocks_name)

        # ADD PLOTTING FUNCTIONS HERE


    def plot_concentrated_forces(structure, step, layer=None, scale=1.0):
        """
        Plots reaction forces for the Structure analysis results.

        Parameters
        ----------
        structure : obj
            Structure object.
        step : str
            Name of the Step.
        layer : str
            Layer name for plotting.
        scale : float
            Scale of the arrows.

        Returns
        -------
        None

        """

        if not layer:
            layer = '{0}-{1}'.format(step, 'forces')

        try:
            clear_layer(layer)
        except:
            create_layer(layer)

        cfx   = array(list(structure.results[step]['nodal']['cfx'].values()))[:, newaxis]
        cfy   = array(list(structure.results[step]['nodal']['cfy'].values()))[:, newaxis]
        cfz   = array(list(structure.results[step]['nodal']['cfz'].values()))[:, newaxis]
        cf    = hstack([cfx, cfy, cfz])
        cfm   = norm(cf, axis=1)
        cmax  = max(cfm)
        nodes = array(structure.nodes_xyz())

        for i in where(cfm > 0)[0]:

            sp   = nodes[i, :]
            ep   = nodes[i, :] + cf[i, :] * -scale * 0.001
            col  = colorbar(cfm[i] / cmax, input='float', type=1)
            line = draw_line(start=sp, end=ep, width=0.01, color=col, layer=layer)

            set_object_property(object=line, property='cfx', value=cf[i, 0])
            set_object_property(object=line, property='cfy', value=cf[i, 1])
            set_object_property(object=line, property='cfz', value=cf[i, 2])
            set_object_property(object=line, property='cfm', value=cfm[i])


    def plot_data(structure, step, field='um', layer=None, scale=1.0, radius=0.05, cbar=[None, None], iptype='mean',
                nodal='mean', mode='', cbar_size=1):
        """
        Plots analysis results on the deformed shape of the Structure.

        Parameters
        ----------
        structure : obj
            Structure object.
        step : str
            Name of the Step.
        field : str
            Field to plot, e.g. 'um', 'sxx', 'sm1'.
        layer : str
            Layer name for plotting.
        scale : float
            Scale on displacements for the deformed plot.
        radius : float
            Radius of the pipe visualisation meshes.
        cbar : list
            Minimum and maximum limits on the colorbar.
        iptype : str
            'mean', 'max' or 'min' of an element's integration point data.
        nodal : str
            'mean', 'max' or 'min' for nodal values.
        mode : int
            Mode or frequency number to plot, for modal, harmonic or buckling analysis.
        cbar_size : float
            Scale on the size of the colorbar.

        Returns
        -------
        None

        Notes
        -----
        - Pipe visualisation of line elements is not based on the element section.

        """

        if field in ['smaxp', 'smises']:
            nodal  = 'max'
            iptype = 'max'

        elif field in ['sminp']:
            nodal  = 'min'
            iptype = 'min'

        # Create and clear Blender layer

        if not layer:
            layer = '{0}-{1}{2}'.format(step, field, mode)

        try:
            clear_layer(layer)
        except:
            create_layer(layer)

        # Node and element data

        nodes      = structure.nodes_xyz()
        elements   = [structure.elements[i].nodes for i in sorted(structure.elements, key=int)]
        nodal_data = structure.results[step]['nodal']
        nkeys      = sorted(structure.nodes, key=int)

        ux = [nodal_data['ux{0}'.format(mode)][i] for i in nkeys]
        uy = [nodal_data['uy{0}'.format(mode)][i] for i in nkeys]
        uz = [nodal_data['uz{0}'.format(mode)][i] for i in nkeys]

        try:
            data  = [nodal_data['{0}{1}'.format(field, mode)][i] for i in nkeys]
            dtype = 'nodal'

        except(Exception):
            data  = structure.results[step]['element'][field]
            dtype = 'element'

        # Postprocess

        result = postprocess(nodes, elements, ux, uy, uz, data, dtype, scale, cbar, 1, iptype, nodal)

        try:
            toc, U, NodeBases, fabs, fscaled, ElementBases, eabs = result
            U = array(U)
            print('\n***** Data processed : {0} s *****'.format(toc))

        except:
            print('\n***** Error encountered during data processing or plotting *****')

        # Plot meshes

        npts = 8
        mesh_faces  = []
        block_faces = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        tet_faces   = [[0, 2, 1], [1, 2, 3], [1, 3, 0], [0, 3, 2]]
        pipes       = []
        mesh_add    = []

        for element, nodes in enumerate(elements):

            n = len(nodes)

            if n == 2:

                u, v = nodes
                pipe = draw_cylinder(start=U[u], end=U[v], radius=radius, div=npts, layer=layer)
                pipes.append(pipe)

                if dtype == 'element':
                    col1 = col2 = ElementBases[element]

                elif dtype == 'nodal':
                    col1 = NodeBases[u]
                    col2 = NodeBases[v]

                try:
                    blendermesh = BlenderMesh(object=pipe)
                    blendermesh.set_vertices_colors({i: col1 for i in range(0, 2 * npts, 2)})
                    blendermesh.set_vertices_colors({i: col2 for i in range(1, 2 * npts, 2)})
                except:
                    pass

            elif n in [3, 4]:

                if structure.elements[element].__name__ in ['ShellElement', 'MembraneElement']:
                    mesh_faces.append(nodes)
                else:
                    for face in tet_faces:
                        mesh_faces.append([nodes[i] for i in face])

            elif n == 8:

                for block in block_faces:
                    mesh_faces.append([nodes[i] for i in block])

        if mesh_faces:

            bmesh = xdraw_mesh(name='bmesh', vertices=U, faces=mesh_faces, layer=layer)
            blendermesh = BlenderMesh(bmesh)
            blendermesh.set_vertices_colors({i: col for i, col in enumerate(NodeBases)})
            mesh_add = [bmesh]

        # Plot colourbar

        xr, yr, _ = structure.node_bounds()
        yran = yr[1] - yr[0] if yr[1] - yr[0] else 1
        s    = yran * 0.1 * cbar_size
        xmin = xr[1] + 3 * s
        ymin = yr[0]

        cmesh = draw_plane(name='colorbar', Lx=s, dx=s, Ly=10*s, dy=s, layer=layer)
        set_objects_coordinates(objects=[cmesh], coords=[[xmin, ymin, 0]])
        blendermesh = BlenderMesh(object=cmesh)
        vertices    = blendermesh.get_vertices_coordinates().values()

        y  = array(list(vertices))[:, 1]
        yn = yran * cbar_size
        colors = colorbar(((y - ymin - 0.5 * yn) * 2 / yn)[:, newaxis], input='array', type=1)
        blendermesh.set_vertices_colors({i: j for i, j in zip(range(len(vertices)), colors)})

        set_deselect()
        set_select(objects=pipes + mesh_add + [cmesh])
        bpy.context.view_layer.objects.active = cmesh
        bpy.ops.object.join()

        h = 0.6 * s

        for i in range(5):

            x0 = xmin + 1.2 * s
            yu = ymin + (5.8 + i) * s
            yl = ymin + (3.8 - i) * s
            vu = +max([eabs, fabs]) * (i + 1) / 5.
            vl = -max([eabs, fabs]) * (i + 1) / 5.

            draw_text(radius=h, pos=[x0, yu, 0], text='{0:.3g}'.format(vu), layer=layer)
            draw_text(radius=h, pos=[x0, yl, 0], text='{0:.3g}'.format(vl), layer=layer)

        draw_text(radius=h, pos=[x0,  ymin + 4.8 * s, 0], text='0', layer=layer)
        draw_text(radius=h, pos=[xmin, ymin + 12 * s, 0], text='Step:{0}   Field:{1}'.format(step, field), layer=layer)


    def plot_reaction_forces(structure, step, layer=None, scale=1.0):
        """
        Plots reaction forces for the Structure analysis results.

        Parameters
        ----------
        structure : obj
            Structure object.
        step : str
            Name of the Step.
        layer : str
            Layer name for plotting.
        scale : float
            Scale of the arrows.

        Returns
        -------
        None

        """

        if not layer:
            layer = '{0}-{1}'.format(step, 'reactions')

        try:
            clear_layer(layer)
        except:
            create_layer(layer)

        rfx   = array(list(structure.results[step]['nodal']['rfx'].values()))[:, newaxis]
        rfy   = array(list(structure.results[step]['nodal']['rfy'].values()))[:, newaxis]
        rfz   = array(list(structure.results[step]['nodal']['rfz'].values()))[:, newaxis]
        rf    = hstack([rfx, rfy, rfz])
        rfm   = norm(rf, axis=1)
        rmax  = max(rfm)
        nodes = array(structure.nodes_xyz())

        for i in where(rfm > 0)[0]:

            sp   = nodes[i, :]
            ep   = nodes[i, :] + rf[i, :] * -scale * 0.001
            col  = colorbar(rfm[i] / rmax, input='float', type=1)
            line = draw_line(start=sp, end=ep, width=0.01, color=col, layer=layer)

            set_object_property(object=line, property='rfx', value=rf[i, 0])
            set_object_property(object=line, property='rfy', value=rf[i, 1])
            set_object_property(object=line, property='rfz', value=rf[i, 2])
            set_object_property(object=line, property='rfm', value=rfm[i])


    def plot_voxels(structure, step, field='smises', cbar=[None, None], iptype='mean', nodal='mean', vdx=None, mode=''):
        """
        Voxel 4D visualisation.

        Parameters
        ----------
        structure : obj
            Structure object.
        step : str
            Name of the Step.
        field : str
            Field to plot, e.g. 'smises'.
        cbar : list
            Minimum and maximum limits on the colorbar.
        iptype : str
            'mean', 'max' or 'min' of an element's integration point data.
        nodal : str
            'mean', 'max' or 'min' for nodal values.
        vdx : float
            Voxel spacing.
        mode : int
            mode or frequency number to plot, in case of modal, harmonic or buckling analysis.

        Returns
        -------
        None

        """

        # Node and element data


        xyz        = structure.nodes_xyz()
        elements   = [structure.elements[i].nodes for i in sorted(structure.elements, key=int)]
        nodal_data = structure.results[step]['nodal']
        nkeys      = sorted(structure.nodes, key=int)

        ux = [nodal_data['ux{0}'.format(mode)][i] for i in nkeys]
        uy = [nodal_data['uy{0}'.format(mode)][i] for i in nkeys]
        uz = [nodal_data['uz{0}'.format(mode)][i] for i in nkeys]

        try:
            data = [nodal_data[field + str(mode)][key] for key in nkeys]
            dtype = 'nodal'

        except(Exception):
            data = structure.results[step]['element'][field]
            dtype = 'element'

        # Postprocess

        result = postprocess(xyz, elements, ux, uy, uz, data, dtype, 1, cbar, 1, iptype, nodal)

        try:
            toc, U, NodeBases, fabs, fscaled, ElementBases, eabs = result
            U = array(U)
            print('\n***** Data processed : {0:.3f} s *****'.format(toc))

        except:
            print('\n***** Error post-processing *****')

        try:
            plotvoxels(values=fscaled, U=U, vdx=vdx)

        except:
            print('\n***** Error plotting voxels *****')


    def weld_meshes_from_layer(layer_input, layer_output):
        """
        Grab meshes on an input layer and weld them onto an output layer.

        Parameters
        ----------
        layer_input : str
            Layer containing the Blender meshes to weld.
        layer_output : str
            Layer to plot single welded mesh.

        Returns
        -------
        None

        """

        print('Welding meshes on layer:{0}'.format(layer_input))

        S = Structure(path=' ')

        add_nodes_elements_from_layers(S, mesh_type='ShellElement', layers=layer_input)

        faces = []

        for element in S.elements.values():
            faces.append(element.nodes)

        try:
            clear_layer(layer_output)
        except:
            create_layer(layer_output)

        vertices = S.nodes_xyz()

        xdraw_mesh(name='welded_mesh', vertices=vertices, faces=faces, layer=layer_output)
