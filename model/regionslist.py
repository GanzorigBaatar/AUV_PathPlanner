from qgis.PyQt.QtCore import QAbstractListModel, QAbstractTableModel, QModelIndex, Qt, pyqtSignal

from ..model.point import Point

class Region(QAbstractTableModel):
    regionModelChanged = pyqtSignal()

    def __init__(self):
        # logging.debug("REGION declaration called")
        QAbstractTableModel.__init__(self)
        # self.parentMission = parentMission
        self.pointsregion = list()
        # removed random id-sequence uuid
        # self.name = "area-" + str(uuid.uuid1())
        self.name = "area-" + str(0)
        self.parentMission = None
        self.headerLabels = ["lon", "lat"]
        self.description = ''
        self.type = "restricted"

    # ListModel - begin
    def rowCount(self, parent=QModelIndex()):
        return len(self.pointsregion)

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role):
        if not index.isValid():
            return None
        if role in [Qt.DisplayRole, Qt.EditRole]:
            from ..config import coord_decimals
            # logging.debug(index.row())
            point = self.pointsregion[index.row()]
            if index.column() == 0:
                return "%.*f" % (coord_decimals, point.getX())
            if index.column() == 1:
                return "%.*f" % (coord_decimals, point.getY())
            return "{}-{}".format(index.row(), index.column())
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid():
            row = index.row()
            col = index.column()
            if col == 0:
                self.pointsregion[row].setX(float(value))
            if col == 1:
                self.pointsregion[row].setY(float(value))
            self.dataChanged.emit(index, index, (Qt.DisplayRole,))
            return True
        return False

    def flags(self, modelIndex):
        ans = QAbstractTableModel.flags(self, modelIndex)
        ans |= Qt.ItemIsEditable
        ans |= Qt.ItemIsEnabled
        #return
        return ans

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and 0 <= section < len(self.headerLabels):
            return self.headerLabels[section]
        return QAbstractTableModel.headerData(self, section, orientation, role)

    def setData(self, index, value, role):
        idx = index.row()
        elem = index.column()

        if isinstance(value, str):
            try:
                v = float(value)
            except (TypeError, ValueError):
                return False
            if elem == 0:  # lat
                self.pointsregion[idx].setX(v)
            if elem == 1:  # lon
                self.pointsregion[idx].setY(v)
            # if elem == 2:  # depth
            #   self.pointsregion[idx].setDepth(v)
            # logging.debug(value)
            self.regionModelChanged.emit()
            return True
        else:
            return False

    # TableModel - end

    def getType(self):
        return self.type

    def setType(self, type):
        self.type = type

    def addPoint(self, point, index=None):
        if not isinstance(point, Point):
            raise ValueError('Parameter is not from class Point.')
        if index is not None:
            self.pointsregion.insert(index, point)
        else:
            self.pointsregion.append(point)
        ##self.emit(SIGNAL("modelReset()"))
        self.regionModelChanged.emit()
        self.modelReset.emit()

    def removePointAt(self, index):
        if len(self.pointsregion) > index:
            del self.pointsregion[index]
            ##self.emit(SIGNAL("modelReset()"))
            self.regionModelChanged.emit()
            # self.properties.propertiesChanged.emit()
            self.modelReset.emit()

    def movePoint(self, oldIndex, newIndex):
        if oldIndex < 0 or newIndex < 0 or oldIndex >= len(self.pointsregion) or newIndex >= len(self.pointsregion):
            return
        self.pointsregion.insert(newIndex, self.pointsregion.pop(oldIndex))
        ##self.emit(SIGNAL("modelReset()"))
        self.regionModelChanged.emit()
        self.modelReset.emit()

    def setParentMission(self, mission):
        from .mission import Mission
        if isinstance(mission, Mission) or mission is None:
            self.parentMission = mission
        else:
            raise ValueError("Illegal argument type")

    def getParentMission(self):
        return self.parentMission

    def getPointAt(self, index):
        if index < len(self.pointsregion):
            return self.pointsregion[index]
        return None

    def indexOfPoint(self, point):
        return self.pointsregion.index(point)

    def numPoints(self):
        return self.countPoints()

    def countPoints(self):
        return len(self.pointsregion)

    def setName(self, name):
        # TODO Parameterwert validieren
        self.name = name

    def getName(self):
        return self.name

    def getDescription(self):
        return self.description

    def setDescription(self, description):
        self.description = description

    def clean(self):
        del self.pointsregion[:]
        #self.emit(SIGNAL("modelReset()"))
        ##self.modelReset.emit()
        self.regionModelChanged.emit()
        self.modelReset.emit()

    def __del__(self):
        self.clean()

class RegionsList(QAbstractListModel):
    modelChanged = pyqtSignal()

    def __init__(self):
        # logging.debug("RegionsList declaration called")
        QAbstractListModel.__init__(self)
        region = Region()
        region.regionModelChanged.connect(self.modelChanged)
        self.regionsItems = [region]  # list()
        self.regionsItems = list()

    # ListModel - begin
    def rowCount(self, parent=QModelIndex()):
        return len(self.regionsItems)

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            item = self.regionsItems[index.row()]
            return "{} ({})".format(item.getName(), item.getType())
        else:
            return None

    # ListModel - end

    def addItem(self, item):
        if isinstance(item, Region):
            item.regionModelChanged.connect(self.modelChanged)
            self.regionsItems.append(item)
            ##self.emit(SIGNAL("modelReset()"))
            self.modelChanged.emit()
            self.modelReset.emit()

    def removeItem(self, item):
        self.regionsItems.remove(item)
        ##self.emit(SIGNAL("modelReset()"))
        self.modelChanged.emit()
        # self.properties.propertiesChanged.emit()
        self.modelReset.emit()

    def removeItemAt(self, index):
        del self.regionsItems[index]
        ##self.emit(SIGNAL("modelReset()"))
        self.modelChanged.emit()
        # self.properties.propertiesChanged.emit()
        self.modelReset.emit()

    def countItems(self):
        return len(self.regionsItems)

    def getItemAt(self, index):
        return self.regionsItems[index]

    def clean(self):
        del self.regionsItems[:]
        ##self.emit(SIGNAL("modelReset()"))
        self.modelChanged.emit()
        self.modelReset.emit()

    def __del__(self):
        self.clean()