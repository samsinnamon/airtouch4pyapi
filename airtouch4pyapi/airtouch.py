import socket
from airtouch4pyapi import helper
from airtouch4pyapi import packetmap
from airtouch4pyapi import communicate
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

class AirTouchGroup:
    def __init__(self):
        self.GroupName = ""
        self.GroupNumber = 0
        self.IsOn = True
        self.OpenPercent = 0
        self.Temperature = 0
        self.TargetSetpoint = 0
        self.BelongsToAc = -1

class AirTouchAc:
    def __init__(self):
        self.AcName = ""
        self.AcNumber = 0
        self.IsOn = True

class AirTouch:
    IpAddress = "";
    SettingValueTranslator = packetmap.SettingValueTranslator();
    def __init__(self, ipAddress):
        self.IpAddress = ipAddress;

    async def UpdateInfo(self):
        #if we are trying to call this again, clear out the errors from last time - we want to still
        #be able to keep going if theres a hiccup such as a bad network connection
        if hasattr(self, "error"):
            delattr(self, "error");
        self.acs = dict();
        self.groups = dict();
        #get the group infos
        message = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupStatus");
        await self.SendMessageToAirtouch(message)

        #if the first call gets an error, not worth doing the subsequent ones
        if hasattr(self, "error"):
            return;
        #get the group nicknames
        nameMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupName");
        await self.SendMessageToAirtouch(nameMessage)

        #get ac infos
        acsMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcStatus");
        await self.SendMessageToAirtouch(acsMessage)

        #allocate acs to groups (ac ability?)
        acAbilityMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcAbility");
        await self.SendMessageToAirtouch(acAbilityMessage)

        for group in self.groups.values():
            #find out which ac this group belongs to
            for ac in self.acs.values():
                if(ac.StartGroupNumber == 0 and ac.GroupCount == 0):
                    #assuming this means theres only one ac? so every group belongs to this ac? 
                    group.BelongsToAc = ac.AcNumber
                if(ac.StartGroupNumber <= group.GroupNumber and ac.StartGroupNumber + ac.GroupCount <= group.GroupNumber):
                    group.BelongsToAc = ac.AcNumber

    async def TurnGroupOnByName(self, groupName):
        targetGroup = self._getTargetGroup(groupName)
        await self.TurnGroupOn(targetGroup.GroupNumber);

    async def TurnGroupOffByName(self, groupName):
        targetGroup = self._getTargetGroup(groupName)
        await self.TurnGroupOff(targetGroup.GroupNumber);
    
    async def SetGroupToTemperatureByGroupName(self, groupName, temperature):
        targetGroup = self._getTargetGroup(groupName)
        await self.SetGroupToTemperature(targetGroup.GroupNumber, temperature);

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

    async def TurnGroupOn(self, groupNumber):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupControl");
        controlMessage.SetMessageValue("Power", 3)
        controlMessage.SetMessageValue("GroupNumber", groupNumber)
        await self.SendMessageToAirtouch(controlMessage)
        return self.groups[groupNumber];

    async def TurnAcOn(self, acNumber):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcControl");
        #these are required to leave these settings unchanged
        controlMessage.SetMessageValue("AcMode", 0x0f);
        controlMessage.SetMessageValue("AcFanSpeed", 0x0f);
        controlMessage.SetMessageValue("TargetSetpoint", 0x3f);

        controlMessage.SetMessageValue("Power", 3)
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

    async def TurnAcOff(self, acNumber):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("AcControl");
        #these are required to leave these settings unchanged
        controlMessage.SetMessageValue("AcMode", 0x0f);
        controlMessage.SetMessageValue("AcFanSpeed", 0x0f);
        controlMessage.SetMessageValue("TargetSetpoint", 0x3f);

        controlMessage.SetMessageValue("Power", 2)
        controlMessage.SetMessageValue("AcNumber", acNumber)
        await self.SendMessageToAirtouch(controlMessage)
    
    async def TurnGroupOff(self, groupNumber):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupControl");
        controlMessage.SetMessageValue("Power", 2)
        controlMessage.SetMessageValue("GroupNumber", groupNumber)
        await self.SendMessageToAirtouch(controlMessage)
        return self.groups[groupNumber];

    async def SetGroupToTemperature(self, groupNumber, temperature):
        controlMessage = packetmap.MessageFactory.CreateEmptyMessageOfType("GroupControl");
        controlMessage.SetMessageValue("Power", 3)
        controlMessage.SetMessageValue("HaveTemperatureControl", 3)
        controlMessage.SetMessageValue("GroupSettingValue", 5)
        controlMessage.SetMessageValue("TargetSetpoint", temperature)
        controlMessage.SetMessageValue("GroupNumber", groupNumber)
        await self.SendMessageToAirtouch(controlMessage)
        return self.groups[groupNumber];
        #should this turn the group on?

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
        
        dataResult = await communicate.SendMessagePacketToAirtouch(MESSAGE, self.IpAddress)
        return self.TranslatePacketToMessage(dataResult)


    def TranslatePacketToMessage(self, dataResult):
        #If the request hasn't gone well, we don't want to update any of the data we have with bad/no data
        if(isinstance(dataResult, Exception)):
            self.error = dataResult;
            return;
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
            chunkSize = communicate.TranslateMapValueToValue(payload[2:], packetmap.DataLocationTranslator.map["AcAbility"]["ChunkSize"]);
            self.DecodeAirtouchMessage(payload[2:], packetmap.DataLocationTranslator.map["AcAbility"], False, chunkSize + 2)

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
    def DecodeAirtouchGroupStatusMessage(self, payload):
        self.DecodeAirtouchMessage(payload, packetmap.DataLocationTranslator.map["GroupStatus"], True, 6);
    
    def DecodeAirtouchAcStatusMessage(self, payload):
        self.DecodeAirtouchMessage(payload, packetmap.DataLocationTranslator.map["AcStatus"], False, 8);
            #read the chunk as a set of bytes concatenated together.
            #use the map of attribute locations
                #for each entry in the map
                    #read out entry value from map
                    #run translate on class matching entry name with entry value
                    #set property of entry name on the group response

    def _getTargetGroup(self, groupName):
        return [group for group in self.groups.values() if group.GroupName == groupName][0]