from abc import ABC, abstractmethod
from OpenGL.GL import *

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
        if not self.get_tessellated_points():
            return 0.0, 0.0, 0.0, 0.0
        
        points_to_check = self.get_tessellated_points()
        
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
    """Represents a line segment defined by two points."""
    def __init__(self, p1: MyPoint, p2: MyPoint):
        super().__init__()
        self.control_points.extend([p1, p2])

    def get_tessellated_points(self):
        return self.control_points

    def get_gl_primitive(self):
        return GL_LINES

class MyQuadBezier(Shape):
    """Represents a quadratic Bézier curve defined by three control points."""
    def __init__(self, p1: MyPoint, p2: MyPoint, p3: MyPoint, steps=20):
        super().__init__()
        self.control_points.extend([p1, p2, p3])
        self.steps = steps
        self._tessellated_points = []
        self._tessellate()

    def _tessellate(self):
        self._tessellated_points.clear()
        p0, p1, p2 = self.control_points
        for i in range(self.steps + 1):
            t = i / self.steps
            inv_t = 1 - t
            
            x = (inv_t**2 * p0.getX()) + (2 * inv_t * t * p1.getX()) + (t**2 * p2.getX())
            y = (inv_t**2 * p0.getY()) + (2 * inv_t * t * p1.getY()) + (t**2 * p2.getY())
            
            self._tessellated_points.append(MyPoint(x, y))

    def get_tessellated_points(self):
        return self._tessellated_points

    def get_gl_primitive(self):
        return GL_LINE_STRIP

class MyCubicBezier(Shape):
    """Represents a cubic Bézier curve defined by four control points."""
    def __init__(self, p1: MyPoint, p2: MyPoint, p3: MyPoint, p4: MyPoint, steps=30):
        super().__init__()
        self.control_points.extend([p1, p2, p3, p4])
        self.steps = steps
        self._tessellated_points = []
        self._tessellate()

    def _tessellate(self):
        self._tessellated_points.clear()
        p0, p1, p2, p3 = self.control_points
        for i in range(self.steps + 1):
            t = i / self.steps
            inv_t = 1 - t
            
            x = (inv_t**3 * p0.getX()) + (3 * inv_t**2 * t * p1.getX()) + \
                (3 * inv_t * t**2 * p2.getX()) + (t**3 * p3.getX())
            y = (inv_t**3 * p0.getY()) + (3 * inv_t**2 * t * p1.getY()) + \
                (3 * inv_t * t**2 * p2.getY()) + (t**3 * p3.getY())
                
            self._tessellated_points.append(MyPoint(x, y))

    def get_tessellated_points(self):
        return self._tessellated_points
        
    def get_gl_primitive(self):
        return GL_LINE_STRIP