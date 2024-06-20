import os
from typing import Iterable

import numpy as np
from compas.colors import Color
from compas.colors import ColorMap
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Polyhedron
from compas.geometry import Translation
from compas.geometry import Vector
from compas.geometry import sum_vectors
from compas.geometry import Scale

import compas_fea2
from compas_fea2.model.bcs import FixedBC
from compas_fea2.model.bcs import PinnedBC
from compas_fea2.model.bcs import RollerBCX
from compas_fea2.model.bcs import RollerBCY
from compas_fea2.model.bcs import RollerBCZ
from compas_fea2.problem.steps import GeneralStep
from compas_fea2.UI.viewer.shapes import FixBCShape
from compas_fea2.UI.viewer.shapes import PinBCShape
from compas_fea2.UI.viewer.shapes import RollerBCShape
from compas_fea2.model.elements import _Element1D


import os
from compas_viewer.viewer import Viewer
from compas_viewer.scene import GroupObject
from compas_viewer.scene import Collection

# from compas_view2.app import App
# from compas_view2.objects import Collection
# from .controller import FEA2Controller
#
# from qt_material import apply_stylesheet

HERE = os.path.dirname(__file__)
CONFIG = os.path.join(HERE, "config.json")

color_palette = {
    "faces": Color.from_hex("#e8e5d4"),
    "edges": Color.from_hex("#4554ba"),
    "nodes": Color.black,
}


# try:
#     from compas_view2.app import App  # type: ignore
#     from compas_view2.objects import Collection  # type: ignore
#     from compas_view2.shapes import Arrow  # type: ignore
#     from compas_view2.shapes import Text  # type: ignore
# except Exception:
#     if compas_fea2.VERBOSE:
#         print("WARNING: Viewer not loaded!")
#     pass


# class FEA2Viewer:
#     """Wrapper for the compas_view2 viewer app.

#     Parameters
#     ----------
#     width : int, optional
#         Width of the viewport, by default 800.
#     height : int, optional
#         Height of the viewport, by default 500.
#     scale_factor : float, optional
#         Scale the content of the viewport, by default 1.

#     Attributes
#     ----------
#     None
#     """

#     def __init__(self, obj, **kwargs):
#         VIEWER_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config_default.json")
#         sf = kwargs.get("scale_factor", 1)
#         self.app = App(config=VIEWER_CONFIG_FILE)
#         self.obj = obj

#         self.app.view.camera.target = [i * sf for i in self.obj.center]
#         # V = V1 + t * (V2 - V1) / | V2 - V1 |
#         V1 = np.array([0, 0, 0])
#         V2 = np.array(self.app.view.camera.target)
#         delta = V2 - V1
#         length = np.linalg.norm(delta)
#         distance = length * 3
#         unitSlope = delta / length
#         new_position = V1 + unitSlope * distance
#         self.app.view.camera.position = new_position.tolist()

#         self.app.view.camera.near *= sf
#         self.app.view.camera.far *= sf
#         self.app.view.camera.scale *= sf
#         self.app.view.grid.cell_size *= sf

#     def draw_mesh(self, mesh, opacity=1):
#         self.app.add(mesh, use_vertex_color=True, opacity=opacity)

#     def draw_nodes(self, nodes=None, node_lables=False):
#         """Draw nodes.

#         Parameters
#         ----------
#         nodes : [:class:`compas_fea2.model.Node]
#             The nodes to draw.
#         node_lables : bool
#             If `True` add the nodes.
#         """
#         if not nodes:
#             nodes = self.obj.nodes
#         pts = [node.point for node in nodes]
#         self.app.add(Collection(pts), facecolor=Color.from_hex("#386641"))

#         if node_lables:
#             txts = [Text(str(node.input_key), node.point, height=35) for node in nodes]
#         self.app.add(Collection(txts), facecolor=Color.from_hex("#386641"))

#     def draw_solid_elements(self, elements, show_vertices=True, opacity=1.0):
#         """Draw the elements of a part.

#         Parameters
#         ----------
#         elements : :class:`compas_fea2.model.ShellElement` | :class:`compas_fea2.model._Element3D` | :class:`compas_fea2.model.BeamElement`
#             _description_
#         show_vertices : bool, optional
#             If `True` show the vertices of the elements, by default True

#         """
#         collection_items = []
#         for element in elements:
#             pts = [node.point for node in element.nodes]
#             collection_items.append(Polyhedron(pts, list(element._face_indices.values())))
#         if collection_items:
#             self.app.add(Collection(collection_items), facecolor=(0.9, 0.9, 0.9), show_points=show_vertices, opacity=opacity)

#     def draw_shell_elements(self, elements, show_vertices=True, opacity=1, thicken=True):
#         """Draw the elements of a part.

#         Parameters
#         ----------
#         elements : :class:`compas_fea2.model.ShellElement` | :class:`compas_fea2.model.Element3D` | :class:`compas_fea2.model.BeamElement`
#             _description_
#         show_vertices : bool, optional
#             If `True` show the vertices of the elements, by default True

#         """
#         collection_items = []
#         for element in elements:
#             pts = [node.point for node in element.nodes]
#             if len(element.nodes) == 4:
#                 mesh = Mesh.from_vertices_and_faces(pts, [[1, 2, 3, 0]])
#             elif len(element.nodes) == 3:
#                 mesh = Mesh.from_vertices_and_faces(pts, [[0, 1, 2]])
#             else:
#                 raise NotImplementedError("only 3 and 4 vertices shells supported at the moment")
#             if thicken:
#                 mesh.thickened(element.section.t)
#             collection_items.append(mesh)
#         if collection_items:
#             self.app.add(Collection(collection_items), facecolor=(0.9, 0.9, 0.9), show_points=show_vertices, opacity=opacity)

#     def draw_beam_elements(self, elements, show_vertices=True, opacity=1):
#         """Draw the elements of a part.

#         Parameters
#         ----------
#         elements :  :class:`compas_fea2.model.BeamElement`
#             _description_
#         show_vertices : bool, optional
#             If `True` show the vertices of the elements, by default True

#         """
#         collection_items = []
#         for element in elements:
#             pts = [node.point for node in element.nodes]
#             collection_items.append(Line(pts[0], pts[1]))
#         if collection_items:
#             self.app.add(Collection(collection_items), linewidth=10, show_points=show_vertices, opacity=opacity)

#     def draw_nodes_vector(self, pts, vectors, scale_factor=1, colors=None):
#         """Draw vector arrows at nodes.

#         Parameters
#         ----------
#         pts : _type_
#             _description_
#         vectors : _type_
#             _description_
#         colors : tuple, optional
#             _description_, by default (0, 1, 0)
#         """
#         arrows = []
#         arrows_properties = []
#         if not colors:
#             colors = [(0, 1, 0)] * len(pts)
#         for pt, vector, color in zip(pts, vectors, colors):
#             if vector.length:
#                 arrows.append(Arrow(position=pt, direction=vector * scale_factor, head_portion=0.3, head_width=0.15, body_width=0.05))
#                 arrows_properties.append({"u": 3, "show_lines": False, "facecolor": color})
#         if arrows:
#             self.app.add(Collection(arrows, arrows_properties))

#     def draw_loads(self, step, scale_factor=1.0, app_point="end"):
#         """Draw the applied loads for given steps.

#         Parameters
#         ----------
#         steps : [:class:`compas_fea2.problem.Step`]
#             List of steps. Only the loads in these steps will be shown.
#         scale_factor : float, optional
#             Scale the loads reppresentation to have a nicer drawing,
#             by default 1.
#         """
#         if isinstance(step, GeneralStep):
#             pts, vectors = [], []
#             for node, load in step.combination.node_load:
#                 vector = Vector(
#                     x=load.components["x"] or 0.0,
#                     y=load.components["y"] or 0.0,
#                     z=load.components["z"] or 0.0,
#                 )
#                 if vector.length == 0:
#                     continue
#                 vector.scale(scale_factor)
#                 vectors.append(vector)
#                 if app_point == "end":
#                     pts.append([node.x - vector.x, node.y - vector.y, node.z - vector.z])
#                 else:
#                     pts.append([node.point])
#                 # TODO add moment components xx, yy, zz

#             self.draw_nodes_vector(pts, vectors, colors=[(0, 1, 1)] * len(pts))
#         else:
#             print("WARNING! Only point loads are currently supported!")

#     def draw_reactions(self, step, scale_factor=1, colors=None, **kwargs):
#         """Draw the reaction forces as vector arrows at nodes.

#         Parameters
#         ----------
#         pts : _type_
#             _description_
#         vectors : _type_
#             _description_
#         colors : tuple, optional
#             _description_, by default (0, 1, 0)
#         """
#         reactions = step.problem.reaction_field
#         locations = []
#         vectors = []
#         for r in reactions.results(step):
#             locations.append(r.location.xyz)
#             vectors.append(r.vector)
#         self.draw_nodes_vector(locations, vectors, scale_factor=scale_factor, colors=colors)

#     def draw_deformed(self, step, scale_factor=1.0, opacity=1.0, **kwargs):
#         """Display the structure in its deformed configuration.

#         Parameters
#         ----------
#         step : :class:`compas_fea2.problem._Step`, optional
#             The Step of the analysis, by default None. If not provided, the last
#             step is used.

#         Returns
#         -------
#         None

#         """

#         # TODO create a copy of the model first
#         displacements = step.problem.displacement_field
#         for displacement in displacements.results(step):
#             vector = displacement.vector.scaled(scale_factor)
#             displacement.location.xyz = sum_vectors([Vector(*displacement.location.xyz), vector])

#         for part in self.obj.parts:
#             self.draw_beam_elements(part.elements_by_dimension(dimension=1), show_vertices=False, opacity=opacity)
#             self.draw_shell_elements(part.elements_by_dimension(dimension=2), show_vertices=False, opacity=opacity)
#             self.draw_solid_elements(part.elements_by_dimension(dimension=3), show_vertices=False, opacity=opacity)

#     def draw_nodes_field_vector(self, field_results, component, step, vector_sf=1, **kwargs):
#         """Display a given vector field.

#         Parameters
#         ----------
#         field : str
#             The field to display, e.g. 'U' for displacements.
#             Check the :class:`compas_fea2.problem.FieldOutput` for more info about
#             valid components.
#         component : str
#             The compoenet of the field to display, e.g. 'U3' for displacements
#             along the 3 axis.
#             Check the :class:`compas_fea2.problem.FieldOutput` for more info about
#             valid components.
#         step : :class:`compas_fea2.problem.Step`, optional
#             The step to show the results of, by default None.
#             if not provided, the last step of the analysis is used.
#         deformed : bool, optional
#             Choose if to display on the deformed configuration or not, by default False
#         width : int, optional
#             Width of the viewer window, by default 1600
#         height : int, optional
#             Height of the viewer window, by default 900

#         Options
#         -------
#         draw_loads : float
#             Displays the loads at the step scaled by the given value
#         draw_bcs : float
#             Displays the bcs of the model scaled by the given value
#         bound : float
#             limit the results to the given value

#         Raises
#         ------
#         ValueError
#             _description_

#         """

#         # cmap = kwargs.get("cmap", ColorMap.from_palette("hawaii"))

#         # Get values
#         # min_value = field.min_invariants["magnitude"].invariants["MIN(magnitude)"]
#         # max_value = field.max_invariants["magnitude"].invariants["MAX(magnitude)"]

#         # Color the vector field
#         pts, vectors, colors = [], [], []
#         for r in field_results.results(step):
#             if r.vector.length == 0:
#                 continue
#             vectors.append(r.vector.scaled(vector_sf))
#             pts.append(r.location.xyz)
#             # colors.append(cmap(r.invariants["magnitude"], minval=min_value, maxval=max_value))

#         # Display results
#         self.draw_nodes_vector(pts=pts, vectors=vectors, colors=colors)

#     def draw_nodes_field_contour(self, field_results, component, step, **kwargs):
#         """Display a contour plot of a given field and component. The field must
#         de defined at the nodes of the model (e.g displacement field).

#         Parameters
#         ----------
#         field : str
#             The field to display, e.g. 'U' for displacements.
#             Check the :class:`compas_fea2.problem.FieldOutput` for more info about
#             valid components.
#         component : str
#             The compoenet of the field to display, e.g. 'U3' for displacements
#             along the 3 axis.
#             Check the :class:`compas_fea2.problem.FieldOutput` for more info about
#             valid components.
#         step : :class:`compas_fea2.problem.Step`, optional
#             The step to show the results of, by default None.
#             if not provided, the last step of the analysis is used.
#         deformed : bool, optional
#             Choose if to display on the deformed configuration or not, by default False
#         width : int, optional
#             Width of the viewer window, by default 1600
#         height : int, optional
#             Height of the viewer window, by default 900

#         Options
#         -------
#         draw_loads : float
#             Displays the loads at the step scaled by the given value
#         draw_bcs : float
#             Displays the bcs of the model scaled by the given value
#         bound : float
#             limit the results to the given value

#         Raises
#         ------
#         ValueError
#             _description_

#         """
#         cmap = kwargs.get("cmap", ColorMap.from_palette("hawaii"))

#         # Get mesh
#         parts_gkey_vertex = {}
#         parts_mesh = {}
#         for part in step.model.parts:
#             if mesh := part.discretized_boundary_mesh:
#                 colored_mesh = mesh.copy()
#                 # FIXME change precision
#                 parts_gkey_vertex[part.name] = colored_mesh.gkey_vertex(3)
#                 parts_mesh[part.name] = colored_mesh
#             else:
#                 raise AttributeError("Discretized boundary mesh not found")

#         # Set the bounding limits
#         if kwargs.get("bound", None):
#             if not isinstance(kwargs["bound"], Iterable) or len(kwargs["bound"]) != 2:
#                 raise ValueError("You need to provide an upper and lower bound -> (lb, up)")
#             if kwargs["bound"][0] > kwargs["bound"][1]:
#                 kwargs["bound"][0], kwargs["bound"][1] = kwargs["bound"][1], kwargs["bound"][0]

#         # Get values
#         min_result, max_result = field_results.get_limits_component(component, step=step)
#         comp_str = field_results.field_name + str(component)
#         min_value = min_result.components[comp_str]
#         max_value = max_result.components[comp_str]

#         # Color the mesh
#         for r in field_results.results(step):
#             if min_value - max_value == 0.0:
#                 color = Color.red()
#             elif kwargs.get("bound", None):
#                 if r.components[comp_str] >= kwargs["bound"][1] or r.components[comp_str] <= kwargs["bound"][0]:
#                     color = Color.red()
#                 else:
#                     color = cmap(r.components[comp_str], minval=min_value, maxval=max_value)
#             else:
#                 color = cmap(r.components[comp_str], minval=min_value, maxval=max_value)
#             if r.location.gkey in parts_gkey_vertex[part.name]:
#                 parts_mesh[part.name].vertex_attribute(parts_gkey_vertex[part.name][r.location.gkey], "color", color)

#         # Display results
#         for part in step.model.parts:
#             self.draw_mesh(parts_mesh[part.name], opacity=0.75)


#     def draw_nodes_contour(self, model, nodes_values, **kwargs):
#         """ """
#         cmap = kwargs.get("cmap", ColorMap.from_palette("hawaii"))

#         # Get mesh
#         parts_gkey_vertex = {}
#         parts_mesh = {}
#         for part in model.parts:
#             if mesh := part.discretized_boundary_mesh:
#                 colored_mesh = mesh.copy()
#                 # FIXME change precision
#                 parts_gkey_vertex[part.name] = colored_mesh.gkey_vertex(3)
#                 parts_mesh[part.name] = colored_mesh
#             else:
#                 raise AttributeError("Discretized boundary mesh not found")

#         # Set the bounding limits
#         if kwargs.get("bound", None):
#             if not isinstance(kwargs["bound"], Iterable) or len(kwargs["bound"]) != 2:
#                 raise ValueError("You need to provide an upper and lower bound -> (lb, up)")
#             if kwargs["bound"][0] > kwargs["bound"][1]:
#                 kwargs["bound"][0], kwargs["bound"][1] = kwargs["bound"][1], kwargs["bound"][0]

#         # Get values
#         values = list(nodes_values.values())
#         min_value = kwargs["bound"][0] if kwargs.get("bound", None) else min(values)
#         max_value = kwargs["bound"][1] if kwargs.get("bound", None) else min(values)

#         # Color the mesh
#         for n, v in nodes_values.items():
#             if min_value - max_value == 0.0:
#                 color = Color.red()
#             elif kwargs.get("bound", None):
#                 if v >= kwargs["bound"][1] or v <= kwargs["bound"][0]:
#                     color = Color.red()
#                 else:
#                     color = cmap(v, minval=min_value, maxval=max_value)
#             else:
#                 color = cmap(v, minval=min_value, maxval=max_value)
#             if n.gkey in parts_gkey_vertex[part.name]:
#                 parts_mesh[part.name].vertex_attribute(parts_gkey_vertex[part.name][n.gkey], "color", color)

#         # Display results
#         for part in model.parts:
#             self.draw_mesh(parts_mesh[part.name], opacity=0.75)


class FEA2Viewer:
    """
    A viewer for FEA2 models.

    Parameters
    ----------
    center : list of float, optional
        The center of the model in 3D space. Default is [1, 1, 1].
    camera : optional
        Camera settings (not used in current implementation).
    grid : optional
        Grid settings (not used in current implementation).
    scale_model : float, optional
        Scaling factor for the model. Default is 1000.
    args : tuple
        Additional arguments.
    kwargs : dict
        Additional keyword arguments.
    """
    def __init__(self, center=None, camera=None, grid=None, scale_model=1000, *args, **kwargs):
        if center is None:
            center = [1, 1, 1]
        self.viewer = Viewer()
        self._setup_camera(center, scale_model)

    def _setup_camera(self, center, scale_model):
        target = [i * scale_model for i in center]
        self.viewer.renderer.camera.target = target
        self.viewer.config.vectorsize = 0.5

        V1 = np.array([0, 0, 0])
        V2 = np.array(target)
        delta = V2 - V1
        length = np.linalg.norm(delta)
        distance = length * 3
        unit_slope = delta / length
        new_position = V1 + unit_slope * distance

        self.viewer.renderer.camera.position = new_position.tolist()
        self.viewer.renderer.camera.near *= 1
        self.viewer.renderer.camera.far *= 10000
        self.viewer.renderer.camera.scale *= scale_model


class FEA2ModelObject(GroupObject):
    """
    Represents an FEA2 model object in the Viewer.

    Parameters
    ----------
    model : object
        The FEA2 model.
    show_bcs : bool, optional
        Whether to show boundary conditions. Default is True.
    show_parts : bool, optional
        Whether to show parts of the model. Default is True.
    show_interfaces : bool, optional
        Whether to show interfaces in the model. Default is True.
    kwargs : dict
        Additional keyword arguments.
    """
    def __init__(self, model, show_bcs=True, show_parts=True, show_interfaces=True, **kwargs):
        self.show_bcs = show_bcs
        self.show_parts = show_parts
        self.show_interfaces = show_interfaces
        self.face_color = kwargs.get("face_color", color_palette["faces"])
        self.line_color = kwargs.get("line_color", color_palette["edges"])
        self.show_faces = kwargs.get("show_faces", True)
        self.show_lines = kwargs.get("show_lines", True)
        self.show_points = kwargs.get("show_points", True)

        part_meshes = self._get_part_meshes(model) if show_parts else []
        bcs_meshes = self._get_bcs_meshes(model) if show_bcs else []
        interfaces_meshes = self._get_interfaces_meshes(model) if show_interfaces else []

        parts = (part_meshes, {"name": "parts"})
        interfaces = (interfaces_meshes, {"name": "interfaces"})
        bcs = (bcs_meshes, {"name": "bcs"})

        super().__init__([parts, interfaces, bcs], name=model.name, **kwargs)

    def _get_part_meshes(self, model):
        """
        Get meshes for the parts of the model.

        Parameters
        ----------
        model : object
            The FEA2 model.

        Returns
        -------
        list
            List of part meshes.
        """
        part_meshes = []
        for part in model.parts:
            if part._discretized_boundary_mesh:
                part_meshes.append(self._create_mesh_entry(part._discretized_boundary_mesh))
            for element in part.elements:
                if isinstance(element, _Element1D):
                    part_meshes.append(self._create_mesh_entry(element.outermesh, opacity=1.0))
        return part_meshes

    def _get_bcs_meshes(self, model):
        """
        Get meshes for the boundary conditions (BCs) of the model.

        Parameters
        ----------
        model : object
            The FEA2 model.

        Returns
        -------
        list
            List of BC meshes.
        """
        def _get_bc_shape(bc, node):
            if isinstance(bc, PinnedBC):
                return PinBCShape(node.xyz, scale=self.show_bcs).shape
            elif isinstance(bc, FixedBC):
                return FixBCShape(node.xyz, scale=self.show_bcs).shape
            elif isinstance(bc, (RollerBCX, RollerBCY, RollerBCZ)):
                return RollerBCShape(node.xyz, scale=self.show_bcs).shape
            else:
                raise ValueError("Unsupported BC type")
        bcs_meshes = []
        for bc, nodes in model.bcs.items():
            for node in nodes:
                shape = _get_bc_shape(bc, node)
                bcs_meshes.append(self._create_mesh_entry(shape, facecolor=Color.red(), linecolor=Color.red(), show_points=False))
        return bcs_meshes

    def _get_interfaces_meshes(self, model):
        """
        Get meshes for the interfaces in the model.

        Parameters
        ----------
        model : object
            The FEA2 model.

        Returns
        -------
        list
            List of interface meshes.
        """
        from compas_fea2.model import FacesGroup
        interfaces_meshes = []
        for interface in model.interfaces:
            if isinstance(interface.master, FacesGroup):
                mesh = interface.master.mesh
                interfaces_meshes.append(self._create_mesh_entry(mesh, facecolor=Color.red(), linecolor=Color.red(), show_points=False))
        return interfaces_meshes

    def _create_mesh_entry(self, mesh, facecolor=None, linecolor=None, show_faces=None, show_lines=None, show_points=None, opacity=None):
        """
        Create a mesh entry for visualization.

        Parameters
        ----------
        mesh : :class:`compas.datastructures.Mesh`
            The mesh object.
        facecolor : Color, optional
            The face color. Default is None.
        linecolor : Color, optional
            The line color. Default is None.
        show_faces : bool, optional
            Whether to show faces. Default is None.
        show_lines : bool, optional
            Whether to show lines. Default is None.
        show_points : bool, optional
            Whether to show points. Default is None.
        opacity : float, optional
            The opacity of the mesh. Default is None.

        Returns
        -------
        tuple
            The mesh and its visualization properties.
        """
        return (
            mesh,
            {
                "show_faces": show_faces if show_faces is not None else self.show_faces,
                "show_lines": show_lines if show_lines is not None else self.show_lines,
                "show_points": show_points if show_points is not None else self.show_points,
                "facecolor": facecolor if facecolor is not None else self.face_color,
                "linecolor": linecolor if linecolor is not None else self.line_color,
                "opacity": opacity
            }
        )




class FEA2ProblemObject(GroupObject):
    def __init__(self, problem, scale_model=0.01, scale_loads=1, **kwargs):
        vector_sf = 50
        face_color = color_palette["faces"]
        line_color = color_palette["edges"]
        show_faces = True

        loads_meshes = []
        for step in problem, step:
            if isinstance(step, GeneralStep):
                pts, vectors = [], []
                for node, load in step.combination.node_load:
                    vector = Vector(
                        x=load.components["x"] or 0.0,
                        y=load.components["y"] or 0.0,
                        z=load.components["z"] or 0.0,
                    )
                    if vector.length == 0:
                        continue
                    vector.scale(scale_loads)
                    vectors.append(vector)
                    if app_point == "end":
                        pts.append([node.x - vector.x, node.y - vector.y, node.z - vector.z])
                    else:
                        pts.append([node.point])
                    # TODO add moment components xx, yy, zz

                self.draw_nodes_vector(pts, vectors, colors=[(0, 1, 1)] * len(pts))
            else:
                print("WARNING! Only point loads are currently supported!")

        loads = (loads_meshes, {"name": "loads"})
        super().__init__([loads], name=model.name, **kwargs)
