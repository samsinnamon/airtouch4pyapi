# This code is a Python script for controlling air conditioning units using the AirTouch4pyapi library. The script can either retrieve information from the Air Touch unit or change the status of the unit. The script uses argparse to specify the command line arguments which are then used to call functions in the AirTouch library.
# The code provides two main functions: getInfo and setStatus. The getInfo function retrieves information from the Air Touch unit and prints it in JSON format. The setStatus function sets the status of either a group of air conditioning units or an individual air conditioning unit.

import sys
import argparse
import json
import asyncio

# Import the AirTouch and its related classes
from airtouch4pyapi import AirTouch, AirTouchStatus, AirTouchVersion

# Function to print groups in JSON format
def print_groups_json(groups):
   # Convert group objects to dictionaries
   group_dicts = [group.to_dict() for group in groups]
   # Use json.dumps to print the result in indented format
   result = json.dumps(group_dicts, indent=4)
   print(result)

# Function to print air conditioning units in JSON format
def print_acs_json(acs):
   # Convert air conditioning unit objects to dictionaries
   ac_dicts = [ac.to_dict() for ac in acs]
   # Use json.dumps to print the result in indented format
   result = json.dumps(ac_dicts, indent=4)
   print(result)

# Function to print both groups and air conditioning units in JSON format
def print_all_json(groups, acs):
    # Convert group objects to dictionaries
    group_dicts = [group.to_dict() for group in groups]
    # Convert air conditioning unit objects to dictionaries
    ac_dicts = [ac.to_dict() for ac in acs]
    # Combine both dictionaries into a single dictionary
    result = {
        "groups": group_dicts,
        "acs": ac_dicts
    }
    # Use json.dumps to print the result in indented format
    print(json.dumps(result, indent=4))

# Asynchronous function to get information
async def getInfo(args) -> asyncio.coroutine:
    # Create an instance of the AirTouch class
    at = AirTouch(args.ip)
    # Update the information
    await at.UpdateInfo()
    # Check if the status is OK
    if(at.Status != AirTouchStatus.OK):
        print("Got an error updating info.  Exiting")
        exit(1)
    # Get the list of air conditioning units
    acs = at.GetAcs()
    # Get the list of groups
    groups = at.GetGroups()
   
    # Call the print_all_json function to print the result
    print_all_json(groups,acs)

# Asynchronous function to set the status
async def setStatus(args) -> asyncio.coroutine:
    # Create an instance of the AirTouch class
    at = AirTouch(args.ip)
    # Update the information
    await at.UpdateInfo()
    # Check if the status is OK
    if(at.Status != AirTouchStatus.OK):
        print("got an error updating info.  Exiting")
        exit(1)

    # Perform operations on the group (zone)
    if args.groupname is not None:
        
        # If the target temperature argument is passed
        if args.targettemp is not None:
            # set the temperature
            print ("Setting Group '" + args.groupname + "' to temperature " + str(args.targettemp))
            await at.SetGroupToTemperatureByGroupName(args.groupname, args.targettemp)

        # the powerstate argument is shared with the ac unit args
        if args.powerstate == "On":
            print ("Setting Group '" + args.groupname + "' powerstate to " + args.powerstate)
            await at.TurnGroupOnByName(args.groupname)
            # any "on" operations require the ac unit to also be on to be effective
        elif args.powerstate == "Off":
            print ("Setting Group '" + args.groupname + "' powerstate to " + args.powerstate)
            await at.TurnGroupOffByName(args.groupname)

    # now perform any ac unit operations
    if args.acnumber is not None:

        # several options depending on which args are passed - multiple actions may be taken
        if args.mode is not None:
            print ("Setting AC Unit '" + str(args.acnumber) + "' to mode " + str(args.mode))
            await at.SetCoolingModeByGroup(args.acnumber, args.mode)

        # the powerstate argument is shared with the group (zone) args
        if args.powerstate == "On":
            print ("Setting AC Unit '" + str(args.acnumber) + "' to powerstate " + str(args.powerstate))
            await at.TurnAcOn(args.acnumber)
        elif args.powerstate == "Off":
            print ("Setting AC Unit '" + str(args.acnumber) + "' to powerstate " + str(args.powerstate))
            await at.TurnAcOff(args.acnumber)
            
    print ("Set for Group '" + args.groupname + "' completed")
        

# ------------------------------------------------------------------------------
def main():
   """ Start airtouch command line """

#   Usage:
#
#   get the status of the unit and groups (zones) in JSON format
#   control.py -f get -i IP 
#
#   set the state of a group (zone)
#   control.py -f set -i IP -g GROUPNAME [-t TARGETTEMP] [-p POWERSTATE]
#
#   set the state of an ac unit
#   control.py -f set -i IP -c ACNUMBER [-p POWERSTATE] [-m MODE]
#
#   set the state of a group (zone) and an ac unit at the same time
#   note that the POWERSTATE is shared by the group (zone) and the ac unit and hence can only be the same value for both
#   control.py -f set -i IP -g GROUPNAME [-t TARGETTEMP] [-p POWERSTATE] -c ACNUMBER [-m MODE]
#   
#   FUNC       get or set
#   IP         DNS name or IP Address of Air Touch unit
#   GROUPNAME  name of the group (zone) to operate on
#   ACNUMBER   number of the ac unit to operate on 
#   TARGETTEMP target temperature for the group (zone)
#   POWERSTATE powerstate for the group (zone) or ac unit
#   MODE       operation mode for the ac unit
   
   parser = argparse.ArgumentParser(description='Read or change status of Air Touch devices')

   # define the arguments as per the Usage comment above
   parser.add_argument('-f', '--func', type=str, choices=[ 'get', 'set' ], help='mode to run the script in', required=True)
   parser.add_argument('-i', '--ip', type=str,  help='DNS name or IP address of the Air Touch unit', required=True)
   parser.add_argument('-p', '--powerstate', type=str, choices=[ 'On', 'Off' ],  help='Configure the power status of a group (zone) or ac unit')
   parser.add_argument('-t', '--targettemp', type=int,  help='Configure the target temperature of a group(zone)')
   parser.add_argument('-m', '--mode', type=str, choices=[ 'Heat', 'Cool', 'Fan', 'Dry', 'Auto' ],  help='Configure the operating mode of the ac unit')
   parser.add_argument('-g', '--groupname', type=str, help='The name of group (zone) to operate on')
   parser.add_argument('-c', '--acnumber', type=int, help='The number of the ac unit to operate on')

   args = parser.parse_args()

   if len(sys.argv) == 1:
      parser.print_usage()
      sys.exit(1)
      
   if args.func == "get":
      asyncio.run(getInfo(args))

   if args.func == "set":
      asyncio.run(setStatus(args))

# ------------------------------------------------------------------------------
if __name__ == "__main__":
   main()
