# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtWidgets import QWidget, QAbstractButton
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QIntValidator, QDoubleValidator

from qgis.core import QgsMessageLog, Qgis
import os

from ..model import Task
from ..PlannerStateMachine import PlannerState

class SurveyPropertyWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(self.path, "SurveyProperties.ui"), self)
        self.model = None
        self.setEditValidator()

    def breakConnection(self):
        if self.model is not None:
            try:
                self.model.surveyModelChanged.disconnect()
            except:
                pass

    def setModel(self, task):
        if isinstance(task, Task):
            self.model = task
            self.model.surveyModelChanged.connect(self.updateView)
            self.updateView()
            self.model.parentMission.missionModelChanged.emit()
            self.setConnections()
        else:
            pass

    def submit(self):
        if self.model.type() == 'survey':
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
                depthIfHeightInv = self.ui.editDepthIfHeightInvalid.text()
                lookAheadDistance = self.ui.editLookAheadDistance.text()
                constantDepth = self.ui.editConstantDepth.text()
                self.model.setDepth(float(constantDepth))

                heightOverGround = self.ui.editHeightOverGround.text()
                heightIterations = self.ui.editHeightIterations.text()
                surveyType = self.ui.comboSurveyType.currentText()
                startPosition = self.ui.comboStartPosition.currentText()

                swath = self.ui.editSwath.text()
                oddLineSpacingFactor = self.ui.editOddLineSpacingFactor.text()
                ssrange = self.ui.editSideScanRange.text()
                nadirgap = self.ui.editNadirGap.text()
                distfactor = self.ui.editDistanceFactor.text()

                if surveyType == 'UnevenMeander':
                    x = float(ssrange) - float(nadirgap)
                    y = float(distfactor) * float(ssrange)
                    swath = (x + y)/2
                    oddLineSpacingFactor = x/swath
                else:
                    try:
                        olsf = float(oddLineSpacingFactor)
                    except:
                        olsf = 1.0

                    #if float(oddLineSpacingFactor) - 1.0 == 0:
                    if (olsf - 1.0) == 0:
                        pass
                    else:
                        QgsMessageLog.logMessage("Meander oddLineSpacingFactor value was changed: %f. Setting the value to 1" % (float(oddLineSpacingFactor)), tag="Pathplanner", level=Qgis.Info)
                        QMessageBox.information(None, "Value Changed","'oddLineSpacingFactor' value was changed! Setting the value to 1.\n 'Swath' value was changed. Please check plausibility. ")
                        oddLineSpacingFactor = 1

                angle = self.ui.spinBoxAngle.cleanText()
                eastWestExtent = self.ui.editEastWestExtent.text()
                northSouthExtent = self.ui.editNorthSouthExtent.text()

                try:
                    df = float(distfactor)
                except:
                    df = 1.5

                if df > 2:
                    QgsMessageLog.logMessage("DistanceFactor can not be more than 2. Side Scan Overlap is not possible.", tag="Pathplanner", level=Qgis.Warning)
                    distfactor = 2
                elif df < 1:
                    QgsMessageLog.logMessage(
                        "DistanceFactor can not be smaller than 1. Side Scan Overlap override.", tag="Pathplanner",
                        level=Qgis.Info)
                    distfactor = 1

                try:
                    ssr = float(ssrange)
                except:
                    ssr = 20

                try:
                    ndg = float(nadirgap)
                except:
                    ndg = 5

                if ssr/ndg < 2.0:
                    QgsMessageLog.logMessage(
                        "NadirGap is too high in comparison to SideScanRange. Consider using 'Meander' Survey with calculated swath.", tag="Pathplanner",
                        level=Qgis.Info)
                    swath = ssr - (ssr - ndg)
                    oddLineSpacingFactor = 1

                properties.setTimeout(timeout)
                properties.setPriority(priority)
                properties.setSpeed(speed)
                properties.setTrackControllerMode(trackControllerMode)
                properties.setDepthControllerMode(depthControllerMode)
                properties.setArrivalRadius(arrivalRadius)
                properties.setDistToLOS(distToLOS)
                properties.setDepthHeightInvalid(depthIfHeightInv)
                properties.setLookAheadDistance(lookAheadDistance)
                properties.setConstantDepth(constantDepth)
                properties.setHeightOverGround(heightOverGround)
                properties.setHeightIterations(heightIterations)
                properties.setSurveyType(surveyType)
                properties.setStartPosition(startPosition)
                properties.setSwath(swath)
                properties.setOddLineSpacingFactor(oddLineSpacingFactor)
                properties.setSideScanRange(ssrange)
                properties.setNadirGap(nadirgap)
                properties.setDistanceFactor(distfactor)
                properties.setRotationAngle(angle)
                properties.setEastWestExtent(eastWestExtent)
                properties.setNorthSouthExtent(northSouthExtent)
                self.model.changeRect(float(eastWestExtent), float(northSouthExtent))
                properties.propertiesChanged.emit()
                self.model.surveyModelChanged.emit()

                #self.model.parentMission.missionModelChanged.emit()
                #properties.setTrackControllerValue(trackControllerValue)
                #properties.meanderChanged.emit()

    @pyqtSlot()
    def updateView(self):

        if self.model is not None:
            prop = self.model.getProperties()
            dist = float(prop.getDistance())
            self.ui.editDistance.setText("%.2f" %(dist))
            self.ui.editSpeed.setText(str(prop.getSpeed()))
            self.ui.editTime.setText(str(prop.getTime()))
            self.ui.editTimeout.setText(str(prop.getTimeout()))
            self.ui.spinBoxPriority.setValue(int(prop.getPriority()))
            self.ui.editArrivalRadius.setText(str(prop.getArrivalRadius()))
            self.ui.editLookAheadDistance.setText(str(prop.getLookAheadDistance()))
            self.ui.editDistToLOS.setText(str(prop.getDistToLOS()))
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

            surveyType = prop.getSurveyType()

            if surveyType == 'Meander':
                self.ui.comboSurveyType.setCurrentIndex(0)
                self.ui.editSwath.setDisabled(False)
                self.ui.editOddLineSpacingFactor.setDisabled(False)
                self.ui.editSideScanRange.setDisabled(True)
                self.ui.editNadirGap.setDisabled(True)
                self.ui.editDistanceFactor.setDisabled(True)
            elif surveyType == 'UnevenMeander':
                self.ui.comboSurveyType.setCurrentIndex(1)
                self.ui.editSwath.setDisabled(True)
                self.ui.editOddLineSpacingFactor.setDisabled(True)
                self.ui.editSideScanRange.setDisabled(False)
                self.ui.editNadirGap.setDisabled(False)
                self.ui.editDistanceFactor.setDisabled(False)
            elif surveyType == 'BufferedMeander':
                self.ui.comboSurveyType.setCurrentIndex(2)
                self.ui.editSwath.setDisabled(False)
                self.ui.editOddLineSpacingFactor.setDisabled(False)
                self.ui.editSideScanRange.setDisabled(True)
                self.ui.editNadirGap.setDisabled(True)
                self.ui.editDistanceFactor.setDisabled(True)
            elif surveyType == 'Idle':
                self.ui.comboSurveyType.setCurrentIndex(3)

            startPos = prop.getStartPosition()

            if startPos == 'NorthEast':
                self.ui.comboStartPosition.setCurrentIndex(0)
            elif startPos == 'NorthWest':
                self.ui.comboStartPosition.setCurrentIndex(1)
            elif startPos == 'SouthEast':
                self.ui.comboStartPosition.setCurrentIndex(2)
            elif startPos == 'SouthWest':
                self.ui.comboStartPosition.setCurrentIndex(3)
            self.ui.spinBoxAngle.setValue(int(prop.getRotationAngle()))
            self.ui.editEastWestExtent.setText(str(prop.getEastWestExtent()))
            self.ui.editNorthSouthExtent.setText(str(prop.getNorthSouthExtent()))
            self.ui.editSwath.setText(str(prop.getSwath()))
            self.ui.editOddLineSpacingFactor.setText(str(prop.getOddLineSpacingFactor()))
            self.ui.editSideScanRange.setText(str(prop.getSideScanRange()))
            self.ui.editNadirGap.setText(str(prop.getNadirGap()))
            self.ui.editDistanceFactor.setText(str(prop.getDistanceFactor()))
            self.model.parentMission.missionModelChanged.emit()

    def setConnections(self):
        # create connections
        self.ui.editSpeed.editingFinished.connect(self.submit)
        self.ui.editSwath.editingFinished.connect(self.submit)
        self.ui.comboSurveyType.currentIndexChanged.connect(self.submit)
        self.ui.editOddLineSpacingFactor.editingFinished.connect(self.submit)
        self.ui.editSideScanRange.editingFinished.connect(self.submit)
        self.ui.editNadirGap.editingFinished.connect(self.submit)
        self.ui.editDistanceFactor.editingFinished.connect(self.submit)
        self.ui.editSideScanRange.editingFinished.connect(self.submit)
        self.ui.comboStartPosition.currentIndexChanged.connect(self.submit)
        self.ui.editEastWestExtent.editingFinished.connect(self.submit)
        self.ui.editNorthSouthExtent.editingFinished.connect(self.submit)
        self.ui.spinBoxAngle.editingFinished.connect(self.submit)
        # spinBoxAngle valueChanged was left not connected intentionally
        self.ui.editArrivalRadius.editingFinished.connect(self.submit)
        self.ui.editLookAheadDistance.editingFinished.connect(self.submit)
        self.ui.editDistToLOS.editingFinished.connect(self.submit)
        self.ui.comboTrackControllerMode.currentIndexChanged.connect(self.submit)
        self.ui.comboDepthControllerMode.currentIndexChanged.connect(self.submit)
        self.ui.editDepthIfHeightInvalid.editingFinished.connect(self.submit)
        self.ui.editHeightIterations.editingFinished.connect(self.submit)
        self.ui.editHeightOverGround.editingFinished.connect(self.submit)
        self.ui.editConstantDepth.editingFinished.connect(self.submit)

    def setEditValidator(self):
        # use validator to allow only numbers for edit fields
        dbl_vld = QDoubleValidator()

        self.ui.editSpeed.setValidator(dbl_vld)
        self.ui.editSwath.setValidator(dbl_vld)
        self.ui.editOddLineSpacingFactor.setValidator(dbl_vld)
        self.ui.editSideScanRange.setValidator(dbl_vld)
        self.ui.editNadirGap.setValidator(dbl_vld)
        self.ui.editDistanceFactor.setValidator(dbl_vld)
        self.ui.editSideScanRange.setValidator(dbl_vld)
        self.ui.editEastWestExtent.setValidator(dbl_vld)
        self.ui.editNorthSouthExtent.setValidator(dbl_vld)
        self.ui.editArrivalRadius.setValidator(dbl_vld)
        self.ui.editLookAheadDistance.setValidator(dbl_vld)
        self.ui.editDistToLOS.setValidator(dbl_vld)
        self.ui.editDepthIfHeightInvalid.setValidator(dbl_vld)
        self.ui.editHeightIterations.setValidator(dbl_vld)
        self.ui.editHeightOverGround.setValidator(dbl_vld)
        self.ui.editConstantDepth.setValidator(dbl_vld)

class SurveyWidget(QWidget):

    def __init__(self, parent, stateMachine):
        QWidget.__init__(self, parent)
        path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(path, "SurveyWidget.ui"), self)
        self.ui.buttonDrawRect.toggled.connect(self.drawRect)
        self.ui.buttonRotation.toggled.connect(self.rotate)
        self.ui.buttonMoveRect.toggled.connect(self.moveRect)
        self.ui.buttonDelete.clicked.connect(self.delete)
        self.ui.buttonSurveySubmit.clicked.connect(self.submitButtonClicked)

        self.ui.editCenterLon.editingFinished.connect(self.submitButtonClicked)
        self.ui.editCenterLat.editingFinished.connect(self.submitButtonClicked)
        self.ui.editCenterDepth.editingFinished.connect(self.submitButtonClicked)
        self.ui.editRotation.editingFinished.connect(self.submitButtonClicked)
        self.ui.editHeight.editingFinished.connect(self.submitButtonClicked)
        self.ui.editLength.editingFinished.connect(self.submitButtonClicked)
        self.ui.checkAddBufferArea.stateChanged.connect(self.bufferAreaChecked)

        dbl_vld = QDoubleValidator()

        self.ui.editCenterLon.setValidator(dbl_vld)
        self.ui.editCenterLat.setValidator(dbl_vld)
        self.ui.editCenterDepth.setValidator(dbl_vld)
        self.ui.editRotation.setValidator(dbl_vld)
        self.ui.editHeight.setValidator(dbl_vld)
        self.ui.editLength.setValidator(dbl_vld)

        self.stateMachine = stateMachine
        self.model = None
        #self.updateView()
        self.firstLoad = 1

    def setModel(self, task):
        if self.model is not None:
            try:
                self.model.surveyModelChanged.disconnect()
            except:
                pass
        if isinstance(task, Task):
            self.model = task
            self.model.surveyModelChanged.connect(self.modelChangedSlot)
            self.eraseView()
            prop = self.model.getProperties()
            stype = prop.getSurveyType()

            if stype == "BufferedMeander":
                self.ui.checkAddBufferArea.setChecked(True)
            else:
                self.ui.checkAddBufferArea.setChecked(False)
        else:
            self.eraseView()
            self.model = None

        self.updateView()

    def eraseView(self):
        if self.model and self.model .type() == 'survey':
            self.ui.editCenterLon.setText("")
            self.ui.editCenterLat.setText("")
            self.ui.editCenterDepth.setText("")
            self.ui.editRotation.setText("")
            self.ui.editHeight.setText("")
            self.ui.editLength.setText("")
            self.ui.editEdgeULx.setText("")
            self.ui.editEdgeULy.setText("")
            self.ui.editEdgeLLx.setText("")
            self.ui.editEdgeLLy.setText("")
            self.ui.editEdgeLRx.setText("")
            self.ui.editEdgeLRy.setText("")
            self.ui.editEdgeURx.setText("")
            self.ui.editEdgeURy.setText("")

    @pyqtSlot()
    def modelChangedSlot(self):
        if self.model.getTaskType() == 'survey':
            if not self.model.isEmpty():
                ul = self.model.getUL()
                ll = self.model.getLL()
                ur = self.model.getUR()
                lr = self.model.getLR()
                center = self.model.getCenterPoint()
                #center = self.model.centerPoint
                prop = self.model.getProperties()
                angle = prop.getRotationAngle()
                width = prop.getEastWestExtent()
                height = prop.getNorthSouthExtent()
                stype = prop.getSurveyType()

                if (stype == 'BufferedMeander'):
                    self.ui.checkAddBufferArea.blockSignals(True)
                    self.ui.checkAddBufferArea.setChecked(True)
                    self.ui.checkAddBufferArea.blockSignals(False)

                self.ui.editCenterLon.setText(str(center.getX()))
                self.ui.editCenterLat.setText(str(center.getY()))
                #self.ui.editCenterDepth.setText(str(center.getDepth()))
                self.ui.editCenterDepth.setText(str(prop.getConstantDepth()))
                #print("depth in modelChangedSlot:", center.getDepth())
                self.ui.editRotation.setText(str(angle))
                self.ui.editHeight.setText(str(height))
                self.ui.editLength.setText(str(width))
                self.ui.editEdgeULx.setText(str(ul.getX()))
                self.ui.editEdgeULy.setText(str(ul.getY()))
                self.ui.editEdgeLLx.setText(str(ll.getX()))
                self.ui.editEdgeLLy.setText(str(ll.getY()))
                self.ui.editEdgeLRx.setText(str(lr.getX()))
                self.ui.editEdgeLRy.setText(str(lr.getY()))
                self.ui.editEdgeURx.setText(str(ur.getX()))
                self.ui.editEdgeURy.setText(str(ur.getY()))
            self.model.parentMission.missionModelChanged.emit()

    def getModel(self):
        return self.model

    @pyqtSlot()
    def updateView(self):
        if self.model is not None:
            prop = self.model.getProperties()
            prop.propertiesChanged.emit()

            if (self.model.firstLoad == False):
                self.submitButtonClicked()

            #self.model.parentMission.xmlLoading = 0
            #self.model.parentMission.missionModelChanged.emit()
        else:
            pass

    @pyqtSlot()
    def submitButtonClicked(self):
        if self.model.type() == 'survey':
            centerlon = self.ui.editCenterLon.text()
            centerlat = self.ui.editCenterLat.text()
            anglestr = self.ui.editRotation.text()
            nsestr = self.ui.editHeight.text()
            ewestr = self.ui.editLength.text()
            depthstr = self.ui.editCenterDepth.text()

            prop = self.model.getProperties()
            try:
                lon = float(centerlon)
                lat = float(centerlat)
            except:
                point = self.model.getCenterPoint()
                lon = point.getX()
                lat = point.getY()

            try:
                angle = float(anglestr)
            except:
                prop = self.model.getProperties()
                anglestr = prop.getRotationAngle()
                angle = float(anglestr)

            try:
                nse=float(nsestr)
            except:
                nsestr = prop.getNorthSouthExtent()
                nse = float(nsestr)
            try:
                ewe=float(ewestr)
            except:
                ewestr = prop.getEastWestExtent()
                ewe = float(ewestr)

            try:
                depth=float(depthstr)
            except:
                depthstr = self.model.properties.getConstantDepth()
                depth = float(depthstr)

            self.model.moveCenterPoint(lon, lat)
            self.model.moveRect(self.model.centerPoint)
            self.model.changeRect(ewe, nse)
            self.model.setAngle(angle)
            self.model.properties.setConstantDepth(depth)

            #self.model.surveyModelChanged.emit()
            #self.model.properties.propertiesChanged.emit()
            ##self.model.parentMission.missionModelChanged.emit()

    @pyqtSlot()
    def uncheckDrawRectButton(self):
        if self.model.type() == 'survey':
            self.ui.buttonDrawRect.setChecked(False)

    @pyqtSlot(bool)
    def drawRect(self, checked):
        if self.model.type() == 'survey':
            if checked:
                self.stateMachine.switchState(PlannerState.SURVEYADDRECT, self.model)
                self.stateMachine.leaveState.connect(self.uncheckDrawRectButton)
            else:
                self.stateMachine.switchState(PlannerState.IDLE)
                self.stateMachine.leaveState.disconnect()

    @pyqtSlot()
    def uncheckRotateButton(self):
        if self.model.type() == 'survey':
            self.ui.buttonRotation.setChecked(False)

    @pyqtSlot(bool)
    def rotate(self, checked):
        if self.model.isEmpty():
            self.ui.buttonRotation.setChecked(False)
            return
        if checked:
            self.stateMachine.switchState(PlannerState.SURVEYROTATE, self.model)
            self.stateMachine.leaveState.connect(self.uncheckRotateButton)
        else:
            self.stateMachine.switchState(PlannerState.IDLE)
            self.stateMachine.leaveState.disconnect()

    @pyqtSlot()
    def delete(self):
        return

    @pyqtSlot()
    def uncheckMoveButton(self):
        if self.model.type() == 'survey':
            self.ui.buttonMoveRect.setChecked(False)

    @pyqtSlot(bool)
    def moveRect(self, checked):
        if self.model.isEmpty():
            self.ui.buttonMoveRect.setChecked(False)
            return
        if checked:
            self.stateMachine.switchState(PlannerState.SURVEYMOVE, self.model)
            self.stateMachine.leaveState.connect(self.uncheckMoveButton)
        else:
            self.stateMachine.switchState(PlannerState.IDLE)
            self.stateMachine.leaveState.disconnect()

    @pyqtSlot(int)
    def bufferAreaChecked(self, state):
        if state == 0:
            # is not checked
            self.model.properties.setSurveyType('Meander')
            self.submitButtonClicked()
        elif state == 2:
            #is checked
            self.model.properties.setSurveyType('BufferedMeander')
            self.submitButtonClicked()
        pass


