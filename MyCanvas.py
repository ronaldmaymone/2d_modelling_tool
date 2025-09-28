from PySide6 import QtOpenGLWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import *
from OpenGL.GL import *
from MyModel import MyModel

class MyCanvas(QtOpenGLWidgets.QOpenGLWidget):
    def __init__(self):
        super(MyCanvas, self).__init__()
        self.m_model: MyModel = None

        self.m_w = 0 # width: GL canvas horizontal size
        self.m_h = 0 # height: GL canvas vertical size

        self.m_L = -1000.0
        self.m_R = 1000.0
        self.m_B = -1000.0
        self.m_T = 1000.0

        self.m_isPanning = False
        self.m_panStartX = 0
        self.m_panStartY = 0

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, _width, _height):
        # store GL canvas sizes in object properties
        self.m_w = _width
        self.m_h = _height
        if(self.m_model==None)or(self.m_model.isEmpty()): 
            self.scaleWorldWindow(1.0)
        else:
            self.m_L,self.m_R,self.m_B,self.m_T = self.m_model.getBoundBox()
            self.scaleWorldWindow(1.1)
        # setup the viewport to canvas dimensions
        glViewport(0, 0, self.m_w, self.m_h)
        # reset the coordinate system
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # establish the clipping volume by setting up an
        # orthographic projection
        glOrtho(self.m_L,self.m_R,self.m_B,self.m_T,-1.0,1.0)
        # setup display in model coordinates
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        # clear the buffer with the current clear color
        glClear(GL_COLOR_BUFFER_BIT)

        # It's good practice to reset the projection matrix on each paint
        # to ensure the viewport is correctly set.
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)

        # Switch back to model-view matrix for drawing
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        if (self.m_model==None)or(self.m_model.isEmpty()):
            return

        # Draw the model directly
        verts = self.m_model.getVerts()
        glShadeModel(GL_SMOOTH)
        glColor3f(0.0, 1.0, 0.0) # green
        glBegin(GL_TRIANGLES)
        for vtx in verts:
            glVertex2f(vtx.getX(), vtx.getY())
        glEnd()

    def setModel(self,_model: MyModel):
        self.m_model = _model
        self.update()

    def fitWorldToViewport(self):
        if self.m_model == None or self.m_model.isEmpty():
            return
        self.m_L,self.m_R,self.m_B,self.m_T = self.m_model.getBoundBox()
        self.scaleWorldWindow(1.10)
        self.update()

    def scaleWorldWindow(self,_scaleFac):
        # Avoid division by zero
        if self.m_w == 0:
            return
        # Compute canvas viewport distortion ratio.
        vpr = self.m_h / self.m_w
        # Get current window center.
        cx = (self.m_L + self.m_R) / 2.0
        cy = (self.m_B + self.m_T) / 2.0
        # Set new window sizes based on scaling factor.
        sizex = (self.m_R - self.m_L) * _scaleFac
        sizey = (self.m_T - self.m_B) * _scaleFac
        # Adjust window to keep the same aspect ratio of the viewport.
        if sizey > (vpr*sizex):
            sizex = sizey / vpr
        else:
            sizey = sizex * vpr
        self.m_L = cx - (sizex * 0.5)
        self.m_R = cx + (sizex * 0.5)
        self.m_B = cy - (sizey * 0.5)
        self.m_T = cy + (sizey * 0.5)
        
        self.update()

    def mousePressEvent(self, event):
        # Pan with the left mouse button
        if event.button() == Qt.MouseButton.LeftButton:
            self.m_isPanning = True
            self.m_panStartX = event.position().x()
            self.m_panStartY = event.position().y()

    def mouseMoveEvent(self, event):
        if self.m_isPanning:
            # Check for valid canvas size to avoid division by zero
            if self.m_w == 0 or self.m_h == 0:
                return
                
            endX = event.position().x()
            endY = event.position().y()
            
            # Calculate displacement in pixels
            dx_pix = endX - self.m_panStartX
            dy_pix = endY - self.m_panStartY

            # Convert pixel displacement to world coordinates displacement
            world_w = self.m_R - self.m_L
            world_h = self.m_T - self.m_B
            
            dx_world = dx_pix * world_w / self.m_w
            # Y is inverted in screen coordinates, so we negate the displacement
            dy_world = -dy_pix * world_h / self.m_h 

            # Update the model's vertices
            if self.m_model:
                self.m_model.panModel(dx_world, dy_world)

            # Update pan start position for the next mouse move event
            self.m_panStartX = endX
            self.m_panStartY = endY
            
            self.update()

    def mouseReleaseEvent(self, event):
        # Stop panning when the left mouse button is released
        if event.button() == Qt.MouseButton.LeftButton:
            self.m_isPanning = False

    def wheelEvent(self, event: QWheelEvent):
        """
        Handles mouse wheel events for zooming.
        """
        # Get the angle of the wheel delta
        angle = event.angleDelta().y()
        
        # Set a zoom factor
        zoom_factor = 1.1

        if angle > 0:
            # Zoom in (scroll up) by making the world window smaller
            self.scaleWorldWindow(1 / zoom_factor)
        elif angle < 0:
            # Zoom out (scroll down) by making the world window larger
            self.scaleWorldWindow(zoom_factor)

