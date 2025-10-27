# MyCanvas.py
from PySide6 import QtOpenGLWidgets
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QWheelEvent
from OpenGL.GL import *
from MyModel import MyModel
from MyGraph import MyGraph # --- NEW ---
from MyShapes import (
    MyPoint, MyLine, MyQuadBezier, MyCubicBezier, MyCircle, 
    MyCircleArc, MyPolyline, Shape, check_box_intersection
)
# --- MODIFIED ---
from MyGeometry import find_segment_intersection, point_on_segment, dist_sq
from enum import Enum
import math

class CanvasModes(Enum):
    # ... (unchanged)
    FREE_MOVE = 0
    LINE_CREATION = 1
    POLYLINE_CREATION = 2
    QUAD_BEZIER_CREATION = 3
    CUBIC_BEZIER_CREATION = 4
    CIRCLE_CREATION = 5
    CIRCLE_ARC_CREATION = 6
    SELECTION_MODE = 7

class HoverManager:
    # ... (class is unchanged)
    def __init__(self, pixel_box_size=10.0):
        self.m_hovered_shape: Shape = None
        self.m_closest_point_on_shape: MyPoint = None
        self.m_current_mouse_pos: MyPoint = None
        self.m_selection_box_world_size: float = 0.0
        self.m_pixel_box_size = pixel_box_size

    def clear(self):
        self.m_hovered_shape = None
        self.m_closest_point_on_shape = None
        self.m_current_mouse_pos = None

    def update_world_box_size(self, world_per_pixel: float):
        self.m_selection_box_world_size = self.m_pixel_box_size * world_per_pixel

    def update_hover(self, mouse_pos: MyPoint, model: MyModel):
        self.m_current_mouse_pos = mouse_pos
        self.m_hovered_shape = None
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
            
            if check_box_intersection(box_xmin, box_xmax, box_ymin, box_ymax, 
                                      s_xmin, s_xmax, s_ymin, s_ymax):
                
                closest_pt, dist = shape.find_closest_point(mouse_pos)
                dist_sq = dist**2
                
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    best_shape = shape
                    best_point = closest_pt
        
        self.m_hovered_shape = best_shape
        self.m_closest_point_on_shape = best_point

    def get_hovered_shape(self) -> Shape:
        return self.m_hovered_shape
    
    def get_closest_point(self) -> MyPoint:
        return self.m_closest_point_on_shape

    def get_selection_box_points(self) -> list[MyPoint]:
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


class MyCanvas(QtOpenGLWidgets.QOpenGLWidget):
    def __init__(self):
        # ... (init is unchanged)
        super(MyCanvas, self).__init__()
        self.m_model: MyModel = None
        self.m_w, self.m_h = 0, 0
        self.m_L, self.m_R, self.m_B, self.m_T = -1000.0, 1000.0, -1000.0, 1000.0
        self.m_isPanning = False
        self.m_panStartX, self.m_panStartY = 0, 0
        self.m_creating_shape_points = []
        self.m_temp_point = None
        self.m_currentMode = CanvasModes.FREE_MOVE
        self.setMouseTracking(True)
        self.m_hover_manager = HoverManager(pixel_box_size=10.0)

    def initializeGL(self):
        # ... (unchanged)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resizeGL(self, _width, _height):
        # ... (unchanged)
        self.m_w, self.m_h = _width, _height
        if self.m_model is not None:
            self.fitWorldToViewport()
        self.update_selection_box_size() 

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        if self.m_model is None: return

        # --- MODIFIED ---: Get graph for rendering
        graph = self.m_model.get_graph()
        selected_shapes = self.m_model.get_selected_shapes()
        glLineWidth(2.0)

        # Draw unselected shapes
        glColor3f(0.0, 0.0, 1.0) # Blue
        for shape in self.m_model.getShapes():
            if shape in selected_shapes:
                continue 
            glBegin(shape.get_gl_primitive())
            for vtx in shape.get_tessellated_points():
                glVertex2f(vtx.getX(), vtx.getY())
            glEnd()
            glPointSize(6.0)
            glColor3f(1.0, 0.0, 0.0) # Red CPs
            glBegin(GL_POINTS)
            for p in shape.get_control_points():
                glVertex2f(p.getX(), p.getY())
            glEnd()
            glColor3f(0.0, 0.0, 1.0) 

        # --- MODIFIED ---: Draw selected shapes OR graph
        if graph:
            # If graph exists, draw it instead of the selected shapes
            
            # 1. Draw Graph Edges
            glColor3f(0.0, 0.5, 0.0) # Dark Green
            glLineWidth(2.0)
            glBegin(GL_LINES)
            for edge in graph.get_edges():
                glVertex2f(edge.n1.point.getX(), edge.n1.point.getY())
                glVertex2f(edge.n2.point.getX(), edge.n2.point.getY())
            glEnd()
            
            # 2. Draw Graph Nodes
            glPointSize(5.0)
            glColor3f(0.0, 0.0, 1.0) # Blue
            glBegin(GL_POINTS)
            for node in graph.get_nodes():
                glVertex2f(node.point.getX(), node.point.getY())
            glEnd()
        
        else:
            # No graph, just draw selected shapes normally
            glColor3f(0.0, 1.0, 0.0) # Green
            glLineWidth(3.0) 
            for shape in selected_shapes:
                glBegin(shape.get_gl_primitive())
                for vtx in shape.get_tessellated_points():
                    glVertex2f(vtx.getX(), vtx.getY())
                glEnd()
                glPointSize(8.0)
                glColor3f(1.0, 0.5, 0.0) # Orange CPs
                glBegin(GL_POINTS)
                for p in shape.get_control_points():
                    glVertex2f(p.getX(), p.getY())
                glEnd()
                glColor3f(0.0, 1.0, 0.0) 
        
        glLineWidth(2.0) 

        # --- Draw creation previews ---
        if self.m_temp_point and self.m_creating_shape_points:
            # ... (unchanged)
            glPointSize(6.0)
            glColor3f(0.0, 0.8, 0.0)
            glBegin(GL_POINTS)
            for p in self.m_creating_shape_points:
                glVertex2f(p.getX(), p.getY())
            glEnd()
            glColor3f(0.5, 0.5, 0.5)
            self.draw_previews()

        # --- Draw Hover Previews ---
        if self.m_currentMode == CanvasModes.SELECTION_MODE:
            self.draw_hover_previews()
            
        # --- Draw Intersection Points (still useful for debugging) ---
        glPointSize(10.0)
        glColor3f(1.0, 1.0, 0.0) # Yellow
        glBegin(GL_POINTS)
        for p in self.m_model.get_intersection_points():
            glVertex2f(p.getX(), p.getY())
        glEnd()

    def draw_hover_previews(self):
        # ... (unchanged)
        box_points = self.m_hover_manager.get_selection_box_points()
        if box_points:
            glColor3f(0.3, 0.3, 0.3) 
            glLineStipple(1, 0xAAAA) 
            glEnable(GL_LINE_STIPPLE)
            glBegin(GL_LINE_LOOP)
            for p in box_points:
                glVertex2f(p.getX(), p.getY())
            glEnd()
            glDisable(GL_LINE_STIPPLE)

        hovered_shape = self.m_hover_manager.get_hovered_shape()
        if hovered_shape:
            closest_point = self.m_hover_manager.get_closest_point()
            if closest_point:
                glPointSize(10.0)
                glColor3f(1.0, 0.0, 1.0) # Magenta
                glBegin(GL_POINTS)
                glVertex2f(closest_point.getX(), closest_point.getY())
                glEnd()

    def draw_previews(self):
        # ... (unchanged)
        num_points = len(self.m_creating_shape_points)
        mode = self.m_currentMode
        if mode == CanvasModes.LINE_CREATION:
            p0 = self.m_creating_shape_points[0]
            glBegin(GL_LINES)
            glVertex2f(p0.getX(), p0.getY())
            glVertex2f(self.m_temp_point.getX(), self.m_temp_point.getY())
            glEnd()
        elif mode == CanvasModes.POLYLINE_CREATION:
            preview_points = self.m_creating_shape_points + [self.m_temp_point]
            glBegin(GL_LINE_STRIP)
            for p in preview_points:
                glVertex2f(p.getX(), p.getY())
            glEnd()
        elif mode == CanvasModes.CIRCLE_CREATION:
            center = self.m_creating_shape_points[0]
            dx = self.m_temp_point.getX() - center.getX()
            dy = self.m_temp_point.getY() - center.getY()
            radius = math.sqrt(dx**2 + dy**2)
            temp_circle = MyCircle(center, radius)
            glBegin(temp_circle.get_gl_primitive())
            for p in temp_circle.get_tessellated_points():
                glVertex2f(p.getX(), p.getY())
            glEnd()
        elif mode == CanvasModes.CIRCLE_ARC_CREATION:
            if num_points == 1:
                p0 = self.m_creating_shape_points[0]
                glBegin(GL_LINES)
                glVertex2f(p0.getX(), p0.getY())
                glVertex2f(self.m_temp_point.getX(), self.m_temp_point.getY())
                glEnd()
            elif num_points == 2:
                p_start, p_end = self.m_creating_shape_points
                p_on_arc = self.m_temp_point
                temp_arc = MyCircleArc(p_start, p_end, p_on_arc)
                glBegin(temp_arc.get_gl_primitive())
                for p in temp_arc.get_tessellated_points():
                    glVertex2f(p.getX(), p.getY())
                glEnd()
        elif mode == CanvasModes.QUAD_BEZIER_CREATION or mode == CanvasModes.CUBIC_BEZIER_CREATION:
            self.draw_bezier_previews(num_points)

    def draw_bezier_previews(self, num_points):
        # ... (unchanged)
        if self.m_currentMode == CanvasModes.QUAD_BEZIER_CREATION:
            if num_points == 2:
                p0, p2 = self.m_creating_shape_points
                p1 = self.m_temp_point
                self.draw_dashed_preview(MyQuadBezier(p0, p1, p2))
        elif self.m_currentMode == CanvasModes.CUBIC_BEZIER_CREATION:
            if num_points == 3:
                p0, p3, p1 = self.m_creating_shape_points
                p2 = self.m_temp_point
                self.draw_dashed_preview(MyCubicBezier(p0, p1, p2, p3))
    
    def draw_dashed_preview(self, temp_curve):
        # ... (unchanged)
        glBegin(temp_curve.get_gl_primitive())
        for vtx in temp_curve.get_tessellated_points():
            glVertex2f(vtx.getX(), vtx.getY())
        glEnd()
        glLineStipple(1, 0xAAAA)
        glEnable(GL_LINE_STIPPLE)
        glBegin(GL_LINE_STRIP)
        for p in temp_curve.get_control_points():
            glVertex2f(p.getX(), p.getY())
        glEnd()
        glDisable(GL_LINE_STIPPLE)

    def mousePressEvent(self, event):
        # ... (this logic is unchanged)
        world_pos = self.screenToWorld(event.position())
        
        if self.m_currentMode == CanvasModes.POLYLINE_CREATION and event.button() == Qt.MouseButton.RightButton:
            if len(self.m_creating_shape_points) > 1:
                self.m_model.addShape(MyPolyline(self.m_creating_shape_points))
            self.clearCreationState()
            return
        
        if event.button() != Qt.MouseButton.LeftButton: return
        
        if self.m_currentMode == CanvasModes.FREE_MOVE:
            self.m_isPanning = True
            self.m_panStartX, self.m_panStartY = event.position().x(), event.position().y()
            return

        if self.m_currentMode == CanvasModes.SELECTION_MODE:
            hovered_shape = self.m_hover_manager.get_hovered_shape()
            ctrl_pressed = event.modifiers() & Qt.ControlModifier
            
            if hovered_shape:
                if ctrl_pressed:
                    if hovered_shape in self.m_model.get_selected_shapes():
                        self.m_model.remove_from_selection(hovered_shape)
                    else:
                        self.m_model.add_to_selection(hovered_shape)
                else:
                    if hovered_shape not in self.m_model.get_selected_shapes():
                        self.m_model.clear_selection()
                        self.m_model.add_to_selection(hovered_shape)
            else:
                if not ctrl_pressed:
                    self.m_model.clear_selection()
            
            self.update()
            return
        
        self.m_creating_shape_points.append(world_pos)
        self.finalize_shape()
        self.update()

    def finalize_shape(self):
        # ... (this function is unchanged)
        mode = self.m_currentMode
        points = self.m_creating_shape_points
        num_points = len(points)

        if mode == CanvasModes.LINE_CREATION and num_points == 2:
            self.m_model.addShape(MyLine(*points))
            self.clearCreationState()
        elif mode == CanvasModes.CIRCLE_CREATION and num_points == 2:
            center, p_radius = points
            dx, dy = p_radius.getX() - center.getX(), p_radius.getY() - center.getY()
            radius = math.sqrt(dx**2 + dy**2)
            self.m_model.addShape(MyCircle(center, radius))
            self.clearCreationState()
        elif mode == CanvasModes.CIRCLE_ARC_CREATION and num_points == 3:
            self.m_model.addShape(MyCircleArc(*points))
            self.clearCreationState()
        elif mode == CanvasModes.QUAD_BEZIER_CREATION and num_points == 3:
            p0, p2, p1 = points
            self.m_model.addShape(MyQuadBezier(p0, p1, p2))
            self.clearCreationState()
        elif mode == CanvasModes.CUBIC_BEZIER_CREATION and num_points == 4:
            p0, p3, p1, p2 = points
            self.m_model.addShape(MyCubicBezier(p0, p1, p2, p3))
            self.clearCreationState()

    def mouseMoveEvent(self, event):
        # ... (unchanged)
        world_pos = self.screenToWorld(event.position())
        
        if self.m_isPanning:
            self.panCanvas(event)
            
        elif self.m_currentMode == CanvasModes.SELECTION_MODE:
            self.m_hover_manager.update_hover(world_pos, self.m_model)
            self.m_temp_point = None 
            self.update()

        elif self.m_currentMode != CanvasModes.FREE_MOVE: 
            self.m_hover_manager.clear() 
            self.m_temp_point = world_pos 
            if self.m_creating_shape_points:
                 self.update()
        else: 
            self.m_hover_manager.clear()
            self.m_temp_point = None
            self.update() 

    def mouseReleaseEvent(self, event):
        # ... (unchanged)
        if event.button() == Qt.MouseButton.LeftButton:
            self.m_isPanning = False

    def changeCanvasMode(self, mode: CanvasModes):
        # --- MODIFIED ---
        self.m_currentMode = mode
        self.clearCreationState() 
        
        if mode != CanvasModes.SELECTION_MODE:
            self.m_hover_manager.clear()
            self.m_model.clear_intersections()
            self.m_model.clear_graph() # Clear graph when switching modes
        
        if mode not in [CanvasModes.FREE_MOVE, CanvasModes.SELECTION_MODE]:
            if self.m_model:
                self.m_model.clear_selection() # This clears graph/intersections too
        
        self.update()

    def clearCreationState(self):
        # ... (unchanged)
        self.m_creating_shape_points.clear()
        self.m_temp_point = None
        self.update()

    def setModel(self, _model: MyModel):
        # ... (unchanged)
        self.m_model = _model

    def fitWorldToViewport(self):
        # ... (unchanged)
        if self.m_model is None or self.m_model.isEmpty():
            self.m_L, self.m_R, self.m_B, self.m_T = -1000.0, 1000.0, -1000.0, 1000.0
        else:
            self.m_L, self.m_R, self.m_B, self.m_T = self.m_model.getBoundBox()
        self.scaleWorldWindow(1.10)
        self.update_selection_box_size() 
        self.update() 

    def clearCanvas(self):
        # ... (unchanged)
        if self.m_model: self.m_model.clear()
        self.fitWorldToViewport() 
        self.update_selection_box_size()
        self.update()
        
    def scaleWorldWindow(self, _scaleFac):
        # ... (unchanged)
        if self.m_w == 0 or self.m_h == 0: return
        vpr = self.m_h / self.m_w
        cx, cy = (self.m_L + self.m_R) / 2.0, (self.m_B + self.m_T) / 2.0
        sizex, sizey = (self.m_R - self.m_L) * _scaleFac, (self.m_T - self.m_B) * _scaleFac
        if sizey > (vpr * sizex): sizex = sizey / vpr
        else: sizey = sizex * vpr
        self.m_L, self.m_R = cx - (sizex * 0.5), cx + (sizex * 0.5)
        self.m_B, self.m_T = cy - (sizey * 0.5), cy + (sizey * 0.5)
        self.update_selection_box_size()
        self.update()
    
    def get_world_units_per_pixel(self) -> float:
        # ... (unchanged)
        if self.m_w == 0:
            return 1.0 
        return (self.m_R - self.m_L) / self.m_w

    def update_selection_box_size(self):
        # ... (unchanged)
        world_per_pixel = self.get_world_units_per_pixel()
        self.m_hover_manager.update_world_box_size(world_per_pixel)

    def screenToWorld(self, pos: QPointF) -> MyPoint:
        # ... (unchanged)
        if self.m_w == 0 or self.m_h == 0: return MyPoint(0, 0)
        world_w = self.m_R - self.m_L
        world_h = self.m_T - self.m_B
        x_world = self.m_L + (pos.x() * world_w / self.m_w)
        y_world = self.m_T - (pos.y() * world_h / self.m_h)
        return MyPoint(x_world, y_world)

    def panCanvas(self, event):
        # ... (unchanged)
        if self.m_w == 0 or self.m_h == 0: return
        endX, endY = event.position().x(), event.position().y()
        dx_pix, dy_pix = endX - self.m_panStartX, endY - self.m_panStartY
        world_w, world_h = self.m_R - self.m_L, self.m_T - self.m_B
        dx_world, dy_world = dx_pix * world_w / self.m_w, -dy_pix * world_h / self.m_h
        self.m_L -= dx_world
        self.m_R -= dx_world
        self.m_B -= dy_world
        self.m_T -= dy_world
        self.m_panStartX, self.m_panStartY = endX, endY
        self.update_selection_box_size()
        self.update()

    def wheelEvent(self, event: QWheelEvent):
        # ... (unchanged)
        zoom_factor = 1.1 if event.angleDelta().y() < 0 else 1 / 1.1
        self.scaleWorldWindow(zoom_factor)

    # --- NEW / RENAMED ---
    def build_intersection_graph(self):
        """Finds intersections, shatters segments, and builds the planar graph."""
        if self.m_model is None:
            return
            
        self.m_model.clear_intersections()
        self.m_model.clear_graph()
        
        selected_shapes = self.m_model.get_selected_shapes()
        if len(selected_shapes) < 2:
            print("Select at least two shapes to build a graph.")
            self.update()
            return

        graph = MyGraph()
        raw_intersection_points = []
        all_segments = []

        # 1. Get all segments from all selected shapes
        for shape in selected_shapes:
            points = shape.get_tessellated_points()
            if not points:
                continue
            is_loop = (shape.get_gl_primitive() == GL_LINE_LOOP)
            
            for i in range(len(points) - 1):
                all_segments.append( (points[i], points[i+1], shape) )
            if is_loop and len(points) > 1:
                all_segments.append( (points[-1], points[0], shape) )

        # 2. Find all intersection points
        for i in range(len(all_segments)):
            for j in range(i + 1, len(all_segments)):
                p1, p2, shape1 = all_segments[i]
                p3, p4, shape2 = all_segments[j]

                if shape1 == shape2:
                    continue # Don't intersect segments from the same shape

                intersection_pt = find_segment_intersection(p1, p2, p3, p4)
                if intersection_pt:
                    raw_intersection_points.append(intersection_pt)
        
        # 3. Create graph nodes
        #    - Add all original vertices
        for p1, p2, shape in all_segments:
            graph.add_node(p1)
            graph.add_node(p2)
        #    - Add all intersection points
        for pt in raw_intersection_points:
            graph.add_node(pt)

        # 4. Create shattered edges (the core logic)
        for p1, p2, shape in all_segments:
            p1_node = graph.find_node_at(p1)
            p2_node = graph.find_node_at(p2)
            
            # Find all nodes that lie ON this segment
            nodes_on_segment = []
            for node in graph.get_nodes():
                if node == p1_node or node == p2_node:
                    continue
                if point_on_segment(node.point, p1, p2):
                    dist = dist_sq(p1_node.point, node.point)
                    nodes_on_segment.append((dist, node))
            
            # Sort the nodes by distance from p1
            nodes_on_segment.sort(key=lambda x: x[0])

            # Create new edges between the sorted nodes
            current_node = p1_node
            for dist, next_node in nodes_on_segment:
                graph.add_edge(current_node, next_node)
                current_node = next_node
            
            # Add the final edge to the end of the segment
            graph.add_edge(current_node, p2_node)

        print(f"Graph built: {len(graph.get_nodes())} nodes, {len(graph.get_edges())} edges.")
        self.m_model.set_graph(graph)
        self.m_model.set_intersection_points(raw_intersection_points)
        self.update()