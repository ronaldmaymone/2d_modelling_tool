import MyModel
from MyShapes import MyPoint, Shape, check_box_intersection

class HoverManager():
    """Manages hover-selection logic."""
    def __init__(self, pixel_box_size=10.0):
        self.m_hovered_shape: Shape = None
        self.m_closest_point_on_shape: MyPoint = None
        self.m_current_mouse_pos: MyPoint = None
        self.m_selection_box_world_size: float = 0.0
        self.m_pixel_box_size = pixel_box_size

    def clear(self):
        """Clears the current hover state."""
        self.m_hovered_shape = None
        self.m_closest_point_on_shape = None
        self.m_current_mouse_pos = None

    def update_world_box_size(self, world_per_pixel: float):
        """Updates the selection box size based on current zoom."""
        self.m_selection_box_world_size = self.m_pixel_box_size * world_per_pixel

    def update_hover(self, mouse_pos: MyPoint, model: MyModel):
        """
        Finds the closest shape whose bounding box intersects the 
        selection box around the mouse.
        """
        self.m_current_mouse_pos = mouse_pos
        self.m_hovered_shape = None # Reset
        self.m_closest_point_on_shape = None

        if self.m_selection_box_world_size == 0.0 or not mouse_pos:
            return

        half_box = self.m_selection_box_world_size / 2.0
        mx, my = mouse_pos.getX(), mouse_pos.getY()
        box_xmin, box_xmax = mx - half_box, mx + half_box
        box_ymin, box_ymax = my - half_box, my + half_box

        min_dist_sq = float('inf')
        best_shape = None
        best_point = None

        for shape in model.getShapes():
            s_xmin, s_xmax, s_ymin, s_ymax = shape.get_bounding_box()
            
            # 1. Check if shape's bounding box intersects the selection box
            if check_box_intersection(box_xmin, box_xmax, box_ymin, box_ymax, 
                                      s_xmin, s_xmax, s_ymin, s_ymax):
                
                # 2. If it does, find the distance from the mouse to this shape
                closest_pt, dist = shape.find_closest_point(mouse_pos)
                dist_sq = dist**2
                
                # 3. Keep track of the one that is closest to the mouse
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    best_shape = shape
                    best_point = closest_pt
        
        # Store the best candidate
        self.m_hovered_shape = best_shape
        self.m_closest_point_on_shape = best_point

    def get_hovered_shape(self) -> Shape:
        return self.m_hovered_shape
    
    def get_closest_point(self) -> MyPoint:
        return self.m_closest_point_on_shape

    def get_selection_box_points(self) -> list[MyPoint]:
        """Gets the 4 corner points of the selection box for drawing."""
        if not self.m_current_mouse_pos:
            return []
        
        half_box = self.m_selection_box_world_size / 2.0
        mx, my = self.m_current_mouse_pos.getX(), self.m_current_mouse_pos.getY()
        
        return [
            MyPoint(mx - half_box, my - half_box), # Bottom-left
            MyPoint(mx + half_box, my - half_box), # Bottom-right
            MyPoint(mx + half_box, my + half_box), # Top-right
            MyPoint(mx - half_box, my + half_box)  # Top-left
        ]