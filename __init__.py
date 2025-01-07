# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pathPlanner
                                 A QGIS plugin
 Tool to set waypoints on map.
                             -------------------
        begin                : 2014-04-02
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
 This script initializes the plugin, making it known to QGIS.
"""
from __future__ import absolute_import

def classFactory(iface):
    # load pathPlanner class from file pathPlanner
    from .pathplanner import pathPlanner
    return pathPlanner(iface)
