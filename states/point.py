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

# imports from PyQt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtCore import QObject, QModelIndex
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.QtCore import QEvent
# imports from qgis
from qgis.gui import QgsRubberBand, QgsMapTool
from qgis.core import QgsCoordinateReferenceSystem, Qgis
from qgis.core import QgsPoint, QgsCoordinateTransform, QgsMessageLog, QgsProject, QgsPointXY
from qgis.core import QgsDistanceArea
from qgis.core import QgsProject
# imports from pathplanner
from ..model.point import Point


import math, sys, inspect

class PointADD(QObject):
    # states
    NODASHLINE = 0
    DASHLINE = 1
    # signals
    leave = pyqtSignal()

    def __init__(self, model, clickTool, canvas):
        QObject.__init__(self)
        self.clickTool = clickTool
        self.canvas = canvas
        self.dashRubberBand = QgsRubberBand(canvas)
        self.dashRubberBand.setColor(QColor(0, 200, 0))
        self.dashRubberBand.setLineStyle(Qt.DashLine)

        self.lastPoint = QgsPointXY(0, 0)
        self.model = model
        if model.getLastWayPoint():
            self.state = self.DASHLINE
        else:
            self.state = self.NODASHLINE

    def start(self):
        self.canvas.setMapTool(self.clickTool)
        self.clickTool.canvasClicked.connect(self.addWaypointClick)

        #QObject.connect(self.clickTool, SIGNAL("canvasClicked"), self.addWaypointClick)
        if self.state == self.DASHLINE:
            self.clickTool.mouseMoved.connect(self.drawDashLine)
            #QObject.connect(self.clickTool, SIGNAL("mouseMoved"), self.drawDashLine)
            self.setLastPoint()

    def stop(self):
        if self.state == self.DASHLINE:
            try:
                self.clickTool.mouseMoved.disconnect()
            except:
                #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass
            self.dashRubberBand.reset()

        try:
            self.clickTool.canvasClicked.disconnect()
        except:
            #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)
            pass

        #QObject.disconnect(self.clickTool, SIGNAL("canvasClicked"), self.addWaypointClick)
        self.canvas.unsetMapTool(self.clickTool)
        self.canvas.scene().removeItem(self.dashRubberBand)
        self.leave.emit()

    def switchState(self, newState):
        if self.state == newState:
            return
        elif self.state == self.DASHLINE and newState == self.NODASHLINE:
            try:
                self.clickTool.mouseMoved.disconnect()
            except:
                #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass
            self.dashRubberBand.reset()
        elif self.state == self.NODASHLINE and newState == self.DASHLINE:
            self.clickTool.mouseMoved.connect(self.drawDashLine)
            #QObject.connect(self.clickTool, SIGNAL("mouseMoved"), self.drawDashLine)
            self.setLastPoint()
        self.state = newState

    def setLastPoint(self):
        if self.model.numPoints() > 0:
            point = self.model.getLastWayPoint()
            mission = self.model.getParentMission()
            if mission:
                missionCRS = mission.getCRS()
            else:
                return
            try:
                mapCRS = self.canvas.mapSettings().destinationCrs()
                if mapCRS is None:
                    mapCRS = self.canvas.mapRenderer().destinationCrs()
            except:
                mapCRS = self.canvas.mapRenderer().destinationCrs()

            xform = QgsCoordinateTransform(missionCRS, mapCRS, QgsProject.instance())
            lastPointQgs = QgsPointXY(point.getX(), point.getY())
            self.lastPoint = xform.transform(lastPointQgs.x(), lastPointQgs.y(), QgsCoordinateTransform.ForwardTransform)

    #@pyqtSlot(QgsPoint, Qt.MouseButtons)
    @pyqtSlot(QgsPointXY, Qt.MouseButton)
    def addWaypointClick(self, point, button):  # (QgsPoint, Qt.MouseButton)
        if button == Qt.LeftButton:
            self.addWaypoint(point)
            if self.state == self.NODASHLINE:
                self.switchState(self.DASHLINE)
        elif button == Qt.RightButton:
            self.stop()

    def addWaypoint(self, qgisPoint):
        mission = self.model.getParentMission()

        if mission:
            missionCRS = mission.getCRS()
        else:
            return
        try:
            mapCRS = self.canvas.mapSettings().destinationCrs()
            if mapCRS is None:
                mapCRS = self.canvas.mapRenderer().destinationCrs()
        except:
            mapCRS = self.canvas.mapRenderer().destinationCrs()

        xform = QgsCoordinateTransform(mapCRS, missionCRS, QgsProject.instance())

        #transformedPoint = xform.transform(qgisPoint)
        #transformedPoint = Point(transformedPoint.x(), transformedPoint.y())
        #transformedX, transformedY = xform.transform(qgisPoint, QgsCoordinateTransform.ForwardTransform)
        transformedX, transformedY = xform.transform(qgisPoint.x(), qgisPoint.y(),  QgsCoordinateTransform.ForwardTransform)
        transformedPoint = Point(transformedX, transformedY)

        self.model.addPoint(transformedPoint)
        self.setLastPoint()

    @pyqtSlot(QgsPointXY)
    def drawDashLine(self, point):
        self.dashRubberBand.reset()
        self.dashRubberBand.addPoint(QgsPointXY(self.lastPoint))
        self.dashRubberBand.addPoint(QgsPointXY(point))

class PointSET(QObject):
    # signals
    leave = pyqtSignal()

    def __init__(self, model, clickTool, canvas):
        QObject.__init__(self)
        self.clickTool = clickTool
        self.canvas = canvas
        self.model = model

    def start(self):
        self.canvas.setMapTool(self.clickTool)
        self.clickTool.canvasClicked.connect(self.setPointClick)
        #QObject.connect(self.clickTool, SIGNAL("canvasClicked"), self.setPointClick)

    def stop(self):
        try:
            self.clickTool.canvasClicked.disconnect()
        except:
            #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)
            pass
        self.canvas.unsetMapTool(self.clickTool)
        self.leave.emit()

    @pyqtSlot(QgsPointXY, Qt.MouseButton)
    def setPointClick(self, point, button):  # (QgsPoint, Qt.MouseButton)
        if button == Qt.LeftButton:
            self.setPoint(point)
            self.stop()

    def setPoint(self, qgisPoint):
        mission = self.model.getParentMission()
        if mission:
            missionCRS = mission.getCRS()
        else:
            return
        try:
            mapCRS = self.canvas.mapSettings().destinationCrs()
            if mapCRS is None:
                mapCRS = self.canvas.mapRenderer().destinationCrs()
        except:
            mapCRS = self.canvas.mapRenderer().destinationCrs()
        xform = QgsCoordinateTransform(mapCRS, missionCRS, QgsProject.instance())

        #transformedPoint = xform.transform(qgisPoint)
        #transformedPoint = Point(transformedPoint.x(), transformedPoint.y())

        transformedX, transformedY = xform.transform(qgisPoint, QgsCoordinateTransform.ForwardTransform)
        transformedPoint = Point(transformedX, transformedY)
        self.model.setPoint(transformedPoint)


class PointMOVE(QObject):
    # states:
    ONEPOINT = 0
    FIRSTPOINT = 1
    LASTPOINT = 2
    MIDDLEPOINT = 3
    # signals
    leave = pyqtSignal()

    def __init__(self, model, clickTool, canvas, index):
        QObject.__init__(self)
        self.clickTool = clickTool
        self.canvas = canvas
        self.model = model

        self.dashRubberBand = QgsRubberBand(canvas)
        self.dashRubberBand.setColor(QColor(0, 200, 0))
        self.dashRubberBand.setLineStyle(Qt.DashLine)
        self.index = index

        count = model.countPoints()
        self.state = None
        if index == 0:
            if count == 1:
                self.state = self.ONEPOINT
            elif count > 1:
                self.state = self.FIRSTPOINT
        elif index > 0:
            if index < count - 1:
                self.state = self.MIDDLEPOINT
            elif index == count - 1:
                self.state = self.LASTPOINT

    def start(self):
        self.canvas.setMapTool(self.clickTool)
        self.setRubberBandPoints()
        self.clickTool.mouseMoved.connect(self.moveTempPoint)
        self.clickTool.canvasClicked.connect(self.moveClick)

        #QObject.connect(self.clickTool, SIGNAL("mouseMoved"), self.moveTempPoint)
        #QObject.connect(self.clickTool, SIGNAL("canvasClicked"), self.moveClick)

    def stop(self):
        try:
            self.clickTool.mouseMoved.disconnect()
        except:
            #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)
            pass
        try:
            self.clickTool.canvasClicked.disconnect()
        except:
            pass
            #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)

        self.dashRubberBand.reset()
        self.canvas.unsetMapTool(self.clickTool)
        self.canvas.scene().removeItem(self.dashRubberBand)
        self.leave.emit()

    def setRubberBandPoints(self):
        # init coordinate transformation
        mission = self.model.getParentMission()
        if mission:
            missionCRS = mission.getCRS()
        else:
            return
        try:
            mapCRS = self.canvas.mapSettings().destinationCrs()
            if mapCRS is None:
                mapCRS = self.canvas.mapRenderer().destinationCrs()
        except:
            mapCRS = self.canvas.mapRenderer().destinationCrs()

        xform = QgsCoordinateTransform(missionCRS, mapCRS, QgsProject.instance())

        # set points
        if self.state == self.ONEPOINT or self.state == self.FIRSTPOINT:
            point = self.model.getPointAt(0)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(QgsPointXY(transformedPoint))

            if self.state == self.FIRSTPOINT:
                point = self.model.getPointAt(1)
                transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
                self.dashRubberBand.addPoint(QgsPointXY(transformedPoint))

        elif self.state == self.LASTPOINT:
            point = self.model.getPointAt(self.index - 1)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(QgsPointXY(transformedPoint))

            point = self.model.getPointAt(self.index)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(QgsPointXY(transformedPoint))
        elif self.state == self.MIDDLEPOINT:
            point = self.model.getPointAt(self.index - 1)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(QgsPointXY(transformedPoint))

            point = self.model.getPointAt(self.index)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(QgsPointXY(transformedPoint))

            point = self.model.getPointAt(self.index + 1)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(QgsPointXY(transformedPoint))

    def moveTempPoint(self, point):
        if self.state == self.ONEPOINT or self.state == self.FIRSTPOINT:
            rbIndex = 0
        elif self.state == self.MIDDLEPOINT or self.state == self.LASTPOINT:
            rbIndex = 1
        self.dashRubberBand.movePoint(rbIndex, point)

    @pyqtSlot(QgsPointXY, Qt.MouseButton)
    def moveClick(self, qgisPoint, button):
        if button == Qt.LeftButton:
            self.dashRubberBand.reset()
            point = Point(qgisPoint.x(), qgisPoint.y())

            # init coordinate transformation
            mission = self.model.getParentMission()
            if mission:
                missionCRS = mission.getCRS()
            else:
                pass
            try:
                mapCRS = self.canvas.mapSettings().destinationCrs()
                if mapCRS is None:
                    mapCRS = self.canvas.mapRenderer().destinationCrs()
            except:
                mapCRS = self.canvas.mapRenderer().destinationCrs()
            xform = QgsCoordinateTransform(mapCRS, missionCRS, QgsProject.instance())

            # get depth of moved point
            oldPoint = self.model.getPointAt(self.index)
            depth = oldPoint.getDepth()

            # transform point
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            transformedPoint = Point(transformedPoint.x(), transformedPoint.y(), depth)

            # give data to model
            self.model.removePointAt(self.index)
            self.model.addPoint(transformedPoint, self.index)
        self.stop()
