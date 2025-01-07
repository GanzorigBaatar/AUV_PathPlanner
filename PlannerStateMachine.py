# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pathPlanner
                                 A QGIS plugin
 Create a path of waypoints using your mouse.
                              -------------------
        begin                : 2014-03-14
        copyright            : (C) 2014 by Fraunhofer AST Ilmenau
        email                : daniel.grabolle@iosb-ast.fraunhofer.de
        modified             : 2016-12-10 btr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 """
from __future__ import absolute_import

# imports from qgis.PyQt
from builtins import object
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QWidget

from qgis.PyQt.QtCore import QModelIndex
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtCore import pyqtSlot

from .states import *

class PlannerState(object):
    IDLE = 0
    POINTADD = 1
    POINTMOVE = 2
    SURVEYADDRECT = 3
    SURVEYROTATE = 4
    AREAMOVEPOINT = 5 
    AREAADDPOINT = 6
    POINTSET = 7
    SURVEYMOVE = 8


#state machine
class PlannerStateMachine(QObject):
    #signals
    leaveState = pyqtSignal()

    def __init__(self, clickTool, canvas, model = None):
        QObject.__init__(self)
        self.currentState = None
        self.clickTool = clickTool
        self.canvas = canvas
        self.index = 0
        self.areaIndex = 0
        if model:
            self.model = model
        else:
            self.model = None

    def setModel(self, model):
        self.switchState(PlannerState.IDLE)
        self.model = model

    def setIndex(self, index):
        self.index = index

    def setRegion(self, region):
        if isinstance(region, Region):
            self.region = region

    def switchState(self, state, model=None):
        if model is not None:
            self.model = model
        if self.model:
            if self.currentState:
                self.currentState.stop()
            if state == PlannerState.POINTADD:
                if self.model.type() == 'waypoint':
                    self.currentState = PointADD(self.model, self.clickTool, self.canvas)
            elif state == PlannerState.POINTMOVE:
                if self.model.type() == 'waypoint':
                    self.currentState = PointMOVE(self.model, self.clickTool, self.canvas, self.index)
            elif state == PlannerState.SURVEYADDRECT:
                if self.model.type() == 'survey':
                    self.currentState = SurveyADDRECT(self.model, self.clickTool, self.canvas)
            elif state == PlannerState.SURVEYROTATE:
                if self.model.type() == 'survey':
                    self.currentState = SurveyROTATE(self.model, self.clickTool, self.canvas)
            elif state == PlannerState.AREAADDPOINT:
                if isinstance(self.model, Region):
                    self.currentState = AreaADDPOINT(self.region, self.clickTool, self.canvas)
            elif state == PlannerState.AREAMOVEPOINT:
                if isinstance(self.model, Region):
                    self.currentState = AreaMOVEPOINT(self.region, self.clickTool, self.canvas, self.index)
            elif state == PlannerState.POINTSET:
                if self.model.type() in ['circle', 'keepstation']:
                    self.currentState = PointSET(self.model, self.clickTool, self.canvas)
            elif state == PlannerState.SURVEYMOVE:
                if self.model.type() == 'survey':
                    self.currentState = SurveyMOVE(self.model, self.clickTool, self.canvas)
            else:
                self.currentState = PlannerState.IDLE
                return
            if self.currentState:
                self.currentState.leave.connect(self.leaveState)
                self.currentState.leave.connect(self.stateLeft)
                self.currentState.start()

    @pyqtSlot()
    def stateLeft(self):
        #self.currentState.leave.disconnect()
        self.currentState.leave.disconnect()
        self.currentState = PlannerState.IDLE
