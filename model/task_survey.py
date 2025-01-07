from qgis.PyQt.QtCore import *
from qgis.PyQt.QtCore import QAbstractListModel, QAbstractTableModel, pyqtSlot, pyqtSignal
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsMessageLog
from qgis.core import Qgis

import os, math

from ..coordtrans import NedToWgs84

from .task import Task
from .point import Point

show_log_messages = False

class SurveyTask(Task):
    surveyModelChanged = pyqtSignal()

    def __init__(self):
        Task.__init__(self, 'survey')
        #self.taskType = 'survey'
        self.centerPoint = Point()
        self.properties.setType(self.taskType)
        self.overlapfactor = 1.5

        self.firstLoad = True
        self.buffered = False

        self.properties.speedChanged.connect(self.computeSurveyTime)
        self.properties.timeChanged.connect(self.computeTaskTimeout)

    # TableModel - begin
    def setData(self, index, value, role):
        idx = index.row()
        elem = index.column()

        if isinstance(value, str):
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
            # logging.debug(value)
            self.surveyModelChanged.emit()
            self.properties.propertiesChanged.emit()
            return True
        else:
            return False

    # TableModel - end

    def setRect(self, point_ul, point_ll, point_lr, point_ur, firstCall):
        if not isinstance(point_ul, Point) or not isinstance(point_ll, Point) or not isinstance(point_lr,
                        Point) or not isinstance(point_ur, Point):
            raise ValueError('Parameter is not from class Point.')

        del self.points
        self.points = list()
        if point_ul.getX() < point_ur.getY():
            if point_ul.getY() > point_ll.getY():
                self.points.append(point_ul)
                self.points.append(point_ll)
                self.points.append(point_lr)
                self.points.append(point_ur)
            else:
                self.points.append(point_ll)
                self.points.append(point_ul)
                self.points.append(point_ur)
                self.points.append(point_lr)
        else:
            if point_ul.getY() > point_ll.getY():
                self.points.append(point_ur)
                self.points.append(point_lr)
                self.points.append(point_ll)
                self.points.append(point_ul)
            else:
                self.points.append(point_lr)
                self.points.append(point_ur)
                self.points.append(point_ul)
                self.points.append(point_ll)

        depth = self.properties.getDepth()
        x = (point_ul.getX() + point_ur.getX()) / 2.0
        y = (point_ul.getY() + point_ll.getY()) / 2.0
        self.moveCenterPoint(x, y)
        self.centerPoint.setDepth(depth)

        if (firstCall):
            measureLengthHeight = self.disTwoPoints(point_ul, point_ll)
            measureLengthWidth = self.disTwoPoints(point_ul, point_ur)
            self.properties.setNorthSouthExtent(measureLengthHeight)
            self.properties.setEastWestExtent(measureLengthWidth)

        if self.properties.getSurveyType() == 'UnevenMeander':
            distance = self.computeUnevenMeanderDistance()
        else:
            distance = self.computeMeanderDistance()

        self.firstLoad = False
        self.properties.setDistance(distance)
        self.computeSurveyTime()

        self.surveyModelChanged.emit()
        self.properties.propertiesChanged.emit()

    def changeRect(self, ewe, nse):
        lon = self.centerPoint.getX()
        lat = self.centerPoint.getY()

        self.properties.setEastWestExtent(ewe)
        self.properties.setNorthSouthExtent(nse)
        conv = NedToWgs84(lon_ref=lon, lat_ref=lat)
        p1_lon, p1_lat = conv.convert_(-(ewe / 2.0), nse / 2.0)
        p2_lon, p2_lat = conv.convert_(ewe / 2.0, -(nse / 2.0))
        self.setRect(Point(p1_lon, p1_lat), Point(p1_lon, p2_lat), Point(p2_lon, p2_lat), Point(p2_lon, p1_lat), 0)

    def moveRect(self, newCenterPoint):
        ewe = self.properties.getEastWestExtent()
        nse = self.properties.getNorthSouthExtent()
        lon = newCenterPoint.getX()
        lat = newCenterPoint.getY()
        self.moveCenterPoint(lon, lat)
        conv = NedToWgs84(lon_ref=lon, lat_ref=lat)
        p1_lon, p1_lat = conv.convert_(-(ewe / 2.0), nse / 2.0)
        p2_lon, p2_lat = conv.convert_(ewe / 2.0, -(nse / 2.0))

        self.setRect(Point(p1_lon, p1_lat), Point(p1_lon, p2_lat), Point(p2_lon, p2_lat), Point(p2_lon, p1_lat), 0)

    def isEmpty(self):
        if len(self.points) == 0:
            return True
        else:
            return False

    def setAngle(self, angle):
        if isinstance(angle, (int, float)):
            self.properties.setRotationAngle(round(angle))
            self.modelReset.emit()
            self.surveyModelChanged.emit()

    def moveCenterPoint(self, x, y):
        self.centerPoint.setX(x)
        self.centerPoint.setY(y)

    def getUL(self):
        if len(self.points) > 3:
            return self.points[0]
        else:
            return None

    def getLL(self):
        if len(self.points) > 3:
            return self.points[1]
        else:
            return None

    def getLR(self):
        if len(self.points) > 3:
            return self.points[2]
        else:
            return None

    def getUR(self):
        if len(self.points) > 3:
            return self.points[3]
        else:
            return None

    def getCenterPoint(self):
        return self.centerPoint

    def getStartPosition(self):
        return self.properties.startPosition

    def type(self):
        return self.taskType

    def computeMeanderDistance(self):
        # compute Meander distance depending on Swath, Width and Height of the Survey
        swath = self.properties.getSwath()
        northSouthExtent = self.properties.getNorthSouthExtent()
        eastWestExtent = self.properties.getEastWestExtent()
        numOfTrackLines = float(northSouthExtent) / float(swath)
        numOfTrackLines = round(numOfTrackLines + 0.5)

        distance = eastWestExtent * numOfTrackLines
        distance = distance + (northSouthExtent)
        self.properties.setDistance(int(distance))
        return distance

    def computeUnevenMeanderDistance(self):
        # if survey type is "UnevenMeander"
        # sidescan range - additional property if UnevenMeander was set
        ssr = self.properties.getSideScanRange()
        northSouthExtent = self.properties.getNorthSouthExtent()
        eastWestExtent = self.properties.getEastWestExtent()
        # getNadir() and Nadirgap property must be added due to new configuration - 17.01.2018
        ng = self.properties.getNadirGap()
        dfactor = self.properties.getDistanceFactor()
        # odd->even line distance (x)
        if ng >= ssr:
            QgsMessageLog.logMessage("Nadir Gap should be less than Sidescan range" , tag="Pathplanner",
                                     level=Qgis.CRITICAL)
            errorbox = QMessageBox()
            errorbox.setText(str("NadirGap should be less than Sidescan Range!"))
            errorbox.exec_()
            ng = ssr
            x = ssr
        else:
            x = ssr - ng
        # even-odd line distance (y)
        if dfactor == None:
            dfactor = 1.5

        y = dfactor * ssr

        k = northSouthExtent / ( x + y )

        if k >= 1:
            r = northSouthExtent - k*(x+y)
            if r > x:
                numOfLines = (k+1)*2
                numOfDoubleLines = k+1
            else:
                numOfLines = k*2 + 1
                numOfDoubleLines = k
        else: # nse < (x+y)
            if x > northSouthExtent:
                if show_log_messages:
                    QgsMessageLog.logMessage("Only one line is possible due to narrow NorthSouthExtent.", tag="Pathplanner",
                                         level=Qgis.Info)
                numOfLines = 1
                numOfDoubleLines = 0
            else:
                if show_log_messages:
                    QgsMessageLog.logMessage("Only two lines possible due to narrow NorthSouthExtent.", tag="Pathplanner",
                                         level=Qgis.Info)
                numOfLines = 2
                numOfDoubleLines = 1

        distance = numOfLines*eastWestExtent + numOfDoubleLines * x + (numOfDoubleLines - 1)*y + (numOfLines - 2*numOfDoubleLines) * y
        self.properties.setDistance(int(distance))
        return distance


    @pyqtSlot()
    def computeSurveyTime(self):
        # compute Survey time according to the set speed and total-distance of the survey
        # self.computeMeanderDistance()
        distance = float(self.properties.getDistance())
        speed = float(self.properties.getSpeed())
        if speed != 0:
            time = round(distance / speed)
        else:
            time = 0
        self.properties.setTime(time)
        timeout = round(time * self.parentMission.getTimeoutFactor())
        self.properties.setTimeout(timeout)
        self.properties.propertiesChanged.emit()

    def disTwoPoints(self, point1, point2):
        # calculate distance between 2 points - for height, width calculation of survey
        p1X, p1Y, p2X, p2Y = map(math.radians, [point1.getX(), point1.getY(), point2.getX(), point2.getY()])
        dlat = p2Y - p1Y
        dlon = p2X - p1X
        a = (math.sin(dlat / 2.0) ** 2.0) + (math.cos(p1Y) * math.cos(p2Y) * math.sin(dlon / 2.0) ** 2.0)
        c = 2.0 * math.asin(math.sqrt(a))
        # Calculate Radius of the earth on given Latitude
        # Req - Radius at equator
        # Rpol - Radius at pole
        Req = 6378137.0
        Rpol = 6356752.0
        # Rpol = 6378137.0
        lat = p1X

        Rt1 = (((Req ** 2.0) * math.cos(lat)) ** 2.0) + (((Rpol ** 2.0) * math.sin(lat)) ** 2.0)
        Rt2 = ((Req * math.cos(lat)) ** 2.0) + ((Rpol * math.sin(lat)) ** 2.0)
        # Earth radius at the Latitude
        R = math.sqrt(Rt1 / Rt2)

        distance = R * c
        totalDistance = float("{:.3f}".format(distance))
        return totalDistance

    def setDepth(self, depth):
        self.centerPoint.setDepth(depth)



