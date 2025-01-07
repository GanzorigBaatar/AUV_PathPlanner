from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot
from qgis.PyQt.QtCore import QAbstractListModel
from qgis.core import QgsMessageLog
from qgis.core import Qgis
from ..config import get_configuration,get_configuration_json

class taskProperties(QObject):
    propertiesChanged = pyqtSignal()
    speedChanged = pyqtSignal()
    timeChanged = pyqtSignal()

    # meanderChanged = pyqtSignal()

    def __init__(self, _type):
        QObject.__init__(self)
        self.type = _type
        self.description = ''
        self._man_props = {}
        self._gui_props = {}
        self.readDefaultProperties()

    def _get_man_prop(self, prop, default=None):
        """Return a maneuver property or default if it not exists"""
        if prop in self._man_props:
            return self._man_props[prop]
        return default

    def _set_man_prop(self, prop, value):
        """Set a maneuver property regardless if its existence"""
        self._man_props[prop] = value

    def setType(self, _type):
        self.type = _type
        self.readDefaultProperties()

    def readDefaultProperties(self):
        parser = get_configuration()
        p = get_configuration_json()
        self._man_props = p.get_defaults_maneuver(self.type)
        self._gui_props = p.get_defaults_gui(self.type)

        self.timeout = parser.get(self.type, 'Timeout')
        self.priority = parser.get(self.type, 'Priority')
        self.speed = parser.get(self.type, 'Speed')
        self.trackControllerMode = parser.get(self.type, 'TrackControllerMode')
        self.depthControllerMode = parser.get(self.type, 'DepthControllerMode')
        self.arrivalRadius = parser.get(self.type, 'ArrivalRadius')
        self.depthHeightInvalid = parser.get(self.type, 'DepthIfHeightInvalid')
        self.distToLOS = parser.get(self.type, 'MaxDistanceToSwitchToLOS')
        self.heightIterations = parser.get(self.type, 'MaxNumberOfInvalidHeightIterations')
        self.heightOverGround = parser.get(self.type, 'HeightOverGroundValue')
        self.lookAheadDistance = parser.get(self.type, 'LookaheadDistance')
        self.constantDepth = parser.get(self.type, 'ConstantDepthValue')
        # self.trackControllerValue = parser.get(self.type, 'TrackControllerValue')

        self.pitchControl = 0
        self.pitchSetPoint = 0
        self.surveyType = None
        self.swath = 0
        self.oddLineSpacingFactor = 0
        self.ssrange = 0
        self.nadirGap = 0
        self.distFactor = 0
        self.startPosition = 'NorthEast'
        self.rotationAngle = 0
        self.eastWestExtent = 0
        self.northSouthExtent = 0
        self.time = 0
        self.distance = 0
        self.supressPropulsion = 0

        if self.type == 'waypoint':
            self.pitchControl = parser.get(self.type, 'PitchControl')
            self.pitchSetPoint = parser.get(self.type, 'PitchSetPoint')

            self.showArrivalCircleWpt = parser.get(self.type, 'ShowArrivalCircle')
            self.selectedPointIndex = -1

        elif self.type == 'circle':
            self.pitchControl = parser.get(self.type, 'PitchControl')
            self.pitchSetPoint = parser.get(self.type, 'PitchSetPoint')
            # supress propulsion?

        elif self.type == 'survey':
            self.surveyType = parser.get(self.type, 'SurveyType')
            # self.rotationAngle = parser.get(self.type, 'RotationAngle')
            self.swath = parser.get(self.type, 'Swath')
            self.startPosition = parser.get(self.type, 'StartPosition')
            self.oddLineSpacingFactor = parser.get(self.type, 'OddLineSpacingFactor')

            self.ssrange = parser.get(self.type, 'SideScanRange')
            self.nadirGap = parser.get(self.type, 'NadirGap')
            self.distFactor = parser.get(self.type, 'DistanceFactor')

            self.showArrivalCircleSrv = parser.get(self.type, 'ShowArrivalCircle')

        self.description = ''

    # survey and waypoint:
    def setTime(self, time):
        self.time = time
        self.timeChanged.emit()

    def setTimeout(self, timeout):
        self.timeout = timeout
        # self.propertiesChanged.emit()

    def setDescription(self, description):
        self.description = description
        # self.propertiesChanged.emit()

    def setPriority(self, priority: int):
        self.priority = priority
        # self.propertiesChanged.emit()

    def setSpeed(self, speed):
        self.speed = speed
        self.speedChanged.emit()

    def setTrackControllerMode(self, trackControllerMode):
        self.trackControllerMode = trackControllerMode
        # self.propertiesChanged.emit()

    def setDepthControllerMode(self, depthControllerMode):
        self.depthControllerMode = depthControllerMode
        # self.propertiesChanged.emit()

    def setArrivalRadius(self, arrivalRadius):
        self.arrivalRadius = arrivalRadius
        # self.propertiesChanged.emit()

    def setLookAheadDistance(self, lookAheadDistance):
        self.lookAheadDistance = lookAheadDistance
        # self.propertiesChanged.emit()

    def setDistToLOS(self, distToLOS):
        self.distToLOS = distToLOS
        # self.propertiesChanged.emit()

    def setHeightIterations(self, heightIterations):
        self.heightIterations = heightIterations
        # self.propertiesChanged.emit()

    def setDepthHeightInvalid(self, depthHeightInvalid):
        self.depthHeightInvalid = depthHeightInvalid
        # self.propertiesChanged.emit()

    def setHeightOverGround(self, heightOverGround):
        self.heightOverGround = heightOverGround
        # self.propertiesChanged.emit()

    def setConstantDepth(self, constantDepth):
        self.depth = constantDepth
        self.constantDepth = constantDepth
        # self.propertiesChanged.emit()

    def getTime(self):
        return self.time

    def getTimeout(self):
        return self.timeout

    def getDescription(self):
        return self.description

    def getPriority(self):
        return self.priority

    def getSpeed(self):
        return self.speed

    def getTrackControllerMode(self):
        return self.trackControllerMode

    def getDepthControllerMode(self):
        return self.depthControllerMode

    def getArrivalRadius(self):
        return self.arrivalRadius

    def getLookAheadDistance(self):
        return self.lookAheadDistance

    def getDistToLOS(self):
        return self.distToLOS

    def getHeightIterations(self):
        return self.heightIterations

    def getDepthHeightInvalid(self):
        return self.depthHeightInvalid

    def getHeightOverGround(self):
        return self.heightOverGround

    def getConstantDepth(self):
        return self.constantDepth

    # def getTrackControllerValue(self):
    #    return self.trackControllerValue

    # only waypoint:
    def setPitchControl(self, pitchControl):
        self.pitchControl = pitchControl
        # self.propertiesChanged.emit()

    def setPitchSetPoint(self, pitchSetPoint):
        self.pitchSetPoint = pitchSetPoint
        # self.propertiesChanged.emit()

    def setDistance(self, distance):
        self.distance = distance
        # logging.debug("setDistance set: {}".format(distance))
        # self.propertiesChanged.emit()

    def getDistance(self):
        return self.distance

    def getPitchControl(self):
        return self.pitchControl

    def getPitchSetPoint(self):
        return self.pitchSetPoint

    def setSupressPropulsion(self, supProp):
        self.supressPropulsion = supProp
        # self.propertiesChanged.emit()

    def getSupressPropulsion(self):
        return self.supressPropulsion

    # only survey:
    def setSurveyType(self, surveyType):
        self.surveyType = surveyType
        # self.propertiesChanged.emit()

    def setEastWestExtent(self, extent):
        self.eastWestExtent = extent
        #self.propertiesChanged.emit()

    def setNorthSouthExtent(self, extent):
        self.northSouthExtent = extent
        #self.propertiesChanged.emit()

    def setRotationAngle(self, angle):
        try:
            self.rotationAngle = float(angle)
        except:
            pass
        # self.propertiesChanged.emit()

    def setStartPosition(self, pos):
        self.startPosition = pos
        # self.propertiesChanged.emit()

    def setSwath(self, swath):
        self.swath = float(swath)
        # self.propertiesChanged.emit()

    def setOddLineSpacingFactor(self, factor):
        self.oddLineSpacingFactor = factor
        # self.propertiesChanged.emit()

    def setSideScanRange(self, range):
        self.ssrange = float(range)

    def setNadirGap(self, nadir):
        self.nadirGap = float(nadir)

    def setDistanceFactor(self, factor):
        self.distFactor = float(factor)

    def setSelectedPoint(self, index):
        self.selectedPointIndex = index

    def getSurveyType(self):
        return self.surveyType

    def getEastWestExtent(self):
        # return int(self.eastWestExtent)
        return self.eastWestExtent

    def getNorthSouthExtent(self):
        # return int(self.northSouthExtent)
        return self.northSouthExtent

    def getRotationAngle(self):
        return self.rotationAngle

    def getStartPosition(self):
        return self.startPosition

    def getSwath(self):
        return float(self.swath)

    def getOddLineSpacingFactor(self):
        return self.oddLineSpacingFactor

    def getSideScanRange(self):
        return self.ssrange

    def getNadirGap(self):
        return self.nadirGap

    def getDistanceFactor(self):
        return self.distFactor

    def getDepth(self):
        # return self.depth
        return self.constantDepth

    def getArrivalCircleBoolWpt(self):
        return int(self.showArrivalCircleWpt)

    def getArrivalCircleBoolSrv(self):
        return int(self.showArrivalCircleSrv)

    def getSelectedPointIndex(self):
        return int(self.selectedPointIndex)
