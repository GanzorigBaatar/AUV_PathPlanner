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

 To check the plugin load times, use the following code in the Python console:

 import pprint
 pprint.pprint(qgis.utils.plugin_times)

 """
from __future__ import absolute_import
# Import the PyQt and QGIS libraries
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import QDockWidget, QMessageBox
from qgis.PyQt.QtCore import QObject, pyqtSignal, pyqtSlot, QEvent, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis
from qgis.gui import *
from qgis.PyQt.QtCore import QAbstractListModel
from qgis.core import QgsMessageLog

# Initialize Qt resources from file resources.py

from . import resources

from .canvasMouseTool import CanvasMouseTool

from .model.pathplannermodel2 import PathPlannerModel2
from .gui.PlannerGui import MainWidget
from .plot.ppMissionPlotter import ppMissionPlotter
from .metadata import get_plugin_metadata

class pathPlanner(QObject):

    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = iface  # reference to the QGIS interface
        self.canvas = self.iface.mapCanvas()  # reference to the map
        self.clickTool = CanvasMouseTool(self.canvas)
        # Init Model
        self.model = PathPlannerModel2()

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/:/plugins/PathPlanner_3/icons/compass.png"),
            u"Path Planner", self.iface.mainWindow())


        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # add about dialog
        self.aboutAction = QAction(QIcon(":/:/plugins/PathPlanner_3/icons/about.png"), "About",
                                   self.iface.mainWindow())
        self.aboutAction.triggered.connect(self.about)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Path Planner", self.action)
        self.iface.addPluginToMenu(u"&Path Planner", self.aboutAction)

    def unload(self):
        self.model.clean()
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&Path Planner", self.action)
        self.iface.removePluginMenu(u"&Path Planner", self.aboutAction)
        self.iface.removeToolBarIcon(self.action)

    def about(self):
        meta = get_plugin_metadata()
        QMessageBox.about(None, "%s - %s" % (meta["name"], meta["version"]), meta["description"])

    #run method that performs all the real work
    def run(self):
        self.main_widget = MainWidget(self.canvas, self.clickTool, self.model)
        # create dockwidget
        self.dockWidget = QDockWidget("Pathplanner")

        self.dockWidget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockWidget)
        self.dockWidget.setWidget(self.main_widget)
        self.closeEventFilter = CloseEventFilter(self)
        self.dockWidget.installEventFilter(self.closeEventFilter)
        self.closeEventFilter.dock_close.connect(self.on_event_close)

        self.plotter = ppMissionPlotter(self.canvas, self.main_widget)
        self.model.plotMission.connect(self.callPlotMission)
        self.main_widget.missionWidget.draw.connect(self.callPlotMission)

    @pyqtSlot()
    def on_event_close(self):
        self.model.clean()
        self.plotter.deleteFromCanvas()
        try:
            self.model.plotMission.disconnect()
            self.main_widget.missionWidget.draw.disconnect()
            self.closeEventFilter.dock_close.disconnect()
        except:
            QgsMessageLog.logMessage("on_event_close: disconnect failed", tag="Pathplanner", level=Qgis.Warning)


    @pyqtSlot(QAbstractListModel)
    def callPlotMission(self, mission):
        self.plotter.plotMission(mission)

class CloseEventFilter(QObject):
    dock_close = pyqtSignal()

    def __init__(self, parent):
        QObject.__init__(self, parent)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Close and type(source) is QDockWidget:
            self.dock_close.emit()
        return QObject.eventFilter(self, source, event)
