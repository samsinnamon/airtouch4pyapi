#region Message Mapping Values
class SettingValueTranslator:
    map = {
        4 : {
            "MessageType" : {
                "GroupControl": 0x2a,
                "GroupStatus": 0x2b,
                "AcControl": 0x2c,
                "AcStatus": 0x2d,
                "GroupName": 0x1e,
            },
            "AcMode" : {
                "Auto": 0x00,
                "Heat": 0x01,
                "Dry": 0x02,
                "Fan": 0x03,
                "Cool": 0x04,
                "AutoHeat": 0x08,
                "AutoCool": 0x09,

            },
            "AcFanSpeed" : {
                "Auto": 0x00,
                "Quiet": 0x01,
                "Low": 0x02,
                "Medium": 0x03,
                "High": 0x04,
                "Powerful": 0x05,
                "Turbo": 0x06,
            },
            "YesNo" : {
                "Yes": 0x01,
                "No": 0x00,
            },
            "PowerState" : {
                "Off": 0b00000000,
                "On" : 0b00000001,
                "Turbo" : 0b00000011
            },
            "ControlMethod": {
                "TemperatureControl": 0x01,
                "PercentageControl": 0x00
            },
            "BatteryLow": {
                "LowBattery": 0x01,
                "Normal": 0x00
            },
            "Sensor": {
                "Yes": 0x01,
                "No": 0x00
            },
            "AcTimer": {
                "Set": 0x01,
                "NotSet": 0x00
            },
            "Spill": {
                "Active": 0x01,
                "Inactive": 0x00
            },
            "Turbo": {
                "Active": 0x01,
                "Inactive": 0x00
            },
            "Bypass": {
                "Active": 0x01,
                "Inactive": 0x00
            },
            "Temperature" : {
                "TranslateMethod" : lambda x : (x-500) / 10
            }
        },
        5 : {
            "MessageType" : {
                "GroupControl": 0x20,
                "GroupStatus": 0x21,
                "AcControl": 0x22,
                "AcStatus": 0x23,
                "GroupName": 0x1e,
            },
            "AcMode" : {
                "Auto": 0x00,
                "Heat": 0x01,
                "Dry": 0x02,
                "Fan": 0x03,
                "Cool": 0x04,
                "AutoHeat": 0x08,
                "AutoCool": 0x09,

            },
            "AcFanSpeed" : {
                "Auto": 0x00,
                "Quiet": 0x01,
                "Low": 0x02,
                "Medium": 0x03,
                "High": 0x04,
                "Powerful": 0x05,
                "Turbo": 0x06,
            },
            "YesNo" : {
                "Yes": 0x01,
                "No": 0x00,
            },
            "PowerState" : {
                "Off": 0b00000000,
                "On" : 0b00000001,
                "Turbo" : 0b00000011
            },
            "ControlMethod": {
                "TemperatureControl": 0x01,
                "PercentageControl": 0x00
            },
            "BatteryLow": {
                "LowBattery": 0x01,
                "Normal": 0x00
            },
            "Sensor": {
                "Yes": 0x01,
                "No": 0x00
            },
            "AcTimer": {
                "Set": 0x01,
                "NotSet": 0x00
            },
            "Spill": {
                "Active": 0x01,
                "Inactive": 0x00
            },
            "Turbo": {
                "Active": 0x01,
                "Inactive": 0x00
            },
            "Bypass": {
                "Active": 0x01,
                "Inactive": 0x00
            },
            "Temperature" : {
                "TranslateMethod" : lambda x : (x-500) / 10
            },
            "AcTargetSetpoint" : {
                "TranslateMethod" : lambda x : (x+100) / 10
            },
            "TargetSetpoint" : {
                "TranslateMethod" : lambda x : (x+100) / 10
            }
        }
    }

    def __init__(self):
        pass

    @staticmethod
    def NamedValueToRawValue(attributeName: str, name: str, atVersion = 4):
        return SettingValueTranslator.map[atVersion][attributeName][name];
        
    @staticmethod
    def RawValueToNamedValue(attributeName: str, rawValue: int, atVersion = 4):
        if attributeName not in SettingValueTranslator.map[atVersion].keys():
            return rawValue
        for namedValue in SettingValueTranslator.map[atVersion][attributeName].keys():
            if "TranslateMethod" in SettingValueTranslator.map[atVersion][attributeName].keys():
                return SettingValueTranslator.map[atVersion][attributeName]["TranslateMethod"](rawValue)
            if(SettingValueTranslator.map[atVersion][attributeName][namedValue] == rawValue):
                return namedValue;
        return ""


class DataLocationTranslator:
    map = {
        4 : {
            "GroupStatus" : {
                "PowerState" : "1:7-8",
                "GroupNumber" : "1:1-6",
                "ControlMethod" : "2:8-8",
                "OpenPercent" : "2:1-7",
                "BatteryLow" : "3:8-8",
                "TurboSupport" : "3:7-7",
                "TargetSetpoint" : "3:1-6",
                "Sensor" : "4:8-8",
                "Temperature" : "5:6-16",
                "Spill": "6:5-5"
            },
            "AcStatus" : {
                "PowerState" : "1:7-8",
                "AcNumber" : "1:1-6",
                "AcMode" : "2:5-8",
                "AcFanSpeed" : "2:1-4",
                "Spill" : "3:8-8",
                "AcTimer" : "3:7-7",
                "AcTargetSetpoint" : "3:1-6",
                "Temperature" : "5:6-16",
            },
            "GroupControl" : {
                "GroupNumber" : "1:1-8",
                "GroupSettingValue" : "2:6-8",
                "HaveTemperatureControl" : "2:4-5",
                "Power" : "2:1-3",
                "TargetSetpoint" : "3:1-8",
                "ZeroedByte" : "4:1-8"
            },
            "AcControl" : {
                "Power" : "1:7-8",
                "AcNumber" : "1:1-6",
                "AcMode" : "2:5-8",
                "AcFanSpeed" : "2:1-4",
                "SetpointControlType" : "3:7-8",
                "TargetSetpoint" : "3:1-6",
                "ZeroedByte" : "4:1-8"
            },
            "AcAbility" : {
                #byte number - 2 from the spec, due to fixed message at start
                "AcNumber" : "1:1-8",
                "ChunkSize" : "2:1-8",
                "StartGroupNumber" : "19:1-8",
                "GroupCount" : "20:1-8",
                "CoolModeSupported" : "21:5-5",
                "FanModeSupported" : "21:4-4",
                "DryModeSupported" : "21:3-3",
                "HeatModeSupported" : "21:2-2",
                "AutoModeSupported" : "21:1-1",
                "TurboFanSpeedSupported" : "22:7-7",
                "PowerfulFanSpeedSupported" : "22:6-6",
                "HighFanSpeedSupported" : "22:5-5",
                "MediumFanSpeedSupported" : "22:4-4",
                "LowFanSpeedSupported" : "22:3-3",
                "QuietFanSpeedSupported" : "22:2-2",
                "AutoFanSpeedSupported" : "22:1-1",
                "MinSetpoint" : "23:1-8",
                "MaxSetpoint" : "24:1-8"
            },
            "GroupName" : { #TODO
            }
        },
        5 : {
                
            "GroupStatus" : {
                "PowerState" : "1:7-8",
                "GroupNumber" : "1:1-6",
                "ControlMethod" : "2:8-8",
                "OpenPercent" : "2:1-7",
                "BatteryLow" : "7:1-1",
                "TargetSetpoint" : "3:1-8",
                "Sensor" : "4:8-8",
                "Temperature" : "5:1-16",
                "Spill": "7:2-2"
            },

            "AcStatus" : {
                "PowerState" : "1:5-8",
                "AcNumber" : "1:1-4",
                "AcMode" : "2:5-8",
                "AcFanSpeed" : "2:1-4",
                "Spill" : "4:2-2",
                "Turbo" : "4:4-4",
                "Bypass" : "4:3-3",
                "AcTimer" : "4:1-1",
                "AcTargetSetpoint" : "3:1-8",
                "Temperature" : "5:1-16",
            },
            "GroupControl" : {
                "GroupNumber" : "1:1-6",
                "GroupSettingValue" : "2:6-8",
                "Power" : "2:1-3",
                "TargetSetpoint" : "3:1-8",
                "ZeroedByte" : "4:1-8"
            },
            "AcControl" : {
                "Power" : "1:5-8",
                "AcNumber" : "1:1-4",
                "AcMode" : "2:5-8",
                "AcFanSpeed" : "2:1-4",
                "SetpointControlType" : "3:1-8",
                "TargetSetpoint" : "4:1-8"
            },
            "AcAbility" : {
                #byte number - 2 from the spec, due to fixed message at start
                "AcNumber" : "1:1-8",
                "ChunkSize" : "2:1-8",
                "StartGroupNumber" : "19:1-8",
                "GroupCount" : "20:1-8",
                "CoolModeSupported" : "21:5-5",
                "FanModeSupported" : "21:4-4",
                "DryModeSupported" : "21:3-3",
                "HeatModeSupported" : "21:2-2",
                "AutoModeSupported" : "21:1-1",
                "TurboFanSpeedSupported" : "22:7-7",
                "PowerfulFanSpeedSupported" : "22:6-6",
                "HighFanSpeedSupported" : "22:5-5",
                "MediumFanSpeedSupported" : "22:4-4",
                "LowFanSpeedSupported" : "22:3-3",
                "QuietFanSpeedSupported" : "22:2-2",
                "AutoFanSpeedSupported" : "22:1-1",
                "MinSetpoint" : "23:1-8",
                "MaxSetpoint" : "24:1-8"
            },
            "GroupName" : { #TODO
            }
        }
        
    }

class Message():
    def __init__(self, messageType):
        self.MessageValues = dict();
        self.MessageType = messageType;
        pass
    def SetMessageValue(self, propertyName, newValue):
        self.MessageValues[propertyName] = newValue
    

class MessageFactory:
    @staticmethod
    def CreateEmptyMessageOfType(messageType, atVersion):
        message = Message(messageType);
        for attr in DataLocationTranslator.map[atVersion.value][messageType]:
            message.MessageValues[attr] = 0;
        return message;
#endregion