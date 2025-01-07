from qgis.PyQt.QtCore import Qt, QModelIndex
from qgis.PyQt.QtCore import QAbstractListModel
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot
from qgis.PyQt.QtCore import QObject
from qgis.core import QgsMessageLog, Qgis
from configparser import ConfigParser
import os

from .mission import Mission
from .. import pathplanner

class PathPlannerModel2(QAbstractListModel):
    """
    New data model for the path planner system
    """
    modelChanged = pyqtSignal(QObject)
    plotMission = pyqtSignal(QAbstractListModel)
    #missionModelChanged = pyqtSignal(Mission)
    ##modelReset = pyqtSignal(object)

    def __init__(self):
        #logging.debug("PathPlannerModel2 declaration called")
        QAbstractListModel.__init__(self)
        self.mission = None
        #self.missions = list()


    @pyqtSlot(Mission)
    def on_submodel_changed(self, mission):
        #self.missionModelChanged.emit(mission)
        #self.modelChanged.emit(self)
        pass

    # ListModel - begin
    def rowCount(self, parent=QModelIndex()):
        return self.countMissions()

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            # logging.debug(index.row())
            mission = self.getMission(index.row())
            if mission is not None:
                return str(mission.getName())
            else:
                return None
        else:
            return None
    # ListModel - end

    def addMission(self, mission=Mission()):
        """
        Adds new Mission
        :param mission: Mission-Object
        :return: MissionID
        """
        #missionID = mission.getMissionID()
        #logging.debug("missionID - addMission: {}".format(missionID))
        #mission.missionModelChanged.connect(self.on_submodel_changed)

        #self.missions.append(mission)
        #QgsMessageLog.logMessage("addMission: {}", tag="Pathplanner2",
        #                         level=Qgis.Critical)
        self.mission = mission
        #self.modelChanged.emit(mission)

        #self.missionModelChanged.emit(mission)
        #self.emit(SIGNAL('modelReset()'))
        ##self.modelReset.emit(self)

        #return self.missions.index(mission)

        self.mission.missionModelChanged.emit()
        return 0

    def getMission(self, index):
        #if index < 0 or index >= len(self.missions):
        #    return None
        #return self.missions[index]
        return self.mission

    def removeMission(self, index):
        #if len(self.missions) <= index:
        #    return
        #self.getMission(index).modelChanged.disconnect(self.on_submodel_changed)  # TODO funktionalitaet pruefen
        #miss = self.getMission(index)
        #miss.missionModelChanged.disconnect()
        ##self.missions.pop(index)
        #del self.missions[index]

        #self.clean()
        #self.modelChanged.emit(self)
        ##self.emit(SIGNAL('modelReset()'))
        #self.modelReset.emit(self)

        if self.mission == None:
            return

        self.clean()


    def countMissions(self):
        #return len(self.missions)
        return 1

    def getMissionCRS(self, missionID):
        #return self.getMission(missionID).getCRS()
        return self.mission.getCRS()

    def addTask(self, missionID, task, index=None):
        """
        :param missionID: id of mission to add the task
        :param task: the task
        :param index: when None, adds at the and of the task list
        :return:
        """
        #logging.debug("addTask missionID: {}".format(self.getMission(missionID)))
        QgsMessageLog.logMessage("addTask to mission: {}".format(self.getMission(missionID)),  tag = "Pathplanner2", level = Qgis.Critical)
        #self.getMission(missionID).addTask(task, index)
        self.mission.addTask(task, index)

    def clean(self):
        #for mission in self.missions:
        #    #mission.missionModelChanged.disconnect(self.on_submodel_changed)
        #    self.missionModelChanged.disconnect(self.on_submodel_changed)
        #del self.missions[:]
        ##self.emit(SIGNAL('modelReset()'))
        #self.modelReset.emit(self)
        #self.modelChanged.emit(self)

        self.mission = None
        return


    def __del__(self):
        self.clean()