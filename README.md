# Airtouch 4 & 5 Python TCP API
An api allowing control of AC state (temperature, on/off, mode) of an Airtouch 4 controller locally over TCP.  Airtouch 5 support is experimental as of 28 Nov 2022, and is fully interface compatible with AT4.  

All you need to do is initialise and specify the correct AirTouchVersion (if you don't, it assumes 4).  

## Warning
I am using this with my own Airtouch 4 and see no issues. Please don't blame me if you have any issues with your Airtouch 4 or AC system after using this - I don't know much about AC systems and will probably not be able to help!

Others are using it with Airtouch 5 and see no issues.  

## Usage
To initialise:
* `airTouch = AirTouch("192.168.1.19")`
* `airTouch = AirTouch("192.168.1.1", AirTouchVersion.AIRTOUCH5)`

As a test:

Use the demo.py file and pass in an AirTouch IP.  It takes you through a few tests.  

## Notes
AirTouch5: If you turn off all zones, the AC itself turns off.  Turning on a zone does not turn the AC back on by itself.  You must turn it back on too.  Same behaviour in 'official' app.  

To load:
* `await airTouch.UpdateInfo();` -- This loads the config from the AirTouch.  Make sure you check for any errors before using it.  It will load the Group/Zone info, the AC info, then capabilities.  This needs to happen prior to using. 

The following functions are available:

Group Level Functions:
* `SetGroupToTemperature` (async)
* `TurnGroupOn` (async)
* `TurnGroupOff` (async)
* `SetCoolingModeByGroup` (async)
* `SetFanSpeedByGroup` (async)
* `GetSupportedCoolingModesByGroup` -- Based on the loaded config.
* `GetSupportedFanSpeedsByGroup` -- Based on the loaded config.

AC Level Functions
* `TurnAcOn` (async)
* `TurnAcOff` (async)
* `SetFanSpeedForAc` (async)
* `SetCoolingModeForAc` (async)
* `GetSupportedCoolingModesForAc`
* `GetSupportedFanSpeedsForAc`
* `GetAcs`

