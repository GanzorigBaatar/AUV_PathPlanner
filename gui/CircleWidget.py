# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QDoubleValidator

import os

from ..model.task import Task
from ..model.point import Point
from ..model.task_circle import CircleTask

from ..PlannerStateMachine import PlannerState

class CirclePropertyWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(self.path, "CircleProperties.ui"), self)
        self.model = None
        self.setEditValidator()

    def setModel(self,model):
        if isinstance(model, Task):
            self.model = model
            self.model.modelChanged.connect(self.updateView)
            self.updateView()
            self.setConnections()
        else:
            pass

    def breakConnection(self):
        if self.model is not None:
            self.model.modelChanged.disconnect()

    def submit(self):
        if self.model.type() == 'circle':
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
                # constant depth will appear as depth in circle task
                self.model.setDepth(float(constantDepth))
                heightOverGround = self.ui.editHeightOverGround.text()
                heightIterations = self.ui.editHeightIterations.text()
                pitchControl = self.ui.comboPitchControl.currentIndex()
                pitchSetPoint = self.ui.editPitchSetPoint.text()
                supProp = self.ui.comboSupressPropulsion.currentIndex()

                #trackControllerValue = self.ui.editTrackControllerValue.text()
                #properties.setTrackControllerValue(trackControllerValue)

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
                properties.setSupressPropulsion(supProp)
                properties.propertiesChanged.emit()
                self.model.modelChanged.emit()

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
            if dcm == 'ConstantDepth':
                self.ui.comboDepthControllerMode.setCurrentIndex(0)
            elif dcm == 'HeightOverGround':
                self.ui.comboDepthControllerMode.setCurrentIndex(1)
            self.ui.editHeightIterations.setText(str(prop.getHeightIterations()))
            self.ui.editDepthIfHeightInvalid.setText(str(prop.getDepthHeightInvalid()))
            self.ui.editHeightOverGround.setText(str(prop.getHeightOverGround()))
            self.ui.editConstantDepth.setText(str(prop.getConstantDepth()))
            self.ui.comboPitchControl.setCurrentIndex(int(prop.getPitchControl()))
            self.ui.editPitchSetPoint.setText(str(prop.getPitchSetPoint()))
            self.ui.editDistToLOS.setText(str(prop.getDistToLOS()))
            self.ui.comboSupressPropulsion.setCurrentIndex(prop.getSupressPropulsion())

            # self.ui.editTrackControllerValue.setText(str(prop.getTrackControllerValue()))

    def setConnections(self):
        self.ui.editSpeed.editingFinished.connect(self.submit)
        self.ui.comboSupressPropulsion.currentIndexChanged.connect(self.submit)
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
        # use validator to allow only numbers for edit fields
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

class CircleWidget(QWidget):
    taskUp = pyqtSignal()
    taskDown = pyqtSignal()

    def __init__(self, parent, stateMachine):
        QWidget.__init__(self, parent)
        path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(path, "CircleWidget.ui"), self)
        self.ui.setButton.toggled.connect(self.setPointSlot)
        self.ui.submitRadiusButton.clicked.connect(self.submitButton_clicked)
        self.ui.editLat.editingFinished.connect(self.submitButton_clicked)
        self.ui.editLon.editingFinished.connect(self.submitButton_clicked)
        self.ui.editVariable.editingFinished.connect(self.submitButton_clicked)
        self.ui.editDepth.editingFinished.connect(self.submitButton_clicked)
        self.ui.editRadius.editingFinished.connect(self.submitButton_clicked)

        dbl_vld = QDoubleValidator()

        self.ui.editLat.setValidator(dbl_vld)
        self.ui.editLon.setValidator(dbl_vld)
        self.ui.editVariable.setValidator(dbl_vld)
        self.ui.editDepth.setValidator(dbl_vld)
        self.ui.editRadius.setValidator(dbl_vld)

        self.stateMachine = stateMachine
        self.model = None
        self.updateView()

    def setModel(self, task):
        if self.model is not None:
            try:
                self.model.modelChanged.disconnect()
            except:
                pass
        if isinstance(task, CircleTask):
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
        self.ui.editRadius.setText("")

    @pyqtSlot()
    def modelChangedSlot(self):
        if self.model.type() == 'circle':
            point = self.model.getPoint()
            prop = self.model.getProperties()
            if point is None:
                self.ui.editLon.setText("n/a")
                self.ui.editLat.setText("n/a")
                self.ui.editDepth.setText("n/a")
            else:
                self.ui.editLon.setText(str(point.getX()))
                self.ui.editLat.setText(str(point.getY()))
                self.ui.editDepth.setText(str(point.getDepth()))
            self.ui.editRadius.setText(str(self.model.getRadius()))
            rotDir = self.model.getRotationDirection()
            if rotDir == 'Clockwise':
                self.ui.comboRotationDirection.setCurrentIndex(0)
            elif rotDir == 'CounterClockwise':
                self.ui.comboRotationDirection.setCurrentIndex(1)
            else:
                self.ui.comboRotationDirection.setCurrentIndex(0)

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
        if self.model.type() == 'circle':
            depth = self.ui.editDepth.text()
            if depth == 'n/a':
                return
            try:
                depth = float(depth)
            except:
                depth = 0

            radius = float(self.ui.editRadius.text())
            rotDir = self.ui.comboRotationDirection.currentText()
            mode = self.ui.comboCompMode.currentIndex()
            var = self.ui.editVariable.text()

            centerlon = float(self.ui.editLon.text())
            centerlat = float(self.ui.editLat.text())

            self.model.setPoint(Point(centerlon, centerlat))
            self.model.setRadius(radius)
            self.model.setDepth(depth)
            self.model.setRotationDirection(rotDir)
            self.model.setComputationMode(mode, var)
            #self.model.modelChanged.emit()
            self.model.properties.propertiesChanged.emit()
            self.model.parentMission.missionModelChanged.emit()

    @pyqtSlot()
    def uncheckSetButton(self):
        self.ui.setButton.setChecked(False)