#!/usr/bin/env python
# -*- coding: utf-8 -*-


from utils import searchListOfObjects

class User(object):

    def __init__(self, config={}):

        self.API = None

        self.allAssets = []
        self.balances = []
        self.openOrders = []

        self.nxtID = ""
        self.nxtRS = ""
        self.nxtPass = ""
        self.pubAddr = ""
        self.privAddr = "" 



    def updateBalances(self):
        pass

    def getBal(self, assetID):

        bal = searchListOfObjects(self.balances, "assetID", assetID)

        return bal[0]


    def getAsset(self, key, val):

        asset = searchListOfObjects(self.allAssets, key, val)

        return asset[0]
            


class Asset(object):

    def __init__(self, config={}):
        
        self.name = ""
        self.assetID = ""
        self.decimals = 0
        self.isSpecial = False




class Balance(object):

    def __init__(self, config={}):
        
        self.name = ""
        self.assetID = ""
        self.decimals = 0
        self.isSpecial = False


    def makeBal(self):

        asset = getBal(assetID)
        aStr = "NAME: "+asset['name'] + ", BAL: " + str(asset['unconfirmedQuantityQNT']) + ", DEC: " + str(asset['decimals'])
        return aStr





