# MyShapes.py
from abc import ABC, abstractmethod
from OpenGL.GL import *
import math

# --- NEW HELPER FUNCTIONS ---

def point_dist_sq(p1: 'MyPoint', p2: 'MyPoint') -> float:
    """Calculates the squared distance between two MyPoint objects."""
    dx = p1.getX() - p2.getX()
    dy = p1.getY() - p2.getY()
    return dx**2 + dy**2

def point_to_segment_dist_sq(p: 'MyPoint', p1: 'MyPoint', p2: 'MyPoint') -> (float, 'MyPoint'):
    """
    Calculates the squared distance from point p to line segment p1-p2.
    Returns (squared_distance, closest_point_on_segment).
    """
    l2 = point_dist_sq(p1, p2)
    if l2 == 0.0: # Segment is just a point
        return point_dist_sq(p, p1), p1
    
    # Project p onto the line defined by p1 and p2
    t = ((p.getX() - p1.getX()) * (p2.getX() - p1.getX()) + 
         (p.getY() - p1.getY()) * (p2.getY() - p1.getY())) / l2
    
    # Clamp t to the [0, 1] range to stay on the segment
    t = max(0.0, min(1.0, t))
    
    projection = MyPoint(p1.getX() + t * (p2.getX() - p1.getX()),
                         p1.getY() + t * (p2.getY() - p1.getY()))
    
    return point_dist_sq(p, projection), projection

def check_box_intersection(xmin1, xmax1, ymin1, ymax1, xmin2, xmax2, ymin2, ymax2) -> bool:
    """Checks if two AABB (Axis-Aligned Bounding Boxes) intersect."""
    # Check for no overlap on X axis
    if xmax1 < xmin2 or xmin1 > xmax2:
        return False
    # Check for no overlap on Y axis
    if ymax1 < ymin2 or ymin1 > ymax2:
        return False
    return True # Overlap on both axes

# --- END NEW HELPER FUNCTIONS ---


class MyPoint:
    """Represents a point in 2D space."""
    def __init__(self, _x=0.0, _y=0.0):
        self.m_x = _x
        self.m_y = _y

    def setX(self, _x):
        self.m_x = _x

    def setY(self, _y):
        self.m_y = _y

    def getX(self):
        return self.m_x

    def getY(self):
        return self.m_y

class Shape(ABC):
    """Abstract base class for all shapes."""
    def __init__(self):
        self.control_points = []

    def get_control_points(self):
        return self.control_points

    @abstractmethod
    def get_tessellated_points(self):
        """Returns a list of vertices for drawing the shape."""
        pass

    @abstractmethod
    def get_gl_primitive(self):
        """Returns the OpenGL primitive type for drawing (e.g., GL_LINES)."""
        pass
        
    # --- NEW ---
    @abstractmethod
    def find_closest_point(self, query_point: MyPoint) -> (MyPoint, float):
        """
        Finds the closest point on the shape to the query_point.
        Returns (closest_point, distance).
        """
        pass

    def get_bounding_box(self):
        """Calculates the bounding box of the shape's tessellated points."""
        # --- MODIFIED ---: Check control points if tessellated points are empty
        points_to_check = self.get_tessellated_points()
        if not points_to_check:
            points_to_check = self.get_control_points()
            if not points_to_check:
                return 0.0, 0.0, 0.0, 0.0
        
        xmin = points_to_check[0].getX()
        xmax = xmin
        ymin = points_to_check[0].getY()
        ymax = ymin

        for p in points_to_check[1:]: # Start from 1
            if p.getX() < xmin: xmin = p.getX()
            if p.getX() > xmax: xmax = p.getX()
            if p.getY() < ymin: ymin = p.getY()
            if p.getY() > ymax: ymax = p.getY()
            
        return xmin, xmax, ymin, ymax
    
    # --- NEW ---
    def _find_closest_point_on_polyline(self, query_point: MyPoint, points: list[MyPoint], is_loop: bool) -> (MyPoint, float):
        """Helper to find the closest point on a list of line segments."""
        if not points:
            return None, float('inf')
        
        min_dist_sq = float('inf')
        closest_point = None

        if len(points) == 1:
            dist_sq = point_dist_sq(query_point, points[0])
            return points[0], math.sqrt(dist_sq)

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            dist_sq, proj_point = point_to_segment_dist_sq(query_point, p1, p2)
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_point = proj_point
        
        if is_loop: # Check the closing segment
            p1 = points[-1]
            p2 = points[0]
            dist_sq, proj_point = point_to_segment_dist_sq(query_point, p1, p2)
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_point = proj_point
                
        return closest_point, math.sqrt(min_dist_sq)


class MyLine(Shape):
    def __init__(self, p1: MyPoint, p2: MyPoint):
        super().__init__()
        self.control_points.extend([p1, p2])

    def get_tessellated_points(self):
        return self.control_points

    def get_gl_primitive(self):
        return GL_LINES

    # --- NEW ---
    def find_closest_point(self, query_point: MyPoint) -> (MyPoint, float):
        p1, p2 = self.control_points
        dist_sq, closest_pt = point_to_segment_dist_sq(query_point, p1, p2)
        return closest_pt, math.sqrt(dist_sq)

class MyPolyline(Shape):
    def __init__(self, points: list[MyPoint]):
        super().__init__()
        self.control_points.extend(points)

    def get_tessellated_points(self):
        return self.control_points

    def get_gl_primitive(self):
        return GL_LINE_STRIP

    # --- NEW ---
    def find_closest_point(self, query_point: MyPoint) -> (MyPoint, float):
        return self._find_closest_point_on_polyline(query_point, self.control_points, is_loop=False)

class MyQuadBezier(Shape):
    def __init__(self, p1: MyPoint, p2: MyPoint, p3: MyPoint, steps=20):
        super().__init__()
        self.control_points.extend([p1, p2, p3])
        self._tessellated_points = []
        self._tessellate(steps)

    def _tessellate(self, steps):
        p0, p1, p2 = self.control_points
        for i in range(steps + 1):
            t = i / steps
            inv_t = 1 - t
            x = (inv_t**2 * p0.getX()) + (2 * inv_t * t * p1.getX()) + (t**2 * p2.getX())
            y = (inv_t**2 * p0.getY()) + (2 * inv_t * t * p1.getY()) + (t**2 * p2.getY())
            self._tessellated_points.append(MyPoint(x, y))

    def get_tessellated_points(self):
        return self._tessellated_points

    def get_gl_primitive(self):
        return GL_LINE_STRIP

    # --- NEW ---
    def find_closest_point(self, query_point: MyPoint) -> (MyPoint, float):
        # Approximate by checking tessellated segments
        return self._find_closest_point_on_polyline(query_point, self._tessellated_points, is_loop=False)

class MyCubicBezier(Shape):
    def __init__(self, p1: MyPoint, p2: MyPoint, p3: MyPoint, p4: MyPoint, steps=30):
        super().__init__()
        self.control_points.extend([p1, p2, p3, p4])
        self._tessellated_points = []
        self._tessellate(steps)

    def _tessellate(self, steps):
        p0, p1, p2, p3 = self.control_points
        for i in range(steps + 1):
            t = i / steps
            inv_t = 1 - t
            x = (inv_t**3 * p0.getX()) + (3 * inv_t**2 * t * p1.getX()) + (3 * inv_t * t**2 * p2.getX()) + (t**3 * p3.getX())
            y = (inv_t**3 * p0.getY()) + (3 * inv_t**2 * t * p1.getY()) + (3 * inv_t * t**2 * p2.getY()) + (t**3 * p3.getY())
            self._tessellated_points.append(MyPoint(x, y))

    def get_tessellated_points(self):
        return self._tessellated_points
        
    def get_gl_primitive(self):
        return GL_LINE_STRIP

    # --- NEW ---
    def find_closest_point(self, query_point: MyPoint) -> (MyPoint, float):
        # Approximate by checking tessellated segments
        return self._find_closest_point_on_polyline(query_point, self._tessellated_points, is_loop=False)

class MyCircle(Shape):
    def __init__(self, center: MyPoint, radius: float, steps=40):
        super().__init__()
        self.control_points.append(center)
        self.radius = radius
        self._tessellated_points = []
        self._tessellate(steps)
    
    def _tessellate(self, steps):
        cx, cy = self.control_points[0].getX(), self.control_points[0].getY()
        for i in range(steps + 1):
            angle = 2.0 * math.pi * i / steps
            x = cx + self.radius * math.cos(angle)
            y = cy + self.radius * math.sin(angle)
            self._tessellated_points.append(MyPoint(x, y))

    def get_tessellated_points(self):
        return self._tessellated_points
    
    def get_gl_primitive(self):
        return GL_LINE_LOOP

    # --- NEW ---
    def find_closest_point(self, query_point: MyPoint) -> (MyPoint, float):
        # For a circle, we can calculate this analytically
        cx, cy = self.control_points[0].getX(), self.control_points[0].getY()
        center = self.control_points[0]
        
        dx = query_point.getX() - cx
        dy = query_point.getY() - cy
        dist_to_center = math.sqrt(dx**2 + dy**2)
        
        if dist_to_center == 0.0: # Query point is the center
            return MyPoint(cx + self.radius, cy), self.radius # Return any point on the circumference
            
        # Calculate point on circumference
        closest_x = cx + dx * (self.radius / dist_to_center)
        closest_y = cy + dy * (self.radius / dist_to_center)
        
        closest_pt = MyPoint(closest_x, closest_y)
        dist = abs(dist_to_center - self.radius)
        
        return closest_pt, dist

class MyCircleArc(Shape):
    def __init__(self, p_start: MyPoint, p_end: MyPoint, p_on_arc: MyPoint, steps=40):
        super().__init__()
        self.control_points.extend([p_start, p_end, p_on_arc])
        self._tessellated_points = []
        self._calculate_and_tessellate(steps)

    def _calculate_and_tessellate(self, steps):
        p1, p2, p3 = self.control_points
        x1, y1 = p1.getX(), p1.getY()
        x2, y2 = p2.getX(), p2.getY()
        x3, y3 = p3.getX(), p3.getY()

        # Denominator for circumcenter calculation
        D = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        if abs(D) < 1e-8: # Points are collinear, draw a line
            self._tessellated_points = [p1, p2]
            return

        # Calculate circumcenter (cx, cy)
        sq1, sq2, sq3 = x1**2 + y1**2, x2**2 + y2**2, x3**2 + y3**2
        cx = (sq1 * (y2 - y3) + sq2 * (y3 - y1) + sq3 * (y1 - y2)) / D
        cy = (sq1 * (x3 - x2) + sq2 * (x1 - x3) + sq3 * (x2 - x1)) / D
        
        radius = math.sqrt((x1 - cx)**2 + (y1 - cy)**2)
        
        # Calculate angles
        start_angle = math.atan2(y1 - cy, x1 - cx)
        end_angle = math.atan2(y2 - cy, x2 - cx)
        on_arc_angle = math.atan2(y3 - cy, y3 - cx)

        # Ensure correct winding order
        angle_range = end_angle - start_angle
        on_arc_range = on_arc_angle - start_angle
        
        # Normalize angles to [0, 2*pi]
        while angle_range <= 0: angle_range += 2 * math.pi
        while on_arc_range <= 0: on_arc_range += 2 * math.pi

        if on_arc_range > angle_range: # p3 is not "between" p1 and p2, swap
             start_angle, end_angle = end_angle, start_angle
             angle_range = end_angle - start_angle
             while angle_range <= 0: angle_range += 2 * math.pi

        # Tessellate
        for i in range(steps + 1):
            angle = start_angle + (angle_range * i / steps)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            self._tessellated_points.append(MyPoint(x, y))

    def get_tessellated_points(self):
        return self._tessellated_points

    def get_gl_primitive(self):
        return GL_LINE_STRIP

    # --- NEW ---
    def find_closest_point(self, query_point: MyPoint) -> (MyPoint, float):
        # Approximate by checking tessellated segments
        return self._find_closest_point_on_polyline(query_point, self._tessellated_points, is_loop=False)
    

class MyPolygon(Shape):
    """Represents a simple, non-self-intersecting polygon."""
    def __init__(self, points: list[MyPoint]):
        super().__init__()
        self.control_points.extend(points)
        # For a simple polygon, tessellated points are the same as control points
        self._tessellated_points = self.control_points

    def get_tessellated_points(self):
        return self._tessellated_points

    def get_gl_primitive(self):
        # GL_TRIANGLE_FAN is a good, efficient way to draw a simple polygon
        return GL_TRIANGLE_FAN

    def find_closest_point(self, query_point: MyPoint) -> (MyPoint, float):
        # Find closest point on the polygon's boundary (edges)
        return self._find_closest_point_on_polyline(query_point, self._tessellated_points, is_loop=True)