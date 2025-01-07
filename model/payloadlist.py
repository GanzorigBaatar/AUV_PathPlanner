from qgis.PyQt.QtCore import *
from qgis.PyQt.QtCore import QAbstractListModel
from qgis.core import QgsMessageLog, Qgis

from ..config import get_configuration

class PayloadList(QAbstractListModel):
    modelChanged = pyqtSignal(object)

    def __init__(self):
        #logging.debug("PayloadList declaration called")
        QAbstractListModel.__init__(self)
        config = get_configuration()
        if config != None:
            payloadNum = config.getint('PlannerModel', 'PAYLOAD_CNT')
            pnum = int(payloadNum)
            #logging.debug(pnum)
            self.payloadItems = list()
            for i in range(1, pnum+1):
                name = 'PAYLOAD_' + str(i)
                payload = config.get('PlannerModel', name)
                self.payloadItems.insert(i, payload)
        else:
            QgsMessageLog.logMessage("Configuration file was not found", tag="PathPlanner", level=Qgis.Warning)

        #payload1 = self.config.get('PlannerModel', 'PAYLOAD_1')
        #payload2 = self.config.get('PlannerModel', 'PAYLOAD_2')
        #self.payloadItems = [payload1, payload2]  # list()

    # ListModel - begin
    def rowCount(self, parent=QModelIndex()):
        return len(self.payloadItems)

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            return self.payloadItems[index.row()]
        else:
            return None
    # ListModel - end

    def addItem(self, payloadItem):
        self.payloadItems.append(payloadItem)
        ##self.emit(SIGNAL("modelReset()"))
        self.modelChanged.emit(self)

    def removeItem(self, payloadItem):
        self.payloadItems.remove(payloadItem)
        ##self.emit(SIGNAL("modelReset()"))
        self.modelChanged.emit(self)
        self.properties.propertiesChanged.emit()

    def removeItemAt(self, index):
        del self.payloadItems[index]
        ##self.emit(SIGNAL("modelReset()"))
        self.modelChanged.emit(self)
        self.properties.propertiesChanged.emit()

    def clean(self):
        del self.payloadItems[:]
        ##self.emit(SIGNAL("modelReset()"))
        self.modelChanged.emit(self)

    def __del__(self):
        self.clean()