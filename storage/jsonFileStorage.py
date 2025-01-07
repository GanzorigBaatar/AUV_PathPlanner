import traceback
import os
import json

from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QFileDialog

from ..model import *
from ..config import get_configuration
from ..model.pathplannermodel2 import PathPlannerModel2
from .storageutils import storageutils


class JsonFileStorage:
    def __init__(self, model):
        if type(model) is not PathPlannerModel2:
            raise ValueError("XmlFileStorage: model parameter has wrong type.")
        self.data_model = model
        self.errorLog = list()
    
    def clearErrors(self):
        del self.errorLog[:]
        
    def hasErrors(self):
        return len(self.errorLog) > 0
    
    def getErrors(self):
        return self.errorLog
    
    def addError(self, text):
        self.errorLog.append(text)
        
    def load(self, filename=None):
        if not filename:
            filename = QFileDialog.getOpenFileName(None, "Load Mission",
                                                         storageutils.getStoragePath(None), "JSON mission file (*.jmiss)")

        if filename[0]:
            filename = self.loadFileContent(filename[0])
        return filename

    def save(self, filename):
        try:
            with open(filename, 'w') as f:
                json.dump(self.dict(), f, indent=2)
                f.close()
                return filename
        except:
            QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)

        return None

    def dict(self):
        if not self.data_model:
            return None

        missions = []

        missionCount = self.data_model.countMissions()
        index = 0
        while index < missionCount:
            mission = self.data_model.getMission(index)
            missionCRS = mission.getCRS()

            mission_dict = {
                "id": mission.getMissionID(),
                "name": mission.getName(),
                "missionTimeout": mission.getTotalTimeOut(),
                "vehicle": mission.getVehicleName(),
                "description": mission.getDescription(),
                "crs": {
                    "crs_id": missionCRS.authid(),
                    "proj4": missionCRS.toProj()
                },
                "properties": {
                    "timeoutFactor": mission.getTimeoutFactor(),
                    "taskTimeoutAction": mission.getTaskTimeoutAction(),
                    "totalDistance": mission.getTotalDistance(),
                    "totalDuration": mission.getTotalTime(),
                    "useHoGLimit": mission.getUseHoGLimit(),
                    "hoGLimit": mission.getHoGLimit(),
                    "useDepthLimit": mission.getUseDepthLimit(),
                    "depthLimit": mission.getDepthLimit(),
                    "minimumHeight": mission.getMinimumHeight()

                }
            }

            # sabuvis extensions
            if get_configuration().plannerType == 'sabuvis':
                try:
                    mission_dict["sabuvis_properties"] = {
                        "depthMode": mission.getDepthMode(),
                        "propellerMode": mission.getPropellerMode()
                    }
                except:
                    QgsMessageLog.logMessage("error writing SABUVIS XML file settings!", tag="Pathplanner", level=Qgis.Critical)
                    pass

            mission_dict["regionslist"] = []
            regionsList = mission.getRegionsList()
            if not regionsList:
                continue
            numOfRegions = regionsList.countItems()
            regionIndex = 0
            while regionIndex < numOfRegions:
                region = regionsList.getItemAt(regionIndex)
                region_dict = {
                    "type": region.getType(),
                    "points": [pt.getDictXYZ() for pt in region.pointsregion]
                }
                mission_dict["regionslist"].append(region_dict)
                regionIndex = regionIndex + 1

            mission_dict["tasklist"] = {}

            taskList = mission.getTaskList()
            if not taskList:
                continue
            for task in taskList:
                # recompute task timeout
                task.computeTaskTimeout()

                taskType = task.type()
                properties = task.getProperties()
                task_dict = {
                    # "name": task.getName(), #  not needed, is key of dict
                    "type": task.type(),
                    "description": properties.getDescription()
                }
                
                if taskType == 'waypoint' or taskType == 'survey' or taskType == 'circle':
                    task_dict["speed"] = properties.getSpeed()
                    task_dict["time"] = properties.getTime()
                    task_dict["timeout"] = properties.getTimeout()
                    task_dict["priority"] = properties.getPriority()
                    task_dict["depthControllerMode"] = properties.getDepthControllerMode()
                    task_dict["arrivalRadius"] = properties.getArrivalRadius()
                    task_dict["lookAheadDistance"] = properties.getLookAheadDistance()
                    task_dict["maxDistanceToSwitchToLOS"] = properties.getDistToLOS()
                    task_dict["trackControllerMode"] = properties.getTrackControllerMode()
                    task_dict["invalidHeightIterations"] = properties.getHeightIterations()
                    task_dict["depthIfHeightInvalid"] = properties.getDepthHeightInvalid()
                    task_dict["heightOverGround"] = properties.getHeightOverGround()
                    task_dict["constantDepth"] = properties.getConstantDepth()
                    task_dict["newTrackControllerMode"] = True

                if taskType == 'waypoint':
                    task_dict["distance"] = properties.getDistance()
                    task_dict["pitchControl"] = properties.getPitchControl()
                    task_dict["pitchSetPoint"] = properties.getPitchSetPoint()

                if taskType == 'survey':
                    sType = properties.getSurveyType()

                    if (sType == 'BufferedMeander'):
                        ewe = float(properties.getEastWestExtent())
                        ar = float(properties.getArrivalRadius())
                        # Add buffer area to the base survey
                        ewe = ewe + 4 * ar
                        # SurveyType BufferedMeander is not implemented in ConSys yet
                        # so, the BufferedMeander will be saved as Meander
                        #sType = 'Meander'
                    else:
                        ewe = properties.getEastWestExtent()

                    task_dict["surveyType"] = sType
                    task_dict["centerPoint"] = task.getCenterPoint().getDictXYZ()
                    task_dict["point"] = task.getCenterPoint().getDictXYDepth() # needed?
                    task_dict["eastWestExtent"] = ewe
                    task_dict["northSouthExtent"] = properties.getNorthSouthExtent()
                    task_dict["rotationAngle"] = properties.getRotationAngle()
                    task_dict["startPosition"] = properties.getStartPosition()
                    task_dict["swath"] = properties.getSwath()
                    task_dict["oddLineSpacingFactor"] = properties.getOddLineSpacingFactor()
                    task_dict["sideScanRange"] = properties.getSideScanRange()
                    task_dict["nadirGap"] = properties.getNadirGap()
                    task_dict["distanceFactor"] = properties.getDistanceFactor()

                if taskType == 'circle':
                    task_dict["Radius"] = task.getRadius()
                    task_dict["SupressPropulsion"] = properties.getSupressPropulsion()
                    task_dict["RotationDirection"] = task.getRotationDirection()
                    task_dict["CenterPoint"] = task.getPoint().getDictXYDepth()

                if taskType == 'keepstation':
                    task_dict["Speed"] = properties.getSpeed()
                    task_dict["Timeout"] = properties.getTimeout()
                    task_dict["Priority"] = properties.getPriority()
                    task_dict["LookAheadDistance"] = properties.getLookAheadDistance()
                    task_dict["InnerRadius"] = task.getInnerRadius()
                    task_dict["OuterRadius"] = task.getOuterRadius()
                    task_dict["CenterPoint"] = task.getPoint().getDictXYDepth()

                if taskType == "waypoint" or taskType == "circle":
                    task_dict["points"] = [pt.getDictXYDepth() for pt in task.points]

                # Payload activation/deactivation
                payloadDisabledList = task.getDisabledPayload()
                payloadEnabledList = task.getEnabledPayload()

                payloads = {}
                for item in payloadEnabledList:
                    payloads[item] = { "eventAtBegin": "enable", "eventAtEnd": "" }
                for item in payloadDisabledList:
                    payloads[item] = { "eventAtBegin": "disable", "eventAtEnd": "" }
                for item in task.payload_event_at_end:
                    if item not in payloads:
                        payloads[item] = {"eventAtBegin": ""}
                    payloads[item]["eventAtEnd"] = task.payload_event_at_end[item]
                task_dict["payloads"] = payloads

                mission_dict["tasklist"][task.getName()] = task_dict
            index += 1
            missions.append(mission_dict)
        return {"version": 1, "missions": missions}
    
    def convertToFloat(self, var, default, name):
        try:
            return float(var)
        except:
            self.addError("Variable {} is not of class float, setting to default value {}.".format(name, default))
            return default
    
    def convertToInt(self, var, default, name):
        try:
            return int(var)
        except:
            self.addError("Variable {} is not of class int, setting to default value {}.".format(name, default))
            return default

    def convertToBool(self, var, default, name):
        try:
            return var.lower() == "true"
        except:
            self.addError("Variable {} is not of class int, setting to default value {}.".format(name, default))
            return default

    def convertToString(self, var, default, name):
        try:
            return str(var)
        except:
            self.addError("Variable {} is not of class string, setting to default value {}.".format(name, default))
            return default

    def _load_v1(self, data):
        mission = None
        for xmlMission in data["missions"]:
            missionName = xmlMission['name']
            QgsMessageLog.logMessage("Found mission %s" % missionName, tag="Pathplanner", level=Qgis.Info)

            xCrs = xmlMission.getElementsByTagName('crs')[0]
            xCrsID = xCrs.getElementsByTagName('id')[0]
            xCrsProj4 = xCrs.getElementsByTagName('proj4')[0]
            id = storageutils.getXmlNodeText(xCrsID)
            proj4 = storageutils.getXmlNodeText(xCrsProj4)
            if Qgis.QGIS_VERSION_INT < 31400:
                missionCRS = QgsCoordinateReferenceSystem()
                missionCRS.createFromProj(proj4)
            else:
                missionCRS = QgsCoordinateReferenceSystem("PROJ:" + proj4)
            mission = Mission(missionCRS, '')
            # set mission properties
            mission.setName(missionName)
            mission.setDescription(xmlMission.getAttribute('description'))
            mission.setVehicleName(xmlMission.getAttribute('vehicle'))

            xProperties = xmlMission.getElementsByTagName('properties')[0]
            xTimeoutFactor = xProperties.getElementsByTagName('timeoutFactor')[0]
            xTaskTimeoutAction = xProperties.getElementsByTagName('taskTimeoutAction')[0]
            xTotalDistance = xProperties.getElementsByTagName('totalDistance')[0]
            xTotalDuration = xProperties.getElementsByTagName('totalDuration')[0]
            xUseHoGLimit = xProperties.getElementsByTagName('useHoGLimit')[0]
            xUseDepthLimit = xProperties.getElementsByTagName('useDepthLimit')[0]
            try:
                xHoGLimit = xProperties.getElementsByTagName('hoGLimit')[0]
            except:
                xHoGLimit = dom.createElement('fail')
            try:
                xDepthLimit = xProperties.getElementsByTagName('depthLimit')[0]
            except:
                xDepthLimit = dom.createElement('fail')

            timeoutFactor = self.convertToFloat(storageutils.getXmlNodeText(xTimeoutFactor), 1, 'timeoutFactor')
            taskTimeoutAction = self.convertToString(storageutils.getXmlNodeText(xTaskTimeoutAction), 'ABORT',
                                                     'taskTimeoutAction')
            useHoGLimit = self.convertToBool(storageutils.getXmlNodeText(xUseHoGLimit), False, 'useHoGLimit')
            useDepthLimit = self.convertToBool(storageutils.getXmlNodeText(xUseDepthLimit), False, 'useDepthLimit')
            hoGLimit = self.convertToFloat(storageutils.getXmlNodeText(xHoGLimit), 0 if not useHoGLimit else 20000,
                                           'hoGLimit')
            depthLimit = self.convertToFloat(storageutils.getXmlNodeText(xDepthLimit), 0, 'depthLimit')

            mission.setTimeoutFactor(timeoutFactor)
            mission.setTaskTimeoutAction(taskTimeoutAction)
            mission.setUseHoGLimit(useHoGLimit)
            mission.setUseDepthLimit(useDepthLimit)
            mission.setHoGLimit(hoGLimit)
            mission.setDepthLimit(depthLimit)

            try:
                xMinimumHeight = xProperties.getElementsByTagName('minimumHeight')[0]
                minimumHeight = self.convertToFloat(storageutils.getXmlNodeText(xMinimumHeight), 0, 'minimumHeight')
            except:
                xMinimumHeight = dom.createElement('fail')
                minimumHeight = 0.0
            mission.setMinimumHeight(minimumHeight)

            # sabuvis extensions
            if get_configuration().plannerType == 'sabuvis':
                try:
                    sProps = xmlMission.getElementsByTagName('sabuvis_properties')[0]
                    mission.setDepthMode(
                        self.convertToString(storageutils.getXmlNodeText(sProps.getElementsByTagName('depthMode')[0]),
                                             'Dynamic', 'depthMode'))
                    mission.setPropellerMode(self.convertToString(
                        storageutils.getXmlNodeText(sProps.getElementsByTagName('propellerMode')[0]), 'Normal',
                        'propellerMode'))
                except:
                    QgsMessageLog.logMessage("error loading SABUVIS XML file settings!", tag="Pathplanner",
                                             level=Qgis.Critical)
                    mission.setDepthMode('Dynamic')
                    mission.setPropellerMode('Normal')

            taskList = xmlMission.getElementsByTagName('tasklist')[0]
            xmlTasks = taskList.getElementsByTagName('task')

            for xmlTask in xmlTasks:
                taskName = xmlTask.getAttribute('name')
                taskType = xmlTask.getAttribute('type')
                QgsMessageLog.logMessage("  loading task %s (%s)" % (taskName, taskType), tag="Pathplanner",
                                         level=Qgis.Info)

                if taskType == 'waypoint' or taskType == 'waypoints':
                    pitchControl = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('pitchControl')[0])
                    pitchSetPoint = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('pitchSetPoint')[0])

                    task = WaypointTask()
                    task.setParentMission(mission)
                    properties = task.getProperties()
                    properties.setPitchControl(pitchControl)
                    properties.setPitchSetPoint(pitchSetPoint)

                    # das noch unterschiedlich machen bei survey und waypoints
                    xmlPoints = xmlTask.getElementsByTagName('point')
                    for xmlPoint in xmlPoints:
                        x = xmlPoint.getAttribute('x')
                        y = xmlPoint.getAttribute('y')
                        depth = xmlPoint.getAttribute('depth')
                        task.addPoint(Point(float(x), float(y), float(depth)))

                    task.modelChanged.emit()
                    task.properties.propertiesChanged.emit()

                elif taskType == 'survey':
                    surveyType = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('surveyType')[0])

                    ewExtent = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('eastWestExtent')[0]))
                    nsExtent = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('northSouthExtent')[0]))
                    angle = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('rotationAngle')[0]))
                    swath = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('swath')[0]))
                    startPos = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('startPosition')[0])
                    oddLineSpacingFactor = float(
                        storageutils.getXmlNodeText(xmlTask.getElementsByTagName('oddLineSpacingFactor')[0]))
                    arrivalRadius = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('arrivalRadius')[0])

                    # new parameters for uneven spaced surveys
                    try:
                        ssrange = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('sideScanRange')[0]))
                        nadirgap = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('nadirGap')[0]))
                        distfactor = float(
                            storageutils.getXmlNodeText(xmlTask.getElementsByTagName('distanceFactor')[0]))
                    except:
                        ssrange = 200
                        nadirgap = 15
                        distfactor = 1.5

                    task = SurveyTask()
                    task.setParentMission(mission)

                    if (surveyType == 'BufferedMeander'):
                        arrivalRadius = 5
                        try:
                            arrivalRadius = storageutils.getXmlNodeText(
                                xmlTask.getElementsByTagName('arrivalRadius')[0])
                            # ewExtent = float(ewExtent) - 4 * float(arrivalRadius)

                        except:
                            QgsMessageLog.logMessage("error loading Arrival Radius value", tag="Pathplanner",
                                                     level=Qgis.Critical)
                        ewExtent = float(ewExtent) - 4 * float(arrivalRadius)
                        task.buffered = True

                    properties = task.getProperties()
                    properties.setSwath(swath)
                    properties.setSurveyType(surveyType)
                    properties.setEastWestExtent(ewExtent)
                    properties.setNorthSouthExtent(nsExtent)
                    properties.setRotationAngle(angle)
                    properties.setStartPosition(startPos)

                    properties.setOddLineSpacingFactor(oddLineSpacingFactor)
                    properties.setSideScanRange(ssrange)
                    properties.setNadirGap(nadirgap)
                    properties.setDistanceFactor(distfactor)

                    cpoint = xmlTask.getElementsByTagName('centerPoint')[0]
                    x = cpoint.getAttribute('x')
                    y = cpoint.getAttribute('y')
                    depth = cpoint.getAttribute('z')

                    # try:
                    #    x = float(x)
                    #    y = float(y)
                    #    depth = float(depth)
                    # except:
                    #    pass  # todo

                    loadedpoint = Point(float(x), float(y))
                    # task.centerPoint = loadedpoint
                    # task.centerPoint.setX(x)
                    # task.centerPoint.setY(y)
                    task.setDepth(float(depth))
                    # task.moveRect(task.centerPoint)
                    task.moveRect(loadedpoint)

                    task.modelChanged.emit()
                    task.surveyModelChanged.emit()

                elif taskType == 'circle':
                    radius = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('radius')[0])
                    rotationDirection = storageutils.getXmlNodeText(
                        xmlTask.getElementsByTagName('rotationDirection')[0])
                    try:
                        radius = float(radius)
                    except:
                        radius = 0

                    supProp = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('supressPropulsion')[0])
                    try:
                        supProp = int(supProp)
                    except:
                        supProp = 0
                    task = CircleTask()
                    task.setParentMission(mission)
                    task.setRadius(radius)
                    task.setRotationDirection(rotationDirection)
                    properties = task.getProperties()
                    properties.setSupressPropulsion(supProp)
                    xmlPoints = xmlTask.getElementsByTagName('point')
                    if len(xmlPoints) >= 1:
                        xPoint = xmlPoints[0]
                        x = xPoint.getAttribute('x')
                        y = xPoint.getAttribute('y')
                        depth = xPoint.getAttribute('depth')
                        task.setPoint(Point(float(x), float(y), float(depth)))
                else:
                    # handle all other types
                    QgsMessageLog.logMessage("  found unknown task type %s, skipped" % taskType, tag="Pathplanner",
                                             level=Qgis.Critical)
                    continue

                if taskType == 'waypoint' or taskType == 'waypoints' or taskType == 'survey' or taskType == "circle":
                    description = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('description')[0])
                    speed = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('speed')[0])
                    # time = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('time')[0])
                    timeout = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('timeout')[0])
                    priority = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('priority')[0])
                    arrivalRadius = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('arrivalRadius')[0])
                    lookAheadDistance = storageutils.getXmlNodeText(
                        xmlTask.getElementsByTagName('lookAheadDistance')[0])
                    distToLOS = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('maxDistanceToSwitchToLOS')[0])
                    trackControllerMode = storageutils.getXmlNodeText(
                        xmlTask.getElementsByTagName('trackControllerMode')[0])
                    # trackControllerValue = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('trackControllerValue')[0])
                    depthControllerMode = storageutils.getXmlNodeText(
                        xmlTask.getElementsByTagName('depthControllerMode')[0])
                    invalidHeightIterations = storageutils.getXmlNodeText(
                        xmlTask.getElementsByTagName('invalidHeightIterations')[0])
                    depthHeightInvalid = storageutils.getXmlNodeText(
                        xmlTask.getElementsByTagName('depthIfHeightInvalid')[0])
                    heightOverGround = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('heightOverGround')[0])
                    constantDepth = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('constantDepth')[0])

                    task.setName(taskName)
                    task.setDescription(description)

                    properties.setSpeed(speed)
                    # properties.setTime(time)
                    properties.setTimeout(timeout)
                    properties.setPriority(priority)
                    properties.setArrivalRadius(arrivalRadius)
                    properties.setLookAheadDistance(lookAheadDistance)
                    properties.setDistToLOS(distToLOS)
                    properties.setTrackControllerMode(trackControllerMode)
                    # properties.setTrackControllerValue(trackControllerValue)
                    properties.setDepthControllerMode(depthControllerMode)
                    properties.setHeightIterations(invalidHeightIterations)
                    properties.setDepthHeightInvalid(depthHeightInvalid)
                    properties.setHeightOverGround(heightOverGround)
                    properties.setConstantDepth(constantDepth)
                    mission.addTask(task)
                    mission.computeTotalDistance()
                    mission.computeTotalTime()

                    # task.properties.propertiesChanged.emit()
                    # task.getParentMission().missionModelChanged.emit()
                    # mission.missionModelChanged.emit()
                    # task.modelChanged.emit()

                # Payload, old version
                errors = []
                try:
                    xPayload = xmlTask.getElementsByTagName('payload')[0]
                    xPayloadDevices = xPayload.getElementsByTagName('device')
                    for xDevice in xPayloadDevices:
                        name = xDevice.getAttribute('payloadName')
                        QgsMessageLog.logMessage("    - payload %s found (old ver)" % name, tag="Pathplanner",
                                                 level=Qgis.Info)
                        event = xDevice.getAttribute('event')
                        if event.lower() == 'enable':
                            task.enablePayload(name)
                        if event.lower() == 'disable':
                            task.disablePayload(name)
                except Exception as e:
                    errors.append(str(e))

                if len(errors) != 0:
                    try:
                        xPayload = xmlTask.getElementsByTagName('payloads')[0]
                        xPayloadDevices = xPayload.getElementsByTagName('pl')
                        for xDevice in xPayloadDevices:
                            name = xDevice.getAttribute('name')
                            QgsMessageLog.logMessage("    - payload %s found (new ver)" % name, tag="Pathplanner",
                                                     level=Qgis.Info)
                            event = xDevice.getAttribute('eventAtBegin')
                            if event.lower() == 'enable':
                                task.enablePayload(name)
                            if event.lower() == 'disable':
                                task.disablePayload(name)
                            eventAtEnd = xDevice.getAttribute('eventAtEnd')
                            if eventAtEnd.lower() == 'enable':
                                task.changePayloadEventAtEnd(name, 'enable')
                            if eventAtEnd.lower() == 'disable':
                                task.changePayloadEventAtEnd(name, 'disable')
                    except Exception as e:
                        errors.append(str(e))
                if len(errors) > 1:
                    err = ", ".join(errors)
                    QgsMessageLog.logMessage("  task %s: no payload settings found, error: %s!" % (taskName, err),
                                             tag="Pathplanner", level=Qgis.Critical)
                    self.addError("Load xml: No Payload settings for task '{}' found.".format(taskName))

            regionsList = mission.getRegionsList()
            xmlRegionsList = xmlMission.getElementsByTagName('regionslist')[0]
            xmlRegions = xmlRegionsList.getElementsByTagName('region')
            for xmlRegion in xmlRegions:
                region = Region()
                region.setParentMission(mission)
                type = xmlRegion.getAttribute('type')
                region.setType(type)
                xmlPoints = xmlRegion.getElementsByTagName('point')
                for xmlPoint in xmlPoints:
                    x = xmlPoint.getAttribute('x')
                    y = xmlPoint.getAttribute('y')
                    point = Point(float(x), float(y))
                    region.addPoint(point)
                regionsList.addItem(region)

        return mission

    def loadFileContent(self, filename):
        try:
            filename = os.path.join(filename)
            QgsMessageLog.logMessage("Loading mission file %s" % filename, tag="Pathplanner", level=Qgis.Info)
            mission_dict = None
            with open(filename, 'r') as f:
                mission_dict = json.load(f)
            if mission_dict["version"] == 1:
                miss = self._load_v1(mission_dict)
                self.data_model.addMission(miss)
                QgsMessageLog.logMessage("Mission %s added to path planner" % miss.getName(), tag="Pathplanner", level=Qgis.Success)
                return filename
            return None
        except:
            QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)
            return None
