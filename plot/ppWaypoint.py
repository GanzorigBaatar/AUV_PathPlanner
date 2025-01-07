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

from qgis.PyQt.QtGui import QPen
from qgis.PyQt.QtGui import QPainter
from qgis.PyQt.QtCore import QLineF
from qgis.PyQt.QtCore import QPointF
from qgis.core import QgsPointXY
from qgis.gui import QgsMapCanvasItem
from qgis.gui import QgsVertexMarker

import math

class ppWaypointMarker(QgsMapCanvasItem):
    def __init__(self, canvas, color):
        QgsMapCanvasItem.__init__(self, canvas)
        self.center = QgsPointXY(0,0)
        self.iconSize = 6
        self.penWidth = 3
        self.color = color
        self.iconType = QgsVertexMarker.ICON_CROSS
        self.arrRadius = 10
        self.canvas = canvas
        self.showArrivalCircle = 0

    def setIconType(self,type):
        self.iconType = type

    def setIconSize(self,iconSize):
        self.iconSize = iconSize

    def setCenter(self,point):
        self.center = point
        pt = QPointF(self.toCanvasCoordinates(point))
        self.setPos(pt)

    def setColor(self,color):
        self.color = color
 
    def setPenWidth(self,width):
        self.penWidth = width

    def setArrivalRadius(self, aradius):
        self.arrRadius = float(aradius)

    def setArrivalCircleBool(self, bvalue):
        self.showArrivalCircle = bvalue

    def paint(self,p,option,widget): # option and widget belong to an overloaded method, but it only works like this
        s = float((self.iconSize-1)/2)
        pen = QPen(self.color)
        pen.setWidth(self.penWidth)
        p.setPen(pen)
        mapsettings = self.canvas.mapSettings()

        if self.iconType == QgsVertexMarker.ICON_NONE:
            pass
        elif self.iconType == QgsVertexMarker.ICON_CROSS:
            p.drawLine(QLineF(-s,0,s,0))
            p.drawLine(QLineF(0,-s,0,s))

        elif self.iconType == QgsVertexMarker.ICON_X:
            p.drawLine(QLineF(-s,-s,s,s))
            p.drawLine(QLineF(-s,s,s,-s))
        elif self.iconType == QgsVertexMarker.ICON_BOX:
            p.drawLine(QLineF(-s,-s,s,-s))
            p.drawLine(QLineF(s,-s,s,s))
            p.drawLine(QLineF(s,s,-s,s))
            p.drawLine(QLineF(-s,s,-s,-s))

        if self.showArrivalCircle == 1:
            myradius = round(self.arrRadius / mapsettings.mapToPixel().mapUnitsPerPixel() * (math.pi / 2))  # ctx.scaleFactor()
            p.drawEllipse(-myradius, -myradius, 2 * myradius, 2 * myradius)

    def updatePosition(self):
        self.setCenter(self.center)

    #def boundingRect(self):
    #    s = float(self.iconSize + self.penWidth) / 2.0
    #    return QRectF(-s,-s,2.0*s,2.0*s)
#
# class ppCircleMarker(QgsMapCanvasItem):
#     def __init__(self, canvas, color):
#         QgsMapCanvasItem.__init__(self,canvas)
#         self.center = QgsPoint(0, 0)
#         self.iconType = QgsVertexMarker.ICON_CROSS
#         self.color = color
#         self.radius = 20
#         self.penWidth = 3
#         self.canvas = canvas
#         self.iconSize = 5
#         self.direction = 1  # 1 - clockwise     -1 - counterclockwise
#
#     def setIconType(self,type):
#         self.iconType = type
#
#     def setIconSize(self,iconSize):
#         self.iconSize = iconSize
#
#     def setCenter(self, point):
#         self.center = point
#         pt = QPointF(self.toCanvasCoordinates(point))
#         self.setPos(pt)
#
#     def setRadius(self, radius):
#         self.radius = radius
#
#     def setColor(self, color):
#         self.color = color
#
#     def setPenWidth(self, width):
#         self.penWidth = width
#
#     def paint(self, p, option, widget):  # option and widget belong to an overloaded method, but it only works like this
#         s = float((self.iconSize-1)/2)
#
#         pen = QPen(self.color)
#         pen.setWidth(self.penWidth)
#         p.setPen(pen)
#
#         mapunits = self.canvas.mapUnits()
#         # ctx = self.canvas.mapRenderer().rendererContext()  # DEPRECATED API-call
#         mapsettings = self.canvas.mapSettings()
#
#         if mapunits == QGis.Meters:
#             myradius = self.radius / mapsettings.mapToPixel().mapUnitsPerPixel()  * (math.pi/2)#ctx.scaleFactor()
#             # QgsMessageLog.logMessage("Painting circle: mapunits={}, mapUnitsPerPixel={}, scaleFactor={}, scale={}".format(mapunits, mapsettings.mapToPixel().mapUnitsPerPixel(), ctx.scaleFactor(), self.canvas.scale()), 'Pathplanner', QgsMessageLog.INFO)
#             p.drawEllipse(-myradius, -myradius, 2*myradius, 2*myradius)
#
#             arrowpoint = myradius
#             px = arrowpoint
#             if (self.direction == "Clockwise"):
#                 dir = 1
#             else:
#                 dir = -1
#             arrow = self.drawCircleArrow(px, dir)
#
#             p.save()
#             p.setBrush(self.color)
#             p.drawPolygon(arrow)
#             p.restore()
#
#         elif mapunits == QGis.Degrees:
#             lon = self.center.x()
#             lat = self.center.y()
#             conv = NedToWgs84(lon_ref=lon, lat_ref=lat)
#             p1_lon, p1_lat = conv.convert_(-self.radius, -self.radius)
#             p2_lon, p2_lat = conv.convert_(self.radius, self.radius)
#
#             # QgsMessageLog.logMessage("Painting circle: center={},{}, ul={},{}, radius={}".format(lon, lat, p1_lon, p1_lat, self.radius), 'Pathplanner', QgsMessageLog.INFO)
#             p.drawEllipse((p1_lat - lat) / mapsettings.mapToPixel().mapUnitsPerPixel(),
#                           (p1_lat - lat) / mapsettings.mapToPixel().mapUnitsPerPixel(),
#                           (p2_lat - p1_lat) / mapsettings.mapToPixel().mapUnitsPerPixel(),
#                           (p2_lat - p1_lat) / mapsettings.mapToPixel().mapUnitsPerPixel())
#
#         if self.iconType == QgsVertexMarker.ICON_NONE:
#             pass
#         elif self.iconType == QgsVertexMarker.ICON_CROSS:
#             p.drawLine(QLineF(-s,0,s,0))
#             p.drawLine(QLineF(0,-s,0,s))
#         elif self.iconType == QgsVertexMarker.ICON_X:
#             p.drawLine(QLineF(-s,-s,s,s))
#             p.drawLine(QLineF(-s,s,s,-s))
#         elif self.iconType == QgsVertexMarker.ICON_BOX:
#             p.drawLine(QLineF(-s,-s,s,-s))
#             p.drawLine(QLineF(s,-s,s,s))
#             p.drawLine(QLineF(s,s,-s,s))
#             p.drawLine(QLineF(-s,s,-s,-s))
#
#     def updatePosition(self):
#         self.setCenter(self.center)
#
#     #def boundingRect(self):
#     #    s = self.radius
#     #    if s is None:
#     #        return None
#     #    return QRectF(-s, -s, 2.0*s, 2.0*s)
#
#     def drawCircleArrow(self, px, dir):
#         # px - starting pont of the arrow head
#         # dir - direction of the arrow head (clockwise = 1, counterclockwise = -1
#         k = px / 5  # arrowhead side length
#         alpha = math.atan(k / px)
#         m_2 = k * math.cos(alpha)
#         m = math.sqrt(k ** 2 - m_2 ** 2)
#         g = -2 * m * math.sin(alpha)
#         j = -2 * m * math.cos(alpha)
#         width1 = j/2
#         width2 = -j
#         height1 = k - g / 2
#         height2 = k + g / 2
#         if (dir>0):
#             arrow = QPolygonF([QPointF(-px, 0), QPointF(-px + width2, height2), QPointF(-px + width1, height1)])
#         else:
#             arrow = QPolygonF([QPointF(-px, 0), QPointF(-px + width2, -height2), QPointF(-px + width1, -height1)])
#         arrow.translate(QPointF(0, 0))
#         return arrow
#
#     def setDirection(self, dir):
#         self.direction = dir
#
#
