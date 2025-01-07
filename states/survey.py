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
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtCore import pyqtSlot

# imports from qgis
from qgis.gui import QgsRubberBand, QgsMapTool
from qgis.core import QgsCoordinateTransform, QgsMessageLog, QgsProject, QgsPointXY
from qgis.core import QgsProject
from qgis.core import Qgis

from ..model.point import Point
import math

class SurveyADDRECT (QObject):
    # states:
    DASHLINE = 0
    NODASHLINE = 1
    #signals
    leave = pyqtSignal()
    
    def __init__(self, model, clickTool, canvas):
        QObject.__init__(self)

        self.clickTool = clickTool
        self.canvas = canvas
        self.model = model
        
        self.firstClickPoint = None
        
        self.dashRubberBand = QgsRubberBand(canvas)
        self.dashRubberBand.setColor(QColor(0,200,0))
        self.dashRubberBand.setLineStyle(Qt.DashLine)
        
        self.state = self.NODASHLINE
    
    def start(self):
        self.canvas.setMapTool(self.clickTool)
        self.clickTool.canvasClicked.connect(self.firstClick)
        
    def stop(self):
        if self.state == self.DASHLINE:
            try:
                self.clickTool.mouseMoved.disconnect()
            except:
                #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass

            try:
                self.clickTool.canvasClicked.disconnect()
            except:
                #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass

        elif self.state == self.NODASHLINE:
            try:
                self.clickTool.canvasClicked.disconnect()
            except:
                #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass

        self.dashRubberBand.reset()
        self.canvas.unsetMapTool(self.clickTool)
        self.canvas.scene().removeItem(self.dashRubberBand)
        self.leave.emit()
        
    def switchState(self, newState):
        if self.state == newState:
            return
        elif self.state == self.DASHLINE and newState == self.NODASHLINE:
            try:
                self.clickTool.canvasClicked.disconnect()
            except:
                #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass

            try:
                self.clickTool.mouseMoved.disconnect()
            except:
                #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass

            self.clickTool.canvasClicked.connect(self.firstClick)

            self.dashRubberBand.reset()
        elif self.state == self.NODASHLINE and newState == self.DASHLINE:
            try:
                self.clickTool.canvasClicked.disconnect()
            except:
                #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass

            self.clickTool.canvasClicked.connect(self.secondClick)
            self.clickTool.mouseMoved.connect(self.drawDashRect)

        self.state = newState

    @pyqtSlot(QgsPointXY, Qt.MouseButton)
    def firstClick(self, point, button):
        if button == Qt.LeftButton:
            self.firstClickPoint = point
            self.switchState(self.DASHLINE)
        elif button == Qt.RightButton:
            self.stop()

    @pyqtSlot(QgsPointXY)
    def drawDashRect(self, point):
        if self.firstClickPoint is not None:
            self.dashRubberBand.reset()
            secondPoint = QgsPointXY(self.firstClickPoint.x(),point.y())
            fourthPoint = QgsPointXY(point.x(), self.firstClickPoint.y())
            self.dashRubberBand.addPoint(self.firstClickPoint)
            self.dashRubberBand.addPoint(secondPoint)
            self.dashRubberBand.addPoint(point)
            self.dashRubberBand.addPoint(fourthPoint)
            self.dashRubberBand.addPoint(self.firstClickPoint)

    @pyqtSlot(QgsPointXY, Qt.MouseButton)
    def secondClick(self, point, button):
        if button == Qt.LeftButton:
            if self.firstClickPoint is not None:
                secondPoint = QgsPointXY(self.firstClickPoint.x(),point.y())
                fourthPoint = QgsPointXY(point.x(), self.firstClickPoint.y())

                # convert crs
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

                transformedFirstPoint = xform.transform(self.firstClickPoint)
                transformedSecondPoint = xform.transform(secondPoint)
                transformedThirdPoint = xform.transform(point)
                transformedFourthPoint = xform.transform(fourthPoint)

                transformedFirstPoint = Point(transformedFirstPoint.x(),transformedFirstPoint.y())
                transformedSecondPoint = Point(transformedSecondPoint.x(),transformedSecondPoint.y())
                transformedThirdPoint = Point(transformedThirdPoint.x(),transformedThirdPoint.y())
                transformedFourthPoint = Point(transformedFourthPoint.x(),transformedFourthPoint.y())
                self.model.setRect(transformedFirstPoint, transformedSecondPoint, transformedThirdPoint, transformedFourthPoint, 1)
                self.stop()
            else:
                #QgsMessageLog.logMessage("secondClick: first click has no point", tag="Pathplanner", level=Qgis.Critical)
                pass
        elif button == Qt.RightButton:
            self.stop()
        elif button == Qt.MidButton:
            self.stop()
        self.dashRubberBand.reset()

class SurveyROTATE (QObject):
    # signals
    leave = pyqtSignal()

    def __init__(self, model, clickTool, canvas):
        QObject.__init__(self)
        self.clickTool = clickTool
        self.canvas = canvas
        self.model = model
        self.angle = 0
        self.centerP = model.getCenterPoint()
        #self.centerXY = QgsPointXY(centerPoint.getX(), centerPoint.getY())
        self.sPosition = self.model.getStartPosition()

        #self.dashRubberBand_arrow = QgsRubberBand(canvas, True)
        self.dashRubberBand_arrow = QgsRubberBand(canvas)
        self.dashRubberBand_arrow.setColor(QColor(200,0,0))
        self.dashRubberBand_arrow.setLineStyle(Qt.DashLine)

        #self.dashRubberBand = QgsRubberBand(canvas, True)
        self.dashRubberBand = QgsRubberBand(canvas)
        self.dashRubberBand.setColor(QColor(0,200,0))
        self.dashRubberBand.setLineStyle(Qt.DashLine)

        #init coordinate transformation
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
            
        self.xform = QgsCoordinateTransform(missionCRS, mapCRS, QgsProject.instance())

        self.centerXY = self.xform.transform(QgsPointXY(self.centerP.getX(), self.centerP.getY()))#, QgsCoordinateTransform.ReverseTransform)

        pointUL = self.xform.transform(QgsPointXY(model.getUL().getX(), model.getUL().getY())) #, QgsCoordinateTransform.ReverseTransform)
        pointUR = self.xform.transform(QgsPointXY(model.getUR().getX(), model.getUR().getY())) #, QgsCoordinateTransform.ReverseTransform)
        pointLL = self.xform.transform(QgsPointXY(model.getLL().getX(), model.getLL().getY())) #, QgsCoordinateTransform.ReverseTransform)
        pointLR = self.xform.transform(QgsPointXY(model.getLR().getX(), model.getLR().getY())) #, QgsCoordinateTransform.ReverseTransform)

        #compute points relative to center:
        self.relPointUL = QgsPointXY(-abs(pointUL.x() - self.centerXY.x()), abs(pointUL.y() - self.centerXY.y()))
        self.relPointUR = QgsPointXY(abs(pointUR.x() - self.centerXY.x()), abs(pointUR.y() - self.centerXY.y()))
        self.relPointLL = QgsPointXY(-abs(pointLL.x() - self.centerXY.x()), -abs(pointLL.y() - self.centerXY.y()))
        self.relPointLR = QgsPointXY(abs(pointLR.x() - self.centerXY.x()), -abs(pointLR.y() - self.centerXY.y()))

    def start(self):
        self.canvas.setMapTool(self.clickTool)
        self.clickTool.canvasClicked.connect(self.mouseClick)
        self.clickTool.mouseMoved.connect(self.mouseMove)

    def stop(self):
        try:
            self.clickTool.mouseMoved.disconnect()
        except:
            #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)
            pass

        try:
            self.clickTool.canvasClicked.disconnect()
        except:
            #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)
            pass

        self.dashRubberBand.reset()
        self.dashRubberBand_arrow.reset()
        self.canvas.unsetMapTool(self.clickTool)
        self.canvas.scene().removeItem(self.dashRubberBand)
        self.canvas.scene().removeItem(self.dashRubberBand_arrow)
        self.leave.emit()
 
    def computeAngle(self, pnt):
        adjacentSide = [0, pnt.y() - self.centerXY.y()]
        oppositeSide = [pnt.x() - self.centerXY.x(), 0]

        # get midpoint of survey
        midx = self.centerXY.x()
        midy = self.centerXY.y()
        # if the courser is moved over the y- or the x- axis, the angle can't be computed
        if pnt.x() == midx or pnt.y() == midy:
            return

        # get lengths of the triangle that will be needed to compute the angle
        #oppositeLen = math.sqrt(oppositeSide[0] * oppositeSide[0])
        #adjacentLen = math.sqrt(adjacentSide[1] * adjacentSide[1])

        # compute angle
        # TODO: Division durch 0 abfangen!!
        tanAlpha = oppositeSide[0]/adjacentSide[1]
        alpha = math.atan(tanAlpha)
        #correct the angle depending on the quadrant of the coordinate system
        if pnt.x() > midx:
            if pnt.y() < midy: # quadrant IV
                alpha = alpha - math.radians(180)
                pass
        else:
            if pnt.y() > midy: # quadrant II
                pass
            else: # quadrand III
                alpha = alpha + math.radians(180)
        return alpha

    def rotateAndMoveEdge(self, center, point):
        if self.angle == None:
            return point
        angle = -(self.angle)
        #
        #point = self.canvas.mapToGlobal(QgsMapTool(self.canvas).toCanvasCoordinates(point))
        # rotate
        new_x = point.x() * math.cos(angle) - point.y() * math.sin(angle)
        new_y = point.x() * math.sin(angle) + point.y() * math.cos(angle)
        # move around center
        new_x = new_x + center.x()
        new_y = new_y + center.y()
        return QgsPointXY(new_x, new_y)

    def drawArrow(self, rotPointUL, rotPointLL, rotPointLR, rotPointUR):
        dx = 20
        dy = 20
        angle = -self.angle
        if (self.sPosition == 'NorthEast'):
            x = rotPointUR.x()
            y = rotPointUR.y()

            arrowPoint1 = QgsPointXY(x - dx * math.sin(angle), y + dy * math.cos(angle))
            arrowPoint2 = QgsPointXY(x + dx * math.sin(angle), y - dy * math.cos(angle))
            arrowPoint3 = QgsPointXY(x - dx * math.cos(angle), y - dy * math.sin(angle))

            self.dashRubberBand_arrow.addPoint(arrowPoint1)
            self.dashRubberBand_arrow.addPoint(arrowPoint2)
            self.dashRubberBand_arrow.addPoint(arrowPoint3)
            self.dashRubberBand_arrow.addPoint(arrowPoint1)

        elif (self.sPosition == 'NorthWest'):
            x = rotPointUL.x()
            y = rotPointUL.y()
            arrowPoint1 = QgsPointXY(x - dx * math.sin(angle), y + dy * math.cos(angle))
            arrowPoint2 = QgsPointXY(x + dx * math.sin(angle), y - dy * math.cos(angle))
            arrowPoint3 = QgsPointXY(x + dx * math.cos(angle), y + dy * math.sin(angle))

            self.dashRubberBand_arrow.addPoint(arrowPoint1)
            self.dashRubberBand_arrow.addPoint(arrowPoint2)
            self.dashRubberBand_arrow.addPoint(arrowPoint3)
            self.dashRubberBand_arrow.addPoint(arrowPoint1)

        elif (self.sPosition == 'SouthWest'):
            x = rotPointLL.x()
            y = rotPointLL.y()
            arrowPoint1 = QgsPointXY(x - dx * math.sin(angle), y + dy * math.cos(angle))
            arrowPoint2 = QgsPointXY(x + dx * math.sin(angle), y - dy * math.cos(angle))
            arrowPoint3 = QgsPointXY(x + dx * math.cos(angle), y + dy * math.sin(angle))

            self.dashRubberBand_arrow.addPoint(arrowPoint1)
            self.dashRubberBand_arrow.addPoint(arrowPoint2)
            self.dashRubberBand_arrow.addPoint(arrowPoint3)
            self.dashRubberBand_arrow.addPoint(arrowPoint1)

        elif (self.sPosition == 'SouthEast'):
            x = rotPointLR.x()
            y = rotPointLR.y()
            arrowPoint1 = QgsPointXY(x - dx * math.sin(angle), y + dy * math.cos(angle))
            arrowPoint2 = QgsPointXY(x + dx * math.sin(angle), y - dy * math.cos(angle))
            arrowPoint3 = QgsPointXY(x - dx * math.cos(angle), y - dy * math.sin(angle))

            self.dashRubberBand_arrow.addPoint(arrowPoint1)
            self.dashRubberBand_arrow.addPoint(arrowPoint2)
            self.dashRubberBand_arrow.addPoint(arrowPoint3)
            self.dashRubberBand_arrow.addPoint(arrowPoint1)

    def drawEdges(self, edges):
        self.dashRubberBand.reset()
        for edge in edges:
            self.dashRubberBand.addPoint(edge)

    @pyqtSlot(QgsPointXY, Qt.MouseButton)
    def mouseClick(self, point, button):
        if button == Qt.LeftButton:
            angle = math.degrees(float(self.angle))
            if angle < 0:
                angle = angle + 360
            self.model.setAngle(angle)
        self.stop()
             
    @pyqtSlot(QgsPointXY)
    def mouseMove(self, point):
        self.dashRubberBand.reset()
        self.dashRubberBand_arrow.reset()
        self.angle = self.computeAngle(point)
        # rotate corners
        rotPointUL = self.rotateAndMoveEdge(self.centerXY, self.relPointUL)
        rotPointUR = self.rotateAndMoveEdge(self.centerXY, self.relPointUR)
        rotPointLL = self.rotateAndMoveEdge(self.centerXY, self.relPointLL)
        rotPointLR = self.rotateAndMoveEdge(self.centerXY, self.relPointLR)
        self.drawEdges((rotPointUL, rotPointLL, rotPointLR, rotPointUR, rotPointUL))
        self.drawArrow(rotPointUL, rotPointLL, rotPointLR, rotPointUR)

class SurveyMOVE(QObject):
    #states:
    DASHLINE = 0
    NODASHLINE = 1
    # signals
    leave = pyqtSignal()

    def __init__(self, model, clickTool, canvas):
        QObject.__init__(self)
        self.clickTool = clickTool
        self.canvas = canvas
        self.model = model
        self.properties = model.getProperties()

        self.firstClickPoint = None

        self.dashRubberBand = QgsRubberBand(canvas)
        self.dashRubberBand.setColor(QColor(0, 200, 0))
        self.dashRubberBand.setLineStyle(Qt.DashLine)

        self.state = self.NODASHLINE
        self.ewe = self.properties.getEastWestExtent()
        self.nse = self.properties.getNorthSouthExtent()
        self.angle = -math.radians(self.properties.getRotationAngle())

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

        self.xform = QgsCoordinateTransform(missionCRS, mapCRS, QgsProject.instance())
        # get lon, lat for all corners and create QgsPoint classes
        pointUL = QgsPointXY(model.getUL().getX(), model.getUL().getY())
        pointUR = QgsPointXY(model.getUR().getX(), model.getUR().getY())
        pointLL = QgsPointXY(model.getLL().getX(), model.getLL().getY())
        pointLR = QgsPointXY(model.getLR().getX(), model.getLR().getY())
        # transform to map CRS
        self.pointUL = self.xform.transform(pointUL)  # , QgsCoordinateTransform.ReverseTransform)
        self.pointUR = self.xform.transform(pointUR)  # , QgsCoordinateTransform.ReverseTransform)
        self.pointLL = self.xform.transform(pointLL)  # , QgsCoordinateTransform.ReverseTransform)
        self.pointLR = self.xform.transform(pointLR)  # , QgsCoordinateTransform.ReverseTransform)
        # transform original center
        centerPoint = self.model.getCenterPoint()
        centerXY = self.xform.transform(QgsPointXY(centerPoint.getX(), centerPoint.getY()))

        # compute points relative to center:
        self.pointUL = QgsPointXY(-abs(self.pointUL.x() - centerXY.x()), abs(self.pointUL.y() - centerXY.y()))
        self.pointUR = QgsPointXY(abs(self.pointUR.x() - centerXY.x()), abs(self.pointUR.y() - centerXY.y()))
        self.pointLL = QgsPointXY(-abs(self.pointLL.x() - centerXY.x()), -abs(self.pointLL.y() - centerXY.y()))
        self.pointLR = QgsPointXY(abs(self.pointLR.x() - centerXY.x()), -abs(self.pointLR.y() - centerXY.y()))

    def start(self):
        self.canvas.setMapTool(self.clickTool)
        try:
            self.clickTool.mouseMoved.disconnect()
        except:
            pass
            #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)

        self.switchState(self.DASHLINE)

    def stop(self):
        if self.state == self.DASHLINE:
            try:
                self.clickTool.mouseMoved.disconnect()
            except:
                #QgsMessageLog.logMessage("mouseMoved: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass
            try:
                self.clickTool.canvasClicked.disconnect()
            except:
                #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass

        self.dashRubberBand.reset()
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
            try:
                self.clickTool.canvasClicked.disconnect()
            except:
                #QgsMessageLog.logMessage("canvasClicked: was not connected", tag="Pathplanner", level=Qgis.Warning)
                pass

            self.dashRubberBand.reset()
        elif self.state == self.NODASHLINE and newState == self.DASHLINE:
            self.clickTool.canvasClicked.connect(self.onClick)
            self.clickTool.mouseMoved.connect(self.drawDashRect)

        self.state = newState

    @pyqtSlot(QgsPointXY)
    def drawDashRect(self, point):
        rotPointUL = self.rotateAndMoveEdge(point, self.pointUL)
        rotPointUR = self.rotateAndMoveEdge(point, self.pointUR)
        rotPointLL = self.rotateAndMoveEdge(point, self.pointLL)
        rotPointLR = self.rotateAndMoveEdge(point, self.pointLR)
        # make a closed rectangle
        self.drawEdges((rotPointUL, rotPointLL, rotPointLR, rotPointUR, rotPointUL))

    def rotateAndMoveEdge(self, center, point):
        new_x = point.x() * math.cos(self.angle) - point.y() * math.sin(self.angle)
        new_y = point.x() * math.sin(self.angle) + point.y() * math.cos(self.angle)
        # move around center
        new_x = new_x + center.x()
        new_y = new_y + center.y()
        return QgsPointXY(new_x, new_y)

    def drawEdges(self, edges):
        self.dashRubberBand.reset()
        for edge in edges:
            self.dashRubberBand.addPoint(edge)

    @pyqtSlot(QgsPointXY, Qt.MouseButton)
    def onClick(self, point, button):
        if button == Qt.LeftButton:
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

            transformedPoint = xform.transform(point)
            transformedPoint = Point(transformedPoint.x(), transformedPoint.y())
            self.model.moveRect(transformedPoint)
        elif button == Qt.RightButton:
            self.stop()

        self.dashRubberBand.reset()
        self.stop()
