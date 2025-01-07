# -*- coding: utf-8 -*-

from qgis.PyQt.QtWidgets import QWidget, QAbstractItemView
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QDoubleValidator

import os

from ..model import Task, WaypointTask
from ..PlannerStateMachine import PlannerState

class WaypointPropertyWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(self.path, "WaypointProperties.ui"), self)
        self.model = None
        self.setEditValidator()

    def setModel(self,model):
        if isinstance(model, Task):
            self.model = model
            self.model.modelChanged.connect(self.updateView)
            self.model.parentMission.missionModelChanged.emit()
            self.setConnections()
        else:
            pass

    def breakConnection(self):
        if self.model is not None:
            try:
                self.model.modelChanged.disconnect()
            except:
                pass
            pass

    def submit(self):
        if self.model.type() == 'waypoint':
            if self.model:
                properties = self.model.getProperties()
                self.model.setDescription(self.ui.editDescription.text())
                timeout = self.ui.editTimeout.text()
                priority = self.ui.spinBoxPriority.cleanText()
                speed = self.ui.editSpeed.text()
                trackControllerMode = self.ui.comboTrackControllerMode.currentText()
                depthControllerMode = self.ui.comboDepthControllerMode.currentText()
                arrivalRadius = self.ui.editArrivalRadius.text()
                distToLOS = self.ui.editDistToLOS.text()
                depthHeightInvalid = self.ui.editDepthIfHeightInvalid.text()
                lookAheadDistance = self.ui.editLookAheadDistance.text()
                constantDepth = self.ui.editConstantDepth.text()
                heightOverGround = self.ui.editHeightOverGround.text()
                heightIterations = self.ui.editHeightIterations.text()
                pitchControl = self.ui.comboPitchControl.currentIndex()
                pitchSetPoint = self.ui.editPitchSetPoint.text()

                properties.setTimeout(timeout)
                properties.setPriority(priority)
                properties.setSpeed(speed)
                properties.setTrackControllerMode(trackControllerMode)
                properties.setDepthControllerMode(depthControllerMode)
                properties.setArrivalRadius(arrivalRadius)
                properties.setDistToLOS(distToLOS)
                properties.setDepthHeightInvalid(depthHeightInvalid)
                properties.setLookAheadDistance(lookAheadDistance)
                properties.setConstantDepth(constantDepth)
                properties.setHeightOverGround(heightOverGround)
                properties.setHeightIterations(heightIterations)
                properties.setPitchControl(pitchControl)
                properties.setPitchSetPoint(pitchSetPoint)
                properties.propertiesChanged.emit()
                self.model.parentMission.missionModelChanged.emit()

    @pyqtSlot()
    def updateView(self):
        if self.model:
            prop = self.model.getProperties()
            dist = float(prop.getDistance())

            self.ui.editDistance.setText("%.2f" %(dist))
            self.ui.editSpeed.setText(str(prop.getSpeed()))
            self.ui.editTime.setText(str(prop.getTime()))
            self.ui.editTimeout.setText(str(prop.getTimeout()))
            self.ui.spinBoxPriority.setValue(int(prop.getPriority()))
            self.ui.editArrivalRadius.setText(str(prop.getArrivalRadius()))
            self.ui.editLookAheadDistance.setText(str(prop.getLookAheadDistance()))
            tcm = prop.getTrackControllerMode()
            if tcm == 'CTE (Cross Track Error)':
                self.ui.comboTrackControllerMode.setCurrentIndex(0)
            elif tcm == 'LOS (Line Of Sight)':
                self.ui.comboTrackControllerMode.setCurrentIndex(1)
            dcm = prop.getDepthControllerMode()
            if dcm == 'Waypoints':
                self.ui.comboDepthControllerMode.setCurrentIndex(0)
            elif dcm == 'ConstantDepth':
                self.ui.comboDepthControllerMode.setCurrentIndex(1)
            elif dcm == 'HeightOverGround':
                self.ui.comboDepthControllerMode.setCurrentIndex(2)
            self.ui.editHeightIterations.setText(str(prop.getHeightIterations()))
            self.ui.editDepthIfHeightInvalid.setText(str(prop.getDepthHeightInvalid()))
            self.ui.editHeightOverGround.setText(str(prop.getHeightOverGround()))
            self.ui.editConstantDepth.setText(str(prop.getConstantDepth()))
            self.ui.comboPitchControl.setCurrentIndex(int(prop.getPitchControl()))
            self.ui.editPitchSetPoint.setText(str(prop.getPitchSetPoint()))
            self.ui.editDistToLOS.setText(str(prop.getDistToLOS()))

    def setConnections(self):
        self.ui.editSpeed.editingFinished.connect(self.submit)
        self.ui.comboPitchControl.currentIndexChanged.connect(self.submit)
        self.ui.editPitchSetPoint.editingFinished.connect(self.submit)
        self.ui.editArrivalRadius.editingFinished.connect(self.submit)
        self.ui.editLookAheadDistance.editingFinished.connect(self.submit)
        self.ui.editDistToLOS.editingFinished.connect(self.submit)
        self.ui.comboTrackControllerMode.currentIndexChanged.connect(self.submit)
        self.ui.comboDepthControllerMode.currentIndexChanged.connect(self.submit)
        self.ui.editHeightIterations.editingFinished.connect(self.submit)
        self.ui.editDepthIfHeightInvalid.editingFinished.connect(self.submit)
        self.ui.editHeightOverGround.editingFinished.connect(self.submit)
        self.ui.editConstantDepth.editingFinished.connect(self.submit)

    def setEditValidator(self):
        # set validator for edit fields
        dbl_vld = QDoubleValidator()
        self.ui.editSpeed.setValidator(dbl_vld)
        self.ui.editPitchSetPoint.setValidator(dbl_vld)
        self.ui.editArrivalRadius.setValidator(dbl_vld)
        self.ui.editLookAheadDistance.setValidator(dbl_vld)
        self.ui.editDistToLOS.setValidator(dbl_vld)
        self.ui.editHeightIterations.setValidator(dbl_vld)
        self.ui.editDepthIfHeightInvalid.setValidator(dbl_vld)
        self.ui.editHeightOverGround.setValidator(dbl_vld)
        self.ui.editConstantDepth.setValidator(dbl_vld)


class WaypointWidget(QWidget):

    def __init__(self, parent, stateMachine):
        QWidget.__init__(self, parent)
        path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(path, "WaypointsWidget.ui"), self)

        self.ui.pointTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.addButton.toggled.connect(self.addPointSlot)
        self.ui.moveButton.toggled.connect(self.movePointSlot)
        self.ui.deleteButton.clicked.connect(self.deletePoint)
        self.ui.buttonPointUp.clicked.connect(self.pointUpSlot)
        self.ui.buttonPointDown.clicked.connect(self.pointDownSlot)
        self.ui.pointTable.pressed.connect(self.selectPoint)

        self.stateMachine = stateMachine
        self.model = None
        self.updateView()

    def setModel(self, task):
        if isinstance(task, WaypointTask):
            self.model = task
            self.ui.pointTable.setModel(task)
        else:
            self.model = None
        self.stateMachine.setModel(task)
        self.updateView()

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

    @pyqtSlot()
    def pointUpSlot(self):
        index = self.getSelectedPoint()
        if index < 0:
            return
        self.model.movePoint(index, index - 1)
        self.updateView()

    @pyqtSlot()
    def pointDownSlot(self):
        index = self.getSelectedPoint()
        if index < 0:
            return
        self.model.movePoint(index, index + 1)
        self.updateView()

    def getSelectedPoint(self):
        return self.ui.pointTable.currentIndex().row()

    @pyqtSlot(bool)
    def addPointSlot(self, checked):
        if checked:
            self.stateMachine.switchState(PlannerState.POINTADD, self.model)
            self.stateMachine.leaveState.connect(self.uncheckAddButton)
        else:
            self.stateMachine.switchState(PlannerState.IDLE)
            try:
                self.stateMachine.leaveState.disconnect()
            except:
                pass

    @pyqtSlot()
    def uncheckAddButton(self):
        self.ui.addButton.setChecked(False)
        self.updateView()

    @pyqtSlot()
    def uncheckMoveButton(self):
        self.ui.moveButton.setChecked(False)

    @pyqtSlot()
    def deletePoint(self):
        self.stateMachine.switchState(PlannerState.IDLE)
        index = self.getSelectedPoint()
        if index != -1:
            self.model.removePointAt(index)
            self.updateView()

    @pyqtSlot()
    def selectPoint(self):
        index = self.getSelectedPoint()
        self.model.highlightPointAt(index)
        # redraw path in order to highlight the point visually
        self.model.parentMission.missionModelChanged.emit()


    @pyqtSlot(bool)
    def movePointSlot(self, checked):
        index = self.ui.pointTable.currentIndex().row()
        if index != -1:
            if checked:
                index = self.getSelectedPoint()
                self.stateMachine.setIndex(index)
                self.stateMachine.switchState(PlannerState.POINTMOVE, self.model)
                self.stateMachine.leaveState.connect(self.uncheckMoveButton)
            else:
                self.stateMachine.switchState(PlannerState.IDLE)
                try:
                    self.stateMachine.leaveState.disconnect()
                except:
                    pass

