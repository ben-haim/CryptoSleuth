#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Case(object):

    def __init__(self, config={}):

        self.stages = []


class Stage(object):

    def __init__(self, config={}):

        self.progress = []
        self.percentComplete = 0
        self.status = None

        self.type = "stage"
        self.name = ""

        self.index = 0
        self.parent = None
        self.siblings = []
        self.children = []


class SubStage(object):

    pass
    #window = allWindows['supernet']
    #pad = window.children["pads"]["progressPad"]
    #progress.append("CASE: " + caseType + ", OFFER TYPE: " + typeOffer + ", EXCHANGE: " + exchangeType + "\n")
    #t = Thread(target=caseRefresher)
    #t.daemon = True
    #t.start()




class MakeOffer(object):

    def __init__(self, config={}):

        self.caseType = "makeoffer3"
        self.offerType = "Sell"
        self.exchangeType = "any"
        self.isExternalExchange = False

        self.baseDecimals = 0
        self.relDecimals = 0

        self.baseAsset = {}
        self.relAsset = {}

        self.postParams = snPostParams['makeoffer3']


    def addFlow(self, method):
        method = getattr(handlers, method)
        self.flow.append(method)



    def initFlow(self):
        for i in range(len(commands)):
            method = getattr(server, command[i])
            data = method()



    def flow(self):
        progress.append("Checking balances...\n")
        self.checkBalances()

        progress.append("Loading orderbook...\n")
        orders = self.loadOrderbook()

        progress.append("Selecting order...\n")
        selectedOrder = self.selectOrder(orders)
    
        progress.append("Calling makeoffer...\n")
        self.doMakeoffer()

        progress.append("Dumping to file...\n")
        self.dumpToFile(data=self.progress)


    def checkBalances(self):

        progress.append("Getting BaseBal...\n")
        baseBal = self.user.getBal(self.baseAsset.assetID, True)
        progress.append(baseBal.makeBalString())

        progress.append("Getting RelBal...\n")
        relBal = self.user.getBal(self.relAsset.assetID, False)
        progress.append(relBal.makeBalString())



    def loadOrderbook(self):

        neededOrdersType = "bids" if self.offerType == "Sell" else "asks"
        orderbook = {}
        orders = []

        try:
            orderbook = getOrderbook(self.baseAsset.AssetID, self.relAsset.assetID)
        except:
            progress.append("Could not load orderbook\n")
        else:
            if neededOrdersType in orderbook:
                orders = orderbook[neededOrdersType]

            if not len(orders):
                progress.append("No orders in orderbook\n")
            else:
                for i in range(len(orders)):
                    try:
                        progress.append(json.dumps(orders[i]))
                    except:
                        progress.append(orders[i])

        return orders



    def selectOrder(self, orders):
        selectedOrder = {}

        if len(orders):
            selectedOrder = orders[0]
            progress.append("Selected Order:\n")
            try:
                progress.append(json.dumps(selectedOrder))
            except:
                progress.append(selectedOrder)
        else:
            progress.append("No orders to choose from\n")

        return selectedOrder


    def doMakeoffer(self, selectedOrder):

        if selectedOrder:
            obj = {}
            obj['requestType'] = "makeoffer3"
            for key in selectedOrder:
                obj[key] = selectedOrder[key]
            obj['perc'] = 1
            try:
                ret = makeoffer(obj)
            except:
                ret = "Failed"

            try:
                ret = json.dumps(ret)
            except:
                pass

            progress.append(ret)
        else:
            progress.append("No order selected\n")



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



            
        
