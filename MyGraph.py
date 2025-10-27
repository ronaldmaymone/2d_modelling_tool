from MyShapes import MyPoint
import math

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
        self.edges = []

class GraphEdge:
    """Represents a shattered segment in the graph."""
    def __init__(self, node1: GraphNode, node2: GraphNode):
        self.n1 = node1
        self.n2 = node2

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