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

#imports from pyqt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt
#imports from qgis
from qgis.gui import QgsRubberBand
from qgis.core import QgsPoint, QgsPointXY
from qgis.core import QgsCoordinateTransform, QgsProject
from qgis.core import QgsGeometry
from qgis.core import QgsMessageLog, Qgis

from qgis.PyQt.QtCore import QPointF
#imports from within pathplanner plugin
from ..model.task import Task
from .ppWaypoint import ppWaypointMarker #, ppCircleMarker
from .ppCircle import ppCircleMarker
from .ppKeepStation import ppKeepStationMarker
from .SurveyGraphic import SurveyTypes
from .SurveyGraphic import StartPositions
from .SurveyGraphic import SurveyGraphic
from math import *
import traceback

class ppTaskPlotter():
    def __init__(self, canvas, crs, task=None, color = QColor(0,0,0)):
        try:    
            self.canvas = canvas
            # int coordinate transformation
            self.missionCRS = crs
            try:
                self.mapCRS = self.canvas.mapSettings().destinationCrs() # WGS 84
                if self.mapCRS is None:
                    self.mapCRS = self.canvas.mapRenderer().destinationCrs()
            except:
                self.mapCRS = self.canvas.mapRenderer().destinationCrs()
            self.xform = QgsCoordinateTransform(self.missionCRS, self.mapCRS, QgsProject.instance())
            
            self.color = color
            self.rubberBand = QgsRubberBand(canvas)
            #QgsMessageLog.logMessage("Added rubberband %s to canvas %s" % (self.rubberBand, canvas), tag="Pathplanner", level=Qgis.INFO)
            self.rubberBand.setColor(color)
            self.vMarkerList = list()
            self.surveyGraphicsList = list()

            self.arrivalRadius = 10
            if task is not None:
                self.plotTask(task)

        except:
            QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)

    def addCircleMarker(self, point, radius, direction):
        marker = ppCircleMarker(self.canvas, self.color)
        marker.setCenter(point)
        marker.setRadius(radius)
        marker.setDirection(direction)
        self.vMarkerList.append(marker)


    def pointToQgsPoint(self, point):
        x = point.getX()
        y = point.getY()
        return QgsPointXY(x,y)
        
    def plotWaypointsTask(self, task):
        numOfPoints = task.numPoints()

        index = 0
        properties = task.getProperties()
        self.arrivalRadius = properties.getArrivalRadius()
        self.showArrivalCircleWpt = properties.getArrivalCircleBoolWpt()
        selIndex = properties.getSelectedPointIndex()
        defColor = self.color
        while index < numOfPoints:
            point = task.getPointAt(index)
            qgsPoint = self.pointToQgsPoint(point)
            transformedPoint = self.xform.transform(qgsPoint)
            self.rubberBand.addPoint(transformedPoint)
            # if a point was selected on the waypoint table, it will be highligted by different color
            if (index == selIndex):
                self.color = QColor(255,140,0)
            self.addMarker(transformedPoint)
            self.color = defColor
            index = index + 1

    def addMarker(self, point):
        marker = ppWaypointMarker(self.canvas, self.color)
        marker.setCenter(point)
        marker.setArrivalRadius(self.arrivalRadius)
        marker.setArrivalCircleBool(self.showArrivalCircleWpt)
        self.vMarkerList.append(marker)
                
    def plotSurveyTask(self, task):
        graphic = SurveyGraphic(self.canvas, self.color)
        center = task.getCenterPoint()
        centerXY = QgsPointXY(center.getX(), center.getY())
        center = self.xform.transform(centerXY)
        graphic.setCenter(center)
        
        point = task.getPointAt(0)
        qgsPoint = self.pointToQgsPoint(point)
        transformedUL = self.xform.transform(qgsPoint)

        point = task.getPointAt(2)
        qgsPoint = self.pointToQgsPoint(point)
        transformedLR = self.xform.transform(qgsPoint)
        
        graphic.setRect(transformedUL, transformedLR)

        # get angle, startpos and survey type from taskproperties
        properties = task.getProperties()
        angle = float(properties.getRotationAngle())
        startPos = properties.getStartPosition()
        surveyType = properties.getSurveyType()
        EWextent = properties.getEastWestExtent()
        NSextent = properties.getNorthSouthExtent()
        swath = properties.getSwath()
        ssrange = properties.getSideScanRange()
        nadir = properties.getNadirGap()
        dfactor = properties.getDistanceFactor()
        radius = properties.getArrivalRadius()
        showArrivalCircleBool = properties.getArrivalCircleBoolSrv()

        if startPos == 'NorthEast':
            startPos = StartPositions.NorthEast

        elif startPos == 'NorthWest':
            startPos = StartPositions.NorthWest

        elif startPos == 'SouthEast':
            startPos = StartPositions.SouthEast

        elif startPos == 'SouthWest':
            startPos = StartPositions.SouthWest

        if surveyType == 'Meander':
            surveyType = SurveyTypes.Meander
        if surveyType == 'UnevenMeander':
            surveyType = SurveyTypes.UnevenMeander
        elif surveyType == 'Idle':
            surveyType = SurveyTypes.Idle
        elif surveyType == 'Descend/Ascend':
            surveyType = SurveyTypes.DescendAscend
        elif surveyType == 'BufferedMeander':
            surveyType = SurveyTypes.BufferedMeander

        graphic.setAngle(angle)
        graphic.setStartPosition(startPos)
        graphic.setSurveyType(surveyType)
        graphic.setEastWestExtent(EWextent)
        graphic.setNorthSouthExtent(NSextent)
        graphic.setSwath(swath)
        graphic.setSideScanRange(ssrange)
        graphic.setNadirGap(nadir)
        graphic.setDistanceFactor(dfactor)
        graphic.setArrivalRadius(radius)
        graphic.setArrivalCircleBool(showArrivalCircleBool)

        self.surveyGraphicsList.append(graphic)

    def plotCircleTask(self, task):
        point = task.getPoint()
        radius = task.getRadius()
        direction = task.getRotationDirection()
        qgsPoint = self.pointToQgsPoint(point)
        transformedPoint = self.xform.transform(qgsPoint)
        self.rubberBand.addPoint(transformedPoint)
        self.addCircleMarker(transformedPoint, radius, direction)

    def plotKeepStationTask(self, task):
        transformedPoint = self.xform.transform(self.pointToQgsPoint(task.getPoint()))
        self.rubberBand.addPoint(transformedPoint)
        self.vMarkerList.append(ppKeepStationMarker(self.canvas, self.color, transformedPoint, task.getInnerRadius(), task.getOuterRadius()))

    def plotTask(self, task):
        if isinstance(task, Task):
            if task.numPoints() > 0:
                #QgsMessageLog.logMessage("Task plot: %s" % task.type(), tag="Pathplanner", level=Qgis.Info)
                if task.type() == 'waypoint' or task.type() == 'waypoints':
                    self.plotWaypointsTask(task)
                elif task.type() == 'survey':
                    self.plotSurveyTask(task)
                elif task.type() == 'circle':
                    self.plotCircleTask(task)
                elif task.type() == 'keepstation':
                    self.plotKeepStationTask(task)

    def deleteFromCanvas(self):
        #QgsMessageLog.logMessage("Removing rubberband %s from canvas %s" % (self.rubberBand, self.canvas), tag="Pathplanner",
        #                         level=Qgis.Info)
        self.rubberBand.reset()
        self.canvas.scene().removeItem(self.rubberBand)
        for marker in self.vMarkerList:
            self.canvas.scene().removeItem(marker)
        for graphic in self.surveyGraphicsList:
            graphic.clean()
            graphic.hideMeOnCanvas()
            self.canvas.scene().removeItem(graphic)
