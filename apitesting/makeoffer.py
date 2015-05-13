#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import *
from api import API
from daemonstream import DaemonStream
import time
import json


class MakeOffer(object):


    def __init__(self, config={}):

        self.progress = []

        self.user = config['user']
        self.snDaemon = config['snDaemon']
        self.api = API()
        self.params = None

        #self.makeofferParams
        self.baseAsset = self.user.getAsset("assetID", config['baseID'])
        self.relAsset = self.user.getAsset("assetID", config['relID'])
        self.baseAmount = 0
        self.minBaseAmount = 0
        self.relAmount = 0
        self.minRelAmount = 0
        self.perc = config['perc']

        self.offerType = config['offerType']
        self.exchangeType = config['exchangeType']
        self.isExternalExchange = False


    def init(self):
        
        pass


    def flow(self):

        self.progress.append("Getting base balance...\n")
        baseBal = self.getBalance(self.baseAsset)

        #self.progress.append("Checking base balance...\n")
        #ret = self.checkBalance(baseBal, self.baseAmount)

        self.progress.append("Getting rel balance...\n")
        relBal = self.getBalance(self.relAsset)

        #self.progress.append("Checking rel balance...\n")
        #ret = self.checkBalance(relBal, self.relAmount)

        self.progress.append("Getting orderbook...\n")
        orderbook = self.getOrderbook()

        self.progress.append("Checking orderbook orders...\n")
        orders = self.checkOrderbookOrders(orderbook)

        self.progress.append("Selecting order...\n")
        selectedOrder = self.selectOrder(orders)

        self.progress.append("Initializing makeoffer...\n")
        params = self.initMakeoffer(selectedOrder)
        self.params = params
    
        callMakeofferStream = DaemonStream({'snDaemon':self.snDaemon, 'name':'callMakeoffer'})
        callMakeofferStream.start()
        startTime = time.time()
        self.progress.append("Calling makeoffer...\n")
        ret = self.doMakeoffer(params)
        refTX = ret['triggerhash']

        self.progress.append("Getting transactions...\n")
        transactions = self.getTransactions(refTX)

        self.progress.append("Sorting transactions...\n")
        transactions = self.sortTransactions(transactions)

        self.progress.append("Checking transactions...\n")
        self.checkTransactions(transactions)

        #self.waitForMakeoffer(callMakeofferStream, startTime)
        #endTime = time.time()
        #temp = self.snDaemon.getPrintouts(None, startTime, endTime)
        #temp = callMakeofferStream.formatStreamData()
        #for i in range(len(temp)):
        #    self.progress.append(getDate(temp[i]['ts'])+": "+temp[i]['line'])

        #self.progress.append("Dumping to file...\n")
        self.dumpToFile(data=self.progress)

    def waitForMakeoffer(self, stream, startTime):

        index = 0
        while True:
            if index < len(stream.streamData):
                #arr = callMakeofferStream.streamData[index:]
                printout = stream.streamData[index]
                if startTime > printout['ts']:
                    continue
                #if prinout['line'].find("SUBMIT"):
                    
                self.progress.append(getDate(printout['ts'])+": "+printout['line'])
                index += 1
                if time.time() - startTime > 10.0:
                    break

    def getTransactions(self, refTX):
        counter = 0
        temp = {}
        #temp['requestType'] = "getTransaction"
        #temp['transaction'] = txid
        transactions = []
        temp['requestType'] = "getUnconfirmedTransactions"
        temp['account'] = self.user.nxtRS

        while True:
            transactions = []
            ret = self.api.doAPICall("getUnconfirmedTransaction", temp, True)
            if "unconfirmedTransactions" in ret:
                unconfs = ret['unconfirmedTransactions']
                for i in range(len(unconfs)):
                    if "referencedTransactionFullHash" in unconfs[i]:
                        if unconfs[i]['referencedTransactionFullHash'] == refTX:
                            transactions.append(unconfs[i])
                    elif unconfs[i]['fullHash'] == refTX:
                        transactions.append(unconfs[i])

            if len(transactions) == 3:
                break
            if counter == 7:
                self.progress.append("failed getting transactions. num transactions = " +str(len(transactions)))
                for i in range(len(transactions)):
                    self.progress.append(json.dumps(transactions[i]))
                break

            counter += 1
            time.sleep(1)

        return transactions


    def sortTransactions(self, transactions):
        obj = {}
        temp = []
        for i in range(len(transactions)):
            transaction = transactions[i]
            if "referencedTransactionFullHash" in transaction:
                attachment = transaction['attachment']
                if attachment['asset'] == self.baseAsset['assetID']:
                    transaction['IDEX_TYPE'] = "base"
                else:
                    transaction['IDEX_TYPE'] = "rel"
            else:
                transaction['IDEX_TYPE'] = "fee"

            self.progress.append(json.dumps(transaction))

            temp.append(transaction)

        return temp


    def checkTransactions(self, transactions):
        for i in range(len(transactions)):
            transaction = transactions[i]
            if transaction['IDEX_TYPE'] == "fee":
                self.checkFeeTransaction(transaction)
            elif transaction['IDEX_TYPE'] == "base":
                self.checkBaseTransaction(transaction)
            elif transaction['IDEX_TYPE'] == "rel":
                self.checkRelTransaction(transaction)
            

    def checkFeeTransaction(self, transaction):
    
        if transaction['amountNQT'] == "250000000":
            self.progress.append("fee correct")
        else:
            self.progress.append("fee incorrect")


    def checkBaseTransaction(self, transaction):

        decimals = self.baseAsset['decimals']
        attachment = transaction['attachment']
        isAsk = "version.AskOrderPlacement" in attachment
        amount = attachment['quantityQNT']
        amount = float(amount) / float(pow(10, int(decimals)))
        #paramAmount = float((int(self.perc) / 100) * self.params['baseiQ']['volume'])
        paramAmount = self.perc + "~" + str(self.params['baseiQ']['volume'])
        isAsk = "version.AskOrderPlacement" in attachment

        

        if isAsk and self.offerType == "Sell":
            self.progress.append("base offer type correct")
        else:
            self.progress.append("base offer type incorrect")

        self.progress.append("BASE AMOUNT: " + paramAmount + " --- ACTUAL AMOUNT: " + str(amount))


    def checkRelTransaction(self, transaction):

        decimals = self.relAsset['decimals']
        attachment = transaction['attachment']
        isAsk = "version.AskOrderPlacement" in attachment
        amount = attachment['quantityQNT']
        amount = float(amount) / float(pow(10, int(decimals)))
        #paramAmount = float((int(self.perc) / 100) * self.params['reliQ']['volume'])
        paramAmount = self.perc + "~" + str(self.params['reliQ']['volume'])
        isAsk = "version.AskOrderPlacement" in attachment

        

        if not isAsk and self.offerType == "Sell":
            self.progress.append("rel offertype correct")
        else:
            self.progress.append("rel offertype incorrect")

        self.progress.append("REL AMOUNT: " + paramAmount + " --- ACTUAL AMOUNT: " + str(amount))
                
            

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


    def getOrderbook(self):

        orderbook = {}
        temp = {}
        temp['requestType'] = "orderbook"
        temp['baseid'] = self.baseAsset['assetID']
        temp['relid'] = self.relAsset['assetID']
        temp['allfields'] = 1
        temp['maxdepth'] = 30

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

        selectedOrder = None

        if len(orders):
            for i in range(len(orders)):
                if self.exchangeType != "any":
                    if orders[i]['exchange'] == self.exchangeType:
                        pass
                    else:
                        continue
                if orders[i]['volume'] >= self.baseAmount:
                    pass
                else:
                    self.perc = "100"
                
                
                selectedOrder = orders[i]
                break

            if selectedOrder:
                self.progress.append("Selected Order:\n")
                try:
                    self.progress.append(json.dumps(selectedOrder))
                except:
                    self.progress.append(selectedOrder)
            else:
                self.progress.append("No order matches matches config:\n")
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
            self.progress.append(json.dumps(obj))

        else:
           self.progress.append("No order selected\n")


        return obj    


    def doMakeoffer(self, params):

        try:
            ret = self.api.doAPICall("makeoffer", params)
        except:
            ret = {}

        self.progress.append(json.dumps(ret))

        return ret


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



