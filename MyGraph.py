from MyShapes import MyPoint
import math
from MyGeometry import get_angle

# --- NEW HELPER ---
# We need this here for the node-finding logic
def dist_sq(p1: MyPoint, p2: MyPoint) -> float:
    """Calculates the squared distance between two MyPoint objects."""
    dx = p1.getX() - p2.getX()
    dy = p1.getY() - p2.getY()
    return dx**2 + dy**2

class GraphNode:
    """Represents a vertex in the graph (an endpoint or intersection)."""
    def __init__(self, point: MyPoint):
        self.point = point
        self.edges: list[GraphEdge] = [] # --- MODIFIED ---

    # --- NEW ---
    def get_sorted_edges(self, incoming_edge: 'GraphEdge' = None) -> list['GraphEdge']:
        """
        Sorts connected edges by angle, clockwise.
        If incoming_edge is provided, sorts relative to that edge's angle.
        """
        if not self.edges:
            return []

        # 1. Get angle of the incoming edge (vector IN to self)
        if incoming_edge:
            # Get the node we came from
            prev_node = incoming_edge.n1 if incoming_edge.n2 == self else incoming_edge.n2
            ref_angle = get_angle(self.point, prev_node.point)
        else:
            ref_angle = -math.pi # Default (points right)

        # 2. Calculate relative angles for all other edges
        edge_angles = []
        for edge in self.edges:
            if edge == incoming_edge:
                continue
            
            # Get the node we are going to
            next_node = edge.n1 if edge.n2 == self else edge.n2
            out_angle = get_angle(self.point, next_node.point)
            
            # Calculate angle relative to ref_angle, in range [0, 2*pi]
            delta = ref_angle - out_angle
            while delta <= 0:
                delta += 2 * math.pi
                
            edge_angles.append((delta, edge))
            
        # 3. Sort by the relative angle (smallest delta is the next one clockwise)
        edge_angles.sort(key=lambda x: x[0])
        
        return [edge for delta, edge in edge_angles]


class GraphEdge:
    """Represents a shattered segment in the graph."""
    def __init__(self, node1: GraphNode, node2: GraphNode):
        self.n1 = node1
        self.n2 = node2
        self.visited_forward = False  # For n1 -> n2
        self.visited_backward = False # For n2 -> n1

    # --- NEW ---
    def set_visited(self, from_node: GraphNode):
        """Marks the edge as visited in the direction *away* from from_node."""
        if from_node == self.n1:
            self.visited_forward = True
        else:
            self.visited_backward = True

    # --- NEW ---
    def get_other_node(self, node: GraphNode) -> GraphNode:
        """Returns the node at the *other* end of the edge."""
        return self.n2 if node == self.n1 else self.n1

    # --- NEW ---
    def was_visited_from(self, from_node: GraphNode) -> bool:
        """Checks if the edge was visited in the direction *away* from from_node."""
        if from_node == self.n1:
            return self.visited_forward
        else:
            return self.visited_backward

class MyGraph:
    """Holds all nodes and edges for the planar graph."""
    def __init__(self, epsilon=1e-6):
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self.epsilon = epsilon
        self.epsilon_sq = epsilon**2

    def get_nodes(self) -> list[GraphNode]:
        return self.nodes

    def get_edges(self) -> list[GraphEdge]:
        return self.edges

    def find_node_at(self, point: MyPoint) -> GraphNode:
        """Finds a node at a given point, checking within an epsilon tolerance."""
        for node in self.nodes:
            if dist_sq(node.point, point) < self.epsilon_sq:
                return node
        return None

    def add_node(self, point: MyPoint) -> GraphNode:
        """Adds a new node at a point if one doesn't already exist."""
        existing_node = self.find_node_at(point)
        if existing_node:
            return existing_node
        
        new_node = GraphNode(point)
        self.nodes.append(new_node)
        return new_node

    def add_edge(self, node1: GraphNode, node2: GraphNode):
        """Adds a new edge between two nodes if it doesn't already exist."""
        if node1 == node2:
            return # Don't add zero-length edges

        # Check for duplicates
        for edge in self.edges:
            if (edge.n1 == node1 and edge.n2 == node2) or \
               (edge.n1 == node2 and edge.n2 == node1):
                return
        
        new_edge = GraphEdge(node1, node2)
        self.edges.append(new_edge)
        node1.edges.append(new_edge)
        node2.edges.append(new_edge)

    def clear(self):
        self.nodes.clear()
        self.edges.clear()

    def reset_visited_flags(self):
        """Resets all edge visited flags to False."""
        for edge in self.edges:
            edge.visited_forward = False
            edge.visited_backward = False