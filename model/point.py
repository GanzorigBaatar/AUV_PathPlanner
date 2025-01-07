from typing import List

class Point:
    """QGis point (x=longitude, y=latitude) """
    def __init__(self, x: [List,float] = 0.0, y: float = 0.0, depth: float = 0.0):
        # logging.debug("Point declaration called")
        if isinstance(x, List):
            if len(x) not in [2,3]:
                raise Exception(f'Point() constructor call needs a list with 2 or 3 elements (given: {x})!')
            y = x[1]
            if len(x) > 2:
                depth = x[2]
            x = x[0]
        self.x = x
        self.y = y
        self.depth = depth

    def getX(self):
        return self.x

    def getY(self):
        return self.y

    def getDepth(self):
        return float(self.depth)

    def setX(self, x):
        self.x = x

    def setY(self, y):
        self.y = y

    def setDepth(self, depth):
        self.depth = depth

    def getVec2d(self):
        return [self.getX(), self.getY()]

    def getVec3d(self):
        return [self.getX(), self.getY(), self.getDepth()]

    def getDictXYZ(self):
        return {"x": self.getX(), "y": self.getY(), "z": self.getDepth()}

    def getDictXYDepth(self):
        return {"x": self.getX(), "y": self.getY(), "depth": self.getDepth()}
