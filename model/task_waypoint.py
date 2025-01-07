from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot

from .task import Task
from .point import Point

class WaypointTask(Task):
    def __init__(self):
        Task.__init__(self, 'waypoint')
        #self.taskType = 'waypoint'
        self.properties.setType(self.taskType)
        # self.dist2Point = list()

        self.properties.speedChanged.connect(self.computeWaypointTime)
        self.properties.timeChanged.connect(self.computeTaskTimeout)

    # TableModel - begin
    def setData(self, index, value, role):
        idx = index.row()
        elem = index.column()

        if isinstance(value, unicode):
            try:
                v = float(value)
            except (TypeError, ValueError):
                return False
            if elem == 0:  # lat
                self.points[idx].setX(v)
            if elem == 1:  # lon
                self.points[idx].setY(v)
            if elem == 2:  # depth
                self.points[idx].setDepth(v)

            self.properties.propertiesChanged.emit()
            self.parentMission.missionModelChanged.emit()
            return True
        else:
            return False
    # TableModel - end

    def addPoint(self, newpoint, index=None):
        if not isinstance(newpoint, Point):
            raise ValueError('Parameter is not from class Point.')
        if index is not None:
            if (self.properties.depthControllerMode == 'ConstantDepth'):
                newpoint.setDepth(self.properties.getConstantDepth())
            else:
                newpoint.setDepth(0)
            self.points.insert(index, newpoint)
        else:
            if (self.properties.depthControllerMode == 'ConstantDepth'):
                newpoint.setDepth(self.properties.getConstantDepth())
            self.points.append(newpoint)

        self.properties.setSelectedPoint(-1)
        time = self.computeTime(self.points)
        distance2 = self.computeDistance(self.points)
        self.properties.setTime(time)
        self.properties.setDistance(distance2)
        self.properties.propertiesChanged.emit()
        self.parentMission.missionModelChanged.emit()

    def removePointAt(self, index):
        del self.points[index]
        self.properties.setSelectedPoint(-1)

        self.modelChanged.emit()
        self.properties.propertiesChanged.emit()

    def movePoint(self, oldIndex, newIndex):
        if oldIndex < 0 or newIndex < 0 or oldIndex >= len(self.points) or newIndex >= len(self.points):
            return
        self.points.insert(newIndex, self.points.pop(oldIndex))
        self.properties.setSelectedPoint(newIndex)
        self.properties.propertiesChanged.emit()

    def highlightPointAt(self, index):
        self.properties.setSelectedPoint(index)

    @pyqtSlot()
    def computeWaypointTime(self):
        if len(self.points) == 0:
            return 0
        distance = self.computeDistance(self.points)
        self.properties.setDistance(distance)
        speed = float(self.properties.getSpeed())

        if not speed == 0:
            time = int(round(distance / speed))
        else:
            time = 0
        self.properties.setTime(time)
        self.properties.propertiesChanged.emit()

    def type(self):
        return self.taskType
