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

# imports from qgis.PyQt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtCore import pyqtSlot
# imports from qgis
from qgis.gui import QgsRubberBand, QgsMapTool
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsPoint, QgsCoordinateTransform, QgsMessageLog, QgsProject, QgsPointXY
from qgis.core import QgsDistanceArea
from qgis.core import QgsProject, Qgis
# imports from pathplanner
from ..model import Point, Region

import math


# state classes
class AreaADDPOINT(QObject):
    # states
    NODASHLINE = 0
    DASHLINEONEPOINT = 1
    DASHLINEPOLYGON = 2
    # signals
    leave = pyqtSignal()

    def __init__(self, region, clickTool, canvas):
        QObject.__init__(self)
        self.clickTool = clickTool
        self.dashRubberBand = QgsRubberBand(canvas)
        self.canvas = canvas
        self.region = region
        if self.region.getType() == 'restricted':
            self.dashRubberBand.setColor(QColor(50, 50, 50))
            self.dashRubberBand.setLineStyle(Qt.DashDotLine)
        elif self.region.getType() == 'mission':
            self.dashRubberBand.setColor(QColor(0, 250, 0))
            self.dashRubberBand.setLineStyle(Qt.DashLine)

        self.lastPoint = QgsPointXY(0, 0)

        numOfPoints = self.region.countPoints()
        if numOfPoints == 0:
            self.state = self.NODASHLINE
        elif numOfPoints == 1:
            self.state = self.DASHLINEONEPOINT
        elif numOfPoints > 1:
            self.state = self.DASHLINEPOLYGON

    def start(self):
        self.canvas.setMapTool(self.clickTool)
        self.clickTool.canvasClicked.connect(self.addPointClick)

        #QObject.connect(self.clickTool, SIGNAL("canvasClicked"), self.addPointClick)

        if self.state == self.DASHLINEONEPOINT or self.state == self.DASHLINEPOLYGON:
            self.clickTool.mouseMoved.connect(self.drawDashLine)
            #QObject.connect(self.clickTool, SIGNAL("mouseMoved"), self.drawDashLine)
        self.getConnectionPoints()

    def stop(self):
        if self.state == self.DASHLINEONEPOINT or self.state == self.DASHLINEPOLYGON:
            try:
                self.clickTool.mouseMoved.disconnect(self.drawDashLine)
            except:
                pass
                #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)


            #QObject.disconnect(self.clickTool, SIGNAL("mouseMoved"), self.drawDashLine)
            self.dashRubberBand.reset()
        try:
            self.clickTool.canvasClicked.disconnect(self.addPointClick)
        except:
            #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)
            pass

        #self.clickTool.canvasClicked.disconnect()
        #QObject.disconnect(self.clickTool, SIGNAL("canvasClicked"), self.addPointClick)
        self.canvas.unsetMapTool(self.clickTool)
        self.canvas.scene().removeItem(self.dashRubberBand)
        self.leave.emit()

    def switchState(self, newState):
        if self.state == newState:
            return
        elif (self.state == self.DASHLINEPOLYGON or self.state == self.DASHLINEONEPOINT) and newState == self.NODASHLINE:
            try:
                self.clickTool.mouseMoved.disconnect(self.drawDashLine)
            except:
                pass
                #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)
            #self.clickTool.mouseMoved.disconnect()
            #QObject.disconnect(self.clickTool, SIGNAL("mouseMoved"), self.drawDashLine)
            self.dashRubberBand.reset()
        elif self.state == self.NODASHLINE and (newState == self.DASHLINEPOLYGON or newState == self.DASHLINEONEPOINT):
            self.clickTool.mouseMoved.connect(self.drawDashLine)
            #QObject.connect(self.clickTool, SIGNAL("mouseMoved"), self.drawDashLine)
            self.getConnectionPoints()
        self.state = newState

    def getConnectionPoints(self):
        numPoints = self.region.countPoints()
        if numPoints > 0:
            firstPoint = self.region.getPointAt(0)
            lastPoint = self.region.getPointAt(numPoints - 1)

            if isinstance(self.region, Region):
                mission = self.region.getParentMission()
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
            firstPointQgs = QgsPointXY(firstPoint.getX(), firstPoint.getY())
            lastPointQgs = QgsPointXY(lastPoint.getX(), lastPoint.getY())
            self.firstPoint = xform.transform(firstPointQgs)
            self.lastPoint = xform.transform(lastPointQgs)

    def addPoint(self, qgisPoint):
        if isinstance(self.region, Region):
            mission = self.region.getParentMission()
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

        transformedPoint = xform.transform(qgisPoint)
        transformedPoint = Point(transformedPoint.x(), transformedPoint.y())

        self.region.addPoint(transformedPoint)
        self.getConnectionPoints()

    @pyqtSlot(QgsPointXY, Qt.MouseButton)
    def addPointClick(self, point, button):
        if button == Qt.LeftButton:
            self.addPoint(point)
            if self.state == self.NODASHLINE:
                num = self.region.countPoints()
                if num == 1:
                    self.switchState(self.DASHLINEONEPOINT)
                elif num >= 1:
                    self.switchState(self.DASHLINEPOLYGON)
            elif self.state == self.DASHLINEONEPOINT:
                num = self.region.countPoints()
                if num >= 1:
                    self.switchState(self.DASHLINEPOLYGON)
        elif button == Qt.RightButton:
            self.stop()

    @pyqtSlot(QgsPointXY)
    def drawDashLine(self, point):
        self.dashRubberBand.reset()
        self.dashRubberBand.addPoint(self.firstPoint)
        self.dashRubberBand.addPoint(point)
        if self.state == self.DASHLINEPOLYGON:
            self.dashRubberBand.addPoint(self.lastPoint)


class AreaMOVEPOINT(QObject):
    # states:
    ONEPOINT = 0
    FIRSTPOINT = 1
    LASTPOINT = 2
    MIDDLEPOINT = 3
    # signals
    leave = pyqtSignal()

    def __init__(self, region, clickTool, canvas, index):
        QObject.__init__(self)
        self.clickTool = clickTool
        self.canvas = canvas
        self.region = region
        self.index = index

        self.dashRubberBand = QgsRubberBand(canvas)
        self.dashRubberBand.setColor(QColor(0, 200, 0))
        self.dashRubberBand.setLineStyle(Qt.DashLine)
        self.index = index

        count = region.countPoints()
        self.state = None
        if index == 0:
            if count == 1:
                self.state = self.ONEPOINT
            elif count > 1:
                self.state = self.FIRSTPOINT
            else:
                pass  # errormessage...
        elif index > 0:
            if index < count - 1:
                self.state = self.MIDDLEPOINT
            elif index == count - 1:
                self.state = self.LASTPOINT
            else:
                self.state = self.ONEPOINT

    def start(self):
        self.canvas.setMapTool(self.clickTool)
        self.setRubberBandPoints()
        self.clickTool.mouseMoved.connect(self.moveTempPoint)
        self.clickTool.canvasClicked.connect(self.moveClick)

        #QObject.connect(self.clickTool, SIGNAL("mouseMoved"), self.moveTempPoint)
        #QObject.connect(self.clickTool, SIGNAL("canvasClicked"), self.moveClick)

    def stop(self):
        try:
            self.clickTool.mouseMoved.disconnect(self.moveTempPoint)
        except:
            #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)
            pass
        try:
            self.clickTool.canvasClicked.disconnect(self.moveClick)
        except:
            #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)
            pass

        #self.clickTool.mouseMoved.disconnect()
        #self.clickTool.canvasClicked.disconnect()
        #QObject.disconnect(self.clickTool, SIGNAL("mouseMoved"), self.moveTempPoint)
        #QObject.disconnect(self.clickTool, SIGNAL("canvasClicked"), self.moveClick)

        self.dashRubberBand.reset()
        self.canvas.unsetMapTool(self.clickTool)
        self.canvas.scene().removeItem(self.dashRubberBand)
        self.leave.emit()

    def setRubberBandPoints(self):
        # init coordinate transformation
        mission = self.region.getParentMission()
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
        if self.state == self.ONEPOINT:
            point = self.region.getPointAt(0)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(transformedPoint)

        if self.state == self.FIRSTPOINT:
            point = self.region.getPointAt(1)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(transformedPoint)

            point = self.region.getPointAt(0)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(transformedPoint)

            point = self.region.getPointAt(self.region.countPoints() - 1)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(transformedPoint)

        elif self.state == self.LASTPOINT:
            point = self.region.getPointAt(self.index - 1)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(transformedPoint)

            point = self.region.getPointAt(self.index)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(transformedPoint)

            point = self.region.getPointAt(0)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(transformedPoint)

        elif self.state == self.MIDDLEPOINT:
            point = self.region.getPointAt(self.index - 1)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(transformedPoint)

            point = self.region.getPointAt(self.index)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(transformedPoint)

            point = self.region.getPointAt(self.index + 1)
            transformedPoint = xform.transform(QgsPointXY(point.getX(), point.getY()))
            self.dashRubberBand.addPoint(transformedPoint)

    def moveTempPoint(self, point):
        if self.state == self.ONEPOINT:
            rbIndex = 0
        elif self.state == self.MIDDLEPOINT or self.state == self.LASTPOINT or self.state == self.FIRSTPOINT:
            rbIndex = 1
        self.dashRubberBand.movePoint(rbIndex, point)

    @pyqtSlot(QgsPointXY, Qt.MouseButton)
    #@pyqtSlot()
    def moveClick(self, qgisPoint, button):
        if button == Qt.LeftButton:
            self.dashRubberBand.reset()
            point = Point(qgisPoint.x(), qgisPoint.y())

            # init coordinate transformation
            mission = self.region.getParentMission()
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
            oldPoint = self.region.getPointAt(self.index)
            depth = oldPoint.getDepth()

            # transform point
            transformedPoint = xform.transform(QgsPoint(point.getX(), point.getY()))
            transformedPoint = Point(transformedPoint.x(), transformedPoint.y(), depth)

            # give data to region
            self.region.removePointAt(self.index)
            self.region.addPoint(transformedPoint, self.index)
        self.stop()
