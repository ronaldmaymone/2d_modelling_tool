from PySide6.QtWidgets import *
from PySide6.QtGui import *
from MyCanvas import *
from MyModel import *

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(100,100,600,400)
        self.setWindowTitle("MyGLDrawer")
        self.canvas = MyCanvas()
        self.setCentralWidget(self.canvas)
        # create a model object and pass to canvas
        self.model = MyModel()
        self.canvas.setModel(self.model)
        # Create Toolbars
        # 1. Manipulation Toolbar
        manipulation_toolbar = self.addToolBar("File")
        fit = QAction(QIcon("icons/fit.jpg"),"fit",self)
        manipulation_toolbar.addAction(fit)
        manipulation_toolbar.actionTriggered[QAction].connect(self.manipToolbarClick)

        # 2. Creation Toolbar
        creation_toolbar = self.addToolBar("Create")
        line = QAction(QIcon("icons/line.jpg"),"line",self)
        creation_toolbar.addAction(line)
        creation_toolbar.actionTriggered[QAction].connect(self.creationToolbarClick)

    def manipToolbarClick(self,a):
        if a.text() == "fit":
            self.canvas.fitWorldToViewport()
        elif a.text() == "pan":
            self.canvas.changeCanvasMode(CanvasModes.FREE_MOVE)

    def creationToolbarClick(self,a):
        if a.text() == "line":
            self.canvas.changeCanvasMode(CanvasModes.LINE_CREATION)