import sys

import asyncio
import time

from airtouch4pyapi import AirTouch, AirTouchStatus, AirTouchVersion

def print_groups(groups):
    for group in groups:
        print(f"Group Name: {group.GroupName:15s} Group Number: {group.GroupNumber:3d} PowerState: {group.PowerState:3s} IsOn: {group.IsOn} OpenPercent: {group.OpenPercent:3d} Temperature: {group.Temperature:3.1f} Target: {group.TargetSetpoint:3.1f} BelongToAc: {group.BelongsToAc:2d}")


def print_acs(acs):
    for ac in acs:
        print(f"AC Name: {ac.AcName:15s} AC Number: {ac.AcNumber:3d} IsOn: {ac.IsOn} PowerState: {ac.PowerState:3s} Target: {ac.AcTargetSetpoint:3.1f} Temp: {ac.Temperature:3.1f} Modes Supported: {ac.ModeSupported} Fans Supported: {ac.FanSpeedSupported} startGroup: {ac.StartGroupNumber: 2d} GroupCount: {ac.GroupCount:2d}")

async def updateInfoAndDisplay(ip) -> asyncio.coroutine:
    at = AirTouch(ip)
    await at.UpdateInfo()
    if(at.Status != AirTouchStatus.OK):
        print("Got an error updating info.  Exiting")
        return
    print("Updated Info on Groups (Zones) and ACs")
    print("AC INFO")
    print("----------")
    acs = at.GetAcs()
    print_acs(acs)
    print("----------\n\n")
    print("GROUP/ZONE INFO")
    print("----------")
    groups = at.GetGroups()
    print_groups(groups)
    val = input("Do you want to turn them all off, wait 10 seconds, turn them all back on? (y/n): ")
    if(val.lower() == "y"):
        for group in groups:
            await at.TurnGroupOffByName(group.GroupName)
        print("GROUP/ZONE INFO AFTER TURNING ALL OFF")
        print("----------")
        print_groups(groups)
        time.sleep(10)
        for group in groups:
            await at.TurnGroupOnByName(group.GroupName)
        await at.TurnAcOn(0)
        print("GROUP/ZONE INFO AFTER TURNING ALL ON")
        print("----------")
        print_groups(groups)
    val = input("Do you want to increment set points by 1 degree then back down by 1? (y/n): ")
    if(val.lower() == "y"):
        for group in groups:
            to_temp = int(group.TargetSetpoint) + 1
            await at.SetGroupToTemperatureByGroupName(group.GroupName, to_temp)
        print("GROUP/ZONE INFO AFTER SET TEMP + 1")
        print("----------")
        print_groups(groups)
        time.sleep(5)
        for group in groups:
            to_temp = int(group.TargetSetpoint) -1
            await at.SetGroupToTemperatureByGroupName(group.GroupName, to_temp)
        print("GROUP/ZONE INFO AFTER SET TEMP + 1")
        print("----------")
        print_groups(groups)
        
    val = input("Do you want to set group 0's mode to heat then back to cool? (y/n): ")
    if(val.lower() == "y"):
        await at.SetCoolingModeByGroup(0, 'Heat')
        print("AC INFO AFTER SETTING GROUP 0 to HEAT")
        print("----------")
        print_acs(acs)
        time.sleep(5)
        await at.SetCoolingModeByGroup(0, 'Cool')
        print("AC INFO AFTER SETTING GROUP 0 to COOL")
        print("----------")
        print_acs(acs)
#    await at.TurnGroupOff(0)
#    print("Turned off group 0, sleeping 4")
#    time.sleep(4);
#    await at.TurnGroupOn(0)
#    print("Turned on group 0")
    
#    await at.TurnAcOff(0)
#    print("Turned off ac 0, sleeping 4")
#    time.sleep(4);
#    await at.TurnAcOn(0)
#    print("Turned on ac 0")
#    print(at.GetSupportedFanSpeedsByGroup(0))
#    await at.SetGroupToPercentByGroupName("Zone 1", 5)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("nom nom nom give me an IP of an AirTouch system")
        sys.exit(1)
    asyncio.run(updateInfoAndDisplay(sys.argv[1]))
    
