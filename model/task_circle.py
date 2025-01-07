from qgis.PyQt.QtCore import *
from qgis.PyQt.QtCore import pyqtSlot, pyqtSignal

from qgis.core import QgsMessageLog, Qgis
from configparser import ConfigParser
import os, math

from .task import Task
from .point import Point


class CircleTask(Task):
    def __init__(self):
        Task.__init__(self, 'circle')
        #self.taskType = 'circle'
        self.properties.setType(self.taskType)
        self.radius = 10  # in m
        self.distance = 0
        self.rotationDirection = 'Clockwise'
        self.numOfRotations = 1

        self.properties.speedChanged.connect(self.computeCircleTime)
        self.properties.timeChanged.connect(self.computeTaskTimeout)

    def setPoint(self, point):
        # logging.debug("set center point")
        if not isinstance(point, Point):
            raise ValueError('Parameter is not from class Point.')

        if len(self.points) < 1:
            self.points.append(point)
        else:
            self.points[0] = point

        self.computeLengthOfSpiral()
        self.parentMission.missionModelChanged.emit()

    def setComputationMode(self, mode, var):
        mode = int(mode)
        if isinstance(mode, int):
            if mode >= 0 and mode <= 2:
                self.computationMode = mode
            else:
                self.computationMode = 0
        else:
            try:
                mode = int(mode)
                if mode >= 0 and mode <= 2:
                    self.computationMode = mode
                else:
                    self.computationMode = 0
            except:
                self.computationMode = 0

        self.setNumOfRotations(float(var))

        self.computeLengthOfSpiral()

    def setNumOfRotations(self, var):
        try:
            var = float(var)
        except:
            var = 1
        depth = self.points[0].getDepth()
        if self.computationMode == 2:  # var = depthPerRotation
            self.numOfRotations = depth / var
            if self.numOfRotations == 0:
                QgsMessageLog.logMessage("numOfRotations at 0m depth in depthPerRotation mode is 0", tag="Pathplanner",
                                         level=Qgis.Warning)

        elif self.computationMode == 1:  # var = diving angle
            if var == 0:
                self.numOfRotations = 1  # TODO: nur einmal im Kreis ohne tauchen
                self.setDepth(0)
            elif var > 0 and var < 90:
                # get circumference
                u = 2 * math.pi * self.radius
                b = math.tan(math.radians(var)) * u
                if b != 0:
                    self.numOfRotations = depth / b
                else:
                    self.numOfRotations = 1
            else:
                self.numOfRotations = 1
        elif self.computationMode == 0:  # var = numOfRotations
            self.numOfRotations = var
        else:
            self.numOfRotations = 1  # logging.debug warning

        # calculate distance using numOfRotations
        self.computeLengthOfSpiral()

    def computeLengthOfSpiral(self):
        # bis festgelegt ist ob Anzahl an Drehungen, Tiefe pro Umdrehung angegeben werden soll oder Tauchwinkel:
        if len(self.points) > 0:
            depth = self.points[0].getDepth()
            self.distance = math.sqrt((2 * math.pi * self.radius * self.numOfRotations) ** 2 + depth ** 2)
            self.properties.setDistance(self.distance)
            self.computeCircleTime()
            self.properties.propertiesChanged.emit()

            self.parentMission.missionModelChanged.emit()

    def setRotationDirection(self, rotDir):
        if isinstance(rotDir, int):
            if rotDir == 0:
                self.rotationDirection = 'Clockwise'
            elif rotDir == 1:
                self.rotationDirection = 'CounterClockwise'
            else:
                self.rotationDirection = 'Clockwise'
        elif isinstance(rotDir, str) or isinstance(rotDir, unicode):
            if rotDir == 'Clockwise' or rotDir == 'CounterClockwise':
                self.rotationDirection = rotDir
            else:
                self.rotationDirection = 'Clockwise'

    def setRadius(self, radius):
        if not isinstance(radius, float):
            raise ValueError('Parameter is not from class float.')
        self.radius = radius

        self.modelChanged.emit()
        self.properties.timeChanged.emit()
        self.properties.propertiesChanged.emit()
        self.parentMission.missionModelChanged.emit()

    def setDepth(self, depth):
        if len(self.points) < 1:
            return
        if not isinstance(depth, float):
            raise ValueError('Parameter is not from class float.')

        self.properties.constantDepth = depth
        self.points[0].setDepth(depth)

    def getRotationDirection(self):
        return self.rotationDirection

    def getPoint(self):
        if len(self.points) < 1:
            return None
        return self.points[0]

    def getRadius(self):
        return self.radius

    @pyqtSlot()
    def computeCircleTime(self):
        distance = float(self.distance)
        speed = float(self.properties.getSpeed())
        if speed != 0:
            time = round(distance / speed)
        else:
            time = 0
        self.properties.setTime(time)
        timeout = round(time * self.parentMission.getTimeoutFactor())
        self.properties.setTimeout(timeout)
        self.properties.propertiesChanged.emit()
        self.modelChanged.emit()
        self.parentMission.missionModelChanged.emit()

    @pyqtSlot()
    def computeTaskTimeout(self):
        self.properties.setTimeout(self.parentMission.getTimeoutFactor() * self.properties.getTime())
        self.modelChanged.emit()

    def type(self):
        return self.taskType

########################################### CIRCLE TASK END ############################################################