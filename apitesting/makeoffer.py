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

        getOrders_Config = {"exchangeType":self.exchangeType, "offerType":self.offerType, "baseAmount":self.baseAmount, "baseAsset":self.baseAsset, "relAsset":self.relAsset}
        getOrders_Case = Handler(config=getOrders_Config, parent=self, mainHandler=self)
        getOrdersHandler(getOrders_Case)

        selectOrder_Config = {"exchangeType":self.exchangeType, "offerType":self.offerType, "baseAmountDecimals":self.baseAmountDecimals, "baseAsset":self.baseAsset, "relAsset":self.relAsset}
        selectOrder_Case = Handler(config=selectOrder_Config, parent=self, mainHandler=self)
        selectOrderHandler(selectOrder_Case)

        makeoffer_Case = Handler(parent=self, mainHandler=self)
        callMakeofferHandler(makeoffer_Case)

        transactions_Config = {"baseAsset":self.baseAsset, "relAsset":self.relAsset, "numTransactions":self.numTransactions, "offerType":self.offerType, "nxtRS":self.user.nxtRS}
        transactions_Case = Handler(config=transactions_Config, parent=self, mainHandler=self)
        transactionsHandler(transactions_Case)

        self.addChild(getOrders_Case)
        self.addChild(selectOrder_Case)
        self.addChild(makeoffer_Case)
        self.addChild(transactions_Case)




################    HANDLERS?    ################


#base handler
def getOrdersHandler(classInstance):

    config = classInstance.config

    buildOrderbookAPIParams_Config = {"baseAsset":config['baseAsset'], "relAsset":config['relAsset']}
    buildOrderbookAPIParams_NeededData = []
    buildOrderbookAPIParams_Func = "buildOrderbookAPIParams"
    buildOrderbookAPIParams_Case = Runner(func=buildOrderbookAPIParams_Func, config=buildOrderbookAPIParams_Config, mainHandler=classInstance.mainHandler)


    doOrderbookAPICall_Config = None
    doOrderbookAPICall_NeededData = ["orderbookAPIParams"]
    doOrderbookAPICall_Func = "doOrderbookAPICall"
    doOrderbookAPICall_Case = Runner(func=doOrderbookAPICall_Func, config=doOrderbookAPICall_Config, neededData=doOrderbookAPICall_NeededData, mainHandler=classInstance.mainHandler)


    getOrderbookOrders_Config = {"offerType":config['offerType']}
    getOrderbookOrders_NeededData = ["orderbook"]
    getOrderbookOrders_Func = "getOrderbookOrders"
    getOrderbookOrders_Case = Runner(func=getOrderbookOrders_Func, config=getOrderbookOrders_Config, neededData=getOrderbookOrders_NeededData, mainHandler=classInstance.mainHandler)


    classInstance.addChild(buildOrderbookAPIParams_Case)
    classInstance.addChild(doOrderbookAPICall_Case)
    classInstance.addChild(getOrderbookOrders_Case)



#base handler
def selectOrderHandler(classInstance):

    config = classInstance.config

    parseOrdersByExchange_Config = {"exchangeType":config['exchangeType']}
    parseOrdersByExchange_NeededData = ["orders"]
    parseOrdersByExchange_Func = "parseOrdersByExchange"
    parseOrdersByExchange_Case = Runner(func=parseOrdersByExchange_Func, config=parseOrdersByExchange_Config, neededData=parseOrdersByExchange_NeededData, mainHandler=classInstance.mainHandler)

    #bad
    if config['baseAmountDecimals'] is not None:
        parseOrdersByBaseAmountDecimals_Config = {"baseAmountDecimals":config['baseAmountDecimals'], "baseAsset":config['baseAsset']}
        parseOrdersByBaseAmountDecimals_NeededData = ["parsedOrdersByExchange"]
        parseOrdersByBaseAmountDecimals_Func = "parseOrdersByBaseAmountDecimals"
        parseOrdersByBaseAmountDecimals_Case = Runner(func=parseOrdersByBaseAmountDecimals_Func, config=parseOrdersByBaseAmountDecimals_Config, neededData=parseOrdersByBaseAmountDecimals_NeededData, mainHandler=classInstance.mainHandler)

    selectOrder_Config = {}
    selectOrder_NeededData = ["lastParsedOrdersName"]
    selectOrder_Func = "selectOrder"
    selectOrder_Case = Runner(func=selectOrder_Func, config=selectOrder_Config, neededData=selectOrder_NeededData, mainHandler=classInstance.mainHandler)

    classInstance.addChild(parseOrdersByExchange_Case)
    if config['baseAmountDecimals'] is not None:
        classInstance.addChild(parseOrdersByBaseAmountDecimals_Case)
    classInstance.addChild(selectOrder_Case)



#base handler
def callMakeofferHandler(classInstance):

    config = classInstance.config

    buildMakeofferAPIParams_Config = {}
    buildMakeofferAPIParams_NeededData = ["selectedOrder"]
    buildMakeofferAPIParams_Func = "buildMakeofferAPIParams"
    buildMakeofferAPIParams_Case = Runner(func=buildMakeofferAPIParams_Func, neededData=buildMakeofferAPIParams_NeededData, mainHandler=classInstance.mainHandler)


    doMakeofferAPICall_Config = {}
    doMakeofferAPICall_NeededData = ["makeofferAPIParams"]
    doMakeofferAPICall_Func = "doMakeofferAPICall"
    doMakeofferAPICall_Case = Runner(func=doMakeofferAPICall_Func, neededData=doMakeofferAPICall_NeededData, mainHandler=classInstance.mainHandler)


    classInstance.addChild(buildMakeofferAPIParams_Case) 
    classInstance.addChild(doMakeofferAPICall_Case)



#base handler
def transactionsHandler(classInstance):

    config = classInstance.config

    getTransactions_Config = {"nxtRS":config['nxtRS'], "numTransactions":config['numTransactions']}
    getTransactions_NeededData = ["makeofferAPIReturn"]
    getTransactions_Func = "getTransactions"
    getTransactions_Case = Runner(func=getTransactions_Func, config=getTransactions_Config, neededData=getTransactions_NeededData, mainHandler=classInstance.mainHandler)

    sortTransactions_Config = {"baseAsset":config['baseAsset']}
    sortTransactions_NeededData = ["transactions"]
    sortTransactions_Func = "sortTransactions"
    sortTransactions_Case = Runner(func=sortTransactions_Func, config=sortTransactions_Config, neededData=sortTransactions_NeededData, mainHandler=classInstance.mainHandler)

    checkTransactions_Config = {"baseAsset":config['baseAsset'], "relAsset":config['relAsset'], "offerType":config['offerType']}
    checkTransactions_Case = Handler(config=checkTransactions_Config, mainHandler=classInstance.mainHandler)

    classInstance.addChild(getTransactions_Case) 
    classInstance.addChild(sortTransactions_Case)
    classInstance.addChild(checkTransactions_Case)

    checkTransactionsHandler(checkTransactions_Case)



def checkTransactionsHandler(classInstance):

    config = classInstance.config

    checkFeeTransaction_Config = {}
    checkFeeTransaction_NeededData = ["feeTransaction"]
    checkFeeTransaction_Func = "checkFeeTransaction"
    checkFeeTransaction_Case = Runner(func=checkFeeTransaction_Func, neededData=checkFeeTransaction_NeededData, mainHandler=classInstance.mainHandler)


    checkBaseTransaction_Config = {"baseAsset":config['baseAsset'], "offerType":config['offerType']}
    checkBaseTransaction_Case = Handler(config=checkBaseTransaction_Config, mainHandler=classInstance.mainHandler)


    checkRelTransaction_Config = {"relAsset":config['relAsset'], "offerType":config['offerType']}
    checkRelTransaction_Case = Handler(config=checkRelTransaction_Config, mainHandler=classInstance.mainHandler)


    classInstance.addChild(checkFeeTransaction_Case) 
    classInstance.addChild(checkBaseTransaction_Case) 
    classInstance.addChild(checkRelTransaction_Case) 

    checkBaseTransactionHandler(checkBaseTransaction_Case)
    checkRelTransactionHandler(checkRelTransaction_Case)



def checkBaseTransactionHandler(classInstance):

    config = classInstance.config

    checkBaseTransactionOrderType_Config = {"offerType":config['offerType']}
    checkBaseTransactionOrderType_NeededData = ["baseTransaction"]
    checkBaseTransactionOrderType_Func = "checkBaseTransactionOrderType"
    checkBaseTransactionOrderType_Case = Runner(func=checkBaseTransactionOrderType_Func, config=checkBaseTransactionOrderType_Config, neededData=checkBaseTransactionOrderType_NeededData, mainHandler=classInstance.mainHandler)


    checkBaseTransactionAmount_Config = {"baseAsset":config['baseAsset']}
    checkBaseTransactionAmount_NeededData = ["baseTransaction", "makeofferAPIReturn"]
    checkBaseTransactionAmount_Func = "checkBaseTransactionAmount"
    checkBaseTransactionAmount_Case = Runner(func=checkBaseTransactionAmount_Func, config=checkBaseTransactionAmount_Config, neededData=checkBaseTransactionAmount_NeededData, mainHandler=classInstance.mainHandler)


    checkBaseTransactionPrice_Config = {"baseAsset":config['baseAsset']}
    checkBaseTransactionPrice_NeededData = ["baseTransaction", "makeofferAPIReturn"]
    checkBaseTransactionPrice_Func = "checkBaseTransactionPrice"
    checkBaseTransactionPrice_Case = Runner(func=checkBaseTransactionPrice_Func, config=checkBaseTransactionPrice_Config, neededData=checkBaseTransactionPrice_NeededData, mainHandler=classInstance.mainHandler)


    classInstance.addChild(checkBaseTransactionOrderType_Case) 
    classInstance.addChild(checkBaseTransactionAmount_Case) 
    classInstance.addChild(checkBaseTransactionPrice_Case) 



def checkRelTransactionHandler(classInstance):

    config = classInstance.config

    checkRelTransactionOrderType_Config = {"offerType":config['offerType']}
    checkRelTransactionOrderType_NeededData = ["relTransaction"]
    checkRelTransactionOrderType_Func = "checkRelTransactionOrderType"
    checkRelTransactionOrderType_Case = Runner(func=checkRelTransactionOrderType_Func, config=checkRelTransactionOrderType_Config, neededData=checkRelTransactionOrderType_NeededData, mainHandler=classInstance.mainHandler)


    checkRelTransactionAmount_Config = {"relAsset":config['relAsset']}
    checkRelTransactionAmount_NeededData = ["relTransaction", "makeofferAPIReturn"]
    checkRelTransactionAmount_Func = "checkRelTransactionAmount"
    checkRelTransactionAmount_Case = Runner(func=checkRelTransactionAmount_Func, config=checkRelTransactionAmount_Config, neededData=checkRelTransactionAmount_NeededData, mainHandler=classInstance.mainHandler)


    checkRelTransactionPrice_Config = {"relAsset":config['relAsset']}
    checkRelTransactionPrice_NeededData = ["relTransaction", "makeofferAPIReturn"]
    checkRelTransactionPrice_Func = "checkRelTransactionPrice"
    checkRelTransactionPrice_Case = Runner(func=checkRelTransactionPrice_Func, config=checkRelTransactionPrice_Config, neededData=checkRelTransactionPrice_NeededData, mainHandler=classInstance.mainHandler)


    classInstance.addChild(checkRelTransactionOrderType_Case) 
    classInstance.addChild(checkRelTransactionAmount_Case) 
    classInstance.addChild(checkRelTransactionPrice_Case) 





################    RUNNER FUNCTIONS?    ###############


################    ORDERBOOK API  + GET ORDERS    ###############


def buildOrderbookAPIParams(classInstance):

    orderbookAPIParams = {}
    orderbookAPIParams['requestType'] = "orderbook"
    orderbookAPIParams['baseid'] = classInstance.config['baseAsset']['assetID']
    orderbookAPIParams['relid'] = classInstance.config['relAsset']['assetID']
    orderbookAPIParams['allfields'] = 1
    orderbookAPIParams['maxdepth'] = 30

    classInstance.addProgress("SUCCESS: Constructed Orderbook API params:")
    classInstance.addProgress(orderbookAPIParams, indent=4)

    classInstance.retLevel = 0
    classInstance.retMsg = "SUCCESS: Constructed Orderbook API params"

    classInstance.retData.append({"orderbookAPIParams":orderbookAPIParams})



def doOrderbookAPICall(classInstance, data):

    orderbookAPIParams = data['orderbookAPIParams']
    orderbook = {}

    classInstance.addProgress("Trying orderbook API call...")

    try:
        orderbook = classInstance.mainHandler.api.doAPICall("orderbook", orderbookAPIParams)
    except:
        classInstance.retLevel = -1
        classInstance.retMsg = "FAIL: Orderbook API call failed"
        
    else:
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Orderbook API call successful"

    classInstance.addProgress(classInstance.retMsg)


    classInstance.retData.append({"orderbook":orderbook})



def getOrderbookOrders(classInstance, data):

    orderbook = data['orderbook']
    neededOrdersType = "bids" if classInstance.config['offerType'] == "Sell" else "asks"
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



################    PARSE ORDERS + SELECT ORDER    ###############


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



#bad
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

    selectedOrder = data['selectedOrder']

    makeofferAPIParams = {}
    makeofferAPIParams['requestType'] = "makeoffer3"
    makeofferAPIParams['perc'] = classInstance.mainHandler.perc

    for key in selectedOrder:
        makeofferAPIParams[key] = selectedOrder[key]

    classInstance.addProgress("Constructed makeoffer API params:")
    classInstance.addProgress(makeofferAPIParams, indent=4)

    classInstance.retLevel = 0
    classInstance.retMsg = "SUCCESS: Constructed makeoffer API params"


    classInstance.retData.append({"makeofferAPIParams":makeofferAPIParams})



def doMakeofferAPICall(classInstance, data):

    params = data['makeofferAPIParams']
    makeofferAPIReturn = {}

    classInstance.addProgress("Trying makeoffer API call...")
    try:
        makeofferAPIReturn = classInstance.mainHandler.api.doAPICall("makeoffer", params)
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



################    TRANSACTIONS    ################


def getTransactions(classInstance, data):

    refTX = data['makeofferAPIReturn']['triggerhash']

    nxtRS = classInstance.config['nxtRS']
    numTransactions = classInstance.config['numTransactions']

    getTransactionsAPIParams = {}
    getTransactionsAPIParams['requestType'] = "getUnconfirmedTransactions"
    getTransactionsAPIParams['account'] = nxtRS

    counter = 0
    transactions = []

    classInstance.addProgress("Starting transactions poll...")

    while True:

        classInstance.addProgress("Loop try #" + str(counter))

        transactions = []
        classInstance.addProgress("Trying getUnconfirmedTransactions API call...", indent=4)

        try:
            ret = classInstance.mainHandler.api.doAPICall("getUnconfirmedTransactions", getTransactionsAPIParams, True)
        except:
            if counter == 8:
                classInstance.retLevel = -1
                classInstance.retMsg = "FAIL: getUnconfirmedTransactions API call failed "
                break
            classInstance.addProgress("getUnconfirmedTransactions API call failed...", indent=4)
            ret = {}
        else:
            if "unconfirmedTransactions" in ret:
                unconfirmedTransactions = ret['unconfirmedTransactions']
                classInstance.addProgress("Got " + str(len(unconfirmedTransactions)) + " unconfirmed transactions", indent=4)
                for i in range(len(unconfirmedTransactions)):
                    if "referencedTransactionFullHash" in unconfirmedTransactions[i]:
                        if unconfirmedTransactions[i]['referencedTransactionFullHash'] == refTX:
                            transactions.append(unconfirmedTransactions[i])
                            classInstance.addProgress("Found a transaction:", indent=4)
                            classInstance.addProgress(unconfirmedTransactions[i], indent=8)

                    elif unconfirmedTransactions[i]['fullHash'] == refTX:
                        transactions.append(unconfirmedTransactions[i])
                        classInstance.addProgress("Found a transaction:", indent=4)
                        classInstance.addProgress(unconfirmedTransactions[i], indent=8)

                classInstance.addProgress("Found " + str(len(transactions)) + " transactions. Need " + str(numTransactions), indent=4)
            else:
                classInstance.addProgress("No unconfirmed transactions", indent=4)


        if len(transactions) == numTransactions:
            classInstance.retLevel = 0
            classInstance.retMsg = "SUCCESS: All transactions found"
            classInstance.addProgress(classInstance.retMsg)
            break

        if counter == 8:
            classInstance.retLevel = -1
            classInstance.retMsg = "FAIL: Could not find all transactions"
            classInstance.addProgress("Failed finding all transactions. Num transactions: " +str(len(transactions)) + ". Found transactions: ")
            for i in range(len(transactions)):
                classInstance.addProgress(transactions[i], indent=4)
            break

        counter += 1
        time.sleep(1)

    classInstance.retData.append({"transactions":transactions})



def sortTransactions(classInstance, data):

    baseAsset = classInstance.config['baseAsset']
    transactions = data['transactions']

    sortedTransactions = []
    feeTransaction = {}
    baseTransaction = {}
    relTransaction = {}

    for i in range(len(transactions)):
        transaction = transactions[i]

        if "referencedTransactionFullHash" in transaction:
            attachment = transaction['attachment']

            if attachment['asset'] == baseAsset['assetID']:
                transaction['IDEX_TYPE'] = "base"
                classInstance.addProgress("Found base transaction:")
                classInstance.addProgress(transaction, indent=4)
                baseTransaction = transaction

            else:
                transaction['IDEX_TYPE'] = "rel"
                classInstance.addProgress("Found rel transaction:")
                classInstance.addProgress(transaction, indent=4)
                relTransaction = transaction
        else:
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



################    CHECK TRANSACTIONS    ################


def checkFeeTransaction(classInstance, data):

    transaction = data['feeTransaction']

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



################    CHECK BASE TRANSACTION    ################
### merge base rel


def checkBaseTransactionOrderType(classInstance, data):

    makeofferOfferType = classInstance.config['offerType']

    attachment = data['baseTransaction']['attachment']

    baseOfferType = makeofferOfferType
    transactionOfferType = "Sell" if "version.AskOrderPlacement" in attachment else "Buy"

    compString = "Transaction offerType: " + transactionOfferType + ". Base offerType: " + str(baseOfferType)    

    if transactionOfferType == baseOfferType:
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Base transaction offerType correct. " + compString
        classInstance.addProgress(classInstance.retMsg)
    else:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Base transaction offerType incorrect. " + compString
        classInstance.addProgress(classInstance.retMsg)




def checkBaseTransactionAmount(classInstance, data):

    import decimal

    decimals = classInstance.config['baseAsset']['decimals']

    makeofferRet = data['makeofferAPIReturn']
    attachment = data['baseTransaction']['attachment']


    #decimalPlaces = decimal.Decimal(10) ** (-abs(int(decimals)))

    perc = makeofferRet['perc']
    percMultiplier_Float = float(int(perc)) / float(100)

    transactionAmountQNT = str(attachment['quantityQNT'])
    transactionAmount = float(transactionAmountQNT) / float(pow(10, int(decimals)))

    makeofferAmountQNT_Raw = str(makeofferRet['baseamount'])
    makeofferAmountQNT_Float = float(makeofferAmountQNT_Raw) / float(pow(10, 8 - int(decimals)))
    makeofferAmountQNT_WithPerc_Float = percMultiplier_Float * makeofferAmountQNT_Float

    makeofferAmount = float(int(makeofferAmountQNT_WithPerc_Float)) / float(pow(10, int(decimals)))


    if int(transactionAmountQNT) == int(makeofferAmountQNT_WithPerc_Float):
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Base transaction amount matches makeoffer return amount"
    else:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Base transaction amount does not equal makeoffer base amount: " + str(int(transactionAmountQNT)) + " vs. " + str(int(makeofferAmountQNT_WithPerc_Float))

    classInstance.addProgress("Base transaction amount QNT: " + str(transactionAmountQNT) + ".  Makeoffer base amount QNT: " + str(int(makeofferAmountQNT_WithPerc_Float)))
    classInstance.addProgress(" ")
    classInstance.addProgress("Makeoffer base amount QNT(float): " + str(makeofferAmountQNT_WithPerc_Float))
    classInstance.addProgress(" ")
    classInstance.addProgress("Makeoffer base amount: " + str(makeofferAmount))
    classInstance.addProgress("Base Transaction amount: " + str(transactionAmount))
    classInstance.addProgress(" ")
    classInstance.addProgress(classInstance.retMsg)




def checkBaseTransactionPrice(classInstance, data):

    assetID = classInstance.config['baseAsset']['assetID']
    decimals = classInstance.config['baseAsset']['decimals']
    makeofferRet = data['makeofferAPIReturn']

    attachment = data['baseTransaction']['attachment']

    transactionPriceNQT = attachment['priceNQT']

    keys = ["buyer", "buyer2", "seller", "seller2"]
    makeofferPriceNQT = None

    for key in keys:
        if key in makeofferRet and makeofferRet[key]['assetid'] == assetID:
            makeofferPriceNQT = str(makeofferRet[key]['priceNQT'])
            break

    if not makeofferPriceNQT:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Unexpected error - check makeofferAPIReturn"
        return

    if int(transactionPriceNQT) == int(makeofferPriceNQT):
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Base transaction price equals makeoffer base price"
    else:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Base transaction price does not equal makeoffer base price: " + str(transactionPriceNQT) + " vs. " + str(makeofferPriceNQT)

    #makeofferPriceNQT = float(makeofferPrice) * float(pow(10, 8 - int(decimals)))

    classInstance.addProgress("Transaction price NQT: " + str(transactionPriceNQT) + ". Makeoffer base price: " + str(makeofferPriceNQT))



################    CHECK REL TRANSACTION    ################
### merge base rel

def checkRelTransactionOrderType(classInstance, data):

    makeofferOfferType = classInstance.config['offerType']

    attachment = data['relTransaction']['attachment']

    relOfferType = "Sell" if makeofferOfferType == "Buy" else "Buy"
    transactionOfferType = "Sell" if "version.AskOrderPlacement" in attachment else "Buy"

    compString = "Transaction offerType: " + transactionOfferType + ". Rel offerType: " + str(relOfferType)    


    if transactionOfferType == relOfferType:
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Rel transaction offerType correct. " + compString
        classInstance.addProgress(classInstance.retMsg)
    else:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Rel transaction offerType incorrect. " + compString
        classInstance.addProgress(classInstance.retMsg)




def checkRelTransactionAmount(classInstance, data):

    import decimal

    decimals = classInstance.config['relAsset']['decimals']

    makeofferRet = data['makeofferAPIReturn']
    attachment = data['relTransaction']['attachment']


    #decimalPlaces = decimal.Decimal(10) ** (-abs(int(decimals)))

    perc = makeofferRet['perc']
    percMultiplier_Float = float(int(perc)) / float(100)

    transactionAmountQNT = str(attachment['quantityQNT'])
    transactionAmount = float(transactionAmountQNT) / float(pow(10, int(decimals)))

    makeofferAmountQNT_Raw = str(makeofferRet['relamount'])
    makeofferAmountQNT_Float = float(makeofferAmountQNT_Raw) / float(pow(10, 8 - int(decimals)))
    makeofferAmountQNT_WithPerc_Float = percMultiplier_Float * makeofferAmountQNT_Float

    makeofferAmount = float(int(makeofferAmountQNT_WithPerc_Float)) / float(pow(10, int(decimals)))


    if int(transactionAmountQNT) == int(makeofferAmountQNT_WithPerc_Float):
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Rel transaction amount equals makeoffer return amount"
    else:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Rel transaction amount does not equal makeoffer rel amount: " + str(int(transactionAmountQNT)) + " vs. " + str(int(makeofferAmountQNT_WithPerc_Float))

    classInstance.addProgress("Rel transaction amount QNT: " + str(transactionAmountQNT) + ".  Makeoffer rel amount QNT: " + str(int(makeofferAmountQNT_WithPerc_Float)))
    classInstance.addProgress(" ")
    classInstance.addProgress("Makeoffer rel amount QNT(float): " + str(makeofferAmountQNT_WithPerc_Float))
    classInstance.addProgress(" ")
    classInstance.addProgress("Makeoffer rel amount: " + str(makeofferAmount))
    classInstance.addProgress("Rel transaction amount: " + str(transactionAmount))
    classInstance.addProgress(" ")
    classInstance.addProgress(classInstance.retMsg)



def checkRelTransactionPrice(classInstance, data):

    assetID = classInstance.config['relAsset']['assetID']
    decimals = classInstance.config['relAsset']['decimals']
    makeofferRet = data['makeofferAPIReturn']

    attachment = data['relTransaction']['attachment']

    transactionPriceNQT = attachment['priceNQT']

    keys = ["buyer", "buyer2", "seller", "seller2"]
    makeofferPriceNQT = None

    for key in keys:
        if key in makeofferRet and makeofferRet[key]['assetid'] == assetID:
            makeofferPriceNQT = str(makeofferRet[key]['priceNQT'])

    if not makeofferPriceNQT:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Unexpected error - check makeofferAPIReturn"
        return

    if int(transactionPriceNQT) == int(makeofferPriceNQT):
        classInstance.retLevel = 0
        classInstance.retMsg = "SUCCESS: Rel transaction price equals makeoffer rel price"
    else:
        classInstance.retLevel = 1
        classInstance.retMsg = "FAIL: Rel transaction price does not equal makeoffer rel price: " + str(transactionPriceNQT) + " vs. " + str(makeofferPriceNQT)

    #makeofferPriceNQT = float(makeofferPrice) * float(pow(10, 8 - int(decimals)))

    classInstance.addProgress("Transaction price NQT: " + str(transactionPriceNQT) + ". Makeoffer ret price: " + str(makeofferPriceNQT))






