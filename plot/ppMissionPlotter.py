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
        modified             : 2016-12-21 btr
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
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QObject, Qt

#imports from qgis
from qgis.gui import QgsRubberBand
from qgis.core import QgsPoint, QgsPointXY, QgsGeometry
from qgis.core import QgsCoordinateTransform,QgsProject
from qgis.PyQt.QtCore import QAbstractListModel
import qgis.utils

from .ppTaskPlotter import ppTaskPlotter
from ..model.mission import Mission
from ..model.point import Point
import math

class ppMissionPlotter(QObject):

    def __init__(self, canvas, mainWidget, mission=None):
        self.canvas = canvas
        self.mainWidget = mainWidget
        self.taskPlotterList = list()
        self.connectingRubberBandList = list()
        self.regions = list()
        Index = 1
        self.mission = mission
        if mission:
            self.plotMission(mission)

    @pyqtSlot(QAbstractListModel)
    def plotMission(self, mission=None):
        #QgsMessageLog.logMessage("ppMissionPlotter: plotMission called", tag="Pathplanner", level=Qgis.Critical)

        if mission is not None:
            self.mission = mission
        #delete existing plot from canvas

        self.deleteFromCanvas()
        if isinstance(self.mission, Mission):

            crs = self.mission.getCRS()
            #taskList = mission.getTaskList()
            numOfTasks = self.mission.countTasks()
            activeTaskIndex = self.mainWidget.getSelectedTask()
            runningIndex = 0

            while runningIndex < numOfTasks:
                task = self.mission.getTask(runningIndex)
                if runningIndex == activeTaskIndex:
                    color = QColor(200,0,0)
                else:
                    prop = task.getProperties()
                    prop.setSelectedPoint(-1)
                    color = QColor(0,0,0)

                taskPlotter = ppTaskPlotter(self.canvas, crs, task, color)
                self.taskPlotterList.append(taskPlotter)

                runningIndex = runningIndex + 1

            self.connectTasks(self.mission)
            self.plotRegionsList(self.mission)

    # @pyqtSlot()
    # def plotMission(self):
    #     QgsMessageLog.logMessage("ppMissionPlotter: plotMission called", tag="Pathplanner", level=Qgis.Critical)
    #     #if mission is not None:
    #     #    self.mission = mission
    #     #delete existing plot from canvas
    #     self.deleteFromCanvas()
    #
    #     if isinstance(self.mission, Mission):
    #
    #         crs = self.mission.getCRS()
    #
    #         #taskList = mission.getTaskList()
    #         numOfTasks = self.mission.countTasks()
    #         activeTaskIndex = self.mainWidget.getSelectedTask()
    #         runningIndex = 0
    #
    #         while runningIndex < numOfTasks:
    #             task = self.mission.getTask(runningIndex)
    #             if runningIndex == activeTaskIndex:
    #                 color = QColor(200,0,0)
    #             else:
    #                 prop = task.getProperties()
    #                 prop.setSelectedPoint(-1)
    #                 color = QColor(0,0,0)
    #                 #color = QColor(255,64,64)
    #             taskPlotter = ppTaskPlotter(self.canvas, crs, task, color)
    #             self.taskPlotterList.append(taskPlotter)
    #
    #             runningIndex = runningIndex + 1
    #
    #         self.connectTasks(self.mission)
    #         self.plotRegionsList(self.mission)

    def plotRegionsList(self, mission):
        regionsList = mission.getRegionsList()
        num = regionsList.countItems()
        index = 0
        while index < num:
            region = regionsList.getItemAt(index)
            self.plotRegion(region, mission)
            index = index + 1

    def plotRegion(self, region, mission):
        numPoints = region.countPoints()
        ppoints = list()
        if numPoints > 0:
            
            missionCRS = mission.getCRS()
            try:
                mapCRS = qgis.utils.iface.mapCanvas().mapSettings().destinationCrs() # WGS 84
            except:
                mapCRS = qgis.utils.iface.mapCanvas().mapRenderer().destinationCrs() # WGS 84
            #mapCRS = self.canvas.mapRenderer().destinationCrs()
            xform = QgsCoordinateTransform(missionCRS, mapCRS, QgsProject.instance())
            
            rubberBand = QgsRubberBand(self.canvas)
            if region.getType() == 'restricted':
                rubberBand.setColor(QColor(120,120,120))
                rubberBand.setLineStyle(Qt.DashDotLine)
                rubberBand.setFillColor(QColor(250,0,0))
                rubberBand.setBrushStyle(Qt.BDiagPattern)
            elif region.getType() == 'mission':
                rubberBand.setColor(QColor(100,180,0))
                rubberBand.setLineStyle(Qt.DashDotLine)
                rubberBand.setFillColor(QColor(0, 250, 0))
                rubberBand.setBrushStyle(Qt.NoBrush)
                rubberBand.setWidth(2)
                #rubberBand.setBrushStyle(Qt.Dense4Pattern)
                rubberBand.setFillColor(QColor(0, 255, 255))
            index = 0
            while index < numPoints:
                point = region.getPointAt(index)
                pointQgs = QgsPointXY(point.getX(), point.getY())

                transformedPoint = xform.transform(pointQgs)
                rubberBand.addPoint(transformedPoint)
                ppoints.append(transformedPoint)

                rubberBand.setToGeometry(QgsGeometry.fromPolygonXY([ppoints]), None)
                rubberBand.show()
                index = index + 1
            self.regions.append(rubberBand)

    def connectTasks(self,mission):
        # init coordinate transform
        missionCRS = mission.getCRS()
        
        try:
            mapCRS = self.canvas.mapSettings().destinationCrs() # WGS 84
            if mapCRS is None:
                try:
                    mapCRS = qgis.utils.iface.mapCanvas().mapSettings().destinationCrs() # WGS 84
                except:
                    mapCRS = qgis.utils.iface.mapCanvas().mapRenderer().destinationCrs() # WGS 84
        except:
            try:
                mapCRS = qgis.utils.iface.mapCanvas().mapSettings().destinationCrs() # WGS 84
            except:
                mapCRS = qgis.utils.iface.mapCanvas().mapRenderer().destinationCrs() # WGS 84

        xform = QgsCoordinateTransform(missionCRS, mapCRS, QgsProject.instance())
        #get task list
        taskList = mission.getTaskList()
        if len(taskList) <= 1:
            return
        previousTask = taskList[0]
        #iterate tasks
        index = 1
        while index < len(taskList):
            nextTask = taskList[index]
            # get points of previous and subsequent task that should be connected 
            if nextTask.type() == 'survey':
                prop = nextTask.getProperties()
                angle = prop.getRotationAngle()
                startPos = prop.getStartPosition()

                # get starting point of next Task
                if startPos == 'NorthWest':
                    pointOfNextTask = nextTask.getUL()
                elif startPos == 'NorthEast':
                    pointOfNextTask = nextTask.getUR()
                elif startPos == 'SouthWest':
                    pointOfNextTask = nextTask.getLL()
                else:
                    pointOfNextTask = nextTask.getLR()

                angle = -math.radians(float(angle))
                if pointOfNextTask is not None:
                    centerPoint = nextTask.getCenterPoint()
                    qgsCenter = QgsPointXY(centerPoint.getX(), centerPoint.getY())
                    transCenter = xform.transform(qgsCenter)
                    nextPoint = xform.transform(QgsPointXY(pointOfNextTask.getX(), pointOfNextTask.getY())) #, QgsCoordinateTransform.ReverseTransform)
                    #compute points relative to center:
                    relPoint = QgsPointXY(nextPoint.x() - transCenter.x(), nextPoint.y() - transCenter.y())
                    
                    midx = transCenter.x()
                    midy = transCenter.y()
                    
                    x = relPoint.x()
                    y = relPoint.y()
                    
                    # compute new point
                    new_x = x * math.cos(angle) - y * math.sin(angle)
                    new_y = x * math.sin(angle) + y * math.cos(angle)
                    
                    # count back
                    new_x = new_x + midx
                    new_y = new_y + midy
                    pointOfNextTask = Point(new_x, new_y)

            elif nextTask.type() == 'waypoint':
                pointOfNextTask = nextTask.getFirstWayPoint()
                if pointOfNextTask is not None:
                    point = xform.transform(QgsPointXY(pointOfNextTask.getX(), pointOfNextTask.getY()))
                    pointOfNextTask = Point(point.x(), point.y())
            elif nextTask.type() in ['circle', 'keepstation']:
                pointOfNextTask = nextTask.getPoint()
                if pointOfNextTask is not None:
                    point = xform.transform(QgsPointXY(pointOfNextTask.getX(), pointOfNextTask.getY()))
                    pointOfNextTask = Point(point.x(), point.y())
            if previousTask.type() == 'survey':
                prop = previousTask.getProperties()
                angle = prop.getRotationAngle()
                startPos = prop.getStartPosition()

                # east west extent, swath to determine number of lines of the survey
                nse = prop.getNorthSouthExtent()
                swath = prop.getSwath()
                nol = int(nse/swath)+1

                rest = nol%2
                ## getting endpoint of the survey depending on StartPoint and number of lines
                if startPos == 'NorthWest': # endpunkt berechnen
                    if rest == 0:
                        pointOfPreviousTask = previousTask.getLL()
                    else:
                        pointOfPreviousTask = previousTask.getLR()
                elif startPos == 'NorthEast':
                    if rest == 0:
                        pointOfPreviousTask = previousTask.getLR()
                    else:
                        pointOfPreviousTask = previousTask.getLL()
                elif startPos == 'SouthWest':
                    if rest == 0:
                        pointOfPreviousTask = previousTask.getUL()
                    else:
                        pointOfPreviousTask = previousTask.getUR()
                else:
                    if rest == 0:
                        pointOfPreviousTask = previousTask.getUR()
                    else:
                        pointOfPreviousTask = previousTask.getUL()

                if pointOfPreviousTask is not None:
                    angle = -math.radians(float(angle))

                    centerPoint = previousTask.getCenterPoint()
                    qgsCenter = QgsPointXY(centerPoint.getX(), centerPoint.getY())
                    transCenter = xform.transform(qgsCenter)
                    prevPoint = xform.transform(QgsPointXY(pointOfPreviousTask.getX(), pointOfPreviousTask.getY())) #, QgsCoordinateTransform.ReverseTransform)

                    #compute points relative to center:
                    relPoint = QgsPointXY(prevPoint.x() - transCenter.x(), prevPoint.y() - transCenter.y())
                    
                    midx = transCenter.x()
                    midy = transCenter.y()
                    x = relPoint.x()
                    y = relPoint.y()
                    
                    # compute new point
                    new_x = x * math.cos(angle) - y * math.sin(angle)
                    new_y = x * math.sin(angle) + y * math.cos(angle)
                    # count back
                    new_x = new_x + midx
                    new_y = new_y + midy
                    pointOfPreviousTask = Point(new_x, new_y)
                    
            #pointOfPreviousTask = previousTask.getCenterPoint()
            elif previousTask.type() == 'waypoint':
                pointOfPreviousTask = previousTask.getLastWayPoint()
                if pointOfPreviousTask is not None:
                    point = xform.transform(QgsPointXY(pointOfPreviousTask.getX(), pointOfPreviousTask.getY()))
                    pointOfPreviousTask = Point(point.x(), point.y())
            elif previousTask.type() in ['circle', 'keepstation']:
                pointOfPreviousTask = previousTask.getPoint()
                if pointOfPreviousTask is not None:
                    point = xform.transform(QgsPointXY(pointOfPreviousTask.getX(), pointOfPreviousTask.getY()))
                    pointOfPreviousTask = Point(point.x(), point.y())
            if pointOfPreviousTask is not None and pointOfNextTask is not None:
                #init rubberband
                rubberBand = QgsRubberBand(self.canvas)
                rubberBand.setColor(QColor(150,0,200))
                rubberBand.setLineStyle(Qt.DashLine)
                
                # transform to qgis points
                point1 = QgsPointXY(pointOfPreviousTask.getX(), pointOfPreviousTask.getY())
                point2 = QgsPointXY(pointOfNextTask.getX(), pointOfNextTask.getY())
                
                #add points to rubberband
                rubberBand.addPoint(point1)
                rubberBand.addPoint(point2)
                
                #store rubberband in list
                self.connectingRubberBandList.append(rubberBand)
                
            # init previous task for next iteration
            previousTask = nextTask
            
            index = index + 1

    def deleteFromCanvas(self):
        # take tasks from canvas
        for plotter in self.taskPlotterList:
            plotter.deleteFromCanvas()
        del self.taskPlotterList[:]

        # take rubberbands from canvas
        for rubberBand in self.connectingRubberBandList:
            rubberBand.reset()
            self.canvas.scene().removeItem(rubberBand)
        #empty list
        del self.connectingRubberBandList[:]
        
        for rubberBand in self.regions:
            rubberBand.reset()
            self.canvas.scene().removeItem(rubberBand)
        del self.regions[:]
        # sometimes needed (e.g. when no polygon is defined around the whole mission plan)
        self.canvas.refresh() # .refreshAllLayers()