import traceback

from ..model import *
from ..config import get_configuration
from ..model.pathplannermodel2 import PathPlannerModel2

from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsMessageLog, Qgis

from qgis.PyQt.QtWidgets import QFileDialog
import os, os.path

from xml.dom import minidom

from .storageutils import storageutils

class XmlFileStorage:
    def __init__(self, model):
        if type(model) is not PathPlannerModel2:
            raise ValueError("XmlFileStorage: model parameter has wrong type.")
        self.data_model = model
        self.stereographic = QgsCoordinateReferenceSystem()
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
                                                         storageutils.getStoragePath(None), "Mission xml (*.xml)")

        if filename[0]:
            filename = self.loadFileContent(filename[0])
        return filename

    def save(self, filename):
        try:
            with open(filename, 'w') as f:
                xData = self.getXML()
                #f.write(xData.toprettyxml(indent="  ", encoding="UTF-8"))
                f.write(xData.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8'))
                f.close()
                return filename
        except:
            QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)

        return None

    def getMissionNames(self, xmlDOM):
        missionIDs = list()
        missionNames = list()
        xmlMissions = xmlDOM.getElementsByTagName('mission')
        for xmlMission in xmlMissions:
            missionIDs.append(xmlMission.getAttribute('ID'))
            missionNames.append(xmlMission.getAttribute('name'))
        return missionNames
    
    def getAllPointsOfMission(self, missionDom):
        xmlTasks = missionDom.getElementsByTagName('task')
        pointList = list()
        for xmlTask in xmlTasks:
            xmlPoints = xmlTask.getElementsByTagName('point')
            for xmlPoint in xmlPoints:
                point = list()
                try:
                    x = float(xmlPoint.getAttribute('x'))
                    y = float(xmlPoint.getAttribute('y'))
                except (TypeError, ValueError):
                    return None
                point.append(float(xmlPoint.getAttribute('x')))
                point.append(float(xmlPoint.getAttribute('y')))
                pointList.append(point)
        return pointList
         
    def computeReferencePosition(self, missionDom):
        pointList = self.getAllPointsOfMission(missionDom)
        
        if pointList:
            return pointList[0]
        else:
            return [0, 0, 0]

    def getXML(self):
        if not self.data_model:
            return None

        xdoc = minidom.Document()
        xroot = xdoc.createElement('consys_mission_planner')
        xdoc.appendChild(xroot)

        missionCount = self.data_model.countMissions()
        index = 0
        while index < missionCount:
            mission = self.data_model.getMission(index)
            missionID = mission.getMissionID()
            missionName = mission.getName()
            missionTotalTimeout = mission.getTotalTimeOut()

            xmission = xdoc.createElement('mission')
            xmission.setAttribute('description', str(mission.getDescription()))
            xmission.setAttribute('name', missionName)
            xmission.setAttribute("missionTimeout", str(missionTotalTimeout))
            xmission.setAttribute('vehicle', mission.getVehicleName())
            xroot.appendChild(xmission)

            missionCRS = mission.getCRS()
            crs_id = missionCRS.authid()
            crs_proj4 = missionCRS.toProj()

            xCrs = xdoc.createElement('crs')
            xCrsID = xdoc.createElement('id')
            xCrsID.appendChild(xdoc.createTextNode(str(crs_id)))
            xCrsProj4 = xdoc.createElement('proj4')
            xCrsProj4.appendChild(xdoc.createTextNode(str(crs_proj4)))
            xCrs.appendChild(xCrsID)
            xCrs.appendChild(xCrsProj4)
            xmission.appendChild(xCrs)

            xMissionProperties = xdoc.createElement('properties')
            #xDescription = xdoc.createElement('Description')
            #xDescription.appendChild(xdoc.createTextNode(str(mission.getDescription())))
            #xMissionProperties.appendChild(xDescription)
            #xTaskTimeoutAction = xdoc.createElement('timeoutAction')
            #xTaskTimeoutAction.appendChild(xdoc.createTextNode(str(mission.getTaskTimeoutAction())))
            #xMissionProperties.appendChild(xTaskTimeoutAction)
            xTimeoutFactor = xdoc.createElement('timeoutFactor')
            xTimeoutFactor.appendChild(xdoc.createTextNode(str(mission.getTimeoutFactor())))
            xMissionProperties.appendChild(xTimeoutFactor)
            
            xTaskTimeoutAction = xdoc.createElement('taskTimeoutAction')
            xTaskTimeoutAction.appendChild(xdoc.createTextNode(str(mission.getTaskTimeoutAction())))
            xMissionProperties.appendChild(xTaskTimeoutAction)
            
            xTotalDistance = xdoc.createElement('totalDistance')
            xTotalDistance.appendChild(xdoc.createTextNode(str(mission.getTotalDistance())))
            xMissionProperties.appendChild(xTotalDistance)
            
            xTotalDuration = xdoc.createElement('totalDuration')
            xTotalDuration.appendChild(xdoc.createTextNode(str(mission.getTotalTime())))
            xMissionProperties.appendChild(xTotalDuration)
            
            xUseHoGLimit = xdoc.createElement('useHoGLimit')
            xUseHoGLimit.appendChild(xdoc.createTextNode(str(mission.getUseHoGLimit())))
            xMissionProperties.appendChild(xUseHoGLimit)
            
            xUseDepthLimit = xdoc.createElement('useDepthLimit')
            xUseDepthLimit.appendChild(xdoc.createTextNode(str(mission.getUseDepthLimit())))
            xMissionProperties.appendChild(xUseDepthLimit)
            
            xHoGLimit = xdoc.createElement('hoGLimit')
            xHoGLimit.appendChild(xdoc.createTextNode(str(mission.getHoGLimit())))
            xMissionProperties.appendChild(xHoGLimit)
            
            xDepthLimit = xdoc.createElement('depthLimit')
            xDepthLimit.appendChild(xdoc.createTextNode(str(mission.getDepthLimit())))
            xMissionProperties.appendChild(xDepthLimit)

            xMinimumHeight = xdoc.createElement('minimumHeight')
            xMinimumHeight.appendChild(xdoc.createTextNode(str(mission.getMinimumHeight())))
            xMissionProperties.appendChild(xMinimumHeight)

            xmission.appendChild(xMissionProperties)

            # sabuvis extensions
            if get_configuration().plannerType == 'sabuvis':
                try:
                    xSabuvisProperties = xdoc.createElement('sabuvis_properties')
                    xDepthMode = xdoc.createElement('depthMode')
                    xDepthMode.appendChild(xdoc.createTextNode(str(mission.getDepthMode())))
                    xSabuvisProperties.appendChild(xDepthMode)
                    xPropellerMode = xdoc.createElement('propellerMode')
                    xPropellerMode.appendChild(xdoc.createTextNode(str(mission.getPropellerMode())))
                    xSabuvisProperties.appendChild(xPropellerMode)
                    xmission.appendChild(xSabuvisProperties)
                except:
                    QgsMessageLog.logMessage("error writing SABUVIS XML file settings!", tag="Pathplanner", level=Qgis.Critical)
                    pass

            xRegions = xdoc.createElement("regionslist")
            xmission.appendChild(xRegions)

            regionsList = mission.getRegionsList()
            if not regionsList:
                continue
            numOfRegions = regionsList.countItems()
            regionIndex = 0
            while regionIndex < numOfRegions:
                region = regionsList.getItemAt(regionIndex)
                xregion = xdoc.createElement("region")
                xRegions.appendChild(xregion)
                regionType = region.getType()
                xregion.setAttribute("type", str(regionType))
                numOfPoints = region.countPoints()
                pointIndex = 0
                while pointIndex < numOfPoints:
                    xpoint = xdoc.createElement('point')
                    point = region.getPointAt(pointIndex)
                    xpoint.setAttribute('x', str(point.getX()))
                    xpoint.setAttribute('y', str(point.getY()))
                    xpoint.setAttribute('z', str(point.getDepth()))
                    xregion.appendChild(xpoint)

                    pointIndex = pointIndex + 1
                regionIndex = regionIndex + 1

            xtasks = xdoc.createElement("tasklist")
            xmission.appendChild(xtasks)

            taskList = mission.getTaskList()
            if not taskList:
                continue
            for task in taskList:
                # recompute task timeout
                task.computeTaskTimeout()

                xtask = xdoc.createElement("task")
                taskType = task.type()
                taskName = task.getName()
                xtask.setAttribute('type', str(taskType))
                xtask.setAttribute('name', str(taskName))

                properties = task.getProperties()
                
                xDescription = xdoc.createElement('description')
                xDescription.appendChild(xdoc.createTextNode(str(properties.getDescription())))
                xtask.appendChild(xDescription)
                #xProperties.appendChild(xDescription)
                
                if taskType in ['waypoint', 'survey', 'circle', 'keepstation']:
                    xSpeed = xdoc.createElement('speed')
                    xSpeed.appendChild(xdoc.createTextNode(str(properties.getSpeed())))
                    #xProperties.appendChild(xSpeed)
                    xtask.appendChild(xSpeed)
                    
                    xTime = xdoc.createElement('time')
                    xTime.appendChild(xdoc.createTextNode(str(properties.getTime())))
                    #xProperties.appendChild(xTime)
                    xtask.appendChild(xTime)
                    
                    xTimeout = xdoc.createElement('timeout')
                    xTimeout.appendChild(xdoc.createTextNode(str(properties.getTimeout())))
                    #xProperties.appendChild(xTimeout)
                    xtask.appendChild(xTimeout)

                    xPriority = xdoc.createElement('priority')
                    xPriority.appendChild(xdoc.createTextNode(str(properties.getPriority())))
                    #xProperties.appendChild(xPriority)
                    xtask.appendChild(xPriority)

                    #xTrackControllerValue = xdoc.createElement('trackControllerValue')
                    #xTrackControllerValue.appendChild(xdoc.createTextNode(str(properties.getTrackControllerValue())))
                    #xProperties.appendChild(xTrackControllerValue)
                    #xtask.appendChild(xTrackControllerValue)
                    
                    xDepthControllerMode = xdoc.createElement('depthControllerMode')
                    xDepthControllerMode.appendChild(xdoc.createTextNode(str(properties.getDepthControllerMode())))
                    #xProperties.appendChild(xDepthControllerMode)
                    xtask.appendChild(xDepthControllerMode)
                    
                    xArrivalRadius = xdoc.createElement('arrivalRadius')
                    xArrivalRadius.appendChild(xdoc.createTextNode(str(properties.getArrivalRadius())))
                    #xProperties.appendChild(xArrivalRadius)
                    xtask.appendChild(xArrivalRadius)

                    xLookAhead = xdoc.createElement('lookAheadDistance')
                    xLookAhead.appendChild(xdoc.createTextNode(str(properties.getLookAheadDistance())))
                    #xProperties.appendChild(xLookAhead)
                    xtask.appendChild(xLookAhead)

                    xDistToLOS = xdoc.createElement('maxDistanceToSwitchToLOS')
                    xDistToLOS.appendChild(xdoc.createTextNode(str(properties.getDistToLOS())))
                    #xProperties.appendChild(xDistToLOS)
                    xtask.appendChild(xDistToLOS)

                    xTrackControllerMode = xdoc.createElement('trackControllerMode')
                    xTrackControllerMode.appendChild(xdoc.createTextNode(str(properties.getTrackControllerMode())))
                    #xProperties.appendChild(xTrackControllerMode)
                    xtask.appendChild(xTrackControllerMode)

                    xInvalHeightIter = xdoc.createElement('invalidHeightIterations')
                    xInvalHeightIter.appendChild(xdoc.createTextNode(str(properties.getHeightIterations())))
                    #xProperties.appendChild(xInvalHeightIter)
                    xtask.appendChild(xInvalHeightIter)

                    xDepthHeightInv = xdoc.createElement('depthIfHeightInvalid')
                    xDepthHeightInv.appendChild(xdoc.createTextNode(str(properties.getDepthHeightInvalid())))
                    #xProperties.appendChild(xDepthHeightInv)
                    xtask.appendChild(xDepthHeightInv)

                    xHeightOverGround = xdoc.createElement('heightOverGround')
                    xHeightOverGround.appendChild(xdoc.createTextNode(str(properties.getHeightOverGround())))
                    #xProperties.appendChild(xHeightOverGround)
                    xtask.appendChild(xHeightOverGround)

                    xConstantDepth = xdoc.createElement('constantDepth')
                    xConstantDepth.appendChild(xdoc.createTextNode(str(properties.getConstantDepth())))
                    #xProperties.appendChild(xConstantDepth)
                    xtask.appendChild(xConstantDepth)

                    newTrackControllerMode = xdoc.createElement('newTrackControllerMode')
                    newTrackControllerMode.appendChild(xdoc.createTextNode(str('1')))
                    xtask.appendChild(newTrackControllerMode)

                if taskType == 'waypoint':
                    xDistance = xdoc.createElement('distance')
                    xDistance.appendChild(xdoc.createTextNode(str(properties.getDistance())))
                    #xProperties.appendChild(xDistance)
                    xtask.appendChild(xDistance)
                    
                    xPitchControl = xdoc.createElement('pitchControl')
                    xPitchControl.appendChild(xdoc.createTextNode(str(properties.getPitchControl())))
                    #xProperties.appendChild(xPitchControl)
                    xtask.appendChild(xPitchControl)

                    xPitchSetPoint = xdoc.createElement('pitchSetPoint')
                    xPitchSetPoint.appendChild(xdoc.createTextNode(str(properties.getPitchSetPoint())))
                    #xProperties.appendChild(xPitchSetPoint)
                    xtask.appendChild(xPitchSetPoint)

                if taskType == 'survey':
                    xSurveyType = xdoc.createElement('surveyType')
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

                    xSurveyType.appendChild(xdoc.createTextNode(str(sType)))
                    #xProperties.appendChild(xSurveyType)
                    xtask.appendChild(xSurveyType)
                    
                    xCenterPoint = xdoc.createElement('centerPoint')
                    surveyCenter = task.getCenterPoint()
                    xCenterPoint.setAttribute('x', (str(surveyCenter.getX())))
                    xCenterPoint.setAttribute('y', (str(surveyCenter.getY())))
                    xCenterPoint.setAttribute('z', (str(surveyCenter.getDepth())))
                    xtask.appendChild(xCenterPoint)

                    xPoint = xdoc.createElement('point')
                    surveyCenter = task.getCenterPoint()
                    xPoint.setAttribute('depth', (str(surveyCenter.getDepth())))
                    xPoint.setAttribute('x', (str(surveyCenter.getX())))
                    xPoint.setAttribute('y', (str(surveyCenter.getY())))
                    xtask.appendChild(xPoint)

                    xEWExtent = xdoc.createElement('eastWestExtent')
                    #xEWExtent.appendChild(xdoc.createTextNode(str(properties.getEastWestExtent())))
                    xEWExtent.appendChild(xdoc.createTextNode(str(ewe)))
                    #xProperties.appendChild(xEWExtent)
                    xtask.appendChild(xEWExtent)

                    xNSExtent = xdoc.createElement('northSouthExtent')
                    xNSExtent.appendChild(xdoc.createTextNode(str(properties.getNorthSouthExtent())))
                    #xProperties.appendChild(xNSExtent)
                    xtask.appendChild(xNSExtent)
                    
                    xRotationAngle = xdoc.createElement('rotationAngle')
                    xRotationAngle.appendChild(xdoc.createTextNode(str(properties.getRotationAngle())))
                    #xProperties.appendChild(xRotationAngle)
                    xtask.appendChild(xRotationAngle)

                    xStartPosition = xdoc.createElement('startPosition')
                    xStartPosition.appendChild(xdoc.createTextNode(str(properties.getStartPosition())))
                    #xProperties.appendChild(xStartPosition)
                    xtask.appendChild(xStartPosition)

                    xSwath = xdoc.createElement('swath')
                    xSwath.appendChild(xdoc.createTextNode(str(properties.getSwath())))
                    #xProperties.appendChild(xSwath)
                    xtask.appendChild(xSwath)
                    
                    xOddLineSpacingFactor = xdoc.createElement('oddLineSpacingFactor')
                    xOddLineSpacingFactor.appendChild(xdoc.createTextNode(str(properties.getOddLineSpacingFactor())))
                    xtask.appendChild(xOddLineSpacingFactor)

                    xSideScanRange = xdoc.createElement('sideScanRange')
                    xSideScanRange.appendChild(xdoc.createTextNode(str(properties.getSideScanRange())))
                    xtask.appendChild(xSideScanRange)

                    xNadirGap = xdoc.createElement('nadirGap')
                    xNadirGap.appendChild(xdoc.createTextNode(str(properties.getNadirGap())))
                    xtask.appendChild(xNadirGap)

                    xDistanceFactor = xdoc.createElement('distanceFactor')
                    xDistanceFactor.appendChild(xdoc.createTextNode(str(properties.getDistanceFactor())))
                    xtask.appendChild(xDistanceFactor)

                    xPitchControl = xdoc.createElement('pitchControl')
                    xPitchControl.appendChild(xdoc.createTextNode(str(properties.getPitchControl())))
                    # xProperties.appendChild(xPitchControl)
                    xtask.appendChild(xPitchControl)

                    xPitchSetPoint = xdoc.createElement('pitchSetPoint')
                    xPitchSetPoint.appendChild(xdoc.createTextNode(str(properties.getPitchSetPoint())))
                    # xProperties.appendChild(xPitchSetPoint)
                    xtask.appendChild(xPitchSetPoint)

                if taskType == 'circle':
                    xRadius = xdoc.createElement('radius')
                    xRadius.appendChild(xdoc.createTextNode(str(task.getRadius())))
                    xtask.appendChild(xRadius)
                    
                    xSupProp = xdoc.createElement('supressPropulsion')
                    xSupProp.appendChild(xdoc.createTextNode(str(properties.getSupressPropulsion())))
                    xtask.appendChild(xSupProp)
                    
                    xRotDirection = xdoc.createElement('rotationDirection')
                    xRotDirection.appendChild(xdoc.createTextNode(str(task.getRotationDirection())))
                    xtask.appendChild(xRotDirection)

                if taskType == 'keepstation':
                    xRadius = xdoc.createElement('innerRadius')
                    xRadius.appendChild(xdoc.createTextNode(str(task.getInnerRadius())))
                    xtask.appendChild(xRadius)

                    xRadius = xdoc.createElement('outerRadius')
                    xRadius.appendChild(xdoc.createTextNode(str(task.getOuterRadius())))
                    xtask.appendChild(xRadius)

                #xtask.appendChild(xProperties)
                if taskType in ["waypoint", "circle", "keepstation"]:
                    pointCount = task.countPoints()
                    indexPoint = 0
                    while indexPoint < pointCount:
                        point = task.getPointAt(indexPoint)
                        xPoint = xdoc.createElement('point')
                        xPoint.setAttribute("x", str(point.getX()))
                        xPoint.setAttribute("y", str(point.getY()))
                        xPoint.setAttribute("depth", str(point.getDepth()))
                        xtask.appendChild(xPoint)
                        indexPoint += 1

                # Payload activation/deactivation
                payloadDisabledList = task.getDisabledPayload()
                payloadEnabledList = task.getEnabledPayload()

                use_old_payload_code = True

                if use_old_payload_code:
                    xPayload = xdoc.createElement('payload')
                    for item in payloadDisabledList:
                        xPayloadDevice = xdoc.createElement('device')
                        xPayloadDevice.setAttribute('payloadName', item)
                        xPayloadDevice.setAttribute('event', 'Disable')
                        xPayload.appendChild(xPayloadDevice)
                    for item in payloadEnabledList:
                        xPayloadDevice = xdoc.createElement('device')
                        xPayloadDevice.setAttribute('payloadName', item)
                        xPayloadDevice.setAttribute('event', 'Enable')
                        xPayload.appendChild(xPayloadDevice)
                    for item in task.payload_event_at_end:
                        xPayloadDevice = xdoc.createElement('device')
                        xPayloadDevice.setAttribute('payloadName', item)
                        xPayloadDevice.setAttribute('eventAtEnd', task.payload_event_at_end[item])
                        xPayload.appendChild(xPayloadDevice)
                    xtask.appendChild(xPayload)
                else:
                    payloads = {}
                    for item in payloadEnabledList:
                        payloads[item] = { "eventAtBegin": "enable", "eventAtEnd": "" }
                    for item in payloadDisabledList:
                        payloads[item] = { "eventAtBegin": "disable", "eventAtEnd": "" }
                    for item in task.payload_event_at_end:
                        if item not in payloads:
                            payloads[item] = {"eventAtBegin": ""}
                        payloads[item]["eventAtEnd"] = task.payload_event_at_end[item]
                    xPayloads = xdoc.createElement('payloads')
                    for item in payloads:
                        xPayloadDevice = xdoc.createElement('pl')
                        xPayloadDevice.setAttribute('name', item)
                        xPayloadDevice.setAttribute('eventAtBegin', payloads[item]["eventAtBegin"])
                        xPayloadDevice.setAttribute('eventAtEnd', payloads[item]["eventAtEnd"])
                        xPayloads.appendChild(xPayloadDevice)
                    xtask.appendChild(xPayloads)

                xtasks.appendChild(xtask)
            index += 1
        return xdoc
    
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
    
    def loadFileContent(self, filename):
        try:
            filename = os.path.join(filename)
            QgsMessageLog.logMessage("Loading mission file %s" % filename, tag="Pathplanner", level=Qgis.Info)
            dom = minidom.parse(filename)
            #print("entered loadFileContent")
            
            xmlMissions = dom.getElementsByTagName('mission')
            #print(xmlMissions)
            for xmlMission in xmlMissions:
                missionName = xmlMission.getAttribute('name')
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
                    missionCRS = QgsCoordinateReferenceSystem("PROJ:"+proj4)
                mission = Mission(missionCRS,'')
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
                taskTimeoutAction = self.convertToString(storageutils.getXmlNodeText(xTaskTimeoutAction), 'ABORT', 'taskTimeoutAction')
                useHoGLimit = self.convertToBool(storageutils.getXmlNodeText(xUseHoGLimit), False, 'useHoGLimit')
                useDepthLimit = self.convertToBool(storageutils.getXmlNodeText(xUseDepthLimit), False, 'useDepthLimit')
                hoGLimit = self.convertToFloat(storageutils.getXmlNodeText(xHoGLimit), 0 if not useHoGLimit else 20000, 'hoGLimit')
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
                        mission.setDepthMode(self.convertToString(storageutils.getXmlNodeText(sProps.getElementsByTagName('depthMode')[0]), 'Dynamic', 'depthMode'))
                        mission.setPropellerMode(self.convertToString(storageutils.getXmlNodeText(sProps.getElementsByTagName('propellerMode')[0]), 'Normal', 'propellerMode'))
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
                    QgsMessageLog.logMessage("  loading task %s (%s)" % (taskName, taskType), tag="Pathplanner", level=Qgis.Info)
                    
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
                            task.addPoint(Point(float(x),float(y),float(depth)))

                        task.modelChanged.emit()
                        task.properties.propertiesChanged.emit()

                    elif taskType == 'survey':
                        surveyType = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('surveyType')[0])

                        ewExtent = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('eastWestExtent')[0]))
                        nsExtent = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('northSouthExtent')[0]))
                        angle = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('rotationAngle')[0]))
                        swath = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('swath')[0]))
                        startPos = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('startPosition')[0])
                        oddLineSpacingFactor = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('oddLineSpacingFactor')[0]))
                        arrivalRadius = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('arrivalRadius')[0])

                        # new parameters for uneven spaced surveys
                        try:
                            ssrange = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('sideScanRange')[0]))
                            nadirgap = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('nadirGap')[0]))
                            distfactor = float(storageutils.getXmlNodeText(xmlTask.getElementsByTagName('distanceFactor')[0]))
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
                                #ewExtent = float(ewExtent) - 4 * float(arrivalRadius)

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

                        #try:
                        #    x = float(x)
                        #    y = float(y)
                        #    depth = float(depth)
                        #except:
                        #    pass  # todo

                        loadedpoint = Point(float(x), float(y))
                        #task.centerPoint = loadedpoint
                        #task.centerPoint.setX(x)
                        #task.centerPoint.setY(y)
                        task.setDepth(float(depth))
                        #task.moveRect(task.centerPoint)
                        task.moveRect(loadedpoint)

                        task.modelChanged.emit()
                        task.surveyModelChanged.emit()

                    elif taskType == 'circle':
                        radius = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('radius')[0])
                        rotationDirection = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('rotationDirection')[0])
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
                    elif taskType == 'keepstation':
                        task = KeepStationTask()
                        task.setParentMission(mission)
                        radius = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('innerRadius')[0])
                        try:
                            radius = float(radius)
                        except:
                            radius = 0.0
                        task.setInnerRadius(radius)
                        radius = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('outerRadius')[0])
                        try:
                            radius = float(radius)
                        except:
                            radius = 0.0
                        task.setOuterRadius(radius)
                        xmlPoints = xmlTask.getElementsByTagName('point')
                        if len(xmlPoints) >= 1:
                            xPoint = xmlPoints[0]
                            x = xPoint.getAttribute('x')
                            y = xPoint.getAttribute('y')
                            depth = xPoint.getAttribute('depth')
                            task.setPoint(Point(float(x), float(y), float(depth)))
                    else:
                        # handle all other types
                        QgsMessageLog.logMessage("  found unknown task type %s, skipped" % taskType, tag="Pathplanner", level=Qgis.Critical)
                        continue
                        
                    if taskType in ['waypoint', 'waypoints', 'survey', 'circle', 'keepstation']:
                        description = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('description')[0])
                        speed = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('speed')[0])
                        #time = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('time')[0])
                        timeout = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('timeout')[0])
                        priority = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('priority')[0])
                        arrivalRadius = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('arrivalRadius')[0])
                        lookAheadDistance = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('lookAheadDistance')[0])
                        distToLOS = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('maxDistanceToSwitchToLOS')[0])
                        trackControllerMode = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('trackControllerMode')[0])
                        #trackControllerValue = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('trackControllerValue')[0])
                        depthControllerMode = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('depthControllerMode')[0])
                        invalidHeightIterations = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('invalidHeightIterations')[0])
                        depthHeightInvalid = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('depthIfHeightInvalid')[0])
                        heightOverGround = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('heightOverGround')[0])
                        constantDepth = storageutils.getXmlNodeText(xmlTask.getElementsByTagName('constantDepth')[0])

                        task.setName(taskName)
                        task.setDescription(description)

                        properties = task.getProperties()
                        properties.setSpeed(speed)
                        #properties.setTime(time)
                        properties.setTimeout(timeout)
                        properties.setPriority(priority)
                        properties.setArrivalRadius(arrivalRadius)
                        properties.setLookAheadDistance(lookAheadDistance)
                        properties.setDistToLOS(distToLOS)
                        properties.setTrackControllerMode(trackControllerMode)
                        #properties.setTrackControllerValue(trackControllerValue)
                        properties.setDepthControllerMode(depthControllerMode)
                        properties.setHeightIterations(invalidHeightIterations)
                        properties.setDepthHeightInvalid(depthHeightInvalid)
                        properties.setHeightOverGround(heightOverGround)
                        properties.setConstantDepth(constantDepth)
                        mission.addTask(task)
                        mission.computeTotalDistance()
                        mission.computeTotalTime()

                        #task.properties.propertiesChanged.emit()
                        #task.getParentMission().missionModelChanged.emit()
                        #mission.missionModelChanged.emit()
                        #task.modelChanged.emit()

                    # Payload, old version
                    errors = []
                    try:
                        xPayload = xmlTask.getElementsByTagName('payload')[0]
                        xPayloadDevices = xPayload.getElementsByTagName('device')
                        for xDevice in xPayloadDevices:
                            name = xDevice.getAttribute('payloadName')
                            QgsMessageLog.logMessage("    - payload %s found (old ver)" % name, tag="Pathplanner", level=Qgis.Info)
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
                                QgsMessageLog.logMessage("    - payload %s found (new ver)" % name, tag="Pathplanner", level=Qgis.Info)
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
                        QgsMessageLog.logMessage("  task %s: no payload settings found, error: %s!" % (taskName, err), tag="Pathplanner", level=Qgis.Critical)
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
                    
                self.data_model.addMission(mission)
                QgsMessageLog.logMessage("Mission %s added to path planner" % missionName, tag="Pathplanner", level=Qgis.Success)
                return filename
        except:
            QgsMessageLog.logMessage(traceback.format_exc(), tag="Pathplanner", level=Qgis.Critical)
            return None
