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

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import QPainter,  QPainterPath, QBrush, QColor
from qgis.PyQt.QtCore import Qt, QPointF, QRectF, pyqtSignal, pyqtSlot

from qgis.core import QgsPointXY
from qgis.gui import QgsMapCanvasItem, QgsMapCanvas
from qgis.core import QgsMessageLog, Qgis, QgsPoint
# set this to true to activate messages

from ..coordtrans import NedToWgs84
show_log_messages = False

import traceback, sys

import math
from ..model.task_properties import taskProperties
from ..model.task_survey import SurveyTask

class SurveyTypes:
    Idle = 0
    Meander = 1
    UnevenMeander = 2
    #DescendAscend = 3
    BufferedMeander = 3
    
class StartPositions:
    NorthEast = 0
    NorthWest = 1
    SouthEast = 2
    SouthWest = 3

class SurveyGraphic(QgsMapCanvasItem, SurveyTask):
    def __init__(self,canvas, color):
        #QgsMapCanvasItem.__init__(self, canvas)
        QgsMapCanvas.__init__(self, canvas)

        self.canvas = canvas
        self.color = color
        [r,g,b,a] = color.getRgb()
        self.startPosition = None
        self.type = None
        self.center = None
        self.rotationAngle = 0
        self.painter = QPainter()
        self.coordinateTransform = self.canvas.getCoordinateTransform()
        self.translationOffsetX = 0
        self.translationOffsetY = 0
        self.boundingWidth = 0
        self.boundingHeight = 0
        self.boundingMidX = 0
        self.boundingMidY = 0
        self.cradius = 10
        self.showArrivalCircle = 0
        self.mapsettings = self.canvas.mapSettings()
        
    def clean(self):
        try:
            self.canvas.scaleChanged.disconnect()
        except:
            pass
        pass

    def setRect(self, pointTL, pointLR):
        self.pointUL = pointTL
        self.pointLR = pointLR

        self.rect = QRectF(QPointF(pointTL.x(), pointTL.y()), QPointF(pointLR.x(), pointLR.y()))

    def setSurveyType(self,type):
        self.type = type

    def setStartPosition(self,startPos):
        self.startPosition = startPos

    def setAngle(self,angle):
        self.rotationAngle = angle

    def setEastWestExtent(self, extent):
        self.eastWestExtent = extent

    def setNorthSouthExtent(self, extent):
        self.northSouthExtent = extent

    def setSwath(self, swath):
        self.wswath = swath

    def setSideScanRange(self, range):
        self.ssrange = float(range)

    def setNadirGap(self, nadir):
        self.nadirgap = float(nadir)

    def setDistanceFactor(self, factor):
        self.dfactor = float(factor)

    def setArrivalRadius(self, radius):
        self.arrivalRadius = radius

    def setArrivalCircleBool(self, bvalue):
        self.showArrivalCircle = bvalue

    @pyqtSlot()
    def scaleChangedSlot(self, scale):
        return

    def hideMeOnCanvas(self):
        self.hide()
        
    def showMeOnCanvs(self):
        self.show()

    def paintSurvey(self, painter, width, height, swath, color):
        # dynamic paint survey depending on height, width and swath
        if show_log_messages: QgsMessageLog.logMessage("paintSurvey(w=%f, h=%f, sw=%f)" % (width, height, swath), tag="Pathplanner", level=Qgis.Info)

        if swath == 0:
          exc_type, exc_value, exc_traceback = sys.exc_info()
          QgsMessageLog.logMessage("swath value is %f, setting to 25\n%s" % (swath, repr(traceback.format_tb(exc_traceback))), tag="Pathplanner", level=Qgis.Warning)
          swath = 25
          
        numOfLines = int(height/swath) + 1
        pointCount = 2*numOfLines
        wpoints1 = [0]*pointCount

        waypoints1 = [0]*pointCount
        waypoints2 = [0]*pointCount
        dswath = swath
        ewExt = width

        y1add = - height/20
        y2add = height/20
        xadd = - width/30

        if self.startPosition == StartPositions.SouthWest:
            # set center point
            waypoints1[0] = height/2
            waypoints2[0] = -width/2
            dswath = -swath
            ewExt = width
            # set Arrow points
            y1add = - height/20
            y2add = height/20
            xadd = - width/30

        elif self.startPosition == StartPositions.NorthWest:
            # set center point
            waypoints1[0] = -height/2
            waypoints2[0] = -width/2
            dswath = swath
            ewExt = width
            # set Arrow points
            y1add = -height/20
            y2add = height/20
            xadd = - width/30
        elif self.startPosition == StartPositions.SouthEast:
            # set center point
            waypoints1[0] = height/2
            waypoints2[0] = width/2
            dswath = -swath
            ewExt = -width
            # set Arrow points
            y1add = height/20
            y2add = -height/20
            xadd = width/30

        elif self.startPosition == StartPositions.NorthEast:
            # set center point
            waypoints1[0] = -height/2
            waypoints2[0] = width/2
            ewExt = -width
            dswath = swath
            # set Arrow point
            y1add = height/20
            y2add = -height/20
            xadd = width/30

        idx = 1
        # set survey points -> add serial points to matrix
        for i in range(0, numOfLines):
            i1 = i%2
            ad = 0
            if i1==0:
                ad = ewExt
            else:
                ad = -ewExt

            waypoints1[idx] = waypoints1[idx-1]
            waypoints2[idx] = waypoints2[idx-1] + ad
            idx += 1

            if i < numOfLines-1:
                waypoints1[idx] = waypoints1[idx-1] + dswath
                waypoints2[idx] = waypoints2[idx-1]
                idx += 1

        for s in range(0, pointCount):
            wpoints1[s] = QPointF(waypoints2[s], waypoints1[s])
            if s > 0:
                painter.drawLine(wpoints1[s - 1], wpoints1[s])
                if self.showArrivalCircle == 1:
                    painter.drawEllipse(wpoints1[s], self.cradius, self.cradius)

        # draw arrow points
        y1 = waypoints1[pointCount-1] + y1add
        y2 = waypoints1[pointCount-1] + y2add

        if numOfLines%2 == 0:
            x = waypoints2[pointCount-1] - xadd
        else:
            x = waypoints2[pointCount-1] + xadd

        arrPoint1 = QPointF(x, y1)
        arrPoint2 = QPointF(x, y2)

        path = QPainterPath()
        path.moveTo(wpoints1[len(wpoints1)-1])
        path.lineTo(arrPoint1)
        path.lineTo(arrPoint2)
        path.lineTo(wpoints1[len(wpoints1)-1])
        painter.setPen(Qt.NoPen)
        painter.fillPath(path, QBrush(color))
        return

    def paintUnevenSurvey(self, painter, width, height, ssrange, nadir, distfact, sw):

        if float(ssrange/nadir) < 2:
            # if side scan range too short and nadir gap is too high,
            # the sidescan coverage could not be guaranteed. In this case is a normal meander proposed.
            oddline = 1
            dswath = sw
            numOfLines = int(height / sw) + 1
        else:
            if ssrange == 0:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                QgsMessageLog.logMessage(
                    "SideScan range value is %f, setting to 25\n%s" % (
                    ssrange, repr(traceback.format_tb(exc_traceback))),
                    tag="Pathplanner", level=Qgis.Warning)
                ssrange = 25

                # odd->even line distance (x)
            if nadir >= ssrange:
                QgsMessageLog.logMessage("Nadir Gap should be less than Sidescan range", tag="Pathplanner",
                                         level=Qgis.Critical)
                nadir = ssrange
                x = nadir
            else:
                x = ssrange - nadir
                # even-odd line distance (y)
            y = distfact * ssrange

            dswath = (x+y)/2
            oddline = x/dswath
            numOfLines = self.calculateNumOfLines(self.northSouthExtent, self.ssrange, self.nadirgap, distfact)

        pointCount = 2 * numOfLines
        wpoints1 = [0] * pointCount

        waypoints1 = [0] * pointCount
        waypoints2 = [0] * pointCount

        evenAdd = oddline*dswath
        oddAdd = (2.0-oddline)*dswath

        ewExt = width

        y1add = - height / 20
        y2add = height / 20
        xadd = - width / 30

        if self.startPosition == StartPositions.SouthWest:
            # set center point
            waypoints1[0] = height / 2
            waypoints2[0] = -width / 2
            oddAdd = -oddAdd
            evenAdd = -evenAdd
            ewExt = width
            # set Arrow points
            y1add = - height / 20
            y2add = height / 20
            xadd = - width / 30

        elif self.startPosition == StartPositions.NorthWest:
            # set center point
            waypoints1[0] = -height / 2
            waypoints2[0] = -width / 2
            ewExt = width
            # set Arrow points
            y1add = -height / 20
            y2add = height / 20
            xadd = - width / 30
        elif self.startPosition == StartPositions.SouthEast:
            # set center point
            waypoints1[0] = height / 2
            waypoints2[0] = width / 2
            oddAdd = -oddAdd
            evenAdd = -evenAdd
            ewExt = -width
            # set Arrow points
            y1add = height / 20
            y2add = -height / 20
            xadd = width / 30

        elif self.startPosition == StartPositions.NorthEast:
            # set center point
            waypoints1[0] = -height / 2
            waypoints2[0] = width / 2
            ewExt = -width
            # set Arrow point
            y1add = height / 20
            y2add = -height / 20
            xadd = width / 30

        idx = 1
        # set survey points -> add serial points to matrix
        for i in range(0, numOfLines):
            i1 = i % 2
            ad = 0
            if i1 == 0:
                ad = ewExt
            else:
                ad = -ewExt

            waypoints1[idx] = waypoints1[idx - 1]
            waypoints2[idx] = waypoints2[idx - 1] + ad
            idx += 1

            if i < numOfLines - 1:
                if i % 2 > 0:
                    waypoints1[idx] = waypoints1[idx - 1] + oddAdd
                    waypoints2[idx] = waypoints2[idx - 1]
                else:
                    waypoints1[idx] = waypoints1[idx - 1] + evenAdd
                    waypoints2[idx] = waypoints2[idx - 1]
                idx += 1

        for s in range(0, pointCount):
            wpoints1[s] = QPointF(waypoints2[s], waypoints1[s])
            if s > 0:
                painter.drawLine(wpoints1[s - 1], wpoints1[s])

                if self.showArrivalCircle == 1:
                    painter.drawEllipse(wpoints1[s], self.cradius, self.cradius)

        # arrow points
        y1 = waypoints1[pointCount - 1] + y1add
        y2 = waypoints1[pointCount - 1] + y2add

        if numOfLines % 2 == 0:
            x = waypoints2[pointCount - 1] - xadd
        else:
            x = waypoints2[pointCount - 1] + xadd

        arrPoint1 = QPointF(x, y1)
        arrPoint2 = QPointF(x, y2)

        path = QPainterPath()
        path.moveTo(wpoints1[len(wpoints1) - 1])
        path.lineTo(arrPoint1)
        path.lineTo(arrPoint2)
        path.lineTo(wpoints1[len(wpoints1) - 1])
        painter.setPen(Qt.NoPen)
        painter.fillPath(path, QBrush(self.color))
        # self.painted = 1
        return

    def calculateNumOfLines(self, height, ssrange, nadir, factor):
        # odd->even line distance (x)
        if nadir >= ssrange:
            QgsMessageLog.logMessage("Nadir Gap should be less than Sidescan range", tag="Pathplanner",
                                     level=Qgis.Critical)
            nadir = ssrange
            x = nadir
        else:
            x = ssrange - nadir
        # even-odd line distance (y)
        y = factor * ssrange
        k = int(math.floor(height / (x + y)))

        if k >= 1:
            r = height - (k * (x + y))
            if r > x:
                numOfLines = (k + 1) * 2
            else:
                numOfLines = k * 2 + 1
        else:  # height < (x+y)
            if x > height:
                QgsMessageLog.logMessage("Only one line is possible due to narrow NorthSouthExtent.", tag="Pathplanner",
                                         level=Qgis.Info)
                numOfLines = 1
            else:
                QgsMessageLog.logMessage("Only two lines possible due to narrow NorthSouthExtent.", tag="Pathplanner",
                                         level=Qgis.Info)
                numOfLines = 2

        return numOfLines

    def paint(self,p,option,widget):
        if show_log_messages: QgsMessageLog.logMessage("SurveyGraphic.paint()", 'Pathplanner', Qgis.Info)
        if self.rect is not None and self.startPosition is not None and self.type is not None:
            p.rotate(self.rotationAngle)
            p.setRenderHint(QPainter.Antialiasing)
            pen = QPen()
            pen.setColor(self.color)
            p.setPen(pen)

            pen2 = QPen()
            pen2.setStyle(Qt.DashDotLine)
            pen2.setColor(QColor(250,0,0))

            tl = self.rect.topLeft()
            br = self.rect.bottomRight()

            # calculate proportion of width and swath to visualize survey lines
            # swath1 get real swath of the survey
            # width1 get real width of the survey
            swt = float(self.wswath)
            he = float(self.northSouthExtent)

            # if width is not given, to prevent calculation error is width1 set to 200
            if (he == 0):
                QgsMessageLog.logMessage("NorthSouthExtent value can not be 0. setting to 200", tag="Pathplanner",
                                         level=QgsMessageLog.Critical)
                he = 200

            fktr = he/swt

            transformedTL = self.toCanvasCoordinates(
                QgsPointXY(tl.x() + self.translationOffsetX, tl.y() + self.translationOffsetY))  # - self.pos()
            transformedBR = self.toCanvasCoordinates(
                QgsPointXY(br.x() + self.translationOffsetX, br.y() + self.translationOffsetY))  # - self.pos()

            midx = (transformedTL.x() + transformedBR.x())/2
            midy = (transformedTL.y() + transformedBR.y())/2

            #self.setCenter(QgsPoint(midx, midy))
            w = abs(midx - abs(transformedTL.x()))
            h = abs(midy - abs(transformedBR.y()))
            rect = QRectF(-w,-h,2*w,2*h)

            p.setPen(pen2)
            p.drawRect(rect)
            p.setPen(pen)

            width = 2 * w
            height = 2 * h

            self.setHeight(height)
            self.setWidth(width)

            if self.type == SurveyTypes.Meander:
                # calculate propotional swath (sw) for visualization
                sw = height/fktr
                fktr = he/float(self.arrivalRadius)
                self.cradius = height/fktr

                if show_log_messages: QgsMessageLog.logMessage("paint() calling paintSurvey with (w=%f, h=%f, sw=%f)" % (width, height, sw), tag="Pathplanner", level=Qgis.Info)
                self.paintSurvey(p, width, height, sw, self.color)

            elif self.type == SurveyTypes.BufferedMeander:

                # calculate propotional swath (sw) for visualization
                sw = height/fktr
                fktr = he/float(self.arrivalRadius)
                self.cradius = height/fktr
                bf = 3 * float(self.arrivalRadius)

                penBuffer = QPen()
                penBuffer.setStyle(Qt.DashDotLine)
                penBuffer.setColor(QColor(0, 190, 190))

                tl = self.rect.topLeft()
                br = self.rect.bottomRight()

                transformedTL = self.toCanvasCoordinates(
                   QgsPointXY(tl.x() - bf + self.translationOffsetX, tl.y() + self.translationOffsetY))
                transformedBR = self.toCanvasCoordinates(
                   QgsPointXY(br.x() + bf + self.translationOffsetX, br.y() + self.translationOffsetY))

                midx = (transformedTL.x() + transformedBR.x()) / 2
                midy = (transformedTL.y() + transformedBR.y()) / 2

                w = abs(midx - abs(transformedTL.x()))
                h = abs(midy - abs(transformedBR.y()))
                rect = QRectF(-w, -h, 2 * w, 2 * h)

                p.setPen(penBuffer)
                p.drawRect(rect)
                p.setPen(pen)
                self.showArrivalCircle = 0
                self.paintSurvey(p, width, height, sw, self.color)
                self.showArrivalCircle = 1

                # set new bounding rectangle for buffered meander
                width = 2 * w
                height = 2 * h
                self.setHeight(height)
                self.setWidth(width)

                pen3 = QPen()
                pen3.setColor(QColor(0, 190, 0))
                pen3.setStyle(Qt.DashDotLine)
                p.setPen(pen3)
                c = QColor(0, 190, 0)
                self.paintSurvey(p, width, height, sw, c)

                p.setPen(pen)

            elif self.type == SurveyTypes.UnevenMeander:
                sw = height / fktr
                fktr = he/self.ssrange
                ssr = height/fktr
                fktr = he/self.nadirgap
                ng = height/fktr
                fktr = he/float(self.arrivalRadius)
                self.cradius = height/fktr

                if show_log_messages: QgsMessageLog.logMessage("paint() calling paintUnevenSurvey with (w=%f, h=%f, sw=%f, nad=%f)" % (width, height, ssr, ng), tag="Pathplanner", level=Qgis.Info)
                self.paintUnevenSurvey(p, width, height, ssr, ng, float(self.dfactor), sw)

            elif self.type == SurveyTypes.Idle:
                rect = QRectF(-width/2, -height/2, width, height)
                path = QPainterPath()
                path.moveTo(QPointF(0,0))
                path.arcMoveTo(rect,-90)
                path.arcTo(rect,-90,330)
                p.drawPath(path)
                # draw arrow            
                point1 = QPointF(0 - width/32, 0 + height/2)
                point2 = QPointF(0 + width/32, 0 + height * 29/64)
                point3 = QPointF(0 + width/32, 0 + height * 35/64)
                #create path of 
                path = QPainterPath()
                path.moveTo(point1)
                path.lineTo(point1)
                path.lineTo(point2)
                path.lineTo(point3)
                #fill triangle
                p.setPen(Qt.NoPen)
                p.fillPath(path,QBrush(QColor("black")))

            elif self.type == SurveyTypes.DescendAscend:
                #specify points
                point1 = QPointF(0 - width/2, 0 + height/2)
                point2 = QPointF(0 - width*3/10, 0 - height/2)
                point3 = QPointF(0 - width/4, 0 - height/2)
                point4 = QPointF(0 - width/20, 0 + height/2)
                 
                point5 = QPointF(0 + width/20, 0 + height/2)
                point6 = QPointF(0 + width/4, 0 - height/2)
                point7 = QPointF(0 + width*3/10, 0 - height/2)
                point8 = QPointF(0 + width/2, 0 + height/2)
                
                p.drawLine(point1,point2)
                p.drawLine(point3,point4)
                 
                p.drawLine(point5,point6)
                p.drawLine(point7,point8)
                 
                # draw arrows
                path1 = QPainterPath()
                path2 = QPainterPath()
                path3 = QPainterPath()
                path4 = QPainterPath()
                 
                # compute angle
                vector1 = [point1.x() - point2.x(),point1.y() - point2.y()]
                vector2 = [0,point1.y() - point2.y()]
                 
                upperLeft = vector1[0] * vector2[0]
                upperRight = vector1[1] * vector2[1]
                top = upperLeft + upperRight
                bottomLeft = math.sqrt((vector1[0] * vector1[0]) + (vector1[1] * vector1[1]))
                bottomRight = math.sqrt((vector2[0] * vector2[0]) + (vector2[1] * vector2[1]))
                bottom = bottomLeft * bottomRight
                cosAlpha = top / bottom
                alpha = math.acos(cosAlpha)
                 
                # ARROW1:
                # get points relativ to point2
                corner1 = [point2.x() + w/16, point2.y() + h/8]
                corner1rel = [corner1[0] - point2.x(), corner1[1] - point2.y()]
                corner2 = [point2.x() - w/16, point2.y() + h/8]
                corner2rel = [corner2[0] - point2.x(), corner2[1] - point2.y()]
                # rotate points
                corner1rotated = [corner1rel[0] * math.cos(alpha) - corner1rel[1] * math.sin(alpha), corner1rel[0] * math.sin(alpha) + corner1rel[1] * math.cos(alpha)]
                corner2rotated = [corner2rel[0] * math.cos(alpha) - corner2rel[1] * math.sin(alpha), corner2rel[0] * math.sin(alpha) + corner2rel[1] * math.cos(alpha)]
                # transform points back to coordinate system 
                corner1 = QPointF(corner1rotated[0] + point2.x(),corner1rotated[1] + point2.y())
                corner2 = QPointF(corner2rotated[0] + point2.x(),corner2rotated[1] + point2.y())
                #create path
                path1.moveTo(point2)
                path1.lineTo(corner1)
                path1.lineTo(corner2)
                path1.lineTo(point2)
                 
                # ARROW2:
                # get points relativ to point4
                corner1 = [point4.x() + w/16, point4.y() - h/8]
                corner1rel = [corner1[0] - point4.x(),corner1[1] - point4.y()]
                corner2 = [point4.x() - w/16, point4.y() - h/8]
                corner2rel = [corner2[0] - point4.x(),corner2[1] - point4.y()]
                # rotate points
                corner1rotated = [corner1rel[0] * math.cos(-alpha) - corner1rel[1] * math.sin(-alpha), corner1rel[0] * math.sin(-alpha) + corner1rel[1] * math.cos(-alpha)]
                corner2rotated = [corner2rel[0] * math.cos(-alpha) - corner2rel[1] * math.sin(-alpha), corner2rel[0] * math.sin(-alpha) + corner2rel[1] * math.cos(-alpha)]
                # transform points back to coordinate system 
                corner1 = QPointF(corner1rotated[0] + point4.x(),corner1rotated[1] + point4.y())
                corner2 = QPointF(corner2rotated[0] + point4.x(),corner2rotated[1] + point4.y())
                #create path
                path1.moveTo(point4)
                path1.lineTo(corner1)
                path1.lineTo(corner2)
                path1.lineTo(point4)
                 
                # ARROW3:
                # get points relativ to point2
                corner1 = [point6.x() + w/16, point6.y() + h/8]
                corner1rel = [corner1[0] - point6.x(), corner1[1] - point6.y()]
                corner2 = [point6.x() - w/16, point6.y() + h/8]
                corner2rel = [corner2[0] - point6.x(), corner2[1] - point6.y()]
                # rotate points
                corner1rotated = [corner1rel[0] * math.cos(alpha) - corner1rel[1] * math.sin(alpha), corner1rel[0] * math.sin(alpha) + corner1rel[1] * math.cos(alpha)]
                corner2rotated = [corner2rel[0] * math.cos(alpha) - corner2rel[1] * math.sin(alpha), corner2rel[0] * math.sin(alpha) + corner2rel[1] * math.cos(alpha)]
                # transform points back to coordinate system 
                corner1 = QPointF(corner1rotated[0] + point6.x(),corner1rotated[1] + point6.y())
                corner2 = QPointF(corner2rotated[0] + point6.x(),corner2rotated[1] + point6.y())
                #create path
                path1.moveTo(point6)
                path1.lineTo(corner1)
                path1.lineTo(corner2)
                path1.lineTo(point6)
                 
                # ARROW4:
                # get points relativ to point2
                corner1 = [point8.x() + w/16, point8.y() - h/8]
                corner1rel = [corner1[0] - point8.x(), corner1[1] - point8.y()]
                corner2 = [point8.x() - w/16, point8.y() - h/8]
                corner2rel = [corner2[0] - point8.x(), corner2[1] - point8.y()]
                # rotate points
                corner1rotated = [corner1rel[0] * math.cos(-alpha) - corner1rel[1] * math.sin(-alpha), corner1rel[0] * math.sin(-alpha) + corner1rel[1] * math.cos(-alpha)]
                corner2rotated = [corner2rel[0] * math.cos(-alpha) - corner2rel[1] * math.sin(-alpha), corner2rel[0] * math.sin(-alpha) + corner2rel[1] * math.cos(-alpha)]
                # transform points back to coordinate system
                corner1 = QPointF(corner1rotated[0] + point8.x(),corner1rotated[1] + point8.y())
                corner2 = QPointF(corner2rotated[0] + point8.x(),corner2rotated[1] + point8.y())
                #create path
                path1.moveTo(point8)
                path1.lineTo(corner1)
                path1.lineTo(corner2)
                path1.lineTo(point8)
     
                # paint arrows
                p.setPen(Qt.NoPen)
                p.fillPath(path1, QBrush(QColor("black")))
                p.fillPath(path2, QBrush(QColor("black")))
                p.fillPath(path3, QBrush(QColor("black")))
                p.fillPath(path4, QBrush(QColor("black")))
        self.canvas.render(p, self.rect)

    def setCenter(self, point):
        self.center = point
        pt = self.toCanvasCoordinates(point)
        self.setPos(pt)
    
    def setPenWidth(self, width):
        self.penWidth = width
        
    def setColor(self, color):
        self.color = color
    
    def setWidth(self, width):
        self.width = width
        #topLeft = QPointF(-width/2,self.height/2)
        #bottomRight = QPointF(width/2,-self.height/2)
        #self.rect = QRectF(topLeft,bottomRight)
    
    def setHeight(self, height):
        self.height = height
        #topLeft = QPointF(-self.width/2,self.height/2)
        #bottomRight = QPointF(self.width/2,-self.height/2)
        #self.rect = QRectF(topLeft,bottomRight)
        
    def reset(self):
        self.hideMeOnCanvas()
    
    def updatePosition(self):
        self.setCenter(self.center)
