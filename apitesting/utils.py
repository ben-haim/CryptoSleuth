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


def checkObj(self, key, default):
    
    a = None

    if key in self.config:
        a = self.config[key]
    else:
        a = default

    return a

