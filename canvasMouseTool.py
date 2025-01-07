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
 
#from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import QMouseEvent
from qgis.core import *
from qgis.gui import QgsMapTool
from qgis.core import QgsPointXY
from qgis.PyQt.QtCore import QObject, pyqtSignal, pyqtSlot, QEvent, Qt

 
class CanvasMouseTool(QgsMapTool):

    canvasClicked = pyqtSignal(QgsPointXY, Qt.MouseButton)
    mouseMoved = pyqtSignal(QgsPointXY)

    def __init__(self,canvas):
        QgsMapTool.__init__(self, canvas)
 
    def canvasMoveEvent(self, e):
        pnt = QgsPointXY(self.toMapCoordinates(e.pos()))
        self.mouseMoved.emit(pnt)
 
    def canvasPressEvent(self,e):
        pnt = QgsPointXY(self.toMapCoordinates(e.pos()))
        self.canvasClicked.emit(pnt, e.button())
 
    def canvasReleaseEvent(self,e):
        pnt = QgsPointXY(self.toMapCoordinates(e.pos()))
        #self.mouseReleased.emit(pnt) # vielleicht braucht es auch den button, falls das event bei allen buttons erzeugt wird
