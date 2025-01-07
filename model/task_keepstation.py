from qgis.PyQt.QtCore import *
from qgis.PyQt.QtCore import pyqtSlot, pyqtSignal

from qgis.core import QgsMessageLog, Qgis

from .task import Task
from .point import Point


class KeepStationTask(Task):
    def __init__(self):
        Task.__init__(self, 'keepstation')
        #self.properties.setType(self.taskType)
        self.innerRadius = 10.0  # in m
        self.outerRadius = 35.0  # in m
        self.distance = 0

        #self.properties.speedChanged.connect(self.computeCircleTime)
        #self.properties.timeChanged.connect(self.computeTaskTimeout)

    def setPoint(self, point):
        # logging.debug("set center point")
        if not isinstance(point, Point):
            raise ValueError('Parameter is not from class Point.')

        if len(self.points) < 1:
            self.points.append(point)
        else:
            self.points[0] = point

        self.properties.propertiesChanged.emit() # needed to update widget!
        self.parentMission.missionModelChanged.emit()

    def setInnerRadius(self, radius):
        if not isinstance(radius, float):
            raise ValueError('Parameter is not from class float.')
        self.innerRadius = radius

        self.modelChanged.emit()
        self.properties.propertiesChanged.emit()
        self.parentMission.missionModelChanged.emit()

    def setOuterRadius(self, radius):
        if not isinstance(radius, float):
            raise ValueError('Parameter is not from class float.')
        self.outerRadius = radius

        self.modelChanged.emit()
        self.properties.propertiesChanged.emit()
        self.parentMission.missionModelChanged.emit()

    def setDepth(self, depth):
        if len(self.points) < 1:
            return
        if not isinstance(depth, float):
            raise ValueError('Parameter is not from class float.')

        self.properties.constantDepth = depth
        self.points[0].setDepth(depth)

    def getPoint(self):
        if len(self.points) < 1:
            return None
        return self.points[0]

    def getInnerRadius(self):
        return self.innerRadius

    def getOuterRadius(self):
        return self.outerRadius

    def type(self):
        return self.taskType

    @pyqtSlot()
    def computeTaskTimeout(self):
        #self.properties.setTimeout(self.parentMission.getTimeoutFactor() * self.properties.getTime())
        #self.modelChanged.emit()
        pass