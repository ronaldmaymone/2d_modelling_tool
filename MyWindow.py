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
        # create a Toolbar
        toolbar = self.addToolBar("File")
        fit = QAction(QIcon("icons/fit.jpg"),"fit",self)
        toolbar.addAction(fit)
        toolbar.actionTriggered[QAction].connect(self.onClickToolbar)

    def onClickToolbar(self,a):
        if a.text() == "fit":
            self.canvas.fitWorldToViewport()