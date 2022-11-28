import socket
from typing import List
from airtouch4pyapi import helper
from airtouch4pyapi import packetmap
from airtouch4pyapi import communicate
from enum import Enum
#### CEMIL TEST
from hexdump import hexdump
from pprint import pprint

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
    NOT_CONNECTED = 0,
    OK = 1,
    CONNECTION_INTERRUPTED = 2,
    CONNECTION_LOST = 3,
    ERROR = 4

class AirTouchVersion(Enum):
    AIRTOUCH4 = 4,
    AIRTOUCH5 = 5

class AirTouchGroup:
    def __init__(self):
        self.GroupName = ""
        self.GroupNumber = 0
        self.IsOn = True
        self.OpenPercent = 0
        self.Temperature = 0
        self.TargetSetpoint = 0
        self.BelongsToAc = -1

class AirTouchError:
    def __init__(self):
        self.Message = ""
        self.Status = AirTouchStatus.OK

class AirTouchAc:
    def __init__(self):
        self.AcName = ""
        self.AcNumber = 0
        self.IsOn = True

class AirTouch:
    IpAddress = "";
    SettingValueTranslator = packetmap.SettingValueTranslator();
    def __init__(self, ipAddress, atVersion = AirTouchVersion.AIRTOUCH4):
        self.IpAddress = ipAddress;
        self.Status = AirTouchStatus.NOT_CONNECTED;
        self.Messages = dict();
        self.atVersion = atVersion;
    
    async def UpdateInfo(self):
        # Init ACs and Groups (AirTouch4)/Zones(AirTouch5)

        self.acs = dict();
        self.groups = dict();

        self.Messages:List[AirTouchError] = [];


        #get the group infos
        await self.UpdateGroupInfo()
        
        #if the first call means we still have an error status, not worth doing the subsequent ones
        if(self.Status != AirTouchStatus.OK):
            print(AirTouchStatus)
            for msg in self.Messages:
                print(msg.Message);
            return;
        
        #get the group nicknames // Appears to be unused anyway
        await self.UpdateGroupNames()
        
        #get ac infos
        await self.UpdateAcInfo()
        
        #sort out which AC belongs to which zone/group
        await self.AssignAcsToGroups()


    async def AssignAcsToGroups(self):
        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
            #allocate acs to groups (ac ability?)

            acAbilityMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcAbility", self.atVersion);
            await self.SendMessageToAirtouch(acAbilityMessage)

            for group in self.groups.values():
                #find out which ac this group belongs to
                for ac in self.acs.values():
                    if(ac.StartGroupNumber == 0 and ac.GroupCount == 0):
                        #assuming this means theres only one ac? so every group belongs to this ac? 
                        group.BelongsToAc = ac.AcNumber
                    if(ac.StartGroupNumber <= group.GroupNumber and ac.StartGroupNumber + ac.GroupCount <= group.GroupNumber):
                        group.BelongsToAc = ac.AcNumber
        elif(self.atVersion == AirTouchVersion.AIRTOUCH5):
            ### TODO special casing because I don't have v 1.0.3 and can't test the extended status call. 
            if(len(self.acs) == 1):
                for group in self.groups.values():
                    group.BelongsToAc = 0;

    async def UpdateAcInfo(self):
        message = packetmap.MessageFactory.CreateEmptyMessageOfType("AcStatus", self.atVersion);
        await self.SendMessageToAirtouch(message)

    async def UpdateGroupInfo(self):
        message = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupStatus", self.atVersion);
        await self.SendMessageToAirtouch(message)
    
    async def UpdateGroupNames(self):
        nameMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupName", self.atVersion);
        await self.SendMessageToAirtouch(nameMessage)

        if(self.Status != AirTouchStatus.OK and self.atVersion == AirTouchVersion.AIRTOUCH5):
            # Likely AT5 version < 1.0.3, so update group names to just be Zone + number
            for group in self.groups.values():
                group.GroupName = "Zone "+str(group.GroupNumber);
    ## Verified in AT5
    async def TurnGroupOnByName(self, groupName):
        targetGroup = self._getTargetGroup(groupName)
        await self.TurnGroupOn(targetGroup.GroupNumber);
    ## Verified in AT5
    async def TurnGroupOffByName(self, groupName):
        targetGroup = self._getTargetGroup(groupName)
        await self.TurnGroupOff(targetGroup.GroupNumber);
    
    ## Verified in AT5
    async def SetGroupToTemperatureByGroupName(self, groupName, temperature):
        targetGroup = self._getTargetGroup(groupName)
        await self.SetGroupToTemperature(targetGroup.GroupNumber, temperature);

    async def SetGroupToPercentByGroupName(self, groupName, percent):
        targetGroup = self._getTargetGroup(groupName)
        await self.SetGroupToPercentage(targetGroup.GroupNumber, percent);

    async def SetCoolingModeByGroup(self, groupNumber, coolingMode):
        self.SetCoolingModeForAc(self.groups[groupNumber].BelongsToAc, coolingMode);
        return self.groups[groupNumber];

    async def SetFanSpeedByGroup(self, groupNumber, fanSpeed):
        await self.SetFanSpeedForAc(self.groups[groupNumber].BelongsToAc, fanSpeed);
        return self.groups[groupNumber];

    def GetSupportedCoolingModesByGroup(self, groupNumber):
        return self.GetSupportedCoolingModesForAc(self.groups[groupNumber].BelongsToAc);

    def GetSupportedFanSpeedsByGroup(self, groupNumber):
        return self.GetSupportedFanSpeedsForAc(self.groups[groupNumber].BelongsToAc);


    ## Verified in AT5
    async def TurnGroupOn(self, groupNumber):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupControl", self.atVersion);
        controlMessage.SetMessageValue("Power", 3)
        controlMessage.SetMessageValue("GroupNumber", groupNumber)
        await self.SendMessageToAirtouch(controlMessage)
        return self.groups[groupNumber];
    
    ## Verified in AT5
    async def TurnGroupOff(self, groupNumber):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupControl", self.atVersion);
        controlMessage.SetMessageValue("Power", 2)
        controlMessage.SetMessageValue("GroupNumber", groupNumber)
        await self.SendMessageToAirtouch(controlMessage)
        return self.groups[groupNumber];
    ## Verified in AT5
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
    ## Verified in AT5

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
    

    #use a fanspeed reported from GetSupportedFanSpeedsForAc
    async def SetFanSpeedForAc(self, acNumber, fanSpeed):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcControl");
        #these are required to leave these settings unchanged
        controlMessage.SetMessageValue("AcMode", 0x0f);
        controlMessage.SetMessageValue("AcFanSpeed", packetmap.SettingValueTranslator.NamedValueToRawValue("AcFanSpeed", fanSpeed));
        controlMessage.SetMessageValue("TargetSetpoint", 0x3f);

        controlMessage.SetMessageValue("AcNumber", acNumber)
        await self.SendMessageToAirtouch(controlMessage)

    #use a mode reported from GetSupportedCoolingModesForAc
    async def SetCoolingModeForAc(self, acNumber, acMode):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcControl");
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



    ## Verified in AT5
    async def SetGroupToTemperature(self, groupNumber, temperature):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupControl", self.atVersion);
        controlMessage.SetMessageValue("Power", 3)
        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
            controlMessage.SetMessageValue("HaveTemperatureControl", 3)
        controlMessage.SetMessageValue("GroupSettingValue", 5)
        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
            controlMessage.SetMessageValue("TargetSetpoint", temperature)
        elif(self.atVersion == AirTouchVersion.AIRTOUCH5):
            controlMessage.SetMessageValue("TargetSetpoint", int(temperature)*10-100)
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
                MESSAGE = communicate.MessageObjectToMessagePacket(messageObject, messageObject.MessageType);
        
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
                MESSAGE = communicate.MessageObject5ToMessagePacket(messageObject, messageObject.MessageType);
        try: 
            dataResult = await communicate.SendMessagePacketToAirtouch(MESSAGE, self.IpAddress, self.atVersion)
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


    def TranslatePacketToMessage(self, dataResult):
        #If the request hasn't gone well, we don't want to update any of the data we have with bad/no data
        if(self.Status != AirTouchStatus.OK):
            return;
        if(self.atVersion == AirTouchVersion.AIRTOUCH4):
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
            messageType = dataResult[17:18]
            messageSubType = dataResult[20:21]
            if(messageType == b'\xc0'):
                ### We got a control message
                if(messageSubType == b'\x21'):
                    ### Zone Status Message
                    self.DecodeAirtouch5ZoneStatusMessage(dataResult[22::]);
                if(messageSubType == b'\x23'):
                    ### AC Status Message
                    self.DecodeAirtouch5AcStatusMessage(dataResult[22::]);
    
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
            packetInfoAttributes = [attr for attr in packetInfoLocationMap.keys()]
            for attribute in packetInfoAttributes:
                mapValue = communicate.TranslateMapValueToValue(chunk, packetInfoLocationMap[attribute])
                translatedValue = packetmap.SettingValueTranslator.RawValueToNamedValue(attribute, mapValue, AirTouchVersion.AIRTOUCH5.value);
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