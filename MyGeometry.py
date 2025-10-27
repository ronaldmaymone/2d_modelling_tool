# MyGeometry.py
from MyShapes import MyPoint
import math # --- NEW ---

# --- NEW ---
def dist_sq(p1: MyPoint, p2: MyPoint) -> float:
    """Calculates the squared distance between two MyPoint objects."""
    dx = p1.getX() - p2.getX()
    dy = p1.getY() - p2.getY()
    return dx**2 + dy**2

# --- NEW ---
def point_on_segment(p: MyPoint, p1: MyPoint, p2: MyPoint, epsilon=1e-6) -> bool:
    """Checks if a point p lies on the line segment p1-p2."""
    x, y = p.getX(), p.getY()
    x1, y1 = p1.getX(), p1.getY()
    x2, y2 = p2.getX(), p2.getY()

    # 1. Check if p is collinear with p1 and p2
    #    (y - y1) * (x2 - x1) == (y2 - y1) * (x - x1)
    cross_product = (y - y1) * (x2 - x1) - (y2 - y1) * (x - x1)
    if abs(cross_product) > epsilon:
        return False # Not collinear

    # 2. Check if p is within the bounding box of the segment
    xmin, xmax = min(x1, x2), max(x1, x2)
    ymin, ymax = min(y1, y2), max(y1, y2)
    
    on_bbox = (xmin - epsilon <= x <= xmax + epsilon) and \
              (ymin - epsilon <= y <= ymax + epsilon)

    return on_bbox


def find_segment_intersection(p1: MyPoint, p2: MyPoint, p3: MyPoint, p4: MyPoint) -> MyPoint:
    # ... (this function is unchanged)
    x1, y1 = p1.getX(), p1.getY()
    x2, y2 = p2.getX(), p2.getY()
    x3, y3 = p3.getX(), p3.getY()
    x4, y4 = p4.getX(), p4.getY()

    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(den) < 1e-8:
        return None

    t_num = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
    u_num = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3))

    t = t_num / den
    u = u_num / den

    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return MyPoint(ix, iy)

    return None