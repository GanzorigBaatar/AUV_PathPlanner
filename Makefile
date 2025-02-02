#/***************************************************************************
# pathPlanner
#
# Tool to set waypoints on map.
#                             -------------------
#        begin                : 2014-04-02
#        copyright            : (C) 2014 by Fraunhofer AST Ilmenau
#        email                : daniel.grabolle@iosb-ast.fraunhofer.de
# ***************************************************************************/
#
#/***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# ***************************************************************************/

# CONFIGURATION
PLUGIN_UPLOAD = $(CURDIR)/plugin_upload.py

# QGISDIR=.qgis3
QGISDIR=C:/Users/bar/AppData/Roaming/QGIS/QGIS3
# Makefile for a PyQGIS plugin

# translation
SOURCES = pathplanner.py ui_pathplanner.py __init__.py pathplannerdialog.py
#TRANSLATIONS = i18n/pathplanner_en.ts
TRANSLATIONS =

# global

PLUGINNAME = PathPlanner_3

PY_FILES = pathplanner.py pathplannerdialog.py __init__.py

#EXTRAS = :/icons/compass.png metadata.txt

EXTRAS = $(QGISDIR)/profiles/default/python/plugins/PathPlanner_3/icons/compass.png metadata.txt

UI_FILES = ui_pathplanner.py

# RESOURCE_FILES = resources.py
RESOURCE_FILES = resources.qrc

HELP = help/build/html

default: compile

compile: $(UI_FILES) $(RESOURCE_FILES)

%_rc.py : %.qrc
	pyrcc5 -o $*.py  $<

%.py : %.ui
	pyuic5 -o $@ $<

%.qm : %.ts
	lrelease $<

# The deploy  target only works on unix like operating system where
# the Python plugin directory is located at:
# $HOME/$(QGISDIR)/profiles/default/python/plugins/

PLUGINDIR=$(QGISDIR)/profiles/default/python/plugins/
deploy: compile doc transcompile
	mkdir -p $(PLUGINDIR)/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(PLUGINDIR)/$(PLUGINNAME)
	cp -vf $(UI_FILES) $(PLUGINDIR)/$(PLUGINNAME)
	cp -vf $(RESOURCE_FILES) $(PLUGINDIR)/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(PLUGINDIR)/$(PLUGINNAME)
	cp -vfr i18n $(PLUGINDIR)/$(PLUGINNAME)
	cp -vfr $(HELP) $(PLUGINDIR)/$(PLUGINNAME)/help

# The dclean target removes compiled python files from plugin directory
# also delets any .svn entry
dclean:
	find $(PLUGINDIR)/$(PLUGINNAME)/$(PLUGINNAME) -iname "*.pyc" -delete
	find $(PLUGINDIR)/$(PLUGINNAME)/$(PLUGINNAME) -iname ".svn" -prune -exec rm -Rf {} \;

# The derase deletes deployed plugin
derase:
	rm -Rf $(PLUGINDIR)/$(PLUGINNAME)

# The zip target deploys the plugin and creates a zip file with the deployed
# content. You can then upload the zip file on http://plugins.qgis.org
zip: deploy dclean
	rm -f $(PLUGINNAME).zip
	cd $(PLUGINDIR)/$(PLUGINNAME); zip -9r $(CURDIR)/$(PLUGINNAME).zip $(PLUGINNAME)

# Create a zip package of the plugin named $(PLUGINNAME).zip.
# This requires use of git (your plugin development directory must be a
# git repository).
# To use, pass a valid commit or tag as follows:
#   make package VERSION=Version_0.3.2
package: compile
		rm -f $(PLUGINNAME).zip
		git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip $(VERSION)
		echo "Created package: $(PLUGINNAME).zip"

upload: zip
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip

# transup
# update .ts translation files
transup:
	pylupdate4 Makefile

# transcompile
# compile translation files into .qm binary format
transcompile: $(TRANSLATIONS:.ts=.qm)

# transclean
# deletes all .qm files
transclean:
	rm -f i18n/*.qm

clean:
	rm $(UI_FILES) $(RESOURCE_FILES)

# build documentation with sphinx
doc:
	cd help; make html
