#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

def searchListOfObjects(listOfObjects, key, val, temp=False):

    retObjs = []

    for i in range(len(listOfObjects)):
        obj = listOfObjects[i]
        if key in obj and obj[key] == val:
            retObjs.append(obj)

    if temp:
        if len(retObjs):
            return retObjs[0]
        else:
            return {}
    else:
        return retObjs


def addAssetID(assets):

    for i in range(len(assets)):
        for key in assets[i]:
            if key == "asset":
                assets[i]['assetID'] = assets[i][key]
                break

    return assets


def getDate(ts):

    return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S.%f")


def getDateNoMS(ts):

    return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")

def getTimer(ts):

    return time.strftime("%M:%S", time.gmtime(ts))


def checkObj(config, key, default):
    
    a = None

    if key in config:
        a = config[key]
    else:
        a = default

    return a


def toString(data):

    try:
        line = json.dumps(data)
    except:
        try:
            line = str(data).rstrip('\r\n') + '\n'
        except:
            line = "****Error dumping this line****\n"

    return line


def prependToFile(filename, data):
    with open(filename, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        for i in range(len(data)):
            line = toString(data[i])
            f.write(line)
        f.write(content)
        f.close()
