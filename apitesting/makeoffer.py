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

    def addChild(self, case):
        index = len(self.children)
        case.childIndex = index
        self.children.append(case)
        for i in range(len(self.children)):
            if i != index:
                self.children[i].siblings.append(case)

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
        TestCase.__init__(self, typeCase="handler")
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


    def initCases(self):
        if self.exchangeType == "nxtae":
            self.numTransactions = 1
        elif self.exchangeType == "nxtae_nxtae":
            self.numTransactions = 3

        selectOrderConfig = {"exchangeType":self.exchangeType, "offerType":self.offerType, "baseAmount":self.baseAmount, "baseAsset":self.baseAsset, "relAsset":self.relAsset}
        selectOrderCase = TestCase(config=selectOrderConfig, typeCase="handler", parent=self, mainHandler=self)
        selectOrderHandler(selectOrderCase)

        makeofferCase = TestCase(typeCase="handler", parent=self, mainHandler=self)
        callMakeofferHandler(makeofferCase)

        transactionsConfig = {"baseAsset":self.baseAsset, "relAsset":self.relAsset, "numTransactions":self.numTransactions, "offerType":self.offerType, "nxtRS":self.user.nxtRS}
        transactionsCase = TestCase(config=transactionsConfig, typeCase="handler", parent=self, mainHandler=self)
        transactionsHandler(transactionsCase)

        self.addChild(selectOrderCase)
        self.addChild(makeofferCase)
        self.addChild(transactionsCase)

        self.run()


        temp = []
        for i in range(len(self.children)):
            child = self.children[i]
            for s in range(len(child.children)):
                sChild = child.children[s]
                for ss in range(len(sChild.children)):
                    ssChild = sChild.children[ss]
                    for q in range(len(ssChild.progress)):
                        temp.append(ssChild.progress[q])
                for qq in range(len(sChild.progress)):
                    temp.append(sChild.progress[qq])
            for qqq in range(len(child.progress)):
                temp.append(child.progress[qqq])
        for qqqq in range(len(self.progress)):
            temp.append(self.progress[qqqq])

        #print temp

        self.dumpToFile(data=temp)
                        

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



def selectOrderHandler(classInstance):

    config = classInstance.config

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

    classInstance.addChild(getOrderbookCase) # orderbook = self.getOrderbook()
    classInstance.addChild(checkOrderbookOrdersCase) # orders = self.checkOrderbookOrders(orderbook)
    classInstance.addChild(selectOrderCase) # selectedOrder = self.selectOrder(orders)

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
    exchangeType = classInstance.config['exchangeType']
    baseAmount = classInstance.config['baseAmount']

    selectedOrder = None

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



def callMakeofferHandler(classInstance):

    config = classInstance.config

    initMakeofferFunc = "initMakeoffer"
    initMakeofferCase = TestCase(func=initMakeofferFunc, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="runner")

    doMakeofferFunc = "doMakeoffer"
    doMakeofferCase = TestCase(func=doMakeofferFunc, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="runner")

    #getMakeofferPrints = TestCase("getTestPrints")

    classInstance.addChild(initMakeofferCase) 
    classInstance.addChild(doMakeofferCase) 
    #classInstance.addChild(getMakeofferPrints)


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



def transactionsHandler(classInstance):

    config = classInstance.config

    getTransactionsConfig = {"nxtRS":config['nxtRS'], "numTransactions":config['numTransactions']}
    getTransactionsFunc = "getTransactions"
    getTransactionsCase = TestCase(func=getTransactionsFunc, config=getTransactionsConfig, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="runner")

    sortTransactionsConfig = {"baseAsset":config['baseAsset']}
    sortTransactionsFunc = "sortTransactions"
    sortTransactionsCase = TestCase(func=sortTransactionsFunc, config=sortTransactionsConfig, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="runner")

    checkTransactionsConfig = {"baseAsset":config['baseAsset'], "relAsset":config['relAsset'], "offerType":config['offerType']}
    checkTransactionsCase = TestCase(config=checkTransactionsConfig, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="handler")

    classInstance.addChild(getTransactionsCase) # transactions = self.getTransactions(refTX)
    classInstance.addChild(sortTransactionsCase) # transactions = self.sortTransactions(transactions)
    classInstance.addChild(checkTransactionsCase) # self.checkTransactions(transactions)

    checkTransactionsHandler(checkTransactionsCase)



def getTransactions(classInstance):

    counter = 0
    temp = {}
    temp['requestType'] = "getUnconfirmedTransactions"
    temp['account'] = classInstance.config['nxtRS']
    numTransactions = classInstance.config['numTransactions']
    refTX = classInstance.mainHandler.getData("makeofferAPIReturn")
    refTX = refTX['triggerhash']

    while True:
        transactions = []
        ret = classInstance.mainHandler.api.doAPICall("getUnconfirmedTransaction", temp, True)
        if "unconfirmedTransactions" in ret:
            unconfs = ret['unconfirmedTransactions']
            for i in range(len(unconfs)):
                if "referencedTransactionFullHash" in unconfs[i]:
                    if unconfs[i]['referencedTransactionFullHash'] == refTX:
                        transactions.append(unconfs[i])
                elif unconfs[i]['fullHash'] == refTX:
                    transactions.append(unconfs[i])

        if len(transactions) == numTransactions:
            break
        if counter == 7:
            classInstance.progress.append("failed getting transactions. num transactions = " +str(len(transactions)))
            for i in range(len(transactions)):
                classInstance.progress.append(json.dumps(transactions[i]))
            break

        counter += 1
        time.sleep(1)

    classInstance.mainHandler.storeData("transactions", transactions)
    return transactions



def sortTransactions(classInstance):

    obj = {}
    temp = []
    baseAsset = classInstance.config['baseAsset']
    transactions = classInstance.mainHandler.getData("transactions")

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

        classInstance.progress.append(json.dumps(transaction))

        temp.append(transaction)


    classInstance.mainHandler.storeData("sortedTransactions", temp)
    return temp



def checkTransactionsHandler(classInstance):

    config = classInstance.config

    checkFeeTransactionFunc = "checkFeeTransaction"
    checkFeeTransactionCase = TestCase(func=checkFeeTransactionFunc, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="runner")

    checkBaseTransactionConfig = {"baseAsset":config['baseAsset'], "offerType":config['offerType']}
    checkBaseTransactionFunc = "checkBaseTransaction"
    checkBaseTransactionCase = TestCase(func=checkBaseTransactionFunc, config=checkBaseTransactionConfig, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="runner")

    checkRelTransactionConfig = {"relAsset":config['relAsset'], "offerType":config['offerType']}
    checkRelTransactionFunc = "checkRelTransaction"
    checkRelTransactionCase = TestCase(func=checkRelTransactionFunc, config=checkRelTransactionConfig, parent=classInstance, mainHandler=classInstance.mainHandler, typeCase="runner")


    classInstance.addChild(checkFeeTransactionCase) 
    classInstance.addChild(checkBaseTransactionCase) 
    classInstance.addChild(checkRelTransactionCase) 

        

def checkFeeTransaction(classInstance):

    transactions = classInstance.mainHandler.getData("sortedTransactions")
    transaction = searchListOfObjects(transactions, "IDEX_TYPE", "fee", True)

    if transaction['amountNQT'] == "250000000":
        classInstance.progress.append("fee correct")
    else:
        classInstance.progress.append("fee incorrect")


def checkBaseTransaction(classInstance):

    decimals = classInstance.config['baseAsset']['decimals']
    offerType = classInstance.config['offerType']
    perc = "1" #classInstance.config['perc']

    params = classInstance.mainHandler.getData("makeofferAPIParams")
    transactions = classInstance.mainHandler.getData("sortedTransactions")

    transaction = searchListOfObjects(transactions, "IDEX_TYPE", "base", True)

    attachment = transaction['attachment']
    isAsk = "version.AskOrderPlacement" in attachment

    amount = attachment['quantityQNT']
    amount = float(amount) / float(pow(10, int(decimals)))
    paramAmount = perc + "~" + str(params['baseiQ']['volume'])   #paramAmount = float((int(self.perc) / 100) * self.params['baseiQ']['volume'])

    price = attachment['priceNQT']
    paramPrice = params['baseiQ']['price']


    if isAsk and offerType == "Sell":
        classInstance.progress.append("base offer type correct")
    else:
        classInstance.progress.append("base offer type incorrect")

    classInstance.progress.append("BASE AMOUNT: " + paramAmount + " --- ACTUAL AMOUNT: " + str(amount))
    classInstance.progress.append("BASE PRICE: " + str(paramPrice) + " --- ACTUAL PRICE: " + str(price))


def checkRelTransaction(classInstance):

    decimals = classInstance.config['relAsset']['decimals']
    offerType = classInstance.config['offerType']
    perc = "1" #classInstance.config['perc']

    params = classInstance.mainHandler.getData("makeofferAPIParams")
    transactions = classInstance.mainHandler.getData("sortedTransactions")

    transaction = searchListOfObjects(transactions, "IDEX_TYPE", "rel", True)

    attachment = transaction['attachment']
    isAsk = "version.AskOrderPlacement" in attachment

    amount = attachment['quantityQNT']
    amount = float(amount) / float(pow(10, int(decimals)))
    paramAmount = perc + "~" + str(params['reliQ']['volume'])  #paramAmount = float((int(self.perc) / 100) * self.params['reliQ']['volume'])

    price = attachment['priceNQT']
    paramPrice = params['reliQ']['price']



    if not isAsk and offerType == "Sell":
        classInstance.progress.append("rel offertype correct")
    else:
        classInstance.progress.append("rel offertype incorrect")

    classInstance.progress.append("REL AMOUNT: " + paramAmount + " --- ACTUAL AMOUNT: " + str(amount))
    classInstance.progress.append("REL PRICE: " + str(paramPrice) + " --- ACTUAL PRICE: " + str(price))
        








