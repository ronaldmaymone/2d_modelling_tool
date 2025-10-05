from MyShapes import Shape

class MyModel:
    def __init__(self):
        self.m_shapes = []

    def getShapes(self):
        return self.m_shapes
    
    def addShape(self, shape: Shape):
        self.m_shapes.append(shape)

    def isEmpty(self):
        return len(self.m_shapes) == 0
    
    def getBoundBox(self):
        if self.isEmpty():
            return -1000.0, 1000.0, -1000.0, 1000.0
        
        xmin, xmax, ymin, ymax = self.m_shapes[0].get_bounding_box()

        for i in range(1, len(self.m_shapes)):
            s_xmin, s_xmax, s_ymin, s_ymax = self.m_shapes[i].get_bounding_box()
            if s_xmin < xmin: xmin = s_xmin
            if s_xmax > xmax: xmax = s_xmax
            if s_ymin < ymin: ymin = s_ymin
            if s_ymax > ymax: ymax = s_ymax
            
        return xmin, xmax, ymin, ymax

    def clear(self):
        """Removes all shapes from the model."""
        self.m_shapes.clear()