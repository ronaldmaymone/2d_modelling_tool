from PySide6 import QtOpenGLWidgets
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QWheelEvent
from OpenGL.GL import *
from MyModel import MyModel
from MyShapes import MyPoint, MyLine, MyQuadBezier, MyCubicBezier
from enum import Enum

class CanvasModes(Enum):
    FREE_MOVE = 0
    LINE_CREATION = 1
    POLILINE_CREATION = 2
    QUAD_BEZIER_CREATION = 3
    CUBIC_BEZIER_CREATION = 4
    CIRCLE_CREATION = 5
    CIRCLE_ARC_CREATION = 6

class MyCanvas(QtOpenGLWidgets.QOpenGLWidget):
    def __init__(self):
        super(MyCanvas, self).__init__()
        self.m_model: MyModel = None

        self.m_w = 0
        self.m_h = 0

        self.m_L, self.m_R, self.m_B, self.m_T = -1000.0, 1000.0, -1000.0, 1000.0

        self.m_isPanning = False
        self.m_panStartX, self.m_panStartY = 0, 0

        self.m_currentMode = CanvasModes.FREE_MOVE
        self.m_creating_shape_points = []
        self.m_temp_point = None

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)

    def resizeGL(self, _width, _height):
        self.m_w = _width
        self.m_h = _height
        self.fitWorldToViewport()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        if self.m_model is None:
            return

        # Draw all committed shapes
        glLineWidth(2.0)
        glColor3f(0.0, 0.0, 1.0)  # Blue for committed shapes
        for shape in self.m_model.getShapes():
            glBegin(shape.get_gl_primitive())
            for vtx in shape.get_tessellated_points():
                glVertex2f(vtx.getX(), vtx.getY())
            glEnd()
            
            glPointSize(6.0)
            glColor3f(1.0, 0.0, 0.0)  # Red for control points
            glBegin(GL_POINTS)
            for p in shape.get_control_points():
                glVertex2f(p.getX(), p.getY())
            glEnd()

        # Draw the shape currently being created
        if self.m_creating_shape_points:
            glPointSize(6.0)
            glColor3f(0.0, 0.8, 0.0) # Green for new points
            glBegin(GL_POINTS)
            for p in self.m_creating_shape_points:
                glVertex2f(p.getX(), p.getY())
            glEnd()
            
            if self.m_temp_point and len(self.m_creating_shape_points) > 0:
                glColor3f(0.5, 0.5, 0.5) # Gray for rubber-band
                glBegin(GL_LINE_STRIP)
                for p in self.m_creating_shape_points:
                    glVertex2f(p.getX(), p.getY())
                glVertex2f(self.m_temp_point.getX(), self.m_temp_point.getY())
                glEnd()

    def setModel(self, _model: MyModel):
        self.m_model = _model

    def clearCanvas(self):
        """Clears all shapes from the model and refreshes the view."""
        if self.m_model:
            self.m_model.clear()
        self.update()

    def fitWorldToViewport(self):
        if self.m_model is None or self.m_model.isEmpty():
            self.m_L, self.m_R, self.m_B, self.m_T = -1000.0, 1000.0, -1000.0, 1000.0
        else:
            self.m_L, self.m_R, self.m_B, self.m_T = self.m_model.getBoundBox()
        
        self.scaleWorldWindow(1.10)
        self.update()

    def scaleWorldWindow(self, _scaleFac):
        if self.m_w == 0 or self.m_h == 0: return
        
        vpr = self.m_h / self.m_w
        cx = (self.m_L + self.m_R) / 2.0
        cy = (self.m_B + self.m_T) / 2.0
        
        sizex = (self.m_R - self.m_L) * _scaleFac
        sizey = (self.m_T - self.m_B) * _scaleFac
        
        if sizey > (vpr * sizex):
            sizex = sizey / vpr
        else:
            sizey = sizex * vpr
            
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

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        world_pos = self.screenToWorld(event.position())
        
        if self.m_currentMode == CanvasModes.FREE_MOVE:
            self.m_isPanning = True
            self.m_panStartX, self.m_panStartY = event.position().x(), event.position().y()
            return

        # Shape creation modes
        self.m_creating_shape_points.append(world_pos)
        
        if self.m_currentMode == CanvasModes.LINE_CREATION and len(self.m_creating_shape_points) == 2:
            p1, p2 = self.m_creating_shape_points
            self.m_model.addShape(MyLine(p1, p2))
            self.clearCreationState()
        elif self.m_currentMode == CanvasModes.QUAD_BEZIER_CREATION and len(self.m_creating_shape_points) == 3:
            p1, p2, p3 = self.m_creating_shape_points
            self.m_model.addShape(MyQuadBezier(p1, p2, p3))
            self.clearCreationState()
        elif self.m_currentMode == CanvasModes.CUBIC_BEZIER_CREATION and len(self.m_creating_shape_points) == 4:
            p1, p2, p3, p4 = self.m_creating_shape_points
            self.m_model.addShape(MyCubicBezier(p1, p2, p3, p4))
            self.clearCreationState()
        
        self.update()

    def mouseMoveEvent(self, event):
        if self.m_isPanning and self.m_currentMode == CanvasModes.FREE_MOVE:
            self.panCanvas(event)
        elif self.m_currentMode != CanvasModes.FREE_MOVE and self.m_creating_shape_points:
            self.m_temp_point = self.screenToWorld(event.position())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.m_isPanning = False

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.1 if event.angleDelta().y() < 0 else 1 / 1.1
        self.scaleWorldWindow(zoom_factor)

    def panCanvas(self, event):
        if self.m_w == 0 or self.m_h == 0: return
        
        endX, endY = event.position().x(), event.position().y()
        dx_pix, dy_pix = endX - self.m_panStartX, endY - self.m_panStartY

        world_w, world_h = self.m_R - self.m_L, self.m_T - self.m_B
        
        dx_world = dx_pix * world_w / self.m_w
        dy_world = -dy_pix * world_h / self.m_h
        
        self.m_L -= dx_world
        self.m_R -= dx_world
        self.m_B -= dy_world
        self.m_T -= dy_world

        self.m_panStartX, self.m_panStartY = endX, endY
        self.update()
    
    def changeCanvasMode(self, mode: CanvasModes):
        self.m_currentMode = mode
        self.clearCreationState()

    def clearCreationState(self):
        self.m_creating_shape_points.clear()
        self.m_temp_point = None
        self.update()