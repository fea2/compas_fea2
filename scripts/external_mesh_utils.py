import numpy as np
from compas.geometry import Plane
from compas.geometry import is_point_on_plane
from compas.datastructures import Mesh
from compas.topology import connected_components

def all_interfaces(part):
    """Extract all interfaces from the part."""
    from compas_fea2.model.interfaces import _Interface
    planes = part.extract_clustered_planes(tol=1, angle_tol=2)
    submeshes = part.extract_submeshes(planes, tol=1, normal_tol=2, split=True)
    return [_Interface(mesh=mesh) for mesh in submeshes]
    
def extract_clustered_planes(mesh, tol=1, angle_tol=2, verbose=False):
    """Extract unique planes from a mesh, clustering coplanar faces."""
    planes = []
    normals = []
    offsets = []
    for fkey in mesh.faces():
        points = [mesh.vertex_coordinates(vkey) for vkey in mesh.face_vertices(fkey)]
        plane = Plane.from_points(*points[:3])
        normal = np.array(plane.normal)
        offset = plane.d
        found = False
        for n, o in zip(normals, offsets):
            angle = np.degrees(np.arccos(np.clip(np.dot(normal, n), -1.0, 1.0)))
            if (abs(angle) < angle_tol or abs(angle - 180) < angle_tol) and abs(offset - o) < tol:
                found = True
                break
        if not found:
            planes.append(plane)
            normals.append(normal)
            offsets.append(offset)
    if verbose:
        print(f"Found {len(planes)} unique planes.")
    return planes

def extract_submeshes(mesh, planes, tol=1, normal_tol=2, split=True):
    """Extract submeshes from a mesh for each plane."""
    submeshes = []
    mesh_normals = np.array([Plane.from_points(*[mesh.vertex_coordinates(vkey) for vkey in mesh.face_vertices(fkey)]).normal for fkey in mesh.faces()])
    for plane in planes:
        normal = np.array(plane.normal)
        dot_products = np.dot(mesh_normals, normal)
        face_indices = np.where(np.abs(dot_products - 1) < normal_tol)[0]
        faces_on_plane = [list(mesh.faces())[i] for i in face_indices]
        submesh = Mesh()
        for fkey in faces_on_plane:
            points = [mesh.vertex_coordinates(vkey) for vkey in mesh.face_vertices(fkey)]
            if all(is_point_on_plane(pt, plane, tol=tol) for pt in points):
                submesh.add_face(points)
        if split:
            for comp in connected_components(submesh):
                submeshes.append(submesh.submesh(comp, delete_faces=False))
        else:
            submeshes.append(submesh)
    return submeshes

def find_boundary_meshes(self, tol) -> List["Mesh"]:
    """Find the boundary meshes of the part.

    Returns
    -------
    list[:class:`compas.datastructures.Mesh`]
        List with the boundary meshes.
    """
    planes = self.extract_clustered_planes(verbose=True)
    submeshes = [Mesh() for _ in planes]
    for element in self.elements:
        for face in element.faces:
            face_points = [node.xyz for node in face.nodes]
            for i, plane in enumerate(planes):
                if all(is_point_on_plane(point, plane, tol=tol) for point in face_points):
                    submeshes[i].join(face.mesh)
                    break

    print("Welding the boundary meshes...")
    from compas_fea2 import PRECISION

    for submesh in submeshes:
        submesh.weld(PRECISION)
    return submeshes


def visualize_node_connectivity(self):
    """Visualizes nodes with color coding based on connectivity."""
    degrees = {node: self.graph.degree(node) for node in self.graph.nodes}
    pos = nx.spring_layout(self.graph)

    node_colors = [degrees[node] for node in self.graph.nodes]

    plt.figure(figsize=(8, 6))
    nx.draw(self.graph, pos, with_labels=True, node_color=node_colors, cmap=plt.cm.Blues, node_size=2000)
    plt.title("Node Connectivity Visualization")
    plt.show()

def visualize_pyvis(self, filename="model_graph.html"):
    """Visualizes the Model-Part and Element-Node graph using Pyvis.
    The graph is saved as an HTML file, which can be opened in a web browser.

    Warnings
    --------
    The Pyvis library must be installed to use this function. This function
    is currently under development and may not work as expected.

    Parameters
    ----------
    filename : str, optional
        The name of the HTML file to save the graph, by default "model_graph.html".
    """
    try:
        from pyvis.network import Network # type: ignore[import]
    except ImportError:
        raise ImportError("The Pyvis library is required for this function. Please install it using 'pip install pyvis'.")

    """Visualizes the Model-Part and Element-Node graph using Pyvis."""
    net = Network(notebook=True, height="750px", width="100%", bgcolor="#222222", font_color="white")

    # # Add all nodes from Model-Part Graph
    # for node in self.model.graph.nodes:
    #     node_type = self.model.graph.nodes[node].get("type", "unknown")

    #     if node_type == "model":
    #         net.add_node(str(node), label="Model", color="red", shape="box", size=30)
    #     elif node_type == "part":
    #         net.add_node(str(node), label=node.name, color="blue", shape="ellipse")

    # # Add all edges from Model-Part Graph
    # for src, dst, data in self.model.graph.edges(data=True):
    #     net.add_edge(str(src), str(dst), color="gray", title=data.get("relation", ""))

    # Add all nodes from Element-Node Graph
    for node in self.graph.nodes:
        node_type = self.graph.nodes[node].get("type", "unknown")

        if node_type == "element":
            net.add_node(str(node), label=node.name, color="yellow", shape="triangle")
        elif node_type == "node":
            net.add_node(str(node), label=node.name, color="green", shape="dot")

    # # Add all edges from Element-Node Graph
    # for src, dst, data in self.graph.edges(data=True):
    #     net.add_edge(str(src), str(dst), color="lightgray", title=data.get("relation", ""))

    # Save and Open
    net.show(filename)
    print(f"Graph saved as {filename} - Open in a browser to view.")