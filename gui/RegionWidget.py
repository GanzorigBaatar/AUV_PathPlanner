# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt import uic

from qgis.core import QgsMessageLog, Qgis
import os

from ..model import Region
from ..PlannerStateMachine import PlannerState

class RegionWidget(QWidget):
    def __init__(self, parent, stateMachine):
        QWidget.__init__(self)
        path = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(path, "RegionsPointTable.ui"), self)
        self.model = None  # Region()
        self.stateMachine = stateMachine

        self.ui.buttonAddRegionPoint.toggled.connect(self.on_button_addRegionPoint)
        self.ui.buttonMoveRegionPoint.toggled.connect(self.on_button_moveRegionPoint)
        self.ui.buttonDeleteRegionPoint.clicked.connect(self.on_button_deleteRegionPoint)

    def setModel(self, model):
        if isinstance(model, Region):
            self.model = model
            self.ui.pointTable.setModel(model)
        else:
            self.model = None
            #self.ui.scrollArea.takeWidget() # Todo

    def getModel(self):
        return self.model

    @pyqtSlot(bool)
    def on_button_addRegionPoint(self, checked):
        if checked:
            self.stateMachine.setRegion(self.model)
            self.stateMachine.switchState(PlannerState.AREAADDPOINT, self.model)
            self.stateMachine.leaveState.connect(self.uncheckAddRegionPointButton)
        else:
            self.stateMachine.switchState(PlannerState.IDLE)
            try:
                self.stateMachine.leaveState.disconnect()
            except:
                QgsMessageLog.logMessage("leaveState: was not connected", tag="Pathplanner", level=Qgis.Warning)

    @pyqtSlot(bool)
    def on_button_moveRegionPoint(self, checked):
        index = self.ui.pointTable.currentIndex().row()
        if index != -1:
            if checked:
                self.stateMachine.setRegion(self.model)
                self.stateMachine.setIndex(index)
                self.stateMachine.switchState(PlannerState.AREAMOVEPOINT, self.model)
                self.stateMachine.leaveState.connect(self.uncheckMoveRegionPointButton)
            else:
                self.stateMachine.switchState(PlannerState.IDLE)
                try:
                    self.stateMachine.leaveState.disconnect()
                except:
                    QgsMessageLog.logMessage("leaveState: was not connected", tag="Pathplanner", level=Qgis.Warning)
        else:
            self.uncheckMoveRegionPointButton()

    @pyqtSlot()
    def on_button_deleteRegionPoint(self):
        self.stateMachine.switchState(PlannerState.IDLE)
        index = self.ui.pointTable.currentIndex().row()
        if index != -1:
            self.model.removePointAt(index)

    @pyqtSlot()
    def uncheckAddRegionPointButton(self):
        self.ui.buttonAddRegionPoint.setChecked(False)

    @pyqtSlot()
    def uncheckMoveRegionPointButton(self):
        self.ui.buttonMoveRegionPoint.setChecked(False)

