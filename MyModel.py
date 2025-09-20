class MyPoint:
    def __init__(self):
        self.m_x = 0
        self.m_y = 0
    def __init__(self,_x,_y):
        self.m_x = _x
        self.m_y = _y
    def setX(self,_x):
        self.m_x = _x
    def setY(self,_y):
        self.m_y = _y
    def getX(self):
        return self.m_x
    def getY(self):
        return self.m_y


class MyModel:
    def __init__(self):
        self.m_verts = []
        p1 = MyPoint(100.0,100.0)
        p2 = MyPoint(200.0,100.0)
        p3 = MyPoint(150.0,175.0)
        self.m_verts.append(p1)
        self.m_verts.append(p2)
        self.m_verts.append(p3)

    def getVerts(self):
        return self.m_verts
    def isEmpty(self):
        return len(self.m_verts) == 0
    
    def getBoundBox(self):
        if len(self.m_verts) < 1:
            return 0.0,10.0,0.0,10.0
        
        xmin = self.m_verts[0].getX()
        xmax = xmin
        ymin = self.m_verts[0].getY()
        ymax = ymin
        for i in range(1,len(self.m_verts)):
            if self.m_verts[i].getX() < xmin:
                xmin = self.m_verts[i].getX()
            if self.m_verts[i].getX() > xmax:
                xmax = self.m_verts[i].getX()
            if self.m_verts[i].getY() < ymin:
                ymin = self.m_verts[i].getY()
            if self.m_verts[i].getY() > ymax:
                ymax = self.m_verts[i].getY()
        return xmin,xmax,ymin,ymax