import os, traceback
from qgis.PyQt import QtGui
from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QFileDialog

from .XmlFileStorage import XmlFileStorage
from .jsonFileStorage import JsonFileStorage

from .storageutils import storageutils

# ConSys mission file support
try:
    from .missFileStorage import MissFileStorage
    consysSupport = True
except:
    consysSupport = False


# MOOS-IvP behavior file support
try:
    from .bhvFileStorage import BhvFileStorage
    bhvSupport = True
except:
    bhvSupport = False

def storage_load(model):
    try:
        fileStorage = XmlFileStorage(model)
        return fileStorage.load()
    except:
        QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)
        return None

# def storage_save1(model):
#     try:
#         fileStorage = XmlFileStorage(model)
#         return fileStorage.save1()
#     except:
#         QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)
#         return None

def storage_save(model):
    try:
        saveFileFilter = "Mission xml (*.xml);;"
        if consysSupport:
            saveFileFilter += "Mission file (*.miss);;"
            saveFileFilter += "JSON mission file (*.jmiss);;"
        if bhvSupport:
            saveFileFilter += "MOOS-IvP behavior file (*.bhv);;"
        filename, saveFileFilter = QFileDialog.getSaveFileName(None,
                                                               "Save Mission",
                                                               storageutils.getStoragePath(None),
                                                               saveFileFilter,
                                                               "Mission xml (*.xml)")
        if not filename:
            return None
        QgsMessageLog.logMessage("Saving mission as %s..." % filename, tag="Pathplanner", level=Qgis.Info)
        if saveFileFilter == "Mission file (*.miss)":
            fileStorage = XmlFileStorage(model)
            missFileStorage = MissFileStorage(fileStorage)
            xData = fileStorage.getXML()
            missionNames = fileStorage.getMissionNames(xData)
            for i, missionName in enumerate(missionNames):
                missionFilename = filename[:-5] + '.miss'  # + str(i) + '.miss'
                data = missFileStorage.saveAsMiss(xData, i)
                with open(missionFilename, "w") as f:
                    data.write(f)
                    f.close()
            return filename
        elif saveFileFilter == "Mission xml (*.xml)":
            fileStorage = XmlFileStorage(model)
            return fileStorage.save(filename)
        elif saveFileFilter == "JSON mission file (*.jmiss)":
            fileStorage = JsonFileStorage(model)
            return fileStorage.save(filename)
        elif saveFileFilter == "MOOS-IvP behavior file (*.bhv)":
            fileStorage = XmlFileStorage(model)
            bhvFileStorage = BhvFileStorage(fileStorage)
            xData = fileStorage.getXML()
            missionFile = os.path.basename(filename)
            (missionFileWoExt, missionFileExt) = os.path.splitext(missionFile)
            missionDir = os.path.dirname(filename)
            missionNames = fileStorage.getMissionNames(xData)
            # Allow only a single mission
            if len(missionNames) != 1:
                msg_box = QtGui.QMessageBox()
                msg_box.setIcon(QtGui.QMessageBox.Warning)
                msg_box.setWindowTitle("Behavior File Write Error")
                if len(missionNames) > 1:
                    msg_box.setText("Only a single mission can be saved to file, please remove other missions. Currenly found:\n"+'\n'.join(missionNames))
                else:
                    msg_box.setText("No mission is defined right now, save request ignored.")
                msg_box.exec_()
                return None
            QgsMessageLog.logMessage("Saving mission file %s/%s." % (missionDir, missionFileWoExt),
                                     tag="Pathplanner", level=Qgis.Critical)
            if not bhvFileStorage.saveAsBhv(xData, 0, missionDir, missionFileWoExt):
                QgsMessageLog.logMessage("Error saving mission %s to file in %s!" % (missionFileWoExt, missionDir),
                                         tag="Pathplanner", level=Qgis.Critical)
            #for i, missionName in enumerate(missionNames):
            #    if not bhvFileStorage.saveAsBhv(xData, i, missionDir, missionName):
            #        QgsMessageLog.logMessage("Error saving mission %s to file in %s!" % (missionName, missionDir),
            #                                 tag="Pathplanner", level=Qgis.Critical)
            return filename

        QgsMessageLog.logMessage("Saving mission using type %s is not yet supported!" % saveFileFilter, tag="Pathplanner",
                                     level=Qgis.Critical)
        return None
    except:
        QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)
        return None