#!/usr/bin/env python
# -*- coding: utf-8 -*-


from utils import *
from api import API

class User(object):

    def __init__(self, config={}):

        self.api = API()

        self.allAssets = config['allAssets']
        self.balances = []
        self.openOrders = []

        self.nxtID = config['nxtid']
        self.nxtRS = config['nxtrs']
        self.nxtPass = ""
        self.pubAddr = ""
        self.privAddr = "" 

    

    def updateAssetBalances(self):
        self.balances = []
        postObj = {'requestType':"getAccountAssets",'account':self.nxtID}
        ret = self.api.doAPICall("getAccountAsset", postObj, True)

        if "errorCode" in ret:
            pass
        else:
            if "accountAssets" in ret:
                assetBalances = ret['accountAssets']
                self.balances = assetBalances
    

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
        self.quantityQNT = ""
        self.account = ""
        self.accountRS = ""
        self.description = ""
        self.numberOfTrades = 0
        self.numberOfAccounts = 0
        self.numberOfTransfers = 0
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





