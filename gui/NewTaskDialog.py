from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt import uic
from configparser import ConfigParser
import os

from qgis.core import QgsMessageLog, Qgis
from ..config import get_configuration

class NewTaskDialog(QDialog):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        path = os.path.dirname(os.path.abspath(__file__))

        self.ui = uic.loadUi(os.path.join(path, "NewTaskDialog.ui"), self)
        self.ui.buttons.accepted.connect(self.accept)
        self.ui.buttons.rejected.connect(self.reject)

        config = get_configuration()
        sectionname = 'Tasklist'
        wayp = config.get(sectionname, 'waypoint')
        surv = config.get(sectionname, 'survey')
        circ = config.get(sectionname, 'circle')
        kest = config.get(sectionname, 'keepstation')

        self.ui.typeList.clear()

        if (int(wayp) == 1):
            self.ui.typeList.addItem('Waypoint')
        if (int(surv) == 1):
            self.ui.typeList.addItem('Survey')
        if (int(circ) == 1):
            self.ui.typeList.addItem('Circle')
        if (int(kest) == 1):
            self.ui.typeList.addItem('KeepStation')

        allowedNewTaskTypes = [self.ui.typeList.itemText(i) for i in range(self.ui.typeList.count())]
        QgsMessageLog.logMessage("Allowed types for new tasks are " + str(allowedNewTaskTypes), tag="Pathplanner", level=Qgis.Info)
        # Todo: modify list if necessary
        self.ui.typeList.clear()
        for item in allowedNewTaskTypes:
            self.ui.typeList.addItem(item)

    def setName(self, value):
        self.ui.nameText.setText(value)

    def getName(self):
        return self.ui.nameText.text()

    def getType(self):
        return str(self.ui.typeList.currentText())

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def execNewTask(parent=None, name="task"):
        dialog = NewTaskDialog(parent)
        dialog.setName(name)
        result = dialog.exec_()
        return dialog.getName(), dialog.getType(), result == QDialog.Accepted

