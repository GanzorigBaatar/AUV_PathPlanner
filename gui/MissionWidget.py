# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtWidgets import QInputDialog
from qgis.PyQt.QtWidgets import QLineEdit, QMessageBox, QListView
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.QtCore import QAbstractListModel, QModelIndex, QObject
from qgis.PyQt import uic

from qgis.core import QgsMessageLog, Qgis

import os, json, glob
import traceback

from ..model.mission import Mission
from ..model.task_waypoint import WaypointTask
from ..model.task_survey import SurveyTask
from ..model.task_circle import CircleTask
from ..model.task_keepstation import KeepStationTask
from ..model.regionslist import Region

from ..config import get_configuration

from .NewTaskDialog import NewTaskDialog
from .RegionWidget import RegionWidget

class MissionWidget(QWidget):
    taskSelectedIndex = pyqtSignal(int)
    regionSelectedIndex = pyqtSignal(int)
    draw = pyqtSignal(QAbstractListModel)

    def __init__(self, parent, stateMachine):
        QWidget.__init__(self, parent)
        path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(path, "MissionWidget.ui"), self)
        self.ui.buttonAddTask.clicked.connect(self.buttonAdd)
        self.ui.buttonRemoveTask.clicked.connect(self.buttonRemove)
        self.ui.buttonRenameTask.clicked.connect(self.taskRename)
        self.ui.buttonTaskUp.clicked.connect(self.taskMoveUp)
        self.ui.buttonTaskDown.clicked.connect(self.taskMoveDown)
        self.ui.buttonAddPayloadItem.clicked.connect(self.taskAddPayload)
        self.ui.buttonRemovePayloadItem.clicked.connect(self.taskRemovePayload)
        self.ui.editTimeoutFactor.editingFinished.connect(self.timeout_factor_changed)
        self.ui.editDepthLimit.editingFinished.connect(self.depth_limit_changed)
        self.ui.editHoGLimit.editingFinished.connect(self.hog_limit_changed)
        self.ui.minimumHeightDoubleSpinBox.valueChanged.connect(self.minimum_height_value_changed)
        self.ui.taskList.pressed.connect(self.on_task_selected)
        self.ui.regionsListView.activated.connect(self.on_region_selected)
        self.ui.regionsListView.pressed.connect(self.on_region_selected)
        self.ui.taskList.doubleClicked.connect(self.task_double_clicked)
        self.ui.buttonAddRestrictedArea.clicked.connect(self.on_button_addRestrictedArea)
        self.ui.buttonAddMissionArea.clicked.connect(self.on_button_addMissionArea)
        self.ui.buttonRemoveArea.clicked.connect(self.on_button_removeArea)
        self.ui.buttonSubmitProperties.clicked.connect(self.submitProperties)
        self.ui.cbHoGLimit.toggled.connect(self.chHoGLimitToggled)
        self.ui.cbDepthLimit.toggled.connect(self.cbDepthLimitToggled)
        self.ui.editName.textChanged.connect(self.on_missionname_changed)
        self.ui.editDescription.textChanged.connect(self.on_description_changed)

        self.regionWidget = RegionWidget(self, stateMachine)
        self.ui.regionsLayout.addWidget(self.regionWidget)

        self.mission = None  # Mission()
        self.taskListWidget = None

        self.readVehicleDefinitions()
        #QgsMessageLog.logMessage("planner type is %s" % get_configuration().plannerType, tag="Pathplanner", level=Qgis.Info)
        if get_configuration().plannerType == 'sabuvis':
            # Remove payload tab
            self.ui.tabWidget.removeTab(self.ui.tabWidget.indexOf(self.ui.payloadTab))
            self.ui.comboDepthMode.currentIndexChanged.connect(self.depthModeChanged)
            self.ui.comboPropellerMode.currentIndexChanged.connect(self.propModeChanged)
            self.ui.buttonAddPayloadItem.hide()
            self.ui.buttonRemovePayloadItem.hide()
            # remove restricted (forbidden) area
            self.ui.buttonAddRestrictedArea.hide()
        else:
            # Remove sabuvis tab
            self.ui.tabWidget.removeTab(self.ui.tabWidget.indexOf(self.ui.sabuvisPropertiesTab))
        self.ui.comboVehicle.currentIndexChanged.connect(self.vehicleChanged)

        self.ui.show()
        self.updateView()

    def all_files(self, pattern, search_path, pathsep=os.pathsep):
        """ Given a search path, yield all files matching the pattern. """
        for path in search_path.split(pathsep):
            for match in glob.glob(os.path.join(path, pattern)):
                yield match

    def readVehicleDefinitions(self):
        self.vehicles = []
        self.ui.comboVehicle.clear()
        # read vdf files from 'vehicles' subdir
        vehDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vehicles")
        QgsMessageLog.logMessage("Trying to load vehicle definition files from %s" % vehDir, tag="Pathplanner",
                                 level=Qgis.Info)
        for match in self.all_files('*.vdf', vehDir):
            try:
                with open(match, 'r') as f:
                    veh = json.load(f)
                    QgsMessageLog.logMessage("Vehicle definition for %s loaded" % (veh['name']),
                                             tag="Pathplanner",
                                             level=Qgis.Info)
                    self.vehicles.append(veh)
                    self.ui.comboVehicle.addItem(veh['name'])
            except:
                QgsMessageLog.logMessage("Error loading vehicle definition %s: %s" % (match, traceback.format_exc()), tag="Pathplanner",
                                         level=Qgis.Critical)

    def on_missionname_changed(self):
        if self.mission:
            self.mission.setName(self.ui.editName.text())

    def on_description_changed(self):
        if self.mission:
            self.mission.setDescription(self.ui.editDescription.text())

    def setMission(self, mission):
        if isinstance(mission, Mission):
            self.mission = mission
            self.mission.missionModelChanged.connect(self.updateView)

            self.ui.payloadList.setModel(self.mission.getPayloadList())
            self.ui.regionsListView.setModel(self.mission.getRegionsList())
        else:
            self.mission = None
            self.regionWidget.setModel(None)
            self.ui.payloadList.setModel(None)
            self.ui.regionsListView.setModel(None)

        try:
            self.ui.taskList.setModel(self.mission)
        except:
            QgsMessageLog.logMessage("Error setting mission: %s" % (traceback.format_exc()),
                                     tag="Pathplanner", level=Qgis.Critical)
            pass

        self.updateView()
        #self.draw.emit(mission)
        self.taskSelectedIndex.emit(-1)

    def setTaskWidget(self, taskWidget):
        self.taskListWidget = taskWidget
        layout = self.ui.taskEditWidget.layout()
        # clearLayout(layout):
        while layout.count():
            layout.takeAt(0).widget().deleteLater()
        layout.addWidget(taskWidget)

    def getModel(self):
        return self.mission

    @pyqtSlot()
    def updateView(self):
        if self.mission:
            self.ui.editName.setText(str(self.mission.getName()))
            self.ui.editDescription.setText(str(self.mission.getDescription()))
            taskTimeoutAction = self.mission.getTaskTimeoutAction()
            if taskTimeoutAction == "ABORT":
                self.ui.comboTaskTimeoutAction.setCurrentIndex(0)
            elif taskTimeoutAction == "CONTINUE":
                self.ui.comboTaskTimeoutAction.setCurrentIndex(1)
            else:
                self.ui.comboTaskTimeoutAction.setCurrentIndex(0)
            self.ui.editTotalTime.setText("%.1f s" % (self.mission.getTotalTime()))
            self.ui.editTimeoutFactor.setText(str(self.mission.getTimeoutFactor()))
            self.ui.editTotalDistance.setText("%.2f m" % (self.mission.getTotalDistance()))
            self.ui.editTotalTimeout.setText("%.1f s" % (self.mission.getTotalTimeOut()))
            self.ui.editHoGLimit.setText(str(self.mission.getHoGLimit()))
            self.ui.editDepthLimit.setText(str(self.mission.getDepthLimit()))
            self.ui.minimumHeightDoubleSpinBox.setValue(self.mission.getMinimumHeight())
            self.ui.cbHoGLimit.setChecked(self.mission.getUseHoGLimit())
            self.ui.cbDepthLimit.setChecked(self.mission.getUseDepthLimit())
            idx = self.ui.comboVehicle.findText(self.mission.getVehicleName(), Qt.MatchFixedString)
            if idx >= 0:
                self.ui.comboVehicle.setCurrentIndex(idx)
            else:
                self.ui.comboVehicle.setCurrentIndex(0)
            # sabuvis extensions
            idx = self.ui.comboDepthMode.findText(self.mission.getDepthMode(), Qt.MatchFixedString)
            if idx >= 0:
                self.ui.comboDepthMode.setCurrentIndex(idx)
            idx = self.ui.comboPropellerMode.findText(self.mission.getPropellerMode(), Qt.MatchFixedString)
            if idx >= 0:
                self.ui.comboPropellerMode.setCurrentIndex(idx)

            self.mission.dataChanged.emit(QModelIndex(), QModelIndex(), [])
            self.draw.emit(self.mission)

        else:
            self.ui.editName.setText("")
            self.ui.editDescription.setText("")
            #self.ui.editCRS.setText("")
            #self.ui.editMissionID.setText("")
            self.ui.editTimeoutFactor.setText("")
            self.ui.editTotalTime.setText("")
            self.ui.editTotalDistance.setText("")
            self.ui.editTotalTimeout.setText("")
            self.ui.editHoGLimit.setText("")
            self.ui.editDepthLimit.setText("")
            self.ui.minimumHeightDoubleSpinBox.setValue(0.0)
            self.ui.comboTaskTimeoutAction.setCurrentIndex(0)
            self.ui.cbHoGLimit.setChecked(False)
            self.ui.cbDepthLimit.setChecked(False)
            self.ui.comboVehicle.setCurrentIndex(0)
            self.ui.comboDepthMode.setCurrentIndex(0)
            self.ui.comboPropellerMode.setCurrentIndex(0)

    @pyqtSlot(bool)
    def cbDepthLimitToggled(self, checked):
        if self.mission is not None:
            self.mission.setUseDepthLimit(checked)

    @pyqtSlot(bool)
    def chHoGLimitToggled(self, checked):
        if self.mission is not None:
            self.mission.setUseHoGLimit(checked)

    @pyqtSlot(bool)
    def submitProperties(self):
        if self.mission is not None:
            self.mission.setMinimumHeight(self.ui.minimumHeightDoubleSpinBox.value())
            timeoutFactor = self.ui.editTimeoutFactor.text()
            hogLimit = self.ui.editHoGLimit.text()
            depthLimit = self.ui.editDepthLimit.text()
            useDepthLimit = self.ui.cbDepthLimit.isChecked()
            useHoGLimit = self.ui.cbHoGLimit.isChecked()
            try:
                timeoutFactor = float(timeoutFactor)
                hogLimit = float(hogLimit)
                depthLimit = float(depthLimit)
            except:
                QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)
                pass
            if timeoutFactor <= 1: # <= 1?
                timeoutFactor = 1
            taskTimeoutAction = self.ui.comboTaskTimeoutAction.currentText()

            self.mission.setTimeoutFactor(timeoutFactor)
            self.mission.setDepthLimit(depthLimit)
            self.mission.setHoGLimit(hogLimit)
            self.mission.setUseDepthLimit(useDepthLimit)
            self.mission.setUseHoGLimit(useHoGLimit)
            self.mission.setTaskTimeoutAction(taskTimeoutAction)
            # the last action (above) is not executed, but reverted!? That's why I moved self.mission.setMinimumHeight()
            # to the beginning of the function
            self.mission.missionModelChanged.emit()

    # sabuvis extension
    @pyqtSlot(int)
    def depthModeChanged(self, index):
        self.mission.setDepthMode(self.ui.comboDepthMode.currentText())
        ###self.mission.modelChanged.emit(self.mission)

    # sabuvis extension
    @pyqtSlot(int)
    def propModeChanged(self, index):
        self.mission.setPropellerMode(self.ui.comboPropellerMode.currentText())
        ###self.mission.modelChanged.emit(self.mission)

    @pyqtSlot(int)
    def vehicleChanged(self, index):
        if self.mission:
            self.mission.setVehicleName(self.ui.comboVehicle.currentText())
            ###self.mission.modelChanged.emit(self.mission)

    @pyqtSlot()
    def buttonAdd(self):
        task = None
        if not self.mission:
            QgsMessageLog.logMessage("buttonAdd - self.mission empty", tag="Pathplanner", level=Qgis.Critical)
            return
        cnt = self.mission.countTasks() + 1
        # task-{id} instead of task-{uuid.uuid1()} - for
        #name, taskType, result = NewTaskDialog.execNewTask(self, "task-" +str(uuid.uuid1()))
        name, taskType, result = NewTaskDialog.execNewTask(self, "task-" + str(cnt))
        #logging.debug("new task", name, taskType, result)
        if result:
            if taskType.lower() == "waypoint" or taskType.lower() == "waypoints":
                task = WaypointTask()
            elif taskType.lower() == "survey":
                task = SurveyTask()
            elif taskType.lower() == "circle":
                task = CircleTask()
            elif taskType.lower() == "keepstation":
                task = KeepStationTask()
            else:
                QMessageBox.information(self, "New task", "Task type '{}' not supported.".format(taskType))

            task.setName(name)
            count = self.mission.addTask(task)
            # select new Task
            index = self.mission.createIndex(count - 1, 0)
            self.ui.taskList.setCurrentIndex(index)
            self.taskSelectedIndex.emit(count - 1)

    @pyqtSlot()
    def taskRename(self):
        index = self.ui.taskList.currentIndex().row()
        if self.mission and index != -1:
            task = self.mission.getTask(index)
            oldName = task.getName()
            [text, ok] = QInputDialog.getText(self, "Rename task", "Name:", QLineEdit.Normal, oldName)
            if ok and text and not text.isspace():
                task.setName(text)

    @pyqtSlot()
    def buttonRemove(self):
        index = self.ui.taskList.currentIndex().row()
        if self.mission and index != -1:
            self.mission.removeTask(index)
            if index == 0:
                self.taskSelectedIndex.emit(-1)
            else:
                self.taskSelectedIndex.emit(0)
        else:
            self.taskSelectedIndex.emit(-1)

        #if self.ui.taskList.currentIndex().row() == -1:
        #    self.taskSelectedIndex.emit(-1)
        #self.taskSelectedIndex.emit(0)

    @pyqtSlot()
    def taskMoveUp(self):
        index = self.ui.taskList.currentIndex().row()
        if self.mission and index != -1 and index > 0:
            task = self.mission.getTask(index)
            self.mission.tasks.pop(index)
            self.mission.addTask(task, index - 1)

    @pyqtSlot()
    def taskMoveDown(self):
        index = self.ui.taskList.currentIndex().row()
        if self.mission and index != -1 and index < self.mission.countTasks() - 1:
            task = self.mission.getTask(index)
            self.mission.tasks.pop(index)
            self.mission.addTask(task, index + 1)

    @pyqtSlot(QModelIndex)
    def on_task_selected(self, value=None):
        if type(value) is QModelIndex:
            self.taskSelectedIndex.emit(value.row())

    @pyqtSlot(QModelIndex)
    def on_region_selected(self, value=None):
        if type(value) is QModelIndex and self.mission:
            if value.row() >= 0:
                regionsList = self.mission.getRegionsList()
                region = regionsList.getItemAt(value.row())
                if region:
                    self.regionWidget.setModel(region)
                else:
                    pass
            else:
                self.regionWidget.setModel(None)

    @pyqtSlot()
    def taskAddPayload(self):
        if not self.mission:
            return
        text, ok = QInputDialog.getText(self, 'New payload item', 'Payload name:')
        text = text.strip()
        if ok and (len(text) > 0):
            self.mission.getPayloadList().addItem(text)

    @pyqtSlot()
    def taskRemovePayload(self):
        index = self.ui.payloadList.currentIndex().row()
        if self.mission and index != -1:
            self.mission.getPayloadList().removeItemAt(index)

    @pyqtSlot()
    def taskRenamePayload(self):
        pass

    @pyqtSlot()
    def on_button_addMissionArea(self):
        if not self.mission:
            return
        area = Region()
        area.setParentMission(self.mission)
        area.setType("mission")
        #self.mission.getRegionsList().addItem(area)
        self.mission.regionsList.addItem(area)

    @pyqtSlot()
    def on_button_addRestrictedArea(self):
        if not self.mission:
            return
        area = Region()
        area.setParentMission(self.mission)
        area.setType("restricted")
        #self.mission.getRegionsList().addItem(area)
        self.mission.regionsList.addItem(area)

    @pyqtSlot()
    def on_button_removeArea(self):
        index = self.ui.regionsListView.currentIndex().row()
        if self.mission and index != -1:
            self.mission.getRegionsList().removeItemAt(index)

        if index == 0:
            # wenn keine regions mehr vohranden ist, lösche RegionWidget
            pass

    @pyqtSlot()
    def timeout_factor_changed(self):
        self.submitProperties()

    @pyqtSlot()
    def depth_limit_changed(self):
        self.submitProperties()

    @pyqtSlot()
    def hog_limit_changed(self):
        self.submitProperties()

    @pyqtSlot()
    def minimum_height_value_changed(self):
        self.submitProperties()

    @pyqtSlot()
    def task_double_clicked(self, index=0):
        self.taskSelectedIndex.emit(index)