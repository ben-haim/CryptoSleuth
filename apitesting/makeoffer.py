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
        self.config = config

        self.progress = []
        self.percentComplete = 0
        self.status = None
        self.errors = []
        self.warnings = []
        self.children = []

        self.titleText = ""
        self.name = ""

        self.childIndex = 0
        self.parent = parent
        self.siblings = []
        self.mainHandler = mainHandler


    @classmethod
    def removeVariable(cls, name):
        return delattr(cls, name)


    @classmethod
    def addMethod(cls, func):
        return setattr(cls, func.__name__, types.MethodType(func, cls))


    def getTestPrints(self):
        temp = self.snDaemon.getPrintouts(None, self.startTime, endTime)
        for i in range(len(temp)):
            self.progress.append(getDate(temp[i]['ts'])+": "+temp[i]['line'])

    def addProgress(self, data):
        filename = self.mainHandler.filename
        f = open(filename, 'a+')
        #for i in range(len(data)):
        try:
            f.write(json.dumps(data)+'\n')
        except:
            try:
                f.write(str(data)+'\n')
            except:
                f.write('****Error dumping this line****\n')
        f.close()


class Handler(TestCase):

    def __init__(self, config=None, mainHandler=None, parent=None):
        TestCase.__init__(self, config=config, mainHandler=mainHandler, parent=parent)

        self.typeCase = "handler"


    def run(self):
        for i in range(len(self.children)):
            testCase = self.children[i]
            testCase.run()


    def addChild(self, case):

        index = len(self.children)
        case.childIndex = index
        case.parent = self
        self.children.append(case)

        for i in range(len(self.children)):
            if i != index:
                self.children[i].siblings.append(case)


class Runner(TestCase):

    def __init__(self, config=None, func=None, neededData=[], mainHandler=None, parent=None):
        TestCase.__init__(self, config=config, mainHandler=mainHandler)

        self.typeCase = "runner"

        self.func = func
        self.neededData = neededData


        self.retLevel = 0
        self.retMsg = ""
        self.retData = []


    def run(self):
        #self.addMethod(globals()[self.func])
        #getattr(self, self.func)()
        prevCaseData = self.getNeededData()
        func = globals()[self.func]
        if prevCaseData:
            func(self, prevCaseData)
        else:
            func(self)

        for i in range(len(self.retData)):
            data = self.retData[i]
            for key in data:
                self.mainHandler.storeData(key, data[key])


    def getNeededData(self):

        allData = {}

        for i in range(len(self.neededData)):
            data = self.mainHandler.getData(self.neededData[i])
            allData[self.neededData[i]] = data

        return allData




class Controller(Handler):

    def __init__(self, config={}):
        Handler.__init__(self)
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

    def getData(self, key):

        data = None

        if key in self.data:
            data = self.data[key]

        return data


    def storeData(self, key, data):

        self.data[key] = data


    def initCases(self):

        if self.exchangeType == "nxtae":
            self.numTransactions = 1
        elif self.exchangeType == "nxtae_nxtae":
            self.numTransactions = 3

        selectOrderConfig = {"exchangeType":self.exchangeType, "offerType":self.offerType, "baseAmount":self.baseAmount, "baseAsset":self.baseAsset, "relAsset":self.relAsset}
        selectOrderCase = Handler(config=selectOrderConfig, parent=self, mainHandler=self)
        selectOrderHandler(selectOrderCase)

        makeofferCase = Handler(parent=self, mainHandler=self)
        callMakeofferHandler(makeofferCase)

        transactionsConfig = {"baseAsset":self.baseAsset, "relAsset":self.relAsset, "numTransactions":self.numTransactions, "offerType":self.offerType, "nxtRS":self.user.nxtRS}
        transactionsCase = Handler(config=transactionsConfig, parent=self, mainHandler=self)
        transactionsHandler(transactionsCase)

        self.addChild(selectOrderCase)
        self.addChild(makeofferCase)
        self.addChild(transactionsCase)

        self.run()


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



def selectOrderHandler(classInstance):

    config = classInstance.config

    buildOrderbookAPIParamsConfig = {"baseAsset":config['baseAsset'], "relAsset":config['relAsset']}
    buildOrderbookAPIParamsNeededData = []
    buildOrderbookAPIParamsFunc = "buildOrderbookAPIParams"
    buildOrderbookAPIParamsCase = Runner(func=buildOrderbookAPIParamsFunc, config=buildOrderbookAPIParamsConfig, mainHandler=classInstance.mainHandler)

    doOrderbookAPICallConfig = None
    doOrderbookAPICallNeededData = ["orderbookAPIParams"]
    doOrderbookAPICallFunc = "doOrderbookAPICall"
    doOrderbookAPICallCase = Runner(func=doOrderbookAPICallFunc, config=doOrderbookAPICallConfig, neededData=doOrderbookAPICallNeededData, mainHandler=classInstance.mainHandler)

    getOrderbookOrdersConfig = {"offerType":config['offerType']}
    getOrderbookOrdersNeededData = ["orderbook"]
    getOrderbookOrdersFunc = "getOrderbookOrders"
    getOrderbookOrdersCase = Runner(func=getOrderbookOrdersFunc, config=getOrderbookOrdersConfig, neededData=getOrderbookOrdersNeededData, mainHandler=classInstance.mainHandler)

    selectOrderConfig = {"exchangeType":config['exchangeType'], "baseAmount":config['baseAmount']}
    selectOrderNeededData = ["orders"]
    selectOrderFunc = "selectOrder"
    selectOrderCase = Runner(func=selectOrderFunc, config=selectOrderConfig, neededData=selectOrderNeededData, mainHandler=classInstance.mainHandler)

    classInstance.addChild(buildOrderbookAPIParamsCase)
    classInstance.addChild(doOrderbookAPICallCase)
    classInstance.addChild(getOrderbookOrdersCase)
    classInstance.addChild(selectOrderCase)

    return classInstance


def buildOrderbookAPIParams(classInstance):

    orderbookAPIParams = {}
    orderbookAPIParams['requestType'] = "orderbook"
    orderbookAPIParams['baseid'] = classInstance.config['baseAsset']['assetID']
    orderbookAPIParams['relid'] = classInstance.config['relAsset']['assetID']
    orderbookAPIParams['allfields'] = 1
    orderbookAPIParams['maxdepth'] = 30

    classInstance.retLevel = 0
    classInstance.retMsg = "SUCCESS: Orderbook API params built"
    classInstance.addProgress(classInstance.retMsg)

    classInstance.retData.append({"orderbookAPIParams":orderbookAPIParams})


def doOrderbookAPICall(classInstance, data):

    orderbookAPIParams = data['orderbookAPIParams']
    orderbook = {}

    classInstance.addProgress("Trying orderbook API call")

    try:
        orderbook = classInstance.mainHandler.api.doAPICall("orderbook", orderbookAPIParams)
    except:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: Orderbook API call failed"
        classInstance.addProgress(classInstance.retMsg)
        
    else:
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Orderbook API call successful"
        classInstance.addProgress(classInstance.retMsg)

    classInstance.retData.append({"orderbook":orderbook})


def getOrderbookOrders(classInstance, data):

    orderbook = data['orderbook']
    neededOrdersType = "bids" if classInstance.config['offerType'] == "Sell" else "asks"
    orders = []

    if neededOrdersType in orderbook:

        orders = orderbook[neededOrdersType]

        if len(orders):
            classInstance.retLevel = 0
            classInstance.retMsg = "SUCCESS: " + neededOrdersType + " in orderbook"
            classInstance.addProgress(classInstance.retMsg)
            #for i in range(len(orders)):
            #    try:
            #        classInstance.progress.append(json.dumps(orders[i]))
            #    except:
            #        classInstance.progress.append(orders[i])
        else:
            classInstance.retLevel = -1
            classInstance.retMsg = "FAIL: No " + neededOrdersType + " in orderbook"
            classInstance.addProgress(classInstance.retMsg)
    else:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: No " + neededOrdersType + " in orderbook"
        classInstance.addProgress(classInstance.retMsg)


    classInstance.retData.append({"orders":orders})


def selectOrder(classInstance, data):

    orders = data['orders']
    exchangeType = classInstance.config['exchangeType']
    baseAmount = classInstance.config['baseAmount']

    selectedOrder = None

    for i in range(len(orders)):
        if exchangeType != "any":
            if orders[i]['exchange'] == exchangeType:
                pass
            else:
                continue
        
        #if orders[i]['volume'] >= baseAmount:
        #    pass
        #else:
        #    classInstance.perc = "100"
        
        
        selectedOrder = orders[i]
        break

    if selectedOrder:
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Selected an order"
        classInstance.addProgress(classInstance.retMsg)
        
        selectedOrderStr = json.dumps(selectedOrder)
        classInstance.addProgress("Selected Order: " + selectedOrderStr)

    else:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: No order matches matches config"
        classInstance.addProgress(classInstance.retMsg)


    classInstance.retData.append({"selectedOrder":selectedOrder})



def callMakeofferHandler(classInstance):

    config = classInstance.config

    buildMakeofferAPIParamsConfig = {}
    buildMakeofferAPIParamsNeededData = ["selectedOrder"]
    buildMakeofferAPIParamsFunc = "buildMakeofferAPIParams"
    buildMakeofferAPIParamsCase = Runner(func=buildMakeofferAPIParamsFunc, neededData=buildMakeofferAPIParamsNeededData, mainHandler=classInstance.mainHandler)


    doMakeofferAPICallConfig = {}
    doMakeofferAPICallNeededData = ["makeofferAPIParams"]
    doMakeofferAPICallFunc = "doMakeofferAPICall"
    doMakeofferAPICallCase = Runner(func=doMakeofferAPICallFunc, neededData=doMakeofferAPICallNeededData, mainHandler=classInstance.mainHandler)


    classInstance.addChild(buildMakeofferAPIParamsCase) 
    classInstance.addChild(doMakeofferAPICallCase) 



def buildMakeofferAPIParams(classInstance, data):

    selectedOrder = data['selectedOrder']

    makeofferAPIParams = {}
    makeofferAPIParams['requestType'] = "makeoffer3"
    makeofferAPIParams['perc'] = "1"

    for key in selectedOrder:
        makeofferAPIParams[key] = selectedOrder[key]

    classInstance.retLevel = 0
    classInstance.retMsg = "SUCCESS: Built makeoffer params"
    classInstance.addProgress(classInstance.retMsg)

    classInstance.retData.append({"makeofferAPIParams":makeofferAPIParams})

 

def doMakeofferAPICall(classInstance, data):

    params = data['makeofferAPIParams']
    makeofferAPIReturn = {}

    try:
        makeofferAPIReturn = classInstance.mainHandler.api.doAPICall("makeoffer", params)
    except:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: Makeoffer API call failed"

        classInstance.addProgress(classInstance.retMsg)
    else:  
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Makeoffer API call succeeded"

        classInstance.addProgress(classInstance.retMsg)
        classInstance.addProgress(makeofferAPIReturn)

    classInstance.retData.append({"makeofferAPIReturn":makeofferAPIReturn})



def transactionsHandler(classInstance):

    config = classInstance.config

    getTransactionsConfig = {"nxtRS":config['nxtRS'], "numTransactions":config['numTransactions']}
    getTransactionsNeededData = ["makeofferAPIReturn"]
    getTransactionsFunc = "getTransactions"
    getTransactionsCase = Runner(func=getTransactionsFunc, config=getTransactionsConfig, neededData=getTransactionsNeededData, mainHandler=classInstance.mainHandler)

    sortTransactionsConfig = {"baseAsset":config['baseAsset']}
    sortTransactionsNeededData = ["transactions"]
    sortTransactionsFunc = "sortTransactions"
    sortTransactionsCase = Runner(func=sortTransactionsFunc, config=sortTransactionsConfig, neededData=sortTransactionsNeededData, mainHandler=classInstance.mainHandler)

    checkTransactionsConfig = {"baseAsset":config['baseAsset'], "relAsset":config['relAsset'], "offerType":config['offerType']}
    checkTransactionsCase = Handler(config=checkTransactionsConfig, mainHandler=classInstance.mainHandler)

    classInstance.addChild(getTransactionsCase) 
    classInstance.addChild(sortTransactionsCase)
    classInstance.addChild(checkTransactionsCase)

    checkTransactionsHandler(checkTransactionsCase)



def getTransactions(classInstance, data):

    refTX = data['makeofferAPIReturn']
    refTX = refTX['triggerhash']

    nxtRS = classInstance.config['nxtRS']
    numTransactions = classInstance.config['numTransactions']

    getTransactionsAPIParams = {}
    getTransactionsAPIParams['requestType'] = "getUnconfirmedTransactions"
    getTransactionsAPIParams['account'] = nxtRS

    counter = 0
    transactions = []

    while True:

        transactions = []
        ret = classInstance.mainHandler.api.doAPICall("getUnconfirmedTransactions", getTransactionsAPIParams, True)

        if "unconfirmedTransactions" in ret:
            unconfirmedTransactions = ret['unconfirmedTransactions']
            for i in range(len(unconfirmedTransactions)):
                if "referencedTransactionFullHash" in unconfirmedTransactions[i]:
                    if unconfirmedTransactions[i]['referencedTransactionFullHash'] == refTX:
                        transactions.append(unconfirmedTransactions[i])
                elif unconfirmedTransactions[i]['fullHash'] == refTX:
                    transactions.append(unconfirmedTransactions[i])

        if len(transactions) == numTransactions:
            classInstance.retLevel = 0
            classInstance.retMsg = "SUCCESS: All transactions found"
            classInstance.addProgress(classInstance.retMsg)
            break

        if counter == 7:
            classInstance.retLevel = -1
            classInstance.retMsg = "FAIL: Could not find all transactions"
            classInstance.addProgress("failed getting transactions. num transactions = " +str(len(transactions)))
            for i in range(len(transactions)):
                classInstance.addProgress(json.dumps(transactions[i]))
            break

        counter += 1
        time.sleep(1)


    classInstance.retData.append({"transactions":transactions})



def sortTransactions(classInstance, data):

    baseAsset = classInstance.config['baseAsset']
    transactions = data['transactions']

    sortedTransactions = []

    for i in range(len(transactions)):
        transaction = transactions[i]
        if "referencedTransactionFullHash" in transaction:
            attachment = transaction['attachment']
            if attachment['asset'] == baseAsset['assetID']:
                transaction['IDEX_TYPE'] = "base"
            else:
                transaction['IDEX_TYPE'] = "rel"
        else:
            transaction['IDEX_TYPE'] = "fee"

        classInstance.addProgress(json.dumps(transaction))

        sortedTransactions.append(transaction)


    classInstance.retData.append({"sortedTransactions":sortedTransactions})



def checkTransactionsHandler(classInstance):

    config = classInstance.config

    checkFeeTransactionConfig = {}
    checkFeeTransactionNeededData = ["sortedTransactions"]
    checkFeeTransactionFunc = "checkFeeTransaction"
    checkFeeTransactionCase = Runner(func=checkFeeTransactionFunc, neededData=checkFeeTransactionNeededData, mainHandler=classInstance.mainHandler)


    checkBaseTransactionConfig = {"baseAsset":config['baseAsset'], "offerType":config['offerType']}
    checkBaseTransactionNeededData = ["sortedTransactions", "makeofferAPIParams"]
    checkBaseTransactionFunc = "checkBaseTransaction"
    checkBaseTransactionCase = Runner(func=checkBaseTransactionFunc, config=checkBaseTransactionConfig, neededData=checkBaseTransactionNeededData, mainHandler=classInstance.mainHandler)


    checkRelTransactionConfig = {"relAsset":config['relAsset'], "offerType":config['offerType']}
    checkRelTransactionNeededData = ["sortedTransactions", "makeofferAPIParams"]
    checkRelTransactionFunc = "checkRelTransaction"
    checkRelTransactionCase = Runner(func=checkRelTransactionFunc, config=checkRelTransactionConfig, neededData=checkRelTransactionNeededData, mainHandler=classInstance.mainHandler)


    classInstance.addChild(checkFeeTransactionCase) 
    classInstance.addChild(checkBaseTransactionCase) 
    classInstance.addChild(checkRelTransactionCase) 

        

def checkFeeTransaction(classInstance, data):

    transactions = data['sortedTransactions']
    transaction = searchListOfObjects(transactions, "IDEX_TYPE", "fee", True)

    if transaction['amountNQT'] == "250000000":
        classInstance.addProgress("fee correct")
    else:
        classInstance.addProgress("fee incorrect")


def checkBaseTransaction(classInstance, data):

    decimals = classInstance.config['baseAsset']['decimals']
    offerType = classInstance.config['offerType']
    perc = "1" #classInstance.config['perc']

    params = data['makeofferAPIParams']
    transactions = data['sortedTransactions']
    transaction = searchListOfObjects(transactions, "IDEX_TYPE", "base", True)

    attachment = transaction['attachment']
    isAsk = "version.AskOrderPlacement" in attachment

    amount = attachment['quantityQNT']
    amount = float(amount) / float(pow(10, int(decimals)))
    paramAmount = perc + "~" + str(params['baseiQ']['volume'])   #paramAmount = float((int(self.perc) / 100) * self.params['baseiQ']['volume'])

    price = attachment['priceNQT']
    paramPrice = params['baseiQ']['price']


    if isAsk and offerType == "Sell":
        classInstance.addProgress("base offer type correct")
    else:
        classInstance.addProgress("base offer type incorrect")

    classInstance.addProgress("BASE AMOUNT: " + paramAmount + " --- ACTUAL AMOUNT: " + str(amount))
    classInstance.addProgress("BASE PRICE: " + str(paramPrice) + " --- ACTUAL PRICE: " + str(price))


def checkRelTransaction(classInstance, data):

    decimals = classInstance.config['relAsset']['decimals']
    offerType = classInstance.config['offerType']
    perc = "1" #classInstance.config['perc']

    params = data['makeofferAPIParams']
    transactions = data['sortedTransactions']
    transaction = searchListOfObjects(transactions, "IDEX_TYPE", "rel", True)

    attachment = transaction['attachment']
    isAsk = "version.AskOrderPlacement" in attachment

    amount = attachment['quantityQNT']
    amount = float(amount) / float(pow(10, int(decimals)))
    paramAmount = perc + "~" + str(params['reliQ']['volume'])  #paramAmount = float((int(self.perc) / 100) * self.params['reliQ']['volume'])

    price = attachment['priceNQT']
    paramPrice = params['reliQ']['price']



    if not isAsk and offerType == "Sell":
        classInstance.addProgress("rel offertype correct")
    else:
        classInstance.addProgress("rel offertype incorrect")

    classInstance.addProgress("REL AMOUNT: " + paramAmount + " --- ACTUAL AMOUNT: " + str(amount))
    classInstance.addProgress("REL PRICE: " + str(paramPrice) + " --- ACTUAL PRICE: " + str(price))
        








