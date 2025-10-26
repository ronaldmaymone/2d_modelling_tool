# MyModel.py
from MyShapes import Shape, MyPoint
import math

class MyModel:
    def __init__(self):
        self.m_shapes = []
        self.m_selected_shapes = [] # --- NEW ---

    def getShapes(self):
        return self.m_shapes
    
    # --- NEW ---
    def get_selected_shapes(self):
        return self.m_selected_shapes

    def addShape(self, shape: Shape):
        self.m_shapes.append(shape)

    # --- NEW ---
    def add_to_selection(self, shape: Shape):
        if shape not in self.m_selected_shapes:
            self.m_selected_shapes.append(shape)

    # --- NEW ---
    def remove_from_selection(self, shape: Shape):
        if shape in self.m_selected_shapes:
            self.m_selected_shapes.remove(shape)

    # --- NEW ---
    def clear_selection(self):
        self.m_selected_shapes.clear()

    def isEmpty(self):
        return len(self.m_shapes) == 0
    
    def getBoundBox(self):
        if self.isEmpty():
            return -1000.0, 1000.0, -1000.0, 1000.0
        
        # --- MODIFIED ---: Get bounding box of all shapes, not just the first
        first_shape = self.m_shapes[0]
        xmin, xmax, ymin, ymax = first_shape.get_bounding_box()
        if xmin == xmax and ymin == ymax: # Handle single point case
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
            
        # --- NEW ---: Add a small margin if bounds are zero
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
        self.clear_selection() # --- NEW ---
    
    # --- NEW ---
    def find_closest_shape(self, query_point: MyPoint, tolerance: float):
        """
        Finds the closest shape to a query point within a given tolerance.
        Returns (shape, distance) or (None, float_max) if no shape is close.
        """
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