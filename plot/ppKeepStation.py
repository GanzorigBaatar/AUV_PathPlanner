# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pathPlanner
                                 A QGIS plugin

                              -------------------
        begin                : 2014-03-14
        copyright            : (C) 2014 by Fraunhofer AST Ilmenau
        email                : ganzorig.baatar@iosb-ast.fraunhofer.de
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
from qgis.PyQt.QtGui import QPolygonF
from qgis.PyQt.QtCore import QLineF
from qgis.PyQt.QtCore import QPointF


from qgis.core import QgsPoint
from qgis.core import QgsPointXY
from qgis.gui import QgsMapCanvasItem
from qgis.gui import QgsVertexMarker
from qgis.core import Qgis
from qgis.core import QgsUnitTypes
#from qgis.core import QgsMessageLog, Qgis

import math

from ..coordtrans import NedToWgs84

class ppKeepStationMarker(QgsMapCanvasItem):
    def __init__(self, canvas, color, point, innerRadius, outerRadius):
        QgsMapCanvasItem.__init__(self,canvas)
        self.center = QgsPointXY(0, 0)
        self.iconType = QgsVertexMarker.ICON_CROSS
        self.iconSize = 5
        self.color = color
        self.innerRadius = innerRadius
        self.outerRadius = outerRadius
        self.penWidth = 3
        self.canvas = canvas
        self.setCenter(point)

    def setIconType(self, type):
        self.iconType = type

    def setIconSize(self, iconSize):
        self.iconSize = iconSize

    def setCenter(self, point):
        self.center = point
        pt = QPointF(self.toCanvasCoordinates(point))
        self.setPos(pt)

    def setColor(self, color):
        self.color = color

    def setPenWidth(self, width):
        self.penWidth = width

    def paint(self, p, option, widget):  # option and widget belong to an overloaded method, but it only works like this
        s = float((self.iconSize-1)/2)

        pen = QPen(self.color)
        pen.setWidth(self.penWidth)
        p.setPen(pen)

        mapunits = self.canvas.mapUnits()
        # ctx = self.canvas.mapRenderer().rendererContext()  # DEPRECATED API-call
        mapsettings = self.canvas.mapSettings()

        #if mapunits == Qgis.Meters:
        if mapunits == QgsUnitTypes.DistanceMeters:
            for radius in [self.innerRadius, self.outerRadius]:
                radius = round(radius / mapsettings.mapToPixel().mapUnitsPerPixel()  * (math.pi/2))  # ctx.scaleFactor()
                p.drawEllipse(-radius, -radius, 2*radius, 2*radius)

        #elif mapunits == QGis.Degrees:
        elif mapunits == QgsUnitTypes.DistanceDegrees:
            lon = self.center.x()
            lat = self.center.y()
            conv = NedToWgs84(lon_ref=lon, lat_ref=lat)
            for radius in [self.innerRadius, self.outerRadius]:
                p1_lon, p1_lat = conv.convert_(-radius, -radius)
                p2_lon, p2_lat = conv.convert_(radius, radius)
                p.drawEllipse((p1_lat - lat) / mapsettings.mapToPixel().mapUnitsPerPixel(),
                              (p1_lat - lat) / mapsettings.mapToPixel().mapUnitsPerPixel(),
                              (p2_lat - p1_lat) / mapsettings.mapToPixel().mapUnitsPerPixel(),
                              (p2_lat - p1_lat) / mapsettings.mapToPixel().mapUnitsPerPixel())

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

    def updatePosition(self):
        self.setCenter(self.center)
