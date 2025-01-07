from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtCore import QAbstractListModel, QAbstractTableModel
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsCoordinateTransform, QgsProject
from qgis.core import QgsDistanceArea
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QModelIndex

from qgis.core import QgsMessageLog, Qgis

import math

from ..model.payloadlist import PayloadList
from ..model.regionslist import RegionsList
from ..model.task_properties import taskProperties

########################################### MISSION ####################################################################
class Mission(QAbstractListModel):

    missionModelChanged = pyqtSignal()

    def __init__(self, crs=None, mission_id=None):
        QAbstractListModel.__init__(self)
        if crs:
            self.coordinateReferenceSystem = crs
        else:
            # WGS84 - System anlegen
            self.coordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:4326")
        self.description = ''
        if not mission_id:
            # mission_id = "mission-{}".format(str(uuid.uuid1()))
            mission_id = "mission"
        self.missionID = mission_id
        self.tasks = list()
        self.name = str('task')
        self.payload = PayloadList()
        #self.payload.modelChanged.connect(self.on_payload_changed)
        self.regionsList = RegionsList()
        self.regionsList.modelChanged.connect(self.on_area_changed)
        self.timeoutFactor = 2
        self.totalTime = 0
        self.totalDistance = 0
        self.hoGLimit = 0
        self.depthLimit = 0
        self.useDepthLimit = False
        self.useHoGLimit = False
        self.taskTimeoutAction = 'ABORT'
        self.minimumHeight = 0.0

        self._vehicleName = None

        # SABUVIS extensions
        self._propellerMode = None
        self._depthMode = None

        self.missionModelChanged.connect(self.missionModelUpdate)

    @pyqtSlot()
    def on_submodel_changed(self, task):
        self.computeTotalDistance()
        self.missionModelChanged.emit()

    @pyqtSlot(QAbstractTableModel)
    def on_payload_changed(self, task):
        #self.payload.modelChanged.emit(self)
        #self.modelChanged.emit(self)
        pass

    @pyqtSlot()
    def on_area_changed(self, task = None):
        #self.regionsList.modelChanged.emit()
        self.missionModelChanged.emit()
        pass

    # ListModel - begin
    def rowCount(self, parent=QModelIndex()):
        return self.countTasks()

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole and index.row() < self.countTasks():
            # logging.debug(index.row())
            task = self.getTask(index.row())
            return str("{0} ({1})".format(task.getName(), task.getTaskType()))
        else:
            return None

    # ListModel - end

    def getMissionID(self):
        return self.missionID

    def getName(self):
        return self.name

    def getDescription(self):
        return self.description

    def getTimeoutFactor(self):
        return self.timeoutFactor

    def getUseDepthLimit(self):
        return self.useDepthLimit

    def getUseHoGLimit(self):
        return self.useHoGLimit

    def getHoGLimit(self):
        return self.hoGLimit

    def getDepthLimit(self):
        return self.depthLimit

    def setHoGLimit(self, hoGLimit):
        self.hoGLimit = hoGLimit

    def setDepthLimit(self, depthLimit):
        self.depthLimit = depthLimit

    def setUseDepthLimit(self, use):
        self.useDepthLimit = use

    def setUseHoGLimit(self, use):
        self.useHoGLimit = use

    def getMinimumHeight(self):
        return self.minimumHeight

    def setMinimumHeight(self, val):
        self.minimumHeight = val

    def setTimeoutFactor(self, factor):
        self.timeoutFactor = factor

    def setName(self, name):
        self.name = name

    def setDescription(self, desc):
        self.description = desc

    def getTotalTime(self):
        return self.totalTime

    def getTotalTimeOut(self):
        return self.getTimeoutFactor() * self.getTotalTime()

    def getTotalDistance(self):
        return self.totalDistance

    def getPayloadList(self):
        return self.payload

    def getRegionsList(self):
        return self.regionsList

    def getCRS(self):
        return self.coordinateReferenceSystem

    def addTask(self, task, index=None):
        task.setParentMission(self)
        if isinstance(index, int):
            self.tasks.insert(index, task)
        else:
            self.tasks.append(task)
        self.missionModelChanged.emit()

        return len(self.tasks)

    def countTasks(self):
        return len(self.tasks)

    def removeTask(self, taskIndex):
        if len(self.tasks) > 0:
            task = self.tasks[taskIndex]
            taskType = task.getTaskType()
            prop = taskProperties(taskType)
            prop.setType(taskType)
            prop.propertiesChanged.emit()
            del self.tasks[taskIndex].points[:]

            self.tasks[taskIndex].setParentMission(None)
            self.tasks.remove(self.tasks[taskIndex])
            self.computeTotalDistance()
            self.computeTotalTime()
            self.missionModelChanged.emit()
        else:
            QgsMessageLog.logMessage("removeTask: task list is empty", tag="Pathplanner", level=Qgis.Warning)

    def getTaskList(self):
        return self.tasks

    def getTask(self, taskIndex):
        if taskIndex < 0 or taskIndex >= len(self.tasks):
            return None
        return self.tasks[taskIndex]

    def clean(self):
        for task in self.tasks:
            task.setParentMission(None)
            del task.points[:]
        del self.tasks[:]

    # @pyqtSlot()
    def computeTotalTime(self):
        # compute total time of the mission - survey, waypoint times added
        totalTime = 0
        index = 0
        if (len(self.tasks) == 1):
            task = self.tasks[0]
            prop = task.getProperties()
            taskTime = prop.getTime()
            totalTime = taskTime
        else:
            while index < len(self.tasks) - 1:
                task = self.tasks[index]
                if index == 0:
                    taskTime = task.getProperties().getTime()
                else:
                    taskTime = 0

                prop = task.getProperties()
                speed = prop.getSpeed()
                task2 = self.tasks[index + 1]
                prop2 = task2.getProperties()
                if speed != 0:
                    dist = self.distBetweenTasks(task, task2)
                    time = round(float(dist) / float(speed))
                else:
                    time = 0
                taskTime2 = prop2.getTime()
                totalTime += taskTime + taskTime2 + time
                index += 1
        totalTime = round(totalTime + 0.5)
        self.setTotalTime(totalTime)

    def computeDistance2Point(self, point1, point2):
        # compute distance between 2 given points
        cRS = QgsCoordinateReferenceSystem("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs")

        dist = QgsDistanceArea()
        #dist.setSourceCrs(cRS)
        dist.setSourceCrs(cRS, QgsProject.instance().transformContext())
        dist.setEllipsoid('')
        #dist.setEllipsoidalMode(True)

        # calculate distance between 2 point coordinates
        p1X, p1Y, p2X, p2Y = map(math.radians, [point1.getX(), point1.getY(), point2.getX(), point2.getY()])
        dlat = p2Y - p1Y
        dlon = p2X - p1X
        a = (math.sin(dlat / 2) ** 2) + (math.cos(p1Y) * math.cos(p2Y) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        # Calculate Radius of the earth on given Latitude
        # Req - Radius at equator in m
        # Rpol - Radius at pole in m
        Req = 6378137
        Rpol = 6356752
        lat = p1X

        Rt1 = (((Req ** 2) * math.cos(lat)) ** 2) + (((Rpol ** 2) * math.sin(lat)) ** 2)
        Rt2 = ((Req * math.cos(lat)) ** 2) + ((Rpol * math.sin(lat)) ** 2)
        R = math.sqrt(Rt1 / Rt2)

        distance = R * c

        # Pythagoras for depth difference:
        depth1 = float(point1.getDepth())
        depth2 = float(point2.getDepth())
        depthDiff = abs(depth1 - depth2)
        distance = math.sqrt(depthDiff ** 2 + distance ** 2)
        distanceFormat = "{:.3f}".format(distance)
        return float(distanceFormat)

    def distBetweenTasks(self, task1, task2):
        # distances between tasks - used to calculate overall distance of mission
        if task1.countPoints() > 0 and task2.countPoints() > 0:
            type1 = task1.getTaskType()
            type2 = task2.getTaskType()
            if type1 == 'waypoints' or type1 == 'waypoint':
                point1 = task1.getLastWayPoint()
            elif type1 == 'survey':
                # beim Survey soll die endposition festgestellt werden
                stpos = task1.getProperties().getStartPosition()
                nse = float(task1.getProperties().getNorthSouthExtent())
                swath = task1.getProperties().getSwath()
                nol = int(nse / swath) + 1
                rest = nol % 2
                # get end point of the survey depending on number of lines
                if stpos == 'SouthEast':
                    if rest == 0:
                        point1 = task1.getUR()
                    else:
                        point1 = task1.getUL()
                elif stpos == 'SouthWest':
                    if rest == 0:
                        point1 = task1.getUL()
                    else:
                        point1 = task1.getUR()
                elif stpos == 'NorthEast':
                    if rest == 0:
                        point1 = task1.getLR()
                    else:
                        point1 = task1.getLL()
                else:
                    if rest == 0:
                        point1 = task1.getLL()
                    else:
                        point1 = task1.getLR()

            elif type1 in ['circle', 'keepstation']:
                point1 = task1.getPoint()

            if type2 == 'waypoints' or type2 == 'waypoint':
                point2 = task2.getFirstWayPoint()
            elif type2 == 'survey':
                stpos1 = task2.getProperties().getStartPosition()
                if stpos1 == 'SouthEast':
                    point2 = task2.getLR()
                elif stpos1 == 'SouthWest':
                    point2 = task2.getLL()
                elif stpos1 == 'NorthEast':
                    point2 = task2.getUR()
                else:
                    point2 = task2.getUL()

            elif type2 in ['circle', 'keepstation']:
                point2 = task2.getPoint()
            dist = self.computeDistance2Point(point1, point2)
            return dist
        else:
            return 0

    @pyqtSlot()
    def computeTotalDistance(self):
        # total distance of the mission - add total distances of the tasks
        totalDistance = 0
        index = 0

        if (len(self.tasks) == 1):
            task = self.tasks[0]
            prop = task.getProperties()
            totalDistance = prop.getDistance()

        else:
            while index < len(self.tasks) - 1:
                task = self.tasks[index]
                if index == 0:
                    prop = task.getProperties()
                    taskDistance = prop.getDistance()
                else:
                    taskDistance = 0
                totalDistance = totalDistance + taskDistance
                task2 = self.tasks[index + 1]
                dist = self.distBetweenTasks(task, task2)
                index = index + 1

                prop2 = task2.getProperties()
                nextTaskDist = prop2.getDistance()

                totalDistance = totalDistance + dist + nextTaskDist
                totalDistance1 = "{:.3f}".format(totalDistance)
                totalDistance = float(totalDistance1)

        self.setTotalDistance(totalDistance)
        self.computeTotalTime()

    def setTotalTime(self, time):
        self.totalTime = time

    def setTotalDistance(self, distance):
        self.totalDistance = distance

    def setTaskTimeoutAction(self, taskTimeoutAction):
        if isinstance(taskTimeoutAction, str):
            if taskTimeoutAction == "ABORT" or taskTimeoutAction == "CONTINUE":
                self.taskTimeoutAction = str(taskTimeoutAction)
            else:
                self.taskTimeoutAction = "ABORT"
        else:
            self.taskTimeoutAction = "ABORT"

    def getTaskTimeoutAction(self):
        return self.taskTimeoutAction

    def __del__(self):
        self.clean()

    def getVehicleName(self):
        return self._vehicleName

    def setVehicleName(self, name):
        self._vehicleName = name

    # SABUVIS extensions
    def getPropellerMode(self):
        return self._propellerMode

    def setPropellerMode(self, mode):
        self._propellerMode = mode

    def getDepthMode(self):
        return self._depthMode

    def setDepthMode(self, mode):
        self._depthMode = mode

    @pyqtSlot()
    def missionModelUpdate(self):
        self.computeTotalDistance()
        self.dataChanged.emit(QModelIndex(), QModelIndex(), [])
        #pass

