import socket
from typing import List
from airtouch4pyapi import helper
from airtouch4pyapi import packetmap
from airtouch4pyapi import communicate
from enum import Enum
# from hexdump import hexdump
#API

# class Airtouch
    #Init - takes IP Address, queries group names and group infos
        #GetInfo - takes nothing, returns Groups list
        
        #SetGroupToTemperature takes group number + temperature
        #TurnGroupOn
        #TurnGroupOff

    #SetCoolingModeByGroup
    #SetFanSpeedByGroup
    #GetSupportedCoolingModesByGroup
    #GetSupportedFanSpeedsByGroup
        
        #TurnAcOn
        #TurnAcOff
        #SetFanSpeedForAc
        #SetCoolingModeForAc
        #GetSupportedCoolingModesForAc
        #GetSupportedFanSpeedsForAc
        #GetAcs

class AirTouchStatus(Enum):
    NOT_CONNECTED = 0
    OK = 1
    CONNECTION_INTERRUPTED = 2
    CONNECTION_LOST = 3
    ERROR = 4

class AirTouchVersion(Enum):
    AIRTOUCH4 = 4
    AIRTOUCH5 = 5

class AirTouchGroup:
    def __init__(self):
        self.GroupName = ""
        self.GroupNumber = 0
        self.OpenPercent = 0
        self.Temperature = 0
        self.TargetSetpoint = 0
        self.BelongsToAc = -1
    @property
    def IsOn(self):
        return self.PowerState

class AirTouchError:
    def __init__(self):
        self.Message = ""
        self.Status = AirTouchStatus.OK

class AirTouchAc:
    def __init__(self):
        self.AcName = ""
        self.AcNumber = 0
        self.StartGroupNumber = 0
        self.GroupCount = 0
    @property
    def IsOn(self):
        return self.PowerState

class AirTouch:
    IpAddress = "";
    SettingValueTranslator = packetmap.SettingValueTranslator();
    def __init__(self, ipAddress, atVersion = None, port = None):
        self.IpAddress = ipAddress;
        self.Status = AirTouchStatus.NOT_CONNECTED;
        self.Messages = dict();
        self.atVersion = atVersion;
        self.atPort = port;
        self.acs = dict();
        self.groups = dict();
        self.Messages:List[AirTouchError] = [];
    
    async def UpdateInfo(self):
        if(self.atPort != None and self.atVersion == None):
            self.Status = AirTouchStatus.ERROR
            errorMessage = AirTouchError()
            errorMessage.Message = "If you specify a port, you must specify a version"
            self.Messages.append(errorMessage)
            print(self.Status)
            for msg in self.Messages:
                print(msg.Message);
            return;

        if(self.atVersion == None):
            await self.findVersion()

        if(self.atVersion == None):
            print(self.Status)
            for msg in self.Messages:
                print(msg.Message);
            return;
        #get the group infos
        await self.UpdateGroupInfo()
        
        #if the first call means we still have an error status, not worth doing the subsequent ones
        if(self.Status != AirTouchStatus.OK):
            print(self.Status)
            for msg in self.Messages:
                print(msg.Message);
            return;
        
        #get the group nicknames 
        await self.UpdateGroupNames()
        
        #get ac infos
        await self.UpdateAcInfo()
        
        #get ac abilities
        await self.UpdateAcAbility()

        #sort out which AC belongs to which zone/group
        self.AssignAcsToGroups()

    async def findVersion(self):
        if(await self.isOpen(self.IpAddress, 9004)):
            self.atVersion = AirTouchVersion.AIRTOUCH4
            self.atPort = 9004
            return
        elif(await self.isOpen(self.IpAddress, 9005)):
            self.atVersion = AirTouchVersion.AIRTOUCH5
            self.atPort = 9005
            return
        else:
            self.Status = AirTouchStatus.ERROR
            errorMessage = AirTouchError()
            errorMessage.Message = "Could not find open port 9004 (v4) or 9005 (v5)"
            self.Messages.append(errorMessage)
    
    async def isOpen(self, ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ip, int(port)))
            s.shutdown(2)
            return True
        except:
            return False
    ## Initial Update Calls
    async def UpdateAcAbility(self):
        acAbilityMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcAbility", self.atVersion);
        await self.SendMessageToAirtouch(acAbilityMessage)

    async def UpdateAcInfo(self):
        message = packetmap.MessageFactory.CreateEmptyMessageOfType("AcStatus", self.atVersion);
        await self.SendMessageToAirtouch(message)

    async def UpdateGroupInfo(self):
        message = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupStatus", self.atVersion);
        await self.SendMessageToAirtouch(message)
    
    async def UpdateGroupNames(self):
        nameMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupName", self.atVersion);
        await self.SendMessageToAirtouch(nameMessage)

    def AssignAcsToGroups(self):
        ## Assign ACs to groups (zones) based on startgroupnumber, count
        for group in self.groups.values():
            #find out which ac this group belongs to
            
            for ac in self.acs.values():
                if(ac.StartGroupNumber == 0 and ac.GroupCount == 0):
                    #assuming this means theres only one ac? so every group belongs to this ac? 
                    group.BelongsToAc = ac.AcNumber
                if(ac.StartGroupNumber <= group.GroupNumber and group.GroupNumber <= ac.StartGroupNumber + ac.GroupCount):
                    group.BelongsToAc = ac.AcNumber

    ## END Initial Update Calls

    ## Turn things on/off/temp by name (just finds the number, calls the right function)
    async def TurnGroupOnByName(self, groupName):
        targetGroup = self._getTargetGroup(groupName)
        await self.TurnGroupOn(targetGroup.GroupNumber);
    
    async def TurnGroupOffByName(self, groupName):
        targetGroup = self._getTargetGroup(groupName)
        await self.TurnGroupOff(targetGroup.GroupNumber);
    
    
    async def SetGroupToTemperatureByGroupName(self, groupName, temperature):
        targetGroup = self._getTargetGroup(groupName)
        await self.SetGroupToTemperature(targetGroup.GroupNumber, temperature);
    
    async def SetGroupToPercentByGroupName(self, groupName, percent):
        targetGroup = self._getTargetGroup(groupName)
        await self.SetGroupToPercentage(targetGroup.GroupNumber, percent);

    ## END Turn things on/off/temp by name (just finds the number, calls the right function)


    ## Group/zone modes
    async def SetCoolingModeByGroup(self, groupNumber, coolingMode):
        await self.SetCoolingModeForAc(self.groups[groupNumber].BelongsToAc, coolingMode);
        return self.groups[groupNumber];

    async def SetFanSpeedByGroup(self, groupNumber, fanSpeed):
        await self.SetFanSpeedForAc(self.groups[groupNumber].BelongsToAc, fanSpeed);
        return self.groups[groupNumber];

    def GetSupportedCoolingModesByGroup(self, groupNumber):
        return self.GetSupportedCoolingModesForAc(self.groups[groupNumber].BelongsToAc);

    def GetSupportedFanSpeedsByGroup(self, groupNumber):
        return self.GetSupportedFanSpeedsForAc(self.groups[groupNumber].BelongsToAc);
    ## END Group/zone modes

    # Main control functions
    async def TurnGroupOn(self, groupNumber):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupControl", self.atVersion);
        controlMessage.SetMessageValue("Power", 3)
        controlMessage.SetMessageValue("GroupNumber", groupNumber)
        await self.SendMessageToAirtouch(controlMessage)
        return self.groups[groupNumber];
    
    async def TurnGroupOff(self, groupNumber):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupControl", self.atVersion);
        controlMessage.SetMessageValue("Power", 2)
        controlMessage.SetMessageValue("GroupNumber", groupNumber)
        await self.SendMessageToAirtouch(controlMessage)
        return self.groups[groupNumber];
    
    async def TurnAcOn(self, acNumber):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcControl", self.atVersion);
        #these are required to leave these settings unchanged
        controlMessage.SetMessageValue("AcMode", 0x0f);
        controlMessage.SetMessageValue("AcFanSpeed", 0x0f);
        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
            controlMessage.SetMessageValue("TargetSetpoint", 0x3f);
        if(self.atVersion == AirTouchVersion.AIRTOUCH5):
            controlMessage.SetMessageValue("SetpointControlType", 0x00);
        controlMessage.SetMessageValue("Power", 3)
        controlMessage.SetMessageValue("AcNumber", acNumber)
        await self.SendMessageToAirtouch(controlMessage)

    async def TurnAcOff(self, acNumber):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcControl", self.atVersion);
        #these are required to leave these settings unchanged
        controlMessage.SetMessageValue("AcMode", 0x0f);
        controlMessage.SetMessageValue("AcFanSpeed", 0x0f);


        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
            controlMessage.SetMessageValue("TargetSetpoint", 0x3f);
        if(self.atVersion == AirTouchVersion.AIRTOUCH5):
            controlMessage.SetMessageValue("SetpointControlType", 0x00);

        controlMessage.SetMessageValue("Power", 2)
        controlMessage.SetMessageValue("AcNumber", acNumber)
        await self.SendMessageToAirtouch(controlMessage)
    
    # END Main control functions

    #use a fanspeed reported from GetSupportedFanSpeedsForAc
    async def SetFanSpeedForAc(self, acNumber, fanSpeed):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcControl", self.atVersion);
        #these are required to leave these settings unchanged
        controlMessage.SetMessageValue("AcMode", 0x0f);
        controlMessage.SetMessageValue("AcFanSpeed", packetmap.SettingValueTranslator.NamedValueToRawValue("AcFanSpeed", fanSpeed));
        controlMessage.SetMessageValue("TargetSetpoint", 0x3f);

        controlMessage.SetMessageValue("AcNumber", acNumber)
        await self.SendMessageToAirtouch(controlMessage)

    #use a mode reported from GetSupportedCoolingModesForAc
    async def SetCoolingModeForAc(self, acNumber, acMode):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcControl", self.atVersion);
        #these are required to leave these settings unchanged
        controlMessage.SetMessageValue("AcMode", packetmap.SettingValueTranslator.NamedValueToRawValue("AcMode", acMode));
        controlMessage.SetMessageValue("AcFanSpeed", 0x0f);
        controlMessage.SetMessageValue("TargetSetpoint", 0x3f);

        controlMessage.SetMessageValue("AcNumber", acNumber)
        await self.SendMessageToAirtouch(controlMessage)

    #GetSupportedCoolingModesForAc
    def GetSupportedCoolingModesForAc(self, acNumber):
        return self.acs[acNumber].ModeSupported;

    #GetSupportedFanSpeedsForAc
    def GetSupportedFanSpeedsForAc(self, acNumber):
        return self.acs[acNumber].FanSpeedSupported;

    

    ## Group/Zone temperatures
    async def SetGroupToTemperature(self, groupNumber, temperature):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupControl", self.atVersion);
        controlMessage.SetMessageValue("Power", 3)
        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
            controlMessage.SetMessageValue("HaveTemperatureControl", 3)
        controlMessage.SetMessageValue("GroupSettingValue", 5)
        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
            controlMessage.SetMessageValue("TargetSetpoint", temperature)
        elif(self.atVersion == AirTouchVersion.AIRTOUCH5):
            controlMessage.SetMessageValue("TargetSetpoint", temperature*10-100)
        controlMessage.SetMessageValue("GroupNumber", groupNumber)
        await self.SendMessageToAirtouch(controlMessage)
        return self.groups[groupNumber];
        #should this turn the group on?

    async def SetGroupToPercentage(self, groupNumber, percent):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupControl", self.atVersion);
        controlMessage.SetMessageValue("Power", 3)
        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
            controlMessage.SetMessageValue("HaveTemperatureControl", 3)
        controlMessage.SetMessageValue("GroupSettingValue", 4)
        controlMessage.SetMessageValue("TargetSetpoint", percent)
        controlMessage.SetMessageValue("GroupNumber", groupNumber)
        await self.SendMessageToAirtouch(controlMessage)
        return self.groups[groupNumber];

    ## END Group/Zone temperatures

    ## Helper functions
    def GetAcs(self):
        acs = [];
        for acNumber in self.acs.keys(): 
            ac = self.acs[acNumber]
            acs.append(ac);
        return acs;
    
    def GetGroupByGroupNumber(self, groupNumber):
        return self.groups[groupNumber];

    def GetGroups(self):
        groups = [];
        for groupNumber in self.groups.keys(): 
            groupInfo = self.groups[groupNumber]
            groups.append(groupInfo);
        return groups;
        #returns a list of groups, each group has a name, a number, on or off, current damper opening, current temp and target temp

    def GetVersion(self):
        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
            return "4"
        elif(self.atVersion == AirTouchVersion.AIRTOUCH5):
            return "5"
        return ""
    ## END Helper functions


    ## Major AT comms.  Set up a message, send it, get the result, translate packet to message at the end.  
    async def SendMessageToAirtouch(self, messageObject):

        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
            if(messageObject.MessageType == "GroupStatus"):
                MESSAGE = "80b0012b0000"
            if(messageObject.MessageType == "GroupName"):
                MESSAGE = "90b0011f0002ff12"
            if(messageObject.MessageType == "AcAbility"):
                MESSAGE = "90b0011f0002ff11"
            if(messageObject.MessageType == "AcStatus"): 
                MESSAGE = "80b0012d0000f4cf"
            if(messageObject.MessageType == "GroupControl" or messageObject.MessageType == "AcControl"):
                MESSAGE = communicate.MessageObjectToMessagePacket(messageObject, messageObject.MessageType, self.atVersion);
        
        elif(self.atVersion == AirTouchVersion.AIRTOUCH5):
            if(messageObject.MessageType == "GroupStatus"):
                MESSAGE = "80b001c000082100000000000000"
            if(messageObject.MessageType == "GroupName"):
                MESSAGE = "90b0011f0002ff13"
            if(messageObject.MessageType == "AcAbility"):
                MESSAGE = "90b0011f0002ff11"
            if(messageObject.MessageType == "AcStatus"):
                MESSAGE = "80b001c000082300000000000000"
            if(messageObject.MessageType == "GroupControl" or messageObject.MessageType == "AcControl"):
                MESSAGE = communicate.MessageObjectToMessagePacket(messageObject, messageObject.MessageType, self.atVersion);
        try: 
            dataResult = await communicate.SendMessagePacketToAirtouch(MESSAGE, self.IpAddress, self.atVersion, self.atPort)
            self.Status = AirTouchStatus.OK
        except Exception as e: 
            if(self.Status == AirTouchStatus.OK):
                self.Status = AirTouchStatus.CONNECTION_INTERRUPTED
            else:
                self.Status = AirTouchStatus.CONNECTION_LOST

            errorMessage = AirTouchError()
            errorMessage.Message = "Could not send message to airtouch: " + str(e)
            self.Messages.append(errorMessage)
            return

        return self.TranslatePacketToMessage(dataResult)

    ## Interpret response object
    def TranslatePacketToMessage(self, dataResult):
        #If the request hasn't gone well, we don't want to update any of the data we have with bad/no data
        if(self.Status != AirTouchStatus.OK):
            return;
        if(self.atVersion == AirTouchVersion.AIRTOUCH4):

            ## AT4 is easy

            address = dataResult[2:4]
            messageId = dataResult[4:5]
            messageType = dataResult[5:6]
            dataLength = dataResult[6:8]

            if(messageType == b'\x2b'):
                self.DecodeAirtouchGroupStatusMessage(dataResult[8::]);
            if(messageType == b'\x1f'):
                self.DecodeAirtouchExtendedMessage(dataResult[8::]);
            if(messageType == b'\x2d'):
                self.DecodeAirtouchAcStatusMessage(dataResult[8::]);
        else:

            ## AT5 requires a bit more knowledge if it's an extended message.  

            messageType = dataResult[17:18]
            
            if(messageType == b'\xc0'):
                messageSubType = dataResult[20:21]
                ### We got a control message
                if(messageSubType == b'\x21'):
                    ### Zone Status Message
                    self.DecodeAirtouch5ZoneStatusMessage(dataResult[22::]);
                if(messageSubType == b'\x23'):
                    ### AC Status Message
                    self.DecodeAirtouch5AcStatusMessage(dataResult[22::]);
            if(messageType == b'\x1f'):
                messageSubType = dataResult[21:22]
                if(messageSubType == b'\x13'):
                    self.DecodeAirtouch5GroupNames(dataResult[17::]);
                if(messageSubType == b'\x11'):
                    self.DecodeAirtouch5AcAbility(dataResult[17::]);


    ## Only for AT4, decode extended.
    def DecodeAirtouchExtendedMessage(self, payload):
        groups = self.groups;
        if(payload[0:2] == b'\xff\x12'):
            for groupChunk in helper.chunks(payload[2:], 9):
                if(len(groupChunk) < 9):
                    continue

                groupNumber = groupChunk[0]
                groupInfo = AirTouchGroup()
                if groupNumber not in groups:
                    groups[groupNumber] = groupInfo;
                else:
                    groupInfo = groups[groupNumber];
                
                groupName = groupChunk[1:9].decode("utf-8").rstrip('\0')
                groups[groupNumber].GroupName = groupName

        if(payload[0:2] == b'\xff\x11'):
            chunkSize = communicate.TranslateMapValueToValue(payload[2:], packetmap.DataLocationTranslator.map[self.atVersion.value]["AcAbility"]["ChunkSize"]);
            self.DecodeAirtouchMessage(payload[2:], packetmap.DataLocationTranslator.map[self.atVersion.value]["AcAbility"], False, chunkSize + 2)

    ## Only for AT4, decode a basic message.  
    def DecodeAirtouchMessage(self, payload, map, isGroupBased, chunkSize):
        for chunk in helper.chunks(payload, chunkSize):
            if(len(chunk) < chunkSize):
                continue
            packetInfoLocationMap = map
            
            resultList = self.groups
            resultObject = AirTouchGroup()
            if(isGroupBased):
                groupNumber = communicate.TranslateMapValueToValue(chunk, packetInfoLocationMap["GroupNumber"]);
                if groupNumber not in resultList:
                    resultList[groupNumber] = resultObject;
                else:
                    resultObject = resultList[groupNumber];
            else:
                resultList = self.acs
                resultObject = AirTouchAc()
                acNumber = communicate.TranslateMapValueToValue(chunk, packetInfoLocationMap["AcNumber"]);
                if acNumber not in resultList:
                    resultObject.AcName = "AC " + str(acNumber)
                    resultList[acNumber] = resultObject;
                else:
                    resultObject = resultList[acNumber];
                
            packetInfoAttributes = [attr for attr in packetInfoLocationMap.keys()]
            for attribute in packetInfoAttributes:
                mapValue = communicate.TranslateMapValueToValue(chunk, packetInfoLocationMap[attribute])
                translatedValue = packetmap.SettingValueTranslator.RawValueToNamedValue(attribute, mapValue);
                #a bit dodgy, to get the mode and fanspeed as lists
                if(attribute.endswith("ModeSupported") and translatedValue != 0):
                    modeSupported = [];
                    if(hasattr(resultObject, "ModeSupported")):
                        modeSupported = resultObject.ModeSupported
                    modeSupported.append(attribute.replace("ModeSupported", ""));
                    setattr(resultObject, "ModeSupported", modeSupported)
                elif(attribute.endswith("FanSpeedSupported") and translatedValue != 0):
                    modeSupported = [];
                    if(hasattr(resultObject, "FanSpeedSupported")):
                        modeSupported = resultObject.FanSpeedSupported
                    modeSupported.append(attribute.replace("FanSpeedSupported", ""));
                    setattr(resultObject, "FanSpeedSupported", modeSupported)
                else:
                    setattr(resultObject, attribute, translatedValue)
            #read the chunk as a set of bytes concatenated together.
            #use the map of attribute locations
                #for each entry in the map
                    #read out entry value from map
                    #run translate on class matching entry name with entry value
                    #set property of entry name on the group response
    

    ## Only for AT5, get additional details

    def DecodeAirtouch5Message(self, payload, map, isGroupBased):
        normalDataLength = int.from_bytes(payload[0:2], byteorder='big')
        repeatDataLength = int.from_bytes(payload[2:4], byteorder='big')
        repeatCount = int.from_bytes(payload[4:6], byteorder='big')
        packetInfoLocationMap = map
        
        for i in range(repeatCount):
            resultList = self.groups
            resultObject = AirTouchGroup()
            chunkStart = 6+(i*repeatDataLength)
            chunk = payload[chunkStart:chunkStart+repeatDataLength]
            if(isGroupBased):
                groupNumber = communicate.TranslateMapValueToValue(chunk, packetInfoLocationMap["GroupNumber"]);
                if groupNumber not in resultList:
                    resultList[groupNumber] = resultObject;
                else:
                    resultObject = resultList[groupNumber];
            else:
                resultList = self.acs
                resultObject = AirTouchAc()
                acNumber = communicate.TranslateMapValueToValue(chunk, packetInfoLocationMap["AcNumber"]);
                if acNumber not in resultList:
                    resultList[acNumber] = resultObject;
                else:
                    resultObject = resultList[acNumber];
            self.DecodeAttributes(chunk, packetInfoLocationMap, resultObject)
    
    ## Specific for AC Ability message
    def DecodeAirtouch5AcAbility(self, payload):
        #decodes AC Abilities based on page 12 of the comms protocol.  

        
        dataLength = int.from_bytes(payload[1:3], byteorder='big')-2 #get the data length, subtract the CRC bytes and "header".  This will allow us to track size.  
        AcCount = 0
        if( dataLength % 26 != 0):
            self.Status = AirTouchStatus.ERROR
            errorMessage = AirTouchError()
            errorMessage.Message = "Got a response to ACAbility without correct field details"
            self.Messages.append(errorMessage)
            return
        else:
            AcCount = dataLength / 26
        
        payload = payload[5::]

        packetInfoLocationMap = packetmap.DataLocationTranslator.map[self.atVersion.value]["AcAbility"]
        for i in range(int(AcCount)):
            AcPayload = payload[i*26:i*26+26]
            resultList = self.acs
            resultObject = AirTouchAc()
            acNumber = communicate.TranslateMapValueToValue(AcPayload, packetInfoLocationMap["AcNumber"]);
            if acNumber not in resultList:
                resultList[acNumber] = resultObject;
            else:
                resultObject = resultList[acNumber];
            self.DecodeAttributes(AcPayload, packetInfoLocationMap, resultObject)
            zoneName = AcPayload[2:18].decode("utf-8").rstrip('\0')
            resultObject.AcName = zoneName


    def DecodeAirtouch5GroupNames(self, payload):
        #decodes group names based on page 14 of the comms protocol.  

        groups = self.groups;
        dataLength = int.from_bytes(payload[1:3], byteorder='big')-2 #get the data length, subtract the CRC bytes.  This will allow us to track size.  
        tracker = 3
        if(payload[tracker:tracker+2] == b'\xff\x13'):
            tracker = 5
            while(tracker < dataLength):
                zoneNumber = int.from_bytes(payload[tracker:tracker+1], byteorder='big')
                nameLength = int.from_bytes(payload[tracker+1:tracker+2], byteorder='big')    
                zoneName = payload[tracker+2:tracker+2+nameLength].decode("utf-8").rstrip('\0')
                tracker += (2+nameLength)
                groups[zoneNumber].GroupName = zoneName
        else:
            self.Status = AirTouchStatus.ERROR
            errorMessage = AirTouchError()
            errorMessage.Message = "Got a response to GroupNames without correct field details"
            self.Messages.append(errorMessage)
            for group in self.groups.values():
                group.GroupName = "Zone "+str(group.GroupNumber);


    def DecodeAttributes(self, chunk, packetInfoLocationMap, resultObject):
        packetInfoAttributes = [attr for attr in packetInfoLocationMap.keys()]
        for attribute in packetInfoAttributes:
            mapValue = communicate.TranslateMapValueToValue(chunk, packetInfoLocationMap[attribute])
            translatedValue = packetmap.SettingValueTranslator.RawValueToNamedValue(attribute, mapValue, AirTouchVersion.AIRTOUCH5.value);
            if(attribute.endswith("ModeSupported") and translatedValue != 0):
                modeSupported = [];
                if(hasattr(resultObject, "ModeSupported")):
                    modeSupported = resultObject.ModeSupported
                if attribute.replace("ModeSupported", "") not in modeSupported:
                    modeSupported.append(attribute.replace("ModeSupported", ""));
                setattr(resultObject, "ModeSupported", modeSupported)
            elif(attribute.endswith("FanSpeedSupported") and translatedValue != 0):
                modeSupported = [];
                if(hasattr(resultObject, "FanSpeedSupported")):
                    modeSupported = resultObject.FanSpeedSupported
                if attribute.replace("FanSpeedSupported", "") not in modeSupported:
                    modeSupported.append(attribute.replace("FanSpeedSupported", ""));
                setattr(resultObject, "FanSpeedSupported", modeSupported)
            else:
                setattr(resultObject, attribute, translatedValue)
    
    def DecodeAirtouchGroupStatusMessage(self, payload):
        self.DecodeAirtouchMessage(payload, packetmap.DataLocationTranslator.map[self.atVersion.value]["GroupStatus"], True, 6);
    
    def DecodeAirtouch5ZoneStatusMessage(self, payload):
        self.DecodeAirtouch5Message(payload, packetmap.DataLocationTranslator.map[self.atVersion.value]["GroupStatus"], True);

    def DecodeAirtouchAcStatusMessage(self, payload):
        self.DecodeAirtouchMessage(payload, packetmap.DataLocationTranslator.map[self.atVersion.value]["AcStatus"], False, 8);
            #read the chunk as a set of bytes concatenated together.
            #use the map of attribute locations
                #for each entry in the map
                    #read out entry value from map
                    #run translate on class matching entry name with entry value
                    #set property of entry name on the group response
    def DecodeAirtouch5AcStatusMessage(self, payload):
        self.DecodeAirtouch5Message(payload, packetmap.DataLocationTranslator.map[self.atVersion.value]["AcStatus"], False);
    
    def _getTargetGroup(self, groupName):
        return [group for group in self.groups.values() if group.GroupName == groupName][0]
    
