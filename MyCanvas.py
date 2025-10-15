# MyCanvas.py
from PySide6 import QtOpenGLWidgets
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QWheelEvent
from OpenGL.GL import *
from MyModel import MyModel
from MyShapes import MyPoint, MyLine, MyQuadBezier, MyCubicBezier, MyCircle, MyCircleArc, MyPolyline
from enum import Enum
import math

class CanvasModes(Enum):
    FREE_MOVE = 0
    LINE_CREATION = 1
    POLYLINE_CREATION = 2
    QUAD_BEZIER_CREATION = 3
    CUBIC_BEZIER_CREATION = 4
    CIRCLE_CREATION = 5
    CIRCLE_ARC_CREATION = 6

class MyCanvas(QtOpenGLWidgets.QOpenGLWidget):
    def __init__(self):
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

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)

    def resizeGL(self, _width, _height):
        self.m_w, self.m_h = _width, _height
        self.fitWorldToViewport()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        if self.m_model is None: return

        # Draw committed shapes
        glLineWidth(2.0)
        glColor3f(0.0, 0.0, 1.0)
        for shape in self.m_model.getShapes():
            glBegin(shape.get_gl_primitive())
            for vtx in shape.get_tessellated_points():
                glVertex2f(vtx.getX(), vtx.getY())
            glEnd()
            glPointSize(6.0)
            glColor3f(1.0, 0.0, 0.0)
            glBegin(GL_POINTS)
            for p in shape.get_control_points():
                glVertex2f(p.getX(), p.getY())
            glEnd()

        # Draw creation previews
        if self.m_temp_point and self.m_creating_shape_points:
            glPointSize(6.0)
            glColor3f(0.0, 0.8, 0.0)
            glBegin(GL_POINTS)
            for p in self.m_creating_shape_points:
                glVertex2f(p.getX(), p.getY())
            glEnd()

            glColor3f(0.5, 0.5, 0.5)
            self.draw_previews()

    def draw_previews(self):
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
        world_pos = self.screenToWorld(event.position())
        
        # Handle Polyline finishing
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
        
        self.m_creating_shape_points.append(world_pos)
        self.finalize_shape()
        self.update()

    def finalize_shape(self):
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
        if self.m_isPanning:
            self.panCanvas(event)
        elif self.m_currentMode != CanvasModes.FREE_MOVE:
            self.m_temp_point = self.screenToWorld(event.position())
            if self.m_creating_shape_points:
                 self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.m_isPanning = False

    def changeCanvasMode(self, mode: CanvasModes):
        self.m_currentMode = mode
        self.clearCreationState()

    def clearCreationState(self):
        self.m_creating_shape_points.clear()
        self.m_temp_point = None
        self.update()

    def setModel(self, _model: MyModel):
        self.m_model = _model

    def fitWorldToViewport(self):
        if self.m_model is None or self.m_model.isEmpty():
            self.m_L, self.m_R, self.m_B, self.m_T = -1000.0, 1000.0, -1000.0, 1000.0
        else:
            self.m_L, self.m_R, self.m_B, self.m_T = self.m_model.getBoundBox()
        self.scaleWorldWindow(1.10)

    def clearCanvas(self):
        if self.m_model: self.m_model.clear()
        self.update()
        
    def scaleWorldWindow(self, _scaleFac):
        if self.m_w == 0 or self.m_h == 0: return
        vpr = self.m_h / self.m_w
        cx, cy = (self.m_L + self.m_R) / 2.0, (self.m_B + self.m_T) / 2.0
        sizex, sizey = (self.m_R - self.m_L) * _scaleFac, (self.m_T - self.m_B) * _scaleFac
        if sizey > (vpr * sizex): sizex = sizey / vpr
        else: sizey = sizex * vpr
        self.m_L, self.m_R = cx - (sizex * 0.5), cx + (sizex * 0.5)
        self.m_B, self.m_T = cy - (sizey * 0.5), cy + (sizey * 0.5)
        self.update()

    def screenToWorld(self, pos: QPointF) -> MyPoint:
        if self.m_w == 0 or self.m_h == 0: return MyPoint(0, 0)
        
        world_w = self.m_R - self.m_L
        world_h = self.m_T - self.m_B
        
        x_world = self.m_L + (pos.x() * world_w / self.m_w)
        y_world = self.m_T - (pos.y() * world_h / self.m_h)
        
        return MyPoint(x_world, y_world)

    def panCanvas(self, event):
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
        self.update()

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.1 if event.angleDelta().y() < 0 else 1 / 1.1
        self.scaleWorldWindow(zoom_factor)