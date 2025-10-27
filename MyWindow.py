# MyWindow.py
from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QAction, QIcon, QActionGroup
from MyCanvas import MyCanvas, CanvasModes
from MyModel import MyModel

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("MyGLDrawer")
        
        self.canvas = MyCanvas()
        self.setCentralWidget(self.canvas)
        
        self.model = MyModel()
        self.canvas.setModel(self.model)
        
        # --- Create Actions ---
        pan_action = QAction(QIcon("icons/pan.png"), "Pan", self)
        pan_action.setCheckable(True)
        pan_action.setChecked(True)

        select_action = QAction(QIcon("icons/select.png"), "Select", self)
        select_action.setCheckable(True)
        
        fit_action = QAction(QIcon("icons/fit.png"), "Fit", self)
        clear_action = QAction(QIcon("icons/clear.png"), "Clear All", self)
        
        # --- MODIFIED ---
        intersect_action = QAction(QIcon("icons/intersect.png"), "Build Regions", self)
        
        line_action = QAction(QIcon("icons/line.png"), "Line", self)
        # ... (rest of shape actions are unchanged)
        line_action.setCheckable(True)
        polyline_action = QAction(QIcon("icons/polyline.png"), "Polyline", self)
        polyline_action.setCheckable(True)
        quad_bezier_action = QAction(QIcon("icons/quad.png"), "Quadratic Bezier", self)
        quad_bezier_action.setCheckable(True)
        cubic_bezier_action = QAction(QIcon("icons/cubic.png"), "Cubic Bezier", self)
        cubic_bezier_action.setCheckable(True)
        circle_action = QAction(QIcon("icons/circle.png"), "Circle", self)
        circle_action.setCheckable(True)
        arc_action = QAction(QIcon("icons/arc.png"), "Circle Arc", self)
        arc_action.setCheckable(True)

        # --- Create a single Toolbar ---
        toolbar = self.addToolBar("Tools")
        toolbar.addAction(pan_action)
        toolbar.addAction(select_action)
        toolbar.addAction(fit_action)
        toolbar.addAction(clear_action)
        toolbar.addSeparator()
        toolbar.addAction(intersect_action) # Name is updated
        toolbar.addSeparator() 
        toolbar.addAction(line_action)
        toolbar.addAction(polyline_action)
        toolbar.addAction(circle_action)
        toolbar.addAction(arc_action)
        toolbar.addAction(quad_bezier_action)
        toolbar.addAction(cubic_bezier_action)

        # --- Group mode actions for mutual exclusivity ---
        self.mode_action_group = QActionGroup(self)
        self.mode_action_group.addAction(pan_action)
        self.mode_action_group.addAction(select_action)
        # ... (rest of actions are unchanged)
        self.mode_action_group.addAction(line_action)
        self.mode_action_group.addAction(polyline_action)
        self.mode_action_group.addAction(quad_bezier_action)
        self.mode_action_group.addAction(cubic_bezier_action)
        self.mode_action_group.addAction(circle_action)
        self.mode_action_group.addAction(arc_action)
        self.mode_action_group.setExclusive(True)

        # --- Connect Signals ---
        fit_action.triggered.connect(self.canvas.fitWorldToViewport)
        clear_action.triggered.connect(self.canvas.clearCanvas)
        # --- MODIFIED ---
        intersect_action.triggered.connect(self.canvas.build_intersection_graph) 
        self.mode_action_group.triggered.connect(self.on_mode_action_triggered)

    def on_mode_action_triggered(self, action: QAction):
        # ... (this function is unchanged)
        text = action.text()
        if text == "Pan":
            self.canvas.changeCanvasMode(CanvasModes.FREE_MOVE)
        elif text == "Select":
            self.canvas.changeCanvasMode(CanvasModes.SELECTION_MODE)
        elif text == "Line":
            self.canvas.changeCanvasMode(CanvasModes.LINE_CREATION)
        elif text == "Polyline":
            self.canvas.changeCanvasMode(CanvasModes.POLYLINE_CREATION)
        elif text == "Quadratic Bezier":
            self.canvas.changeCanvasMode(CanvasModes.QUAD_BEZIER_CREATION)
        elif text == "Cubic Bezier":
            self.canvas.changeCanvasMode(CanvasModes.CUBIC_BEZIER_CREATION)
        elif text == "Circle":
            self.canvas.changeCanvasMode(CanvasModes.CIRCLE_CREATION)
        elif text == "Circle Arc":
            self.canvas.changeCanvasMode(CanvasModes.CIRCLE_ARC_CREATION)