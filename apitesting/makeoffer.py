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
        self.startTime = None
        self.endTime = None

        self.titleText = ""
        self.name = ""

        self.childIndex = 0
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


    def getTestPrints(self):
        temp = self.snDaemon.getPrintouts(None, self.startTime, endTime)
        for i in range(len(temp)):
            self.progress.append(getDate(temp[i]['ts'])+": "+temp[i]['line'])

    def addProgress(self, data):
        filename = self.mainHandler.filename
        with open(filename, 'a+') as f:
        #for i in range(len(data)):
            f.write(toString(data))
            f.close()


    def prependToFile(self, filename, data):
        with open(filename, 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            for i in range(len(data)):
                line = toString(data[i])
                f.write(line)
            f.write(content)
            f.close()





class Handler(TestCase):

    def __init__(self, config=None, mainHandler=None, parent=None):
        TestCase.__init__(self, config=config, mainHandler=mainHandler, parent=parent)

        self.typeCase = "handler"


    def run(self):
        for i in range(len(self.children)):
            testCase = self.children[i]

            try:
                testCase.run()
            except Exception as e:
                raise e


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

        self.startingLogs(prevCaseData)

        func = globals()[self.func]
        if prevCaseData:
            func(self, prevCaseData)
        else:
            func(self)

        self.endingLogs()

        for i in range(len(self.retData)):
            data = self.retData[i]
            for key in data:
                self.mainHandler.storeData(key, data[key])

        if self.retLevel == -1:
            raise NameError("test")


    def startingLogs(self, prevCaseData):

        self.addProgress(" ")
        self.addProgress("*"*20)
        self.addProgress("Starting case: " + self.func)

        if prevCaseData:
            self.addProgress("Using data: ")
            for key in prevCaseData:
                line = key + ": " + toString(prevCaseData[key])
                self.addProgress(line)

        if self.config:
            self.addProgress("Using config options: ")
            for key in self.config:
                line = key + ": " + toString(self.config[key])
                self.addProgress(line)

        self.addProgress("-"*20)
        self.addProgress(" ")

    
    def endingLogs(self):

        self.addProgress(" ")
        self.addProgress("-"*20)

        self.addProgress("Finished case: " + self.func)
        self.addProgress("retLevel: " + str(self.retLevel))
        self.addProgress("retMsg: " + self.retMsg)

        if len(self.retData):
            self.addProgress("Retrieved data: ")
            for i in range(len(self.retData)):
                data = self.retData[i]
                for key in data:
                    line = key + ": " + toString(data[key])
                    self.addProgress(line)

        self.addProgress("*"*20)
        self.addProgress(" ")


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



    def run(self):

        self.startTime = time.time()
        for i in range(len(self.children)):
            testCase = self.children[i]

            try:
                testCase.run()
            except Exception as e:
                break

        self.endTime = time.time()

        self.makeOverview()



    def getAllRunners(self, children):
        for i in range(len(children)):
            child = children[i]
            if child.typeCase == "runner":
                yield child
            else:
                for j in self.getAllRunners(child.children):
                    yield j

    def makeOverview(self):
        allRunners = self.getAllRunners(self.children)
        overview = []
        
        numRunners = 0
        numFailed = 0
        numComplete = 0

        parsed = []
        for runner in allRunners:
            obj = {}
            obj['caseName'] = runner.func
            obj['retLevel'] = runner.retLevel
            obj['retMsg'] = runner.retMsg
            parsed.append(obj)

            if runner.retLevel == 0:
                numComplete += 1
            elif runner.retLevel == -1:
                numFailed += 1

            numRunners += 1

        temp = []
        temp.append({'offerType':self.offerType})
        temp.append({'exchangeType':self.exchangeType})
        temp.append({'baseID':self.baseAsset['assetID']})
        temp.append({'relID':self.relAsset['assetID']})

        overview.append("*"*30)
        overview.append("Test Name: " + self.filename)
        overview.append("Start time: " + getDateNoMS(int(self.startTime)))
        overview.append("End time: " + getDateNoMS(int(self.endTime)))
        #overview.append("Elapsed time: " + time.strftime("%M:%S", time.gmtime(int(self.endTime - self.startTime))))
        overview.append("Params: ")
        for i in range(len(temp)):
            for key in temp[i]:
                overview.append("    " + key + ": " + temp[i][key])
        overview.append("Num runners: " + str(numRunners))
        overview.append("Num failed: " + str(numFailed) + "/" + str(numRunners))
        overview.append("Num complete: " + str(numComplete) + "/" + str(numRunners))
        overview.append("All runners: ")
        for i in range(len(parsed)):
            overview.append("    " + "Case Name: " + parsed[i]['caseName'])
            overview.append("        " + "Ret Level: " + str(parsed[i]['retLevel'])) 
            overview.append("        " + "Ret Message: " + parsed[i]['retMsg'])
        overview.append("*"*30)
        overview.append(" ")
        overview.append(" ")

        self.prependToFile(self.filename, overview)

    def dumpToFile(self, data=[]):
        filename = "aba"
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

    classInstance.addProgress("Constructed orderbook API params:")
    classInstance.addProgress(orderbookAPIParams)

    classInstance.retLevel = 0
    classInstance.retMsg = "SUCCESS: Orderbook API params built"

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
        
    else:
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Orderbook API call successful"

    classInstance.retData.append({"orderbook":orderbook})


def getOrderbookOrders(classInstance, data):

    orderbook = data['orderbook']
    neededOrdersType = "bids" if classInstance.config['offerType'] == "Sell" else "asks"
    orders = []

    if neededOrdersType in orderbook:

        orders = orderbook[neededOrdersType]

        if len(orders):

            classInstance.addProgress("Orderbook orders:")
            for i in range(len(orders)):
                    classInstance.addProgress(orders[i])

            classInstance.retLevel = 0
            classInstance.retMsg = "SUCCESS: " + neededOrdersType + " in orderbook"
        else:
            classInstance.retLevel = -1
            classInstance.retMsg = "FAIL: No " + neededOrdersType + " in orderbook"

    else:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: No " + neededOrdersType + " in orderbook"


    classInstance.retData.append({"orders":orders})


def selectOrder(classInstance, data):

    orders = data['orders']
    exchangeType = classInstance.config['exchangeType']
    baseAmount = classInstance.config['baseAmount']

    selectedOrder = None

    classInstance.addProgress("Searching through orders...")
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
        #selectedOrderStr = json.dumps(selectedOrder)
        classInstance.addProgress("Selected Order: ")
        classInstance.addProgress(selectedOrder)

        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Selected an order"

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

    classInstance.addProgress("Constructed makeoffer API params:")
    classInstance.addProgress(makeofferAPIParams)

    classInstance.retLevel = 0
    classInstance.retMsg = "SUCCESS: Built makeoffer params"

    classInstance.retData.append({"makeofferAPIParams":makeofferAPIParams})

 

def doMakeofferAPICall(classInstance, data):

    params = data['makeofferAPIParams']
    makeofferAPIReturn = {}

    classInstance.addProgress("Trying makeoffer API call")
    try:
        makeofferAPIReturn = classInstance.mainHandler.api.doAPICall("makeoffer", params)
    except:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: Makeoffer API call failed"

        classInstance.addProgress(classInstance.retMsg)
    else:  
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Makeoffer API call succeeded"

        #classInstance.addProgress(classInstance.retMsg)
        #classInstance.addProgress(makeofferAPIReturn)

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

    classInstance.addProgress("Starting transactions poll...")

    while True:

        transactions = []
        classInstance.addProgress("Trying getUnconfirmedTransactions API call...")
        try:
            ret = classInstance.mainHandler.api.doAPICall("getUnconfirmedTransactions", getTransactionsAPIParams, True)
        except:
            ret = {}
            pass

        if "unconfirmedTransactions" in ret:
            unconfirmedTransactions = ret['unconfirmedTransactions']
            for i in range(len(unconfirmedTransactions)):

                if "referencedTransactionFullHash" in unconfirmedTransactions[i]:
                    if unconfirmedTransactions[i]['referencedTransactionFullHash'] == refTX:
                        transactions.append(unconfirmedTransactions[i])
                        classInstance.addProgress("Found a transaction:")
                        classInstance.addProgress(unconfirmedTransactions[i])

                elif unconfirmedTransactions[i]['fullHash'] == refTX:
                    transactions.append(unconfirmedTransactions[i])
                    classInstance.addProgress("Found a transaction:")
                    classInstance.addProgress(unconfirmedTransactions[i])
        else:
            classInstance.addProgress("No unconfirmed transactions")

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
                classInstance.addProgress(transactions[i])
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
                classInstance.addProgress("Found base transaction:")
                classInstance.addProgress(transaction)

            else:
                transaction['IDEX_TYPE'] = "rel"
                classInstance.addProgress("Found rel transaction:")
                classInstance.addProgress(transaction)
        else:
            transaction['IDEX_TYPE'] = "fee"
            classInstance.addProgress("Found fee transaction:")
            classInstance.addProgress(transaction)


        sortedTransactions.append(transaction)

    classInstance.retLevel = 0
    classInstance.retMsg = "OK: No checks here"

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

    if "amountNQT" in transaction:
        if transaction['amountNQT'] == "250000000":
            classInstance.addProgress("Fee transaction has correct fee of 250000000")
            classInstance.retLevel = 0
            classInstance.retMsg = "SUCCESS: Correct fee amount"
        else:
            classInstance.addProgress("Incorrect fee for fee transaction: " + str(transaction['amountNQT']) + ". Expected 250000000")
            classInstance.retLevel = 1
            classInstance.retMsg = "FAIL: Incorrect fee"
    else:
        classInstance.addProgress("Unexpected error - could not parse fee transaction:")
        classInstance.addProgress(transaction)
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Could not parse fee transaction"



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
        classInstance.addProgress("Base offerType correct. transaction offerType: " + str(isAsk) + ". proper offerType: " + str(offerType))
    else:
        classInstance.addProgress("Base offerType incorrect. transaction offerType: " + str(isAsk) + ". proper offerType: " + str(offerType))

    classInstance.addProgress("BASE AMOUNT: " + paramAmount + " --- ACTUAL AMOUNT: " + str(amount))
    classInstance.addProgress("BASE PRICE: " + str(paramPrice) + " --- ACTUAL PRICE: " + str(price))

    classInstance.retLevel = 0
    classInstance.retMsg = "OK: Pass"


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
        classInstance.addProgress("Rel offerType correct. transaction offerType: " + str(isAsk) + ". proper offerType: " + str(offerType))
    else:
        classInstance.addProgress("Rel offerType incorrect. transaction offerType: " + str(isAsk) + ". proper offerType: " + str(offerType))

    classInstance.addProgress("REL AMOUNT: " + paramAmount + " --- ACTUAL AMOUNT: " + str(amount))
    classInstance.addProgress("REL PRICE: " + str(paramPrice) + " --- ACTUAL PRICE: " + str(price))

    classInstance.retLevel = 0
    classInstance.retMsg = "OK: Pass"








