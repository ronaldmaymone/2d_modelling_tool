# MyModel.py
from MyShapes import MyPolygon, Shape, MyPoint
from MyGraph import MyGraph # --- NEW ---
import math

class MyModel:
    def __init__(self):
        self.m_shapes = []
        self.m_selected_shapes = [] 
        self.m_intersection_points = []
        self.m_graph: MyGraph = None   
        self.m_found_faces: list[MyPolygon] = []

    def getShapes(self):
        return self.m_shapes
    
    def get_selected_shapes(self):
        return self.m_selected_shapes
    
    def get_intersection_points(self):
        return self.m_intersection_points
        
    # --- NEW ---
    def get_graph(self) -> MyGraph:
        return self.m_graph
    
    def get_found_faces(self) -> list[MyPolygon]:
        return self.m_found_faces
        
    # --- NEW ---
    def add_found_face(self, polygon: MyPolygon):
        self.m_found_faces.append(polygon)
        
    # --- NEW ---
    def clear_found_faces(self):
        self.m_found_faces.clear()

    # --- MODIFIED ---
    def set_intersection_points(self, points_list: list[MyPoint]):
        self.m_intersection_points = points_list

    def clear_intersections(self):
        self.m_intersection_points.clear()

    # --- NEW ---
    def set_graph(self, graph: MyGraph):
        self.m_graph = graph
        
    # --- NEW ---
    def clear_graph(self):
        if self.m_graph:
            self.m_graph.clear()
        self.m_graph = None

    def addShape(self, shape: Shape):
        self.m_shapes.append(shape)

    def add_to_selection(self, shape: Shape):
        if shape not in self.m_selected_shapes:
            self.m_selected_shapes.append(shape)

    def remove_from_selection(self, shape: Shape):
        if shape in self.m_selected_shapes:
            self.m_selected_shapes.remove(shape)

    def clear_selection(self):
        self.m_selected_shapes.clear()
        self.clear_intersections()
        self.clear_graph() # --- NEW ---

    def isEmpty(self):
        return len(self.m_shapes) == 0
    
    def getBoundBox(self):
        # ... (this function is unchanged)
        if self.isEmpty():
            return -1000.0, 1000.0, -1000.0, 1000.0
        
        first_shape = self.m_shapes[0]
        xmin, xmax, ymin, ymax = first_shape.get_bounding_box()
        if xmin == xmax and ymin == ymax: 
            xmin, xmax, ymin, ymax = first_shape.get_control_points()[0].getX(), \
                                     first_shape.get_control_points()[0].getX(), \
                                     first_shape.get_control_points()[0].getY(), \
                                     first_shape.get_control_points()[0].getY()

        for i in range(1, len(self.m_shapes)):
            s_xmin, s_xmax, s_ymin, s_ymax = self.m_shapes[i].get_bounding_box()
            if s_xmin < xmin: xmin = s_xmin
            if s_xmax > xmax: xmax = s_xmax
            if s_ymin < ymin: ymin = s_ymin
            if s_ymax > ymax: ymax = s_ymax
            
        if abs(xmin - xmax) < 1e-6:
            xmin -= 1.0
            xmax += 1.0
        if abs(ymin - ymax) < 1e-6:
            ymin -= 1.0
            ymax += 1.0

        return xmin, xmax, ymin, ymax

    def clear(self):
        """Removes all shapes from the model."""
        self.m_shapes.clear()
        self.clear_selection() # This already clears intersections and graph

    def find_closest_shape(self, query_point: MyPoint, tolerance: float):
        # ... (this function is unchanged)
        min_dist = float('inf')
        closest_shape = None

        for shape in self.m_shapes:
            closest_pt_on_shape, dist = shape.find_closest_point(query_point)
            if dist < min_dist:
                min_dist = dist
                closest_shape = shape
        
        if min_dist <= tolerance:
            return closest_shape, min_dist
        else:
            return None, min_dist