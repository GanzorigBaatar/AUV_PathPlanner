# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.QtCore import QAbstractListModel, QModelIndex, QObject
from qgis.PyQt.QtWidgets import QScrollArea
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QMessageBox

import os

from ..model.task import Task
from .CircleWidget import CircleWidget, CirclePropertyWidget
from .SurveyWidget import SurveyWidget,SurveyPropertyWidget
from .WaypointWidget import WaypointWidget, WaypointPropertyWidget
from .KeepStationWidget import KeepStationWidget, KeepStationPropertyWidget
from qgis.core import QgsMessageLog, Qgis


class TaskPayloadModel(QAbstractListModel):

    '''
    Model to help with the data handling of the payload enable disable widget of the tasks widget
    '''
    def __init__(self, payloadList, task):
        QAbstractListModel.__init__(self)
        self.payloadList = payloadList  # TODO Datentyp prüfen
        self.task = task
        self.task.payloadStateChanged.connect(self.on_list_changed)

    # ListModel - begin
    def rowCount(self, parent=QModelIndex()):
        return self.payloadList.rowCount(parent)

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            text = self.payloadList.data(index, role)
            evtAtEnd = self.task.getPayloadEventAtEnd(text)
            if evtAtEnd is None:
                evtAtEndText = " \t " + "       "
            else:
                evtAtEndText = " \t E: " + evtAtEnd
            evtAtBegin = " \t " + "       "
            if text in self.task.getEnabledPayload():
                evtAtBegin = "\t B: enable"
            elif text in self.task.getDisabledPayload():
                evtAtBegin = "\t B: disable"
            return text + evtAtBegin + evtAtEndText
        else:
            return None
    # ListModel - end

    @pyqtSlot()
    def on_list_changed(self):
        self.modelReset.emit()
        pass

    def __del__(self):
        self.task.payloadStateChanged.disconnect(self.on_list_changed)

class TaskWidget(QWidget):

    def __init__(self, parent, canvas, clickTool, stateMachine):
        QWidget.__init__(self, parent)
        path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(path, "TaskWidget.ui"), self)
        self.task = None
        self.canvas = canvas
        self.clickTool = clickTool

        self.waypointWidget = WaypointWidget(self, stateMachine)
        self.waypointWidget.hide()
        self.surveyWidget = SurveyWidget(self, stateMachine)
        self.surveyWidget.hide()
        self.circleWidget = CircleWidget(self, stateMachine)
        self.circleWidget.hide()
        self.kestWidget = KeepStationWidget(self, stateMachine)
        self.kestWidget.hide()

        self.propertyWidget = None
        self.ui.buttonSubmit.clicked.connect(self.submitTaskProperties)
        self.ui.buttonReset.clicked.connect(self.updateView)
        self.ui.buttonPayloadEnable.clicked.connect(self.on_button_payload_enable)
        self.ui.buttonPayloadDisable.clicked.connect(self.on_button_payload_disable)
        self.ui.buttonPayloadKeepState.clicked.connect(self.on_button_payload_ignore)
        self.ui.buttonPayloadEnableAtEnd.clicked.connect(self.on_button_payload_enable_at_end)
        self.ui.buttonPayloadDisableAtEnd.clicked.connect(self.on_button_payload_disable_at_end)
        self.ui.buttonPayloadClearStateAtEnd.clicked.connect(self.on_button_payload_clear_at_end)
        self.updateView()

    def setModel(self, task):
        if self.task is not None and self.propertyWidget is not None:
            self.propertyWidget.breakConnection()
        if self.ui.taskTabWidget.count() > 2:
            self.ui.taskTabWidget.removeTab(2)
        if isinstance(task, Task):
            self.task = task
            self.ui.payloadList.setModel(TaskPayloadModel(self.task.getParentMission().getPayloadList(), self.task))
            if task.getTaskType() == "waypoint":
                self.waypointWidget.setModel(task)
                self.waypointWidget.show()
                self.ui.taskTabWidget.addTab(self.waypointWidget, "Waypoints")
                self.propertyWidget = WaypointPropertyWidget(self)

            elif task.getTaskType() == "survey":
                self.surveyWidget.setModel(task)
                self.surveyWidget.show()

                # add Survey Widget to an Scroll area due to the size compatibility problem
                self.surveyArea = QScrollArea()
                self.ui.taskTabWidget.addTab(self.surveyArea, "Survey")
                self.surveyArea.setWidget(self.surveyWidget)
                self.surveyArea.setWidgetResizable(True)
                self.propertyWidget = SurveyPropertyWidget(self)

            elif task.getTaskType() == "circle":
                self.circleWidget.setModel(task)
                self.circleWidget.show()
                self.ui.taskTabWidget.addTab(self.circleWidget, "Circle")
                self.propertyWidget = CirclePropertyWidget(self)
            elif task.getTaskType() == "keepstation":
                self.kestWidget.setModel(task)
                self.kestWidget.show()
                self.ui.taskTabWidget.addTab(self.kestWidget, "KeepStation")
                self.propertyWidget = KeepStationPropertyWidget(self)
            else:
                QMessageBox.critical(self, "Invalid task type", "Task type '{}' currently not supported by TaskWidget!".format(task.getTaskType()))
            self.ui.scrollArea.setWidget(self.propertyWidget)
            self.propertyWidget.setModel(task)
            self.taskTabWidget.setCurrentIndex(2)

        else:
            self.task = None
            self.waypointWidget.setModel(None)
            self.surveyWidget.setModel(None)
            self.circleWidget.setModel(None)
            self.kestWidget.setModel(None)
            self.ui.scrollArea.takeWidget()
        #self.updateView()

    def removeTab(self):
        self.ui.taskTabWidget.removeTab(2)

    def getModel(self):
        return self.task

    @pyqtSlot()
    def submitTaskProperties(self):
        if self.task and self.propertyWidget:
            self.propertyWidget.submit()

    @pyqtSlot()
    def updateView(self):
        if self.propertyWidget:
            self.propertyWidget.updateView()
        if self.task:
            self.ui.editName.setText(self.task.getName())
        else:
            self.ui.editName.setText("")

    def __getSelectedPayload__(self):
        if self.task:
            # index = self.ui.payloadList.currentIndex().row()
            return self.task.getParentMission().getPayloadList().data(self.ui.payloadList.currentIndex(), Qt.DisplayRole)

        else:
            return None

    @pyqtSlot()
    def on_button_payload_enable(self):
        text = self.__getSelectedPayload__()
        if text:
            self.task.enablePayload(text)

    @pyqtSlot()
    def on_button_payload_disable(self):
        text = self.__getSelectedPayload__()
        if text:
            self.task.disablePayload(text)

    @pyqtSlot()
    def on_button_payload_ignore(self):
        text = self.__getSelectedPayload__()
        if text:
            self.task.ignorePayload(text)

    @pyqtSlot()
    def on_button_payload_enable_at_end(self):
        text = self.__getSelectedPayload__()
        if text:
            QgsMessageLog.logMessage("enabling payload %s at end" % text, tag="Pathplanner", level=Qgis.Info)
            self.task.changePayloadEventAtEnd(text, "enable")

    @pyqtSlot()
    def on_button_payload_disable_at_end(self):
        text = self.__getSelectedPayload__()
        if text:
            QgsMessageLog.logMessage("disabling payload %s at end" % text, tag="Pathplanner", level=Qgis.Info)
            self.task.changePayloadEventAtEnd(text, "disable")

    @pyqtSlot()
    def on_button_payload_clear_at_end(self):
        text = self.__getSelectedPayload__()
        if text:
            QgsMessageLog.logMessage("clearing payload %s at end event" % text, tag="Pathplanner", level=Qgis.Info)
            self.task.changePayloadEventAtEnd(text)
