#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json, sys
import bitcoinrpc, bitcoinrpc.authproxy
import decimal 
import random
import time
import operator
import ConfigParser
from decimal import *

sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=32, cols=100))

getcontext().prec = 10
getcontext().rounding = ROUND_FLOOR

Config = ConfigParser.ConfigParser()
Config.read('sleuther.conf')
rpcuser = Config.get('BitcoinDark', 'rpcuser')
rpcpass = Config.get('BitcoinDark', 'rpcpass')
rpcport = Config.get('BitcoinDark', 'rpcport')

assetInfo = json.load(open('assetInfo.txt'))

class Orders(object):
    def __init__(self, config = {}):
        self.pair = ""
        self.obookid = ""
        self.baseid = ""
        self.relid = ""
        self.asks = []
        self.flipAsks = []
        self.bids = []
        self.flipBids = []

    #@classmethod
    def FromOrderbook(self, orderbook):
        try:
            self.pair = orderbook['pair']
            self.obookid = orderbook['obookid']
            self.baseid = orderbook['baseid']
            self.relid = orderbook['relid']
            self.asks = orderbook['asks']
            self.bids = orderbook['bids']
        except:
            raise Exception(orderbook)
            #self.flipAsks = flipOrder(self.bids)
            #self.flipBids = flipOrder(self.asks) 


def placeOrder(authService, baseid, relid, price, volume, orderType):

    return json.loads(authService.SuperNET('{"requestType":"'+orderType+'","baseid":"'+baseid+'","relid":"'+relid+'","price":"'+price+'","volume":"'+volume+'"}'))


def getOrderbook(authService, baseid, relid):
    
    return json.loads(authService.SuperNET('{"requestType":"orderbook","baseid":"'+baseid+'","relid":"'+relid+'","allfields":1}'))


def getOpenOrders(authService):
    
    return json.loads(authService.SuperNET('{"requestType":"openorders"}'))


def getAllOrderbooks(authService):
    
    return json.loads(authService.SuperNET('{"requestType":"allorderbooks"}'))


def printToBottom(linesToClear):

    for i in range(0,linesToClear):
        print

def getBothOrderbooks(authService, baseid, relid):

    bothOrderbooks = []
    baseOrderbook = Orders()
    relOrderbook = Orders()
    try:
        baseOrderbook.FromOrderbook(getOrderbook(authService, baseid, relid))
        relOrderbook.FromOrderbook(getOrderbook(authService, relid, baseid))
    except Exception as e:
        raise
    else:
        bothOrderbooks.append(baseOrderbook)
        bothOrderbooks.append(relOrderbook)

    return bothOrderbooks


def verifyAsset(value):

    retval = {}
    retval['asset'] = value
    retval['name'] = ''
    try:
        int(value)
        for asset in assetInfo:
            if asset['asset'] == value:
                retval['asset'] = value
                retval['name'] = asset['name']
    except:
        for asset in assetInfo:
            if asset['name'] == value:
                retval['asset'] = asset['asset']
                retval['name'] = asset['name']

    if len(value) and not len(retval['name']):
        retval['name'] = "Warning: asset not found"

    return retval


def userInterface():

    os.system("clear")
    print "1) View an orderbook"
    print "2) Place a bid"
    print "3) Place an ask"
    print "4) **Make an offer** not available yet..."
    print "5) View all open orders"
    print "6) View all orderbooks"
    print "0) Exit"
    printToBottom(24)


def openOrdersInterface():

    os.system("clear")
    print "OPENORDERS MENU:"
    print "    1) View all openorders"
    print "    2) Search by asset ID"
    print "    3) Search by type (bid/ask)"
    print "    0) Go back"
    printToBottom(26)


def getBaseAndRel():

    baseid = {}; baseid['asset'] = ''; baseid['name'] = ''
    relid = {}; relid['asset'] = ''; relid['name'] = '' 

    while True:
        if baseid['asset'] == '0':
            break
        if relid['asset'] == '0':
            baseid['asset'] = ''
            relid['asset'] = ''
            continue
        baseid = verifyAsset(baseid['asset'])
        relid = verifyAsset(relid['asset'])
        print "baseid: %s (%s)" %(baseid['asset'], baseid['name'])
        print "reld:   %s (%s)" %(relid['asset'], relid['name'])
        printToBottom(29)
        if not len(baseid['asset']):
            baseid['asset'] = raw_input('Enter a baseid (0 to go back):')
            #baseid = "11060861818140490423"
            continue
        if not len(relid['asset']):
            relid['asset'] = raw_input('Enter a relid (0 to go back):')
            #relid = "12071612744977229797"
            continue
        break

    return (baseid['asset'], relid['asset'])

#merge these
def getUserOrder(typeOrder):

    baseid = ''
    relid = ''
    price = ''
    volume = ''

    while True:
        if baseid == '0':
            break
        if relid == '0':
            baseid = ''
            relid = ''
            continue
        if price == '0':
            relid = ''
            price = ''
            continue
        if volume == '0':
            price = ''
            volume = ''
            continue
        print "Placing a(n) %s order\n" %typeOrder
        print "baseid: %s" %baseid
        print "relid:  %s" %relid
        print "price:  %s" %price
        print "volume: %s" %volume
        printToBottom(25)
        if not len(baseid):
            baseid = raw_input('Enter a baseid (0 to go back): ')
            continue
        if not len(relid):
            relid = raw_input('Enter a relid (0 to go back): ')
            continue
        if not len(price):
            price = raw_input('Enter a price (0 to go back): ')
            continue
        if not len(volume):
            volume = raw_input('Enter a volume (0 to go back): ')
            continue
        break

    return (baseid, relid, price, volume)
        

def printOrderbook(orderbook):

    orderbook[0] = priceToSortedDecimal(orderbook[0])
    orderbook[1] = priceToSortedDecimal(orderbook[1])
    flipBook = 0
    numLines = 10
    askPos = 10
    bidPos = 0
    retstat = 0

    #for i in range(0,12):
        #orderbook[0].asks.append(orderbook[0].asks[0])

    while True:
        asks = orderbook[flipBook].asks
        bids = orderbook[flipBook].bids
        numAsks = len(asks)
        numBids = len(bids)

        print "pair:    {0:20} baseid:  {1:24} {2}".format(orderbook[flipBook].pair, orderbook[flipBook].baseid, "W = ↑ ask, E = ↑ bid, 0: go back")
        print "obookid: {0:20} relid:   {1:24} {2}".format(orderbook[flipBook].obookid, orderbook[flipBook].relid, "S = ↓ ask, D = ↓ bid, 1: flip")
        print "{0}".format("2: refresh".rjust(96))
        print
        printBidAskLine(asks, numLines, askPos, -1)
        print " asks"
        print
        print " bids"
        printBidAskLine(bids, numLines, bidPos, 1)
        printToBottom(2)

        userSelection = raw_input("Enter an option: ")
        if userSelection == "W" or userSelection == "w":
            if askPos < numAsks:
                askPos += 1
        elif userSelection == "S" or userSelection == "s":
            if askPos-numLines > 0:
                askPos -= 1
        elif userSelection == "E" or userSelection == "e":
            if bidPos > 0:
                bidPos -= 1
        elif userSelection == "D" or userSelection == "d":
            if bidPos+numLines < numBids:
                bidPos += 1
        elif userSelection == '1':
            flipBook = 1 - flipBook
        elif userSelection == '2':
            retstat = '2'
            break
        elif userSelection == '0':
            break

    return retstat


def priceToSortedDecimal(orderbook):

    #print(orderbook)
    for askObj, bidObj in zip(orderbook.asks,orderbook.bids):
        askObj['price'] = decimal.Decimal(askObj['price'])
        bidObj['price'] = decimal.Decimal(bidObj['price'])
    orderbook.asks = sorted(orderbook.asks, key=operator.itemgetter('price'))
    orderbook.bids = sorted(orderbook.bids, key=operator.itemgetter('price'))
    #print(orderbook)

    return orderbook

        
def printBidAskLine(order, numLines, startPos, typeOrder):

    typeTrader = "Buyer" if typeOrder == 1 else "Seller"
    currentPos = startPos
    i = 0

    while i < numLines+1:
        sys.stdout.write('    {0:5}'.format("#"+str(currentPos)+")"))
        try:
            obj = order[currentPos]
        except:
            print
        else:
            print('{0:23} {1:23} {2:20}'.format("price: "+str(obj['price']),"volume: "+obj['volume'],typeTrader+": "+obj['other']))

        currentPos += typeOrder
        i += 1


def paginateData(dataList, typeData):

    leftOrder = 0
    rightOrder = 1
    counter = 0
    numDataObj = len(dataList)
    x = 0;


    if numDataObj > 0:
        while True:
            counter = 0
            os.system('clear')
            obj = dataList[x]
            print "%s #%s:\n" %(typeData, x)
            counter +=2
            for prop in obj:
                print "%s: %s" %(prop, obj[prop])
                counter += 1

            printToBottom(31 - counter)

            navigate = raw_input('Use A and D to navigate or 0 to go back: ')
            if navigate == "A" or navigate == "a":
                if x == 0:
                    x = numDataObj - 1
                else:
                    x -= 1
            elif navigate == "D" or navigate == "d":
                if x == numDataObj - 1:
                    x = 0
                else:
                    x += 1
            elif navigate == "0":
                break

    else:
        print "No %s found" %(typeData)
        printToBottom(30)
        raw_input('Press any key to go back...')


def searchOpenOrders(key, value, openOrders):
    
    searchedOpenOrders = []

    for obj in openOrders:
        if obj[key] == value:
            searchedOpenOrders.append(obj)

    return searchedOpenOrders
    

if __name__ == '__main__':

    rpc = 'http://'+rpcuser+':'+rpcpass+'@127.0.0.1:'+rpcport
    bit = bitcoinrpc.authproxy.AuthServiceProxy(rpc)

    #os.system("clear")

    while True:
        userInterface()
        userSelection = raw_input('Enter an option: ')

        if userSelection == '1':

            retstat = '2'
            baseid, relid = getBaseAndRel()
            if baseid == '0':
                continue

            while retstat == '2':

                try:
                    bothOrderbooks = getBothOrderbooks(bit, baseid, relid)
                except Exception as e:
                    printToBottom(31)
                    try:
                        raw_input("Error: (%s). Enter any key to continue..."%(e.args))
                    except:
                        raw_input("Error: (%s). Enter any key to continue..."%(e))
                    break
                else:
                    #if 'error' in bothOrderbooks[0] or 'error' in bothOrderbooks[1]:
                    if 'error' in bothOrderbooks:
                        print(retdata['error'])
                        retstat = 'error'
                        raw_input('Enter any key to go back to main menu: ')
                        break
                    os.system("clear")
                    retstat = printOrderbook(bothOrderbooks)
            


        elif userSelection == '2' or userSelection == '3':

            typeOrder = 'bid' if userSelection == '2' else 'ask'
            baseid, relid, price, volume = getUserOrder(typeOrder)
            if baseid == '0':
                continue
            print "Placing a(n) %s order\n" %typeOrder
            print "baseid: %s" %baseid
            print "relid:  %s" %relid
            print "price:  %s" %price
            print "volume: %s" %volume
            printToBottom(25)
            userSelection = raw_input('Enter 1 to confirm or 0 to cancel: ')
            if userSelection == '1':
                retdata = placeOrder(bit, baseid, relid, price, volume, 'place'+typeOrder)
                if 'result' in retdata and retdata['result'] is not None:
                    print 'result: %s' %(retdata['result'])
                    print 'txid: %s' %(retdata['txid'])
                    printToBottom(29)
                else:
                    print "Error: could not place %s" %typeOrder
                    printToBottom(30)

                raw_input('Press any key to continue')


        elif userSelection == '4':

            print "makeoffer: Not available yet"
            printToBottom(30)
            raw_input('Press any key to continue')


        elif userSelection == '5':

            retOpenOrders = getOpenOrders(bit)

            while True:
                openOrdersInterface()
                userSelection = raw_input('Enter an option: ')
                
                if userSelection == '1':
                    paginateData(retOpenOrders['openorders'], 'OPENORDERS')
                
                elif userSelection == '2' or userSelection == '3':

                    if userSelection == '2':
                        key = "baseid"
                    elif userSelection == '3':
                        key = "requestType"

                    os.system('clear')
                    print "Filtering by: %s" %(key)
                    printToBottom(30)
                    value = raw_input('Enter the value to search for: ')
                    searchedOpenOrders = searchOpenOrders(key, value, retOpenOrders['openorders'])
                    
                    paginateData(searchedOpenOrders, "OPENORDERS")

                elif userSelection == '0':
                    break


        elif userSelection == '6':

            allOrderbooks = getAllOrderbooks(bit)
            paginateData(allOrderbooks['orderbooks'], "ALLORDERBOOK")

        
        elif userSelection == '0':
            sys.exit(1)
            break



    #########################################################################################################

    #use later
    #menu = {}
    #menu['1'] = "orderbooks"
    #menu['2'] = "bid"
    #menu['3'] = "ask"
    #menu['4'] = "makeoffer"
    #menu['5'] = "openorders"
    #menu['6'] = "allorderbooks"
    #menu['0'] = "exit"

    #try:
    #    if menu[userSelection] is not None:
    #        a = True
    #except:
    #    continue

    #class UserInput(object):
    #    def orderbooks(self):
    #        print 'tests'

    #testinput = UserInput()
    #method = getattr(testinput, menu[userSelection])
    #method()

    #regRetOrders.flipAsks = flipOrder(regRetOrders.bids)
    #regRetOrders.flipBids = flipOrder(regRetOrders.asks) 

    #print "Check asks:"
    #checkOrders(regRetOrders.flipAsks, flipRetOrders.asks)
    #print "Check bids:"
    #checkOrders(regRetOrders.flipBids, flipRetOrders.bids)
    





