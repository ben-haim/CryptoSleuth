#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import *
from api import API
from daemonstream import DaemonStream
import time
import json
from testcase import *


class Makeoffer(Controller):

    def __init__(self, config={}, filename=None, user=None, snDaemon=None, controllerName=None):
        Controller.__init__(self, config=config, filename=filename, user=user, snDaemon=snDaemon, controllerName=controllerName)

        self.baseAsset = checkObj(config, "baseAsset", None)
        self.baseAmount = checkObj(config, "baseAmount", 0)
        self.baseAmountDecimals = checkObj(config, "baseAmountDecimals", None)
        self.minBaseAmount = checkObj(config, "minBaseAmount", 0)

        self.relAsset = checkObj(config, "relAsset", None)
        self.relAmount = checkObj(config, "relAmount", 0)
        self.minRelAmount = checkObj(config, "minRelAmount", 0)

        self.perc = checkObj(config, "perc", 1)
        self.offerType = checkObj(config, "offerType", None)
        self.exchangeType = checkObj(config, "exchangeType", None)
        #self.isExternalExchange = False

    def initTestParams(self):

        defaults = {
            "baseAsset": None,
            "baseAmount": 0,
            "minBaseAmount": 0,
            "relAsset": None,
            "relAmount": 0,
            "minRelAmount": 0,
            "perc": 1,
            "offerType": None,
            "exchangeType": None
            #"isExternalExchange": {"value":None, "default":None}
        }

        newConfig = {}

        for param in defaults:
            if param in self.config:
                pass
            else:
                self.config[param] = defaults[param]


    def initCases(self):

        if self.exchangeType == "nxtae":
            self.numTransactions = 1
        elif self.exchangeType == "nxtae_nxtae":
            self.numTransactions = 3


        getOrderbook_Config = {"baseAsset":self.baseAsset, "relAsset":self.relAsset}
        getOrderbook_Case = Handler(config=getOrderbook_Config, parent=self, mainHandler=self)
        getOrderbookHandler(getOrders_Case)
        self.addChild(getOrderbook_Case)


        parseOrders_Config = {"exchangeType":self.exchangeType, "offerType":self.offerType, "baseAmountDecimals":self.baseAmountDecimals}
        parseOrders_Case = Handler(config=parseOrders_Config, parent=self, mainHandler=self)
        parseOrdersHandler(selectOrder_Case)
        self.addChild(parseOrders_Case)


        selectOrder_Config = {}
        selectOrder_Case = Handler(config=selectOrder_Config, parent=self, mainHandler=self)
        selectOrderHandler(selectOrder_Case)
        self.addChild(selectOrder_Case)


        makeofferAPICall_Case = Handler(parent=self, mainHandler=self)
        callMakeofferHandler(makeofferAPICall_Case)
        self.addChild(makeofferAPICall_Case)


        getTransactions_Config = {"baseAsset":self.baseAsset, "relAsset":self.relAsset, "numTransactions":self.numTransactions, "nxtRS":self.user.nxtRS}
        getTransactions_Case = HandlerLooper(config=getTransactions_Config, parent=self, mainHandler=self)
        getTransactionsHandler(getTransactions_Case)
        self.addChild(getTransactions_Case)


        checkTransactions_Config = {"baseAsset":config['baseAsset'], "relAsset":config['relAsset'], "offerType":config['offerType']}
        checkTransactions_Case = Handler(config=checkTransactions_Config, mainHandler=classInstance.mainHandler)
        checkTransactionsHandler(checkTransactions_Case)
        self.addChild(checkTransactions_Case)




################    HANDLERS?    ################



#base handler
def getOrderbookHandler(classInstance):

    config = classInstance.config

    buildOrderbookAPIParams_Config = {"baseAsset":config['baseAsset'], "relAsset":config['relAsset']}
    buildOrderbookAPIParams_NeededData = []
    buildOrderbookAPIParams_Func = "buildOrderbookAPIParams"
    buildOrderbookAPIParams_Case = Runner(func=buildOrderbookAPIParams_Func, config=buildOrderbookAPIParams_Config, mainHandler=classInstance.mainHandler)
    classInstance.addChild(buildOrderbookAPIParams_Case)


    doOrderbookAPICall_Config = None
    doOrderbookAPICall_NeededData = ["orderbookAPIParams"]
    doOrderbookAPICall_Func = "doOrderbookAPICall"
    doOrderbookAPICall_Case = Runner(func=doOrderbookAPICall_Func, config=doOrderbookAPICall_Config, neededData=doOrderbookAPICall_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(doOrderbookAPICall_Case)




#base handler
def parseOrdersHandler(classInstance):

    config = classInstance.config


    parseOrdersByOfferType_Config = {"offerType":config['offerType']}
    parseOrdersByOfferType_NeededData = ["orderbook"]
    parseOrdersByOfferType_Func = "parseOrdersByOfferType"
    parseOrdersByOfferType_Case = Runner(func=parseOrdersByOfferType_Func, config=parseOrdersByOfferType_Config, neededData=parseOrdersByOfferType_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(parseOrdersByOfferType_Case)


    parseOrdersByExchange_Config = {"exchangeType":config['exchangeType']}
    parseOrdersByExchange_NeededData = ["orders"]
    parseOrdersByExchange_Func = "parseOrdersByExchange"
    parseOrdersByExchange_Case = Runner(func=parseOrdersByExchange_Func, config=parseOrdersByExchange_Config, neededData=parseOrdersByExchange_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(parseOrdersByExchange_Case)


    if config['baseAmountDecimals'] is not None:
        parseOrdersByBaseAmountDecimals_Config = {"baseAmountDecimals":config['baseAmountDecimals'], "baseAsset":config['baseAsset']}
        parseOrdersByBaseAmountDecimals_NeededData = ["parsedOrdersByExchange"]
        parseOrdersByBaseAmountDecimals_Func = "parseOrdersByBaseAmountDecimals"
        parseOrdersByBaseAmountDecimals_Case = Runner(func=parseOrdersByBaseAmountDecimals_Func, config=parseOrdersByBaseAmountDecimals_Config, neededData=parseOrdersByBaseAmountDecimals_NeededData, mainHandler=classInstance.mainHandler)
        classInstance.addChild(parseOrdersByBaseAmountDecimals_Case)




#base handler
def selectOrderHandler(classInstance):

    config = classInstance.config

    selectOrder_Config = {}
    selectOrder_NeededData = ["lastParsedOrdersName"]
    selectOrder_Func = "selectOrder"
    selectOrder_Case = Runner(func=selectOrder_Func, config=selectOrder_Config, neededData=selectOrder_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(selectOrder_Case)




#base handler
def callMakeofferHandler(classInstance):

    config = classInstance.config


    buildMakeofferAPIParams_Config = {}
    buildMakeofferAPIParams_NeededData = ["selectedOrder"]
    buildMakeofferAPIParams_Func = "buildMakeofferAPIParams"
    buildMakeofferAPIParams_Case = Runner(func=buildMakeofferAPIParams_Func, neededData=buildMakeofferAPIParams_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(buildMakeofferAPIParams_Case) 


    doMakeofferAPICall_Config = {}
    doMakeofferAPICall_NeededData = ["makeofferAPIParams"]
    doMakeofferAPICall_Func = "doMakeofferAPICall"
    doMakeofferAPICall_Case = Runner(func=doMakeofferAPICall_Func, neededData=doMakeofferAPICall_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(doMakeofferAPICall_Case)




#base handler
def getTransactionsHandler(classInstance):

    config = classInstance.config

    classInstance.numLoops = 5
    classInstance.sleepTime = 1
    classInstance.breaker = 2

    getTransactionAPICall_Config = {"nxtRS":config['nxtRS']}
    getTransactionAPICall_NeededData = ["makeofferAPIReturn"]
    getTransactionAPICall_Func = "doUnconfirmedTransactionsAPICall"
    getTransactionAPICall_Case = Runner(func=getTransactionAPICall_Func, config=getTransactionAPICall_Config, neededData=getTransactionAPICall_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(getTransactionAPICall_Case) 


    parseTransactions_Config = {"baseAsset":config['baseAsset'], "relAsset":config['relAsset']}
    parseTransactions_NeededData = ["unconfirmedTransactions", "makeofferAPIReturn"]
    parseTransactions_Func = "parseTransactions"
    parseTransactions_Case = Runner(func=parseTransactions_Func, config=parseTransactions_Config, neededData=parseTransactions_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(parseTransactions_Case)


    countTransactions_Config = {"numTransactions":config['numTransactions']}
    countTransactions_NeededData = ["sortedTransactions"]
    countTransactions_Func = "countTransactions"
    countTransactions_Case = Runner(func=countTransactions_Func, config=countTransactions_Config, neededData=countTransactions_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(countTransactions_Case)




def checkTransactionsHandler(classInstance):

    config = classInstance.config


    checkFeeTransaction_Config = {}
    checkFeeTransaction_NeededData = ["feeTransaction"]
    checkFeeTransaction_Func = "checkFeeTransaction"
    checkFeeTransaction_Case = Runner(func=checkFeeTransaction_Func, neededData=checkFeeTransaction_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(checkFeeTransaction_Case)


    checkBaseTransaction_Config = {"baseAsset":config['baseAsset'], "offerType":config['offerType']}
    checkBaseTransaction_Case = Handler(config=checkBaseTransaction_Config, mainHandler=classInstance.mainHandler)
    classInstance.addChild(checkBaseTransaction_Case) 
    checkBaseTransactionHandler(checkBaseTransaction_Case)


    checkRelTransaction_Config = {"relAsset":config['relAsset'], "offerType":config['offerType']}
    checkRelTransaction_Case = Handler(config=checkRelTransaction_Config, mainHandler=classInstance.mainHandler)
    classInstance.addChild(checkRelTransaction_Case) 
    checkRelTransactionHandler(checkRelTransaction_Case)




def checkBaseTransactionHandler(classInstance):

    config = classInstance.config


    checkBaseTransactionOrderType_Config = {"offerType":config['offerType'], "isBase":True}
    checkBaseTransactionOrderType_NeededData = ["baseTransaction"]
    checkBaseTransactionOrderType_Func = "checkTransactionOrderType"
    checkBaseTransactionOrderType_Case = Runner(func=checkBaseTransactionAmount_Func, config=checkBaseTransactionOrderType_Config, neededData=checkBaseTransactionOrderType_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(checkBaseTransactionOrderType_Case) 


    checkBaseTransactionAmount_Config = {"baseAsset":config['baseAsset'], "isBase":True}
    checkBaseTransactionAmount_NeededData = ["baseTransaction", "makeofferAPIReturn"]
    checkBaseTransactionAmount_Func = "checkTransactionAmount"
    checkBaseTransactionAmount_Case = Runner(func=checkBaseTransactionAmount_Func, config=checkBaseTransactionAmount_Config, neededData=checkBaseTransactionAmount_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(checkBaseTransactionAmount_Case) 


    checkBaseTransactionPrice_Config = {"baseAsset":config['baseAsset'], "isBase":True}
    checkBaseTransactionPrice_NeededData = ["baseTransaction", "makeofferAPIReturn"]
    checkBaseTransactionPrice_Func = "checkTransactionPrice"
    checkBaseTransactionPrice_Case = Runner(func=checkBaseTransactionPrice_Func, config=checkBaseTransactionPrice_Config, neededData=checkBaseTransactionPrice_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(checkBaseTransactionPrice_Case) 




def checkRelTransactionHandler(classInstance):

    config = classInstance.config


    checkRelTransactionOrderType_Config = {"offerType":config['offerType'], "isBase":False}
    checkRelTransactionOrderType_NeededData = ["relTransaction"]
    checkRelTransactionOrderType_Func = "checkTransactionOrderType"
    checkRelTransactionOrderType_Case = Runner(func=checkRelTransactionOrderType_Func, config=checkRelTransactionOrderType_Config, neededData=checkRelTransactionOrderType_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(checkRelTransactionOrderType_Case) 


    checkRelTransactionAmount_Config = {"relAsset":config['relAsset'], "isBase":False}
    checkRelTransactionAmount_NeededData = ["relTransaction", "makeofferAPIReturn"]
    checkRelTransactionAmount_Func = "checkTransactionAmount"
    checkRelTransactionAmount_Case = Runner(func=checkRelTransactionAmount_Func, config=checkRelTransactionAmount_Config, neededData=checkRelTransactionAmount_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(checkRelTransactionAmount_Case) 


    checkRelTransactionPrice_Config = {"relAsset":config['relAsset'], "isBase":False}
    checkRelTransactionPrice_NeededData = ["relTransaction", "makeofferAPIReturn"]
    checkRelTransactionPrice_Func = "checkTransactionPrice"
    checkRelTransactionPrice_Case = Runner(func=checkRelTransactionPrice_Func, config=checkRelTransactionPrice_Config, neededData=checkRelTransactionPrice_NeededData, mainHandler=classInstance.mainHandler)
    classInstance.addChild(checkRelTransactionPrice_Case) 





################    RUNNER FUNCTIONS?    ###############


################    ORDERBOOK API  + GET ORDERS    ###############


def buildOrderbookAPIParams(classInstance):

    #dependant
    baseAssetID = classInstance.config['baseAsset']['assetID']
    relAssetID = classInstance.config['relAsset']['assetID']
    #

    orderbookAPIParams = {}
    orderbookAPIParams['requestType'] = "orderbook"
    orderbookAPIParams['baseid'] = baseAssetID
    orderbookAPIParams['relid'] = relAssetID
    orderbookAPIParams['allfields'] = 1
    orderbookAPIParams['maxdepth'] = 30

    classInstance.addProgress("SUCCESS: Constructed Orderbook API params:")
    classInstance.addProgress(orderbookAPIParams, indent=4)

    classInstance.retLevel = 0
    classInstance.retMsg = "SUCCESS: Constructed Orderbook API params"

    classInstance.retData.append({"orderbookAPIParams":orderbookAPIParams})


def doOrderbookAPICall(classInstance, data):

    #dependant
    orderbookAPIParams = data['orderbookAPIParams']
    api = classInstance.mainHandler.api
    #

    orderbook = {}

    classInstance.addProgress("Trying orderbook API call...")

    try:
        orderbook = api.doAPICall("orderbook", orderbookAPIParams)
    except:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: Orderbook API call failed"
        
    else:
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Orderbook API call successful"

    classInstance.addProgress(classInstance.retMsg)


    classInstance.retData.append({"orderbook":orderbook})




################    PARSE ORDERS    ###############



def parseOrdersByOfferType(classInstance, data):

    #dependant
    neededOrdersType = "bids" if classInstance.config['offerType'] == "Sell" else "asks"
    orderbook = data['orderbook']
    #

    orders = []
    classInstance.addProgress("Checking orderbook orders for " + neededOrdersType + "...")

    if neededOrdersType in orderbook:

        orders = orderbook[neededOrdersType]

        if len(orders):

            classInstance.addProgress("Found " + str(len(orders)) + " " + neededOrdersType + "in orderbook object:")
            for i in range(len(orders)):
                    classInstance.addProgress(orders[i], indent=4)

            classInstance.retLevel = 0
            classInstance.retMsg = "SUCCESS: " + neededOrdersType + " in orderbook"
        else:
            classInstance.retLevel = -1
            classInstance.retMsg = "FAIL: " + neededOrdersType + " key in orderbook object has length of 0"

    else:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: Unexpected - No " + neededOrdersType + " key in orderbook object"

    #classInstance.addProgress(classInstance.retMsg)

    classInstance.retData.append({"orders":orders})


def parseOrdersByExchange(classInstance, data):

    orders = data['orders']
    exchangeType = classInstance.config['exchangeType']

    parsedOrders = []

    classInstance.addProgress("Searching for orders with exchange: " + exchangeType + "...")

    for i in range(len(orders)):

        order = orders[i]
        classInstance.addProgress("Checking order #" + str(i) + ":", indent=4)
        classInstance.addProgress(order, indent=8)

        if exchangeType != "any":

            if orders[i]['exchange'] == exchangeType:
                classInstance.addProgress("MATCH. Order's exchange matches exchangeType", indent=8)
                pass

            else:
                classInstance.addProgress("Order's exchange does not match exchangeType. " + "(" + order['exchange'] + " vs. " + exchangeType + ")", indent=8)
                continue
        
        parsedOrders.append(order)


    if len(parsedOrders):
        classInstance.addProgress("Parsed " + str(len(parsedOrders)) + " orders")
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Parsed " + str(len(parsedOrders)) + " orders"
    else:
        classInstance.addProgress("Could not parse. No orders matched exchangeType")
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: No orders matched exchangeType"


    classInstance.retData.append({"lastParsedOrdersName":"parsedOrdersByExchange"})
    classInstance.retData.append({"parsedOrdersByExchange":parsedOrders})



def parseOrdersByBaseAmountDecimals(classInstance, data):

    baseAssetDecimals = classInstance.config['baseAsset']['decimals']
    baseAmountDecimals = classInstance.config['baseAmountDecimals']

    orders = data['parsedOrdersByExchange']

    #decimalPlaces = decimal.Decimal(10) ** (-abs(int(decimals)))
    parsedOrders = []
    qntDecimals = 8 - int(baseAssetDecimals)

    for i in range(len(orders)):

        perc = 1
        order = orders[i]

        while perc <= 100:

            numTrailingZeroes = 0
            stringLength = 0

            percMultiplier = float(perc) / float(100)
            makeofferAmountQNT_Raw = str(order['baseamount'])
            makeofferAmountQNT_Float = float(makeofferAmountQNT_Raw) / float(pow(10, qntDecimals))
            makeofferAmountQNT_WithPerc_Float = percMultiplier * makeofferAmountQNT_Float
            makeofferAmountQNT_Str = str(int(makeofferAmountQNT_WithPerc_Float))

            stringLength = len(makeofferAmountQNT_Str)

            counter = 0
            for char in reversed(makeofferAmountQNT_Str):
                if counter == baseAssetDecimals:
                    break
                if char == "0":
                    numTrailingZeroes += 1
                else:
                    break
                counter += 1

            numDecimals = baseAssetDecimals - numTrailingZeroes

            if numDecimals == int(baseAmountDecimals):
                parsedOrders.append({"order":order, "perc":str(perc)})
                break

            perc += 1


    if len(parsedOrders):
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Found orders with correct amount decimals"
    else:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: No orders that would lead to correct decimals in base amount"



    #classInstance.addProgress("Searching for orders with exchange: " + exchangeType + "...")



    classInstance.retData.append({"lastParsedOrdersName":"parsedOrdersByAmount"})
    classInstance.retData.append({"parsedOrdersByAmount":parsedOrders})



################    SELECT ORDER    ################


def selectOrder(classInstance, data):

    parsedOrdersName = data['lastParsedOrdersName']
    parsedOrders = classInstance.mainHandler.getData(parsedOrdersName)

    if parsedOrdersName == "parsedOrdersByAmount":
        classInstance.mainHandler.config['perc'] = parsedOrders[0]['perc']
        classInstance.mainHandler.perc = parsedOrders[0]['perc']
        selectedOrder = parsedOrders[0]['order']

    else:
        selectedOrder = parsedOrders[0]

    classInstance.addProgress("Selected an order from " + str(len(parsedOrders)) + " orders:")
    classInstance.addProgress(selectedOrder, indent=4)

    classInstance.retLevel = 0
    classInstance.retMsg = "SUCCESS: Selected an order"

    classInstance.retData.append({"selectedOrder":selectedOrder})



################    MAKEOFFER API    ################


def buildMakeofferAPIParams(classInstance, data):

    #dependant
    selectedOrder = data['selectedOrder']
    perc = classInstance.mainHandler.perc
    #

    makeofferAPIParams = {}
    makeofferAPIParams['requestType'] = "makeoffer3"
    makeofferAPIParams['perc'] = perc

    for key in selectedOrder:
        makeofferAPIParams[key] = selectedOrder[key]


    classInstance.addProgress("Constructed makeoffer API params:")
    classInstance.addProgress(makeofferAPIParams, indent=4)

    classInstance.retLevel = 0
    classInstance.retMsg = "SUCCESS: Constructed makeoffer API params"


    classInstance.retData.append({"makeofferAPIParams":makeofferAPIParams})


def doMakeofferAPICall(classInstance, data):

    #dependant
    params = data['makeofferAPIParams']
    api = classInstance.mainHandler.api
    #

    makeofferAPIReturn = {}

    classInstance.addProgress("Trying makeoffer API call...")
    try:
        makeofferAPIReturn = api.doAPICall("makeoffer", params)
    except:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: Makeoffer API call failed"
    else:
        if "triggerhash" in makeofferAPIReturn:
            classInstance.retLevel = 0
            classInstance.retMsg = "SUCCESS: Makeoffer API call succeeded"
        else:
            classInstance.retLevel = -1
            classInstance.retMsg = "FAIL: No triggerhash in makeoffer return"

    classInstance.addProgress(classInstance.retMsg)
    classInstance.addProgress(makeofferAPIReturn, indent=4)

    classInstance.retData.append({"makeofferAPIReturn":makeofferAPIReturn})




################    GET TRANSACTIONS    ################



def doUnconfirmedTransactionsAPICall(classInstance, data):

    #dependant
    api = classInstance.mainHandler.api
    nxtRS = classInstance.config['nxtRS']

    getTransactionsAPIParams = {}   #getTransactionsAPIParams = data['getTransactionsAPIParams']
    getTransactionsAPIParams['requestType'] = "getUnconfirmedTransactions"
    getTransactionsAPIParams['account'] = nxtRS

    #


    classInstance.addProgress("Trying getUnconfirmedTransactions API call...", indent=4)

    try:
        orderbook = api.doAPICall("orderbook", getTransactionsAPIParams)
    except:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: getUnconfirmedTransactions API call failed..."
        ret = {}
        
    else:
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: getUnconfirmedTransactions API call successful"
        #classInstance.addProgress("Got " + str(len(unconfirmedTransactions)) + " unconfirmed transactions", indent=4)

    classInstance.addProgress(classInstance.retMsg)

    classInstance.retData.append({"unconfirmedTransactions":unconfirmedTransactions})



def checkAPICallReturn(classInstance, data):

    if "unconfirmedTransactions" in ret:
        unconfirmedTransactions = ret['unconfirmedTransactions']

    else:
        classInstance.addProgress("No unconfirmed transactions", indent=4)



def parseTransactions(classInstance, data):

    #dependant
    baseID = classInstance.config['baseAsset']['assetID']
    relID = classInstance.config['relAsset']['assetID']
    transactions = data['unconfirmedTransactions']
    refTX = data['makeofferAPIReturn']['triggerhash']
    #

    sortedTransactions = []
    feeTransaction = {}
    baseTransaction = {}
    relTransaction = {}

    for i in range(len(transactions)):
        transaction = transactions[i]

        if "referencedTransactionFullHash" in transaction:
            if unconfirmedTransactions[i]['referencedTransactionFullHash'] == refTX:
                if "attachment" in transaction:
                    attachment = transaction['attachment']

                    if attachment['asset'] == baseID:
                        transaction['IDEX_TYPE'] = "base"
                        classInstance.addProgress("Found base transaction:")
                        classInstance.addProgress(transaction, indent=4)
                        baseTransaction = transaction
                        sortedTransactions.append(transaction)

                    elif attachment['asset'] == relID:
                        transaction['IDEX_TYPE'] = "rel"
                        classInstance.addProgress("Found rel transaction:")
                        classInstance.addProgress(transaction, indent=4)
                        relTransaction = transaction
                        sortedTransactions.append(transaction)

        elif unconfirmedTransactions[i]['fullHash'] == refTX
            transaction['IDEX_TYPE'] = "fee"
            classInstance.addProgress("Found fee transaction:")
            classInstance.addProgress(transaction, indent=4)
            feeTransaction = transaction
            sortedTransactions.append(transaction)


    classInstance.retLevel = 0
    classInstance.retMsg = "SUCCESS: Sorted all transactions"

    classInstance.retData.append({"sortedTransactions":sortedTransactions})
    classInstance.retData.append({"feeTransaction":feeTransaction})
    classInstance.retData.append({"baseTransaction":baseTransaction})
    classInstance.retData.append({"relTransaction":relTransaction})


def countTransactions(classInstance):

    transactions = data['sortedTransactions']
    numTransactions = classInstance.config['numTransactions']

    if len(transactions) == numTransactions:
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: All transactions found"
        classInstance.addProgress(classInstance.retMsg)
    else:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: Could not find all transactions"
        classInstance.addProgress(classInstance.retMsg)


################    CHECK TRANSACTIONS    ################



def checkFeeTransaction(classInstance, data):

    #dependant
    transaction = data['feeTransaction']
    #

    if "amountNQT" in transaction:
        if transaction['amountNQT'] == "250000000":
            classInstance.addProgress("Fee transaction has correct fee of 250000000")
            classInstance.retLevel = 0
            classInstance.retMsg = "SUCCESS: Correct fee amount"
        else:
            classInstance.addProgress("Incorrect fee for fee transaction: " + str(transaction['amountNQT']) + ". Expected 250000000")
            classInstance.retLevel = 1
            classInstance.retMsg = "FAIL: Incorrect fee in fee transaction"
    else:
        classInstance.addProgress("Unexpected error - no amountNQT in fee transaction:")
        classInstance.addProgress(transaction, indent=4)
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: (Internal) No amountNQT in fee transaction"



def checkTransactionOrderType(classInstance, data):

    #dependant
    makeofferOfferType = classInstance.config['offerType']



    isBase = classInstance.config['isBase']

    if isBase:
        attachment = data['baseTransaction']['attachment']
        offerType = makeofferOfferType
    else:
        attachment = data['relTransaction']['attachment']
        offerType = "Sell" if makeofferOfferType == "Buy" else "Buy"

    transactionOfferType = "Sell" if "version.AskOrderPlacement" in attachment else "Buy"
    #


    compString = "Transaction offerType: " + transactionOfferType + ". Needed offerType: " + str(offerType)    

    if transactionOfferType == offerType:
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Transaction offerType correct. " + compString
        classInstance.addProgress(classInstance.retMsg)
    else:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Transaction offerType incorrect. " + compString
        classInstance.addProgress(classInstance.retMsg)


def checkTransactionAmount(classInstance, data):

    #import decimal
    #decimalPlaces = decimal.Decimal(10) ** (-abs(int(decimals)))

    #dependant
    makeofferRet = data['makeofferAPIReturn']
    perc = makeofferRet['perc']
    isBase = classInstance.config['isBase']

    if isBase:
        decimals = classInstance.config['baseAsset']['decimals']
        attachment = data['baseTransaction']['attachment']
        amount = makeofferRet['baseamount']


    else:
        decimals = classInstance.config['relAsset']['decimals']
        attachment = data['relTransaction']['attachment']
        amount = makeofferRet['relamount']


    transactionAmountQNT = str(attachment['quantityQNT'])
    #


    transactionAmount = float(transactionAmountQNT) / float(pow(10, int(decimals)))

    amount_Raw = amount
    convertedAmount = convertAssetAmount(amount_Raw, decimals, perc):

    if int(transactionAmountQNT) == int(makeofferAmountQNT_WithPerc_Float):
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Transaction amount equals makeoffer amount"
    else:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Transaction amount does not equal makeoffer amount: " + str(int(transactionAmountQNT)) + " vs. " + str(int(makeofferAmountQNT_WithPerc_Float))

    classInstance.addProgress("Transaction amount QNT: " + str(transactionAmountQNT) + ".  Makeoffer amount QNT: " + str(int(makeofferAmountQNT_WithPerc_Float)))
    classInstance.addProgress("Makeoffer amount QNT(float): " + str(makeofferAmountQNT_WithPerc_Float))
    classInstance.addProgress("Makeoffer amount: " + str(makeofferAmount))
    classInstance.addProgress("Transaction amount: " + str(transactionAmount))
    classInstance.addProgress(classInstance.retMsg)



def checkTransactionPrice(classInstance, data):

    #dependant
    makeofferRet = data['makeofferAPIReturn']

    isBase = classInstance.config['isBase']

    if isBase:
        assetID = classInstance.config['baseAsset']['assetID']
        decimals = classInstance.config['baseAsset']['decimals']
        attachment = data['baseTransaction']['attachment']

    else:
        assetID = classInstance.config['relAsset']['assetID']
        decimals = classInstance.config['relAsset']['decimals']
        attachment = data['relTransaction']['attachment']

    transactionPriceNQT = attachment['priceNQT']
    keys = ["buyer", "buyer2", "seller", "seller2"]
    #

    makeofferPriceNQT = None

    for key in keys:
        if key in makeofferRet and makeofferRet[key]['assetid'] == assetID:
            makeofferPriceNQT = str(makeofferRet[key]['priceNQT'])
            break

    if makeofferPriceNQT:

        classInstance.addProgress("Transaction price NQT: " + str(transactionPriceNQT) + ". Makeoffer base price: " + str(makeofferPriceNQT))
        if int(transactionPriceNQT) == int(makeofferPriceNQT):
            classInstance.retLevel = 0
            classInstance.retMsg = "SUCCESS: Base transaction price equals makeoffer base price"
        else:
            classInstance.retLevel = 1
            classInstance.retMsg = "FAIL: Base transaction price does not equal makeoffer base price: " + str(transactionPriceNQT) + " vs. " + str(makeofferPriceNQT)

    else:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Unexpected error - check makeofferAPIReturn"




