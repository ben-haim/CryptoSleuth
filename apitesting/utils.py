#!/usr/bin/env python
# -*- coding: utf-8 -*-


def searchListOfObjects(listOfObjects, key, val):

    retObjs = []

    for i in range(len(listOfObjects)):
        obj = listOfObjects[i]
        if key in obj and obj[key] == val:
            retObjs.append(obj)

    return retObjs



def getDate(ts):
    import datetime
    return datetime.datetime.fromtimestamp(int(ts)).strftime("%H:%M:%S")

