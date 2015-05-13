#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import *
from api import API
from daemonstream import DaemonStream
import time
import json
import types

class TestCase(object):
    def __init__(self, config=None, typeCase=None, func=None, parent=None, mainHandler=None):

        self.typeCase = typeCase
        self.func = func
        self.config = config

        self.progress = []
        self.percentComplete = 0
        self.status = None
        self.errors = []
        self.warnings = []
     
        self.titleText = ""
        self.name = ""

        self.sibIndex = 0
        self.parent = parent
        self.siblings = []
        self.children = []
        self.mainHandler = mainHandler


    @classmethod
    def removeVariable(cls, name):
        return delattr(cls, name)

    @classmethod
    def addMethod(cls, func):
        return setattr(cls, func.__name__, types.MethodType(func, cls))

    #def addChild(self):
    #    pass

    def run(self):
        if self.typeCase == "handler":
            self.runChildren()
        elif self.typeCase == "runner":
            #self.addMethod(globals()[self.func])
            #getattr(self, self.func)()
            globals()[self.func](self)


    def runChildren(self):
        for i in range(len(self.children)):
            testCase = self.children[i]
            testCase.run()

    #def getResults(self):
    #    pass


    def getTestPrints(self):
        temp = self.snDaemon.getPrintouts(None, self.startTime, endTime)
        for i in range(len(temp)):
            self.progress.append(getDate(temp[i]['ts'])+": "+temp[i]['line'])


class MakeOffer(TestCase):

    def __init__(self, config={}):
        TestCase.__init__(self)
        self.user = config['user']
        self.snDaemon = config['snDaemon']
        self.api = API()
        self.params = None

        self.filename = config['filename']
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

        self.data = {}


    def init(self):
        if self.exchangeType == "nxtae":
            self.numTransactions = 1
        elif self.exchangeType == "nxtae_nxtae":
            self.numTransactions = 3

        selectOrderConfig = {"exchangeType":self.exchangeType, "offerType":self.offerType, "baseAmount":self.baseAmount, "baseAsset":self.baseAsset, "relAsset":self.relAsset}
        selectOrder = TestCase(config=selectOrderConfig, typeCase="handler", parent=self, mainHandler=self)
        selectOrderHandler(selectOrder, selectOrderConfig)
        selectOrder.run()


    def flow(self):
        self.dumpToFile(data=self.progress)


    def getData(self, key):
        data = None

        if key in self.data:
            data = self.data[key]

        return data


    def storeData(self, key, data):

        self.data[key] = data


    def dumpToFile(self, data=[]):
        filename = self.filename
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



def selectOrderHandler(classInstance, config):

    getOrderbookConfig = {"baseAsset":config['baseAsset'], "relAsset":config['relAsset']}
    getOrderbookFunc = "getOrderbook"
    getOrderbookCase = TestCase(func=getOrderbookFunc, config=getOrderbookConfig, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="runner")
    #getOrderbook.addMethod(globals()[getOrderbook.func])

    checkOrderbookOrdersConfig = {"offerType":config['offerType']}
    checkOrderbookOrdersFunc = "checkOrderbookOrders"
    checkOrderbookOrdersCase = TestCase(func=checkOrderbookOrdersFunc, config=checkOrderbookOrdersConfig, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="runner")

    selectOrderConfig = {"exchangeType":config['exchangeType'], "baseAmount":config['baseAmount']}
    selectOrderFunc = "selectOrder"
    selectOrderCase = TestCase(func=selectOrderFunc, config=selectOrderConfig, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="runner")

    classInstance.children.append(getOrderbookCase) # orderbook = self.getOrderbook()
    classInstance.children.append(checkOrderbookOrdersCase) # orders = self.checkOrderbookOrders(orderbook)
    classInstance.children.append(selectOrderCase) # selectedOrder = self.selectOrder(orders)

    return classInstance


def getOrderbook(classInstance):

    orderbook = {}
    temp = {}
    temp['requestType'] = "orderbook"
    temp['baseid'] = classInstance.config['baseAsset']['assetID']
    temp['relid'] = classInstance.config['relAsset']['assetID']
    temp['allfields'] = 1
    temp['maxdepth'] = 30

    try:
        orderbook = classInstance.mainHandler.api.doAPICall("orderbook", temp)
    except:
        classInstance.progress.append("Could not load orderbook\n")
    else:
        
        pass

    classInstance.mainHandler.storeData("orderbook", orderbook)
    return orderbook


def checkOrderbookOrders(classInstance):

    orderbook = classInstance.mainHandler.getData("orderbook")
    neededOrdersType = "bids" if classInstance.config['offerType'] == "Sell" else "asks"
    orders = []

    if neededOrdersType in orderbook:
        orders = orderbook[neededOrdersType]

    if not len(orders):
        classInstance.progress.append("No orders in orderbook\n")
    else:
        for i in range(len(orders)):
            try:
                classInstance.progress.append(json.dumps(orders[i]))
            except:
                classInstance.progress.append(orders[i])

    classInstance.mainHandler.storeData("orders", orders)
    return orders


def selectOrder(classInstance):

    orders = classInstance.mainHandler.getData("orders")
    selectedOrder = None
    exchangeType = classInstance.config['exchangeType']
    baseAmount = classInstance.config['baseAmount']

    if len(orders):
        for i in range(len(orders)):
            if exchangeType != "any":
                if orders[i]['exchange'] == exchangeType:
                    pass
                else:
                    continue
            if orders[i]['volume'] >= baseAmount:
                pass
            else:
                classInstance.perc = "100"
            
            
            selectedOrder = orders[i]
            break

        if selectedOrder:
            classInstance.progress.append("Selected Order:\n")
            try:
                classInstance.progress.append(json.dumps(selectedOrder))
            except:
                classInstance.progress.append(selectedOrder)
        else:
            classInstance.progress.append("No order matches matches config:\n")
    else:
        classInstance.progress.append("No orders to choose from\n")

    classInstance.mainHandler.storeData("selectedOrder", selectedOrder)
    return selectedOrder



def callMakeofferHandler(classInstance, config):

    #initMakeofferConfig = {"baseAsset":config['baseAsset'], "relAsset":config['relAsset']}
    initMakeofferFunc = "initMakeoffer"
    initMakeoffer = TestCase(func=initMakeofferFunc)

    doMakeofferFunc = "doMakeoffer"
    doMakeoffer = TestCase(func=doMakeofferFunc)

    #getMakeofferPrints = TestCase("getTestPrints")

    classInstance.flow.append(initMakeoffer) 
    classInstance.flow.append(doMakeoffer) 
    #classInstance.flow.append(getMakeofferPrints)


def initMakeoffer(classInstance):

    selectedOrder = classInstance.mainHandler.getData("selectedOrder")
    obj = {}

    if selectedOrder:
        obj['requestType'] = "makeoffer3"
        for key in selectedOrder:
            obj[key] = selectedOrder[key]
        obj['perc'] = 1
        classInstance.progress.append(json.dumps(obj))

    else:
       classInstance.progress.append("No order selected\n")
    # params = self.initMakeoffer(selectedOrder)
    classInstance.mainHandler.storeData("makeofferAPIParams", obj)
    return obj    


def doMakeoffer(classInstance):

    params = classInstance.mainHandler.getData("makeofferAPIParams")

    try:
        ret = classInstance.mainHandler.api.doAPICall("makeoffer", params)
    except:
        ret = {}

    classInstance.progress.append(json.dumps(ret))
    # ret = self.doMakeoffer(params)     refTX = ret['triggerhash']
    classInstance.mainHandler.storeData("makeofferAPIReturn", ret)
    return ret



def checkTransactionsHandler(self, n):

    getTransactions = TestCase("getTransactions")
    sortTransactions = TestCase("sortTransactions")
    checkTransactions = TestCase("checkTransactions")

    self.flow.append(initMakeoffer) # transactions = self.getTransactions(refTX)
    self.flow.append(doMakeoffer) # transactions = self.sortTransactions(transactions)
    self.flow.append(getMakeofferPrints) # self.checkTransactions(transactions)



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

        if len(transactions) == self.numTransactions:
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
    price = attachment['priceNQT']
    #paramAmount = float((int(self.perc) / 100) * self.params['baseiQ']['volume'])
    paramAmount = self.perc + "~" + str(self.params['baseiQ']['volume'])
    paramPrice = self.params['baseiQ']['price']
    isAsk = "version.AskOrderPlacement" in attachment

    if isAsk and self.offerType == "Sell":
        self.progress.append("base offer type correct")
    else:
        self.progress.append("base offer type incorrect")

    self.progress.append("BASE AMOUNT: " + paramAmount + " --- ACTUAL AMOUNT: " + str(amount))
    self.progress.append("BASE PRICE: " + str(paramPrice) + " --- ACTUAL PRICE: " + str(price))


def checkRelTransaction(self, transaction):

    decimals = self.relAsset['decimals']
    attachment = transaction['attachment']
    isAsk = "version.AskOrderPlacement" in attachment
    amount = attachment['quantityQNT']
    amount = float(amount) / float(pow(10, int(decimals)))
    price = attachment['priceNQT']
    #paramAmount = float((int(self.perc) / 100) * self.params['reliQ']['volume'])
    paramAmount = self.perc + "~" + str(self.params['reliQ']['volume'])
    paramPrice = self.params['reliQ']['price']
    isAsk = "version.AskOrderPlacement" in attachment

    

    if not isAsk and self.offerType == "Sell":
        self.progress.append("rel offertype correct")
    else:
        self.progress.append("rel offertype incorrect")

    self.progress.append("REL AMOUNT: " + paramAmount + " --- ACTUAL AMOUNT: " + str(amount))
    self.progress.append("REL PRICE: " + str(paramPrice) + " --- ACTUAL PRICE: " + str(price))
        








