# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pathPlannerDialog
                                 A QGIS plugin
 Tool to set waypoints on map.
                             -------------------
        begin                : 2014-04-02
        copyright            : (C) 2014 by Fraunhofer AST Ilmenau
        email                : daniel.grabolle@iosb-ast.fraunhofer.de
        modified             : 2016-11-15 btr
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

#import from qgis.PyQt
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QObject, pyqtSignal, pyqtSlot, QAbstractListModel
from qgis.PyQt import uic

#imports from qgis
from qgis.core import QgsMessageLog, Qgis

from ..model import *
from ..storage import storage_load, storage_save
from ..PlannerStateMachine import PlannerStateMachine
from ..metadata import get_plugin_metadata
from ..model.pathplannermodel2 import PathPlannerModel2

import os.path, traceback, time, io, sys

def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    meta = get_plugin_metadata()

    log_to_file = False
    separator = '-' * 80
    if log_to_file:
        logFile = "simple.log"
    notice = \
        """An unhandled exception occurred. Please report the problem\n""" \
        """using the error reporting dialog or via email to %s <%s>.\n""" % ("Ganzorig Baatar", meta["email"])
    if log_to_file:
        notice += "A log has been written to '%s'.\n\n" % (logFile)
    notice += "Error information:\n"

    versionInfo = "%s %s (%s)\n" % (meta['name'], meta['version'], meta['author'])
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")

    tbinfofile = io.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(excType), str(excValue))
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    if log_to_file:
        try:
            f = open(logFile, "w")
            f.write(msg)
            f.write(versionInfo)
            f.close()
        except IOError:
            pass
    errorbox = QMessageBox()
    errorbox.setText(str(versionInfo) + "\n" + str(notice) + str(msg))
    errorbox.exec_()

# install the hook globally
sys.excepthook = excepthook

from .MissionWidget import MissionWidget
from .TaskWidget import TaskWidget

class MainWidget(QWidget):
    # Signals
    missionSave = pyqtSignal()
    missionLoad = pyqtSignal()

    def __init__(self, canvas, clickTool, model=PathPlannerModel2()):
        try:
            QWidget.__init__(self)
            self.model = model
            self.canvas = canvas
            self.clickTool = clickTool
            self.selectedTask = -1

            # initialize plugin directory
            self.plugin_dir = os.path.dirname(__file__)
            path = os.path.dirname(os.path.abspath(__file__))
            self.ui = uic.loadUi(os.path.join(path, "PathPlanner.ui"), self)
            self.stateMachine = PlannerStateMachine(self.clickTool, self.canvas)
            self.missionWidget = MissionWidget(self, self.stateMachine)
            self.taskWidget = TaskWidget(self, self.canvas, self.clickTool, self.stateMachine)

            self.missionLoad.connect(self.on_load_mission)
            self.initGui()
        except:
            QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)

    def initGui(self):
        layout = self.ui.layout()
        if layout:
            layout.addWidget(self.missionWidget)
            # layout.addWidget(self.taskWidget)
            # splitter = QSplitter(Qt.Horizontal, self)
            # splitter.addWidget(self.missionWidget)
            # splitter.addWidget(self.missionWidget)
            # layout.addWidget(splitter)
        self.missionWidget.setTaskWidget(self.taskWidget)

        # connect signals and slots
        self.ui.buttonNewMission.clicked.connect(self.on_button_NewMission)
        self.ui.buttonSave.clicked.connect(self.on_button_SaveMission)
        self.ui.buttonLoad.clicked.connect(self.on_button_LoadMission)

        self.missionWidget.taskSelectedIndex.connect(self.on_task_selected)

    def getSelectedTask(self):
        return self.selectedTask

    @pyqtSlot(int)
    def on_mission_selected(self, value):
        if value >= 0:
            mission = self.model.getMission(value)
            if mission:
                self.missionWidget.setMission(mission)
            else:
                self.missionWidget.setMission(None)

            self.model.modelChanged.emit(self.model)
            self.model.modelReset.emit()
            mission.missionModelChanged.emit()

        else:
            self.missionWidget.setMission(None)
            self.taskWidget.setModel(None)

    @pyqtSlot(int)
    def on_task_selected(self, value):
        if self.selectedTask != value and value >= 0:
            self.selectedTask = value
            missionIdx = 0 #self.ui.missionList.currentIndex()
            if value >= 0 and missionIdx >= 0:
                mission = self.model.getMission(missionIdx)
                task = mission.getTask(value)

                if task:
                    num = task.numPoints()
                else:
                    QgsMessageLog.logMessage("No Task was selected", tag="Pathplanner", level=Qgis.Warning)
                    pass
                self.taskWidget.setModel(task)

                task.modelChanged.emit()
                mission.missionModelChanged.emit()
            else:
                self.taskWidget.setModel(None)
        elif self.selectedTask == value:
           pass
        elif value == -1:
            self.taskWidget.removeTab()
        else:
            QgsMessageLog.logMessage("on_task_selected: invalid value", tag="Pathplanner", level=Qgis.Info)

    @pyqtSlot()
    def on_button_NewMission(self):
        try:
            QgsMessageLog.logMessage("Removing mission data...", tag="Pathplanner", level=Qgis.Info)
            # remove old mission
            self.model.removeMission(0)
            self.on_mission_selected(-1)
            # Add new mission
            QgsMessageLog.logMessage("Creating empty mission...", tag="Pathplanner", level=Qgis.Info)
            idx = self.model.addMission(Mission())
            mission = self.model.getMission(idx)
            mission.setName(mission.getMissionID() + "-" + str(idx+1))
            self.on_mission_selected(0)
            QgsMessageLog.logMessage("Mission %s created" % mission.getName(), tag="Pathplanner", level=Qgis.Info)
        except:
            QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)

    @pyqtSlot()
    def on_button_RemoveMission(self):
        index = self.ui.missionList.currentIndex()
        if self.model and not index == -1:
            self.model.removeMission(index)

            count = self.ui.missionList.model().rowCount()
            if index < count:
                self.ui.missionList.setCurrentIndex(index)
            elif index == count and index > 0:
                self.ui.missionList.setCurrentIndex(index - 1)
            else:
                self.ui.missionList.setCurrentIndex(-1)

    @pyqtSlot()
    def on_button_LoadMission(self):
        try:
            #fileStorage = XmlFileStorage(self.model)
            #fileName = fileStorage.load()
            # remove old mission
            if self.model:
                self.model.removeMission(0)
                self.on_mission_selected(-1)
            fileName = storage_load(self.model)
            if fileName:
                self.missionLoad.emit()
                self.on_mission_selected(0)
        except:
            QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)

    @pyqtSlot()
    def on_button_SaveMission(self):
        fileName = storage_save(self.model)
        if fileName:
            self.missionSave.emit()

    @pyqtSlot()
    def on_load_mission(self):
        self.model.mission.xmlLoading = 1
