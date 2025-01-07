from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtCore import QAbstractTableModel, QModelIndex, pyqtSignal, pyqtSlot, QAbstractListModel
from qgis.core import QgsMessageLog, Qgis
from configparser import ConfigParser
import os, math

from .task_properties import taskProperties
from ..model.mission import Mission

EQUATORRADIUS = 6378137
POLRADIUS = 6356752

class Task(QAbstractTableModel):
    modelChanged = pyqtSignal()
    payloadStateChanged = pyqtSignal(object)

    def __init__(self, _task_type='basic'):
        QAbstractTableModel.__init__(self)
        # self.parentMission = parentMission
        self.points = list()
        # task - numbered sequentially - removed random id-sequence uuid
        self.name = "task"  # + str(uuid.uuid1())
        self.taskType = _task_type
        self.payload_enabled = list()
        self.payload_disabled = list()
        # payload events at end - dict
        self.payload_event_at_end = {}
        self.parentMission = None
        self.headerLabels = ["lon [deg]", "lat [deg]", "depth [m]", "distance [m]", "duration [s]"]
        self.description = ''
        self.dist2Point = list()
        self.time2Point = list()

        # self.dist2Point.insert(0,0)
        self.time2Point.insert(0, 0)
        self.properties = taskProperties(self.taskType)
        self.properties.propertiesChanged.connect(self.sendChangedSignals)

    def getProperties(self):
        return self.properties

    @pyqtSlot()
    def computeTaskTimeout(self):
        self.properties.setTimeout(self.parentMission.getTimeoutFactor() * self.properties.getTime())

    # ListModel - begin
    def rowCount(self, parent=QModelIndex()):
        return len(self.points)

    def columnCount(self, parent=QModelIndex()):
        # 5 dtermined columns - lat, lon, depth, distance, duration
        return 5

    def data(self, index, role):
        # table entries
        if index.isValid() and role == Qt.DisplayRole:
            point = self.points[index.row()]

            if index.column() == 0:
                return point.getX()
            if index.column() == 1:
                return point.getY()
            if index.column() == 2:
                if (self.properties.depthControllerMode == 'ConstantDepth'):
                    try:
                        depth = float(self.properties.constantDepth)
                    except:
                        QgsMessageLog.logMessage("ConstantDepth mode: cannot convert '%s' to float!" % self.properties.constantDepth, tag="Pathplanner",
                                                 level=Qgis.Warning)
                        depth = 0.0
                    point.setDepth(depth)
                return point.getDepth()
            ##################################
            if index.column() == 3:
                # compute sequential point distances and add to table
                return self.dist2Point[index.row()]
            if index.column() == 4:
                # compute times between points and add to table
                return self.time2Point[index.row()]
            return "{}-{}".format(index.row(), index.column())
        else:
            return None

    def computeDistance(self, pointList):
        # compute total distance of tasks and distances between points
        if len(pointList) == 0:
            return 0
        index = 0
        # first entry of dist2Point array should be 0
        totalDistance = 0
        self.dist2Point.insert(0, 0)

        while index < len(pointList) - 1:
            # calculate distances between 2 sequential points
            point1 = pointList[index]
            point2 = pointList[index + 1]

            p1X, p1Y, p2X, p2Y = map(math.radians, [point1.getX(), point1.getY(), point2.getX(), point2.getY()])
            dlat = p2Y - p1Y
            dlon = p2X - p1X
            a = (math.sin(dlat / 2) ** 2) + (math.cos(p1Y) * math.cos(p2Y) * math.sin(dlon / 2) ** 2)
            c = 2 * math.asin(math.sqrt(a))
            # Calculate Radius of the earth on given Latitude
            # Req - Radius at equator 6378137
            # Rpol - Radius at pole 6356752
            Req = EQUATORRADIUS
            Rpol = POLRADIUS
            #Req = 6378137
            #Rpol = 6356752
            lat = p1X

            Rt1 = (((Req ** 2) * math.cos(lat)) ** 2) + (((Rpol ** 2) * math.sin(lat)) ** 2)
            Rt2 = ((Req * math.cos(lat)) ** 2) + ((Rpol * math.sin(lat)) ** 2)
            R = math.sqrt(Rt1 / Rt2)
            distance1 = R * c

            self.dist2Point.insert(index + 1, distance1)
            speed = float(self.properties.getSpeed())
            if not speed == 0:
                time = int(distance1 / speed)
            else:
                time = 0
            self.time2Point.insert(index + 1, time)

            # distance = round(dist.measureLine([qgisPoint1, qgisPoint2]),2)
            # Pythagoras:
            depth1 = point1.getDepth()
            depth2 = point2.getDepth()
            depthDiff = abs(float(depth1) - float(depth2))
            distance = math.sqrt(depthDiff ** 2 + distance1 ** 2)
            # add distances to total distance
            totalDistance = totalDistance + distance
            index = index + 1

        totalDistance1 = "{:.3f}".format(totalDistance)
        return float(totalDistance1)

    def computeTime(self, pointList):
        if len(pointList) == 0:
            return 0
        distance = self.computeDistance(pointList)
        speed = float(self.properties.getSpeed())

        if not speed == 0:
            time = int(round(distance / speed))
        else:
            time = 0
        return time

    def computeEnergyConsumption(self):
        """
        Compute energy consumption of task
        :return: consumed energy in Ws
        """
        return 0.0

    def flags(self, modelIndex):
        ans = QAbstractTableModel.flags(self, modelIndex)
        ans |= Qt.ItemIsEditable
        ans |= Qt.ItemIsEnabled
        return ans

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and 0 <= section < len(self.headerLabels):
            return self.headerLabels[section]
        return QAbstractTableModel.headerData(self, section, orientation, role)

    # ListModel - end

    def setParentMission(self, mission):
        if isinstance(mission, Mission) or mission is None:
            self.parentMission = mission
            #if mission is not None:
                #QgsMessageLog.logMessage("setParentMission - called", tag="Pathplanner", level=Qgis.Info)
        else:
            raise ValueError("Illegal argument type")

    def getParentMission(self):
        return self.parentMission

    def disablePayload(self, payloadItem):
        if payloadItem in self.payload_enabled:
            self.payload_enabled.remove(payloadItem)
        if payloadItem not in self.payload_disabled:
            self.payload_disabled.append(payloadItem)
            self.payloadStateChanged.emit(self)

    def enablePayload(self, payloadItem):
        if payloadItem in self.payload_disabled:
            self.payload_disabled.remove(payloadItem)
        if payloadItem not in self.payload_enabled:
            self.payload_enabled.append(payloadItem)
            self.payloadStateChanged.emit(self)

    def ignorePayload(self, payloadItem):
        if payloadItem in self.payload_enabled:
            self.payload_enabled.remove(payloadItem)
        if payloadItem in self.payload_disabled:
            self.payload_disabled.remove(payloadItem)
        self.payloadStateChanged.emit(self)

    def getEnabledPayload(self):
        return self.payload_enabled

    def getDisabledPayload(self):
        return self.payload_disabled

    def changePayloadEventAtEnd(self, payloadItem, event=None):
        if event is None:
            # To delete a key regardless of whether it is in the dictionary, use the two-argument form of dict.pop():
            self.payload_event_at_end.pop(payloadItem, None)
            self.payloadStateChanged.emit(self)
            return
        self.payload_event_at_end[payloadItem] = event
        self.payloadStateChanged.emit(self)

    def getPayloadEventAtEnd(self, payloadItem):
        if payloadItem in self.payload_event_at_end:
            return self.payload_event_at_end[payloadItem]
        return None

    def getPointAt(self, index):
        if index < len(self.points):
            return self.points[index]
        return None

    def indexOfPoint(self, point):
        return self.points.index(point)

    def numPoints(self):
        return self.countPoints()

    def countPoints(self):
        return len(self.points)

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name

    def getDescription(self):
        return self.description

    def setDescription(self, description):
        self.description = description

    def getFirstWayPoint(self):
        if len(self.points) < 1:
            return None
        return self.points[0]

    def getLastWayPoint(self):
        if len(self.points) < 1:
            return None
        return self.points[-1]

    def getTaskType(self):
        return self.taskType

    @pyqtSlot()
    def sendChangedSignals(self):
        self.modelReset.emit()
        self.modelChanged.emit()

    def clean(self):
        del self.points[:]
        self.properties.propertiesChanged.emit()

        # disconnect Signals
        try:
            self.properties.propertiesChanged.disconnect()
            self.properties.speedChanged.disconnect()
            self.properties.timeChanged.disconnect()
        except:
            QgsMessageLog.logMessage("clean: disconnecting signals was not successful", tag="Pathplanner", level=Qgis.Warning)

    def __del__(self):
        self.clean()