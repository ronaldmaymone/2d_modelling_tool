# MyShapes.py
from abc import ABC, abstractmethod
from OpenGL.GL import *
import math

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

    def get_bounding_box(self):
        """Calculates the bounding box of the shape's tessellated points."""
        points_to_check = self.get_tessellated_points()
        if not points_to_check:
            return 0.0, 0.0, 0.0, 0.0
        
        xmin = points_to_check[0].getX()
        xmax = xmin
        ymin = points_to_check[0].getY()
        ymax = ymin

        for p in points_to_check:
            if p.getX() < xmin: xmin = p.getX()
            if p.getX() > xmax: xmax = p.getX()
            if p.getY() < ymin: ymin = p.getY()
            if p.getY() > ymax: ymax = p.getY()
            
        return xmin, xmax, ymin, ymax

class MyLine(Shape):
    def __init__(self, p1: MyPoint, p2: MyPoint):
        super().__init__()
        self.control_points.extend([p1, p2])

    def get_tessellated_points(self):
        return self.control_points

    def get_gl_primitive(self):
        return GL_LINES

class MyPolyline(Shape):
    def __init__(self, points: list[MyPoint]):
        super().__init__()
        self.control_points.extend(points)

    def get_tessellated_points(self):
        return self.control_points

    def get_gl_primitive(self):
        return GL_LINE_STRIP

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
        if start_angle > end_angle:
            start_angle, end_angle = end_angle, start_angle
        
        if not (start_angle <= on_arc_angle <= end_angle):
            start_angle, end_angle = end_angle, start_angle + 2 * math.pi
        
        # Tessellate
        angle_range = end_angle - start_angle
        for i in range(steps + 1):
            angle = start_angle + (angle_range * i / steps)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            self._tessellated_points.append(MyPoint(x, y))

    def get_tessellated_points(self):
        return self._tessellated_points

    def get_gl_primitive(self):
        return GL_LINE_STRIP