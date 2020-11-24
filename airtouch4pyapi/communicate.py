from airtouch4pyapi import packetmap
import socket
import errno
from socket import error as socket_error

def MessageObjectToMessagePacket(messageObject, mapName):
    messageString = "80b001";
    messageString += hex(packetmap.SettingValueTranslator.NamedValueToRawValue("MessageType", messageObject.MessageType))[2:]
    dataPayload = "";
    groupControlPacketLocationMap = packetmap.DataLocationTranslator.map[mapName]
    packetInfoAttributes = [attr for attr in groupControlPacketLocationMap.keys()]
    binaryMessagePayloadString = "";
    
    for attribute in packetInfoAttributes:
        binaryMessagePayloadString = AddMapValueToBinaryValue(binaryMessagePayloadString, groupControlPacketLocationMap[attribute], messageObject.MessageValues[attribute])

    dataPayload = format(int(binaryMessagePayloadString, 2), '08x');
    dataLength = len(dataPayload) / 2;
    lengthString = "0000"[0: 4 - (len(hex((int(dataLength)))[2:]))] + hex((int(dataLength)))[2:];
    messageString += lengthString + dataPayload
    return messageString

def AddMapValueToBinaryValue(binaryMessagePayloadString, map, value):
    byteNumber = int(map.split(":")[0])
    length = 8;
    #spec counts bytes backwards so so do we
    bitmaskstart = length - (int(map.split(":")[1].split("-")[1]) - 1);
    bitmaskend = length - (int(map.split(":")[1].split("-")[0]) - 1);

    #binaryMessage needs to be at least as long as (byteNumber - 1) * 8 + bitmaskstart, so add as many zeroes as required to make that happen

    while(len(binaryMessagePayloadString) < (byteNumber - 1) * 8 + (bitmaskstart - 1)):
        binaryMessagePayloadString += "0"

    binOfValueAsString = bin(value)[2:];
    lengthNeededForBinValue = bitmaskend - (bitmaskstart - 1);
    binaryMessagePayloadString = binaryMessagePayloadString + "00000000"[0: lengthNeededForBinValue - len(binOfValueAsString)] + binOfValueAsString
    return binaryMessagePayloadString

def TranslateMapValueToValue(groupChunk, map):
    byteNumber = int(map.split(":")[0])
    length = 8;
    if(int(map.split(":")[1].split("-")[1]) > 8):
        length = 16;
    #spec counts bytes backwards so so do we
    bitmaskstart = length - (int(map.split(":")[1].split("-")[1]) - 1);
    bitmaskend = length - (int(map.split(":")[1].split("-")[0]) - 1);
    byteAsString = bin(groupChunk[byteNumber - 1])
    byteStringAdjusted = "00000000"[0: 8 - (len(byteAsString) - 2)] + byteAsString[2:];

    if(length > 8):
        byteStringAdjusted += ("00000000"[0: 8 - (len(bin(groupChunk[byteNumber])) - 2)] + bin(groupChunk[byteNumber])[2:]);

    byteSegment = byteStringAdjusted[bitmaskstart - 1: bitmaskend];
    byteSegmentAsValue = int(byteSegment, 2)
    return byteSegmentAsValue

def SendMessagePacketToAirtouch(messageString, ipAddress):
    #add header, add crc
    messageString = "5555" + messageString + format(crc16(bytes.fromhex(messageString)), '08x')[4:];

    TCP_PORT = 9004
    BUFFER_SIZE = 4096
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(7)
    data = ""
    try:
        s.connect((ipAddress, TCP_PORT))
        s.send(bytearray.fromhex(messageString))
        data = s.recv(BUFFER_SIZE)
        s.close()
    except socket_error as serr:
        data = serr;
    return data;

import numpy as np

def crc16(data: bytes):
    '''
    CRC-16-ModBus Algorithm
    '''
    data = bytearray(data)
    poly = 0xA001
    crc = 0xFFFF
    for b in data:
        crc ^= (0xFF & b)
        for _ in range(0, 8):
            if (crc & 0x0001):
                crc = ((crc >> 1) & 0xFFFF) ^ poly
            else:
                crc = ((crc >> 1) & 0xFFFF)

    return np.uint16(crc)