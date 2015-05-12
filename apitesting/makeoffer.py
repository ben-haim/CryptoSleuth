#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import *
from api import API

class MakeOffer(object):


    def __init__(self, config={}):

        #self.caseName = "test"
        #self.caseType = "makeoffer3"
        self.progress = []
        self.offerType = config['offerType']
        self.exchangeType = config['exchangeType']
        self.perc = config['perc']
        self.user = config['user']
        self.baseAsset = self.user.getAsset("assetID", config['baseID'])
        self.relAsset = self.user.getAsset("assetID", config['relID'])

        self.api = API()

        self.isExternalExchange = False
        #self.makeofferParams
        self.baseDecimals = 0
        self.relDecimals = 0
        self.baseAmount = 0
        self.relAmount = 0


    def init(self):
        
        pass


    def flow(self):

        self.progress.append("Getting base balance...\n")
        baseBal = self.getBalance(self.baseAsset)

        self.progress.append("Checking base balance...\n")
        #ret = self.checkBalance(baseBal, self.baseAmount)


        self.progress.append("Getting rel balance...\n")
        relBal = self.getBalance(self.relAsset)

        self.progress.append("Checking rel balance...\n")
        #ret = self.checkBalance(relBal, self.relAmount)


        self.progress.append("Getting orderbook...\n")
        orderbook = self.loadOrderbook()

        self.progress.append("Checking orderbook orders...\n")
        orders = self.checkOrderbookOrders(orderbook)

        self.progress.append("Selecting order...\n")
        selectedOrder = self.selectOrder(orders)

    
        self.progress.append("Initializing makeoffer...\n")
        params = self.initMakeoffer(selectedOrder)

        self.progress.append("Calling makeoffer...\n")
        self.doMakeoffer(params)


        self.progress.append("Dumping to file...\n")
        self.dumpToFile(data=self.progress)


    def getBalance(self, asset):

        bal = 0
        retObj = None
        retBool = True
        retStat = ""

        try:
            bal = self.user.getBal(asset.assetID, True)
        except:
            pass
        else:
            pass

        return bal


    def checkBalance(self, bal, makeofferBal):

        retObj = None
        retBool = True
        retStat = ""

        if bal >= makeofferBal:
            pass
        else:
            retBool = False

        return retBool


    def loadOrderbook(self):

        orderbook = {}
        temp = {}
        temp['requestType'] = "orderbook"
        temp['baseid'] = self.baseAsset['assetID']
        temp['relid'] = self.relAsset['assetID']
        temp['allfields'] = 1

        try:
            orderbook = self.api.doAPICall("orderbook", temp)
        except:
            self.progress.append("Could not load orderbook\n")
        else:
            pass

        return orderbook


    def checkOrderbookOrders(self, orderbook):

        neededOrdersType = "bids" if self.offerType == "Sell" else "asks"
        orders = []

        if neededOrdersType in orderbook:
            orders = orderbook[neededOrdersType]

        if not len(orders):
            self.progress.append("No orders in orderbook\n")
        else:
            for i in range(len(orders)):
                try:
                    self.progress.append(json.dumps(orders[i]))
                except:
                    self.progress.append(orders[i])

        return orders


    def selectOrder(self, orders):

        selectedOrder = {}

        if len(orders):
            selectedOrder = orders[0]
            self.progress.append("Selected Order:\n")
            try:
                self.progress.append(json.dumps(selectedOrder))
            except:
                self.progress.append(selectedOrder)
        else:
            self.progress.append("No orders to choose from\n")

        return selectedOrder


    def initMakeoffer(self, selectedOrder):

        obj = {}

        if selectedOrder:
            obj['requestType'] = "makeoffer3"
            for key in selectedOrder:
                obj[key] = selectedOrder[key]
            obj['perc'] = self.perc

        else:
           self.progress.append("No order selected\n")

        return obj    


    def doMakeoffer(self, params):

        try:
            ret = self.api.doAPICall("makeoffer", params)
        except:
            ret = "Failed"

        try:
            ret = json.dumps(ret)
        except:
            pass

        self.progress.append(ret)


    def dumpToFile(self, filename="dump", data=[]):
        f = open(filename, 'w')
        for i in range(len(data)):
            try:
                f.write(json.dumps(data[i])+'\n')
            except:
                try:
                    f.write(str(data[i])+'\n')
                except:
                    f.write('****Error dumping this line****\n')
        f.close()



