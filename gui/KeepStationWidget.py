# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QDoubleValidator, QIntValidator
from qgis.core import QgsMessageLog, Qgis

import os

from ..model.task import Task
from ..model.point import Point
from ..model.task_keepstation import KeepStationTask

from ..PlannerStateMachine import PlannerState

class KeepStationPropertyWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(self.path, "KeepStationProperties.ui"), self)
        self.model = None
        self.ui.editTimeout.setValidator(QIntValidator(bottom=0, top=86400))
        self.ui.editSpeed.setValidator(QDoubleValidator(bottom=0.0, top=3.0))


    def setModel(self,model):
        if isinstance(model, Task):
            self.model = model
            self.model.modelChanged.connect(self.updateView)
            self.updateView()
            self.setConnections()

    def breakConnection(self):
        if self.model is not None:
            self.model.modelChanged.disconnect()

    def submit(self):
        if self.model.type() == 'keepstation':
            if self.model:
                properties = self.model.getProperties()
                self.model.setDescription(self.ui.editDescription.text())
                timeout = self.ui.editTimeout.text()
                priority = self.ui.spinBoxPriority.cleanText()
                speed = self.ui.editSpeed.text()
                properties.setTimeout(timeout)
                properties.setPriority(priority)
                properties.setSpeed(speed)
                properties.propertiesChanged.emit()
                self.model.modelChanged.emit()

    def updateView(self):
        if self.model:
            prop = self.model.getProperties()
            self.ui.editSpeed.setText(str(prop.getSpeed()))
            self.ui.editTimeout.setText(str(prop.getTimeout()))
            self.ui.spinBoxPriority.setValue(int(prop.getPriority()))

    def setConnections(self):
        self.ui.editSpeed.editingFinished.connect(self.submit)
        self.ui.editTimeout.editingFinished.connect(self.submit)


class KeepStationWidget(QWidget):
    taskUp = pyqtSignal()
    taskDown = pyqtSignal()

    def __init__(self, parent, stateMachine):
        QWidget.__init__(self, parent)
        path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(path, "KeepStationWidget.ui"), self)
        self.ui.setButton.toggled.connect(self.setPointSlot)
        self.ui.submitRadiusButton.clicked.connect(self.submitButton_clicked)
        self.ui.editLat.editingFinished.connect(self.submitButton_clicked)
        self.ui.editLon.editingFinished.connect(self.submitButton_clicked)
        self.ui.editDepth.editingFinished.connect(self.submitButton_clicked)
        self.ui.editInnerRadius.editingFinished.connect(self.submitButton_clicked)
        self.ui.editOuterRadius.editingFinished.connect(self.submitButton_clicked)

        dbl_vld = QDoubleValidator()

        self.ui.editLat.setValidator(dbl_vld)
        self.ui.editLon.setValidator(dbl_vld)
        self.ui.editDepth.setValidator(dbl_vld)
        self.ui.editInnerRadius.setValidator(dbl_vld)
        self.ui.editOuterRadius.setValidator(dbl_vld)

        self.stateMachine = stateMachine
        self.model = None
        self.updateView()

    def setModel(self, task):
        if self.model is not None:
            try:
                self.model.modelChanged.disconnect()
            except:
                pass
        if isinstance(task, KeepStationTask):
            self.model = task
            self.model.modelChanged.connect(self.modelChangedSlot)
            self.model.parentMission.missionModelChanged.emit()
            self.updateView()
        else:
            self.model = None
            self.eraseView()
        self.stateMachine.setModel(task)
        self.updateView()

    def eraseView(self):
        self.ui.editLon.setText("")
        self.ui.editLat.setText("")
        self.ui.editDepth.setText("")
        self.ui.editInnerRadius.setText("")
        self.ui.editOuterRadius.setText("")

    @pyqtSlot()
    def modelChangedSlot(self):
        # QgsMessageLog.logMessage("KeepStationWidget.modelChangedSlot() - model %s" % (self.model.type()),
        #                          tag="Pathplanner", level=Qgis.Info)
        if self.model.type() == 'keepstation':
            point = self.model.getPoint()
            if point is None:
                self.ui.editLon.setText("n/a")
                self.ui.editLat.setText("n/a")
                self.ui.editDepth.setText("n/a")
            else:
                self.ui.editLon.setText(str(point.getX()))
                self.ui.editLat.setText(str(point.getY()))
                self.ui.editDepth.setText(str(point.getDepth()))
            self.ui.editInnerRadius.setText(str(self.model.getInnerRadius()))
            self.ui.editOuterRadius.setText(str(self.model.getOuterRadius()))

    def getModel(self):
        return self.model

    def updateView(self):
        if self.model:
            prop = self.model.getProperties()
            prop.propertiesChanged.emit()
            self.model.parentMission.missionModelChanged.emit()
        else:
            pass
        return

    @pyqtSlot(bool)
    def setPointSlot(self, checked):
        if checked:
            self.stateMachine.switchState(PlannerState.POINTSET, self.model)
            self.stateMachine.leaveState.connect(self.uncheckSetButton)
        else:
            self.stateMachine.switchState(PlannerState.IDLE)
            self.stateMachine.leaveState.disconnect()

    @pyqtSlot()
    def submitButton_clicked(self):
        if self.model.type() == 'keepstation':
            depth = self.ui.editDepth.text()
            if depth == 'n/a':
                return
            try:
                depth = float(depth)
            except:
                depth = 0

            centerlon = float(self.ui.editLon.text())
            centerlat = float(self.ui.editLat.text())

            self.model.setPoint(Point(centerlon, centerlat))
            self.model.setInnerRadius(float(self.ui.editInnerRadius.text()))
            self.model.setOuterRadius(float(self.ui.editOuterRadius.text()))
            self.model.setDepth(depth)
            #self.model.modelChanged.emit()
            self.model.properties.propertiesChanged.emit()
            self.model.parentMission.missionModelChanged.emit()

    @pyqtSlot()
    def uncheckSetButton(self):
        self.ui.setButton.setChecked(False)