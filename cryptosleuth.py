#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# CryptoSleuth 
# TUI for sleuthing around the cryptocurrency world
# Powered by SuperNET
# Created by CryptoSleuth

import io
import sys
import os
import signal
import threading
import time
import decimal
import operator
import random

import curses
from curses.textpad import Textbox, rectangle
import curses.panel

import json
import bitcoinrpc, bitcoinrpc.authproxy
import ConfigParser


#getcontext().prec = 10
#getcontext().rounding = ROUND_FLOOR


##########  CURSES  ###################

mainWindow = curses.initscr()
curses.cbreak()
curses.noecho()
curses.curs_set(0)
mainWindow.keypad(1) 
curses.start_color() 
curses.use_default_colors()
curses.init_pair(1,curses.COLOR_BLACK, curses.COLOR_WHITE) 
h = curses.color_pair(1)
n = curses.A_NORMAL


########## CONSTANTS  ###########

SQUIGGLY = 96
DOWN_ARROW = 258
UP_ARROW = 259
LEFT_ARROW = 260
RIGHT_ARROW = 261


######### EXIT HANDLER ###########

def exit_handler(message=None):
    curses.echo()
    curses.curs_set(1)
    curses.nocbreak()
    curses.endwin()
    if message:
        print(message)
    sys.exit(0)


##########  CONFIG  ##############

Config = ConfigParser.ConfigParser()
try:
    Config.read('cryptosleuth.conf')
    rpcuser = Config.get('BitcoinDark', 'rpcuser')
    rpcpass = Config.get('BitcoinDark', 'rpcpass')
    rpcport = Config.get('BitcoinDark', 'rpcport')
    assetFile = Config.get('General', 'assetFile')
except:
    exit_handler("Invalid sleuther.conf")

try:
    assetInfo = json.load(open(assetFile))
except:
    exit_handler("Could not find assetInfo file")


############  GLOBALS  ##############

rpc = 'http://'+rpcuser+':'+rpcpass+'@127.0.0.1:'+rpcport
bit = bitcoinrpc.authproxy.AuthServiceProxy(rpc)

windowStack = []

allWindows = {
    "mainMenu":None,
    "subMenu":None,
    "allOrderbooks":None,
    "activeOrderbooks":None,
    "orderbook":None,
    "openOrders":None
}


#################   RPC    ######################

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
        if not 'error' in orderbook:
            self.pair = orderbook['pair']
            self.obookid = orderbook['obookid']
            self.baseid = orderbook['baseid']
            self.relid = orderbook['relid']
            self.asks = orderbook['asks']
            self.bids = orderbook['bids']
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


##############  CTRL+C HANDLER    #####################

def signal_handler(signal, frame):
    exit_handler()


###############    FOUR ARROW UI    ########################

def fourArrowUI(window):

    global windowStack

    userInput = None 

    while userInput !=ord('\n'):

        window.menu.updateMenu()
        userInput = mainWindow.getch()

        if userInput == DOWN_ARROW:
            if window.userPos[0] < window.menu.maxRows-1 and (window.userPos[0] < window.menu.lastPos[0] or window.userPos[1] < window.menu.lastPos[1]):           
                window.userPos[0] += 1
            else:
                window.userPos[0] = 0

        elif userInput == UP_ARROW:
            if window.userPos[0] > 0:
                window.userPos[0] -= 1
            else:
                if window.userPos[1] == window.menu.lastPos[1]:
                    window.userPos[0] = window.menu.lastPos[0]
                else:
                    window.userPos[0] = window.menu.maxRows-1

        elif userInput == LEFT_ARROW:
            #and (userPos[0] < lastPos[0] or userPos[1] < lastPos[1])
            if window.userPos[1] > 0:
                window.userPos[1] -= 1
            else:
                pass

        elif userInput == RIGHT_ARROW:
            if window.userPos[1] < window.menu.lastPos[1] and (window.userPos[0] <= window.menu.lastPos[0] or window.userPos[1] < window.menu.lastPos[1]-1):
                window.userPos[1] += 1
            else:
                pass
    
        elif userInput == ord('\t'):
            if len(windowStack) > 1:
                window.popStack()
                processWindow(windowStack[len(windowStack)-1])
            else:
                processWindow(window)

        elif userInput == SQUIGGLY and window.parent and len(window.parent.childrenList) > 0:
            return -2

    return


##########   WINDOW   ###################


class cWindow(object):

    def __init__(self, config={}):

        self.cursesObj = None
        self.userPos = [0,0]
        self.prevUserPos = [0,0]
        self.titlePos = [[],[]]
        self.titleData = []
        self.contentPos = [[],[]]
        self.contentData = []
        self.windowPos = None

        self.menu = None

        self.parent = None
        self.children = {
            "windows":{},
            "pads":{},
            "popups":{}  
        }
        self.childrenList = []
        
        self.name = ""
        self.typeWin = "menu"


    @classmethod
    def initWindow(self, windowFormat, typeWin=None, parent=None, title=None, content=None):

        self = cWindow()

        height, width = windowFormat[0]
        startPosY = windowFormat[1][0]
        startPosX = windowFormat[1][1]
        endPosY = startPosY+height - 1
        endPosX = startPosX+width - 1

        self.cursesObj = curses.newwin(height, width, startPosY, startPosX)   # height, width, startPosY, 
        self.windowPos = [[startPosY, startPosX], [endPosY, endPosX]]
        self.typeWin = typeWin
        self.parent = parent
        try:
            self.initTitle(title[0],title[1])
        except:
            pass
        #self.initContent(content[0], content[1])

        return self


    def initTitle(self, titlePos, title, underlined=None):
    
        self.titlePos = titlePos
        startRow, stopRow = self.centerText(titlePos, title)
        self.cursesObj.addstr(startRow,stopRow,"{0}".format(title))
        if underlined:
            line = '-'*(titlePos[1][1]-titlePos[0][1])
            self.cursesObj.addstr(titlePos[1][0],1,"{0}".format(line))


    def initContent(self, contentPos, content):

        pass

    
    def centerText(self, pos, text):
    
        rowLength = pos[1][0] - pos[0][0]
        colHeight = pos[1][1] - pos[0][1]
        textLength = len(text)

        #startRow = rowLength/2 - textLength/2
        #stopRow = startRow + textLength

        startCol = colHeight/2 - textLength/2
        stopCol = startCol + textLength

        return (pos[0][0], startCol)


    def addChild(self, childType, childName, childObj):

        self.children[childType][childName] = childObj
        self.childrenList.append(childObj)


    def popStack(self):
        if self.parent:
            for window in self.parent.childrenList:
                window.cursesObj.clear()
            self.parent.cursesObj.clear()
            self.parent.cursesObj.refresh()
        self.cursesObj.clear()
        self.cursesObj.refresh()
        self.userPos = [0,0]
        windowStack.pop()
        mainWindow.refresh()


##########  POPUP   ##################

class cPopup(cWindow):
    def __init__(self):
        cWindow.__init__(self)

        popupHeight = 16; popupWidth = 50

        container = mainWindow
        containerHeight, containerWidth = container.getmaxyx()
        startHeight = containerHeight/2 - popupHeight/2
        stopHeight = startHeight + popupHeight
        startWidth = containerWidth/2 - popupWidth/2
        stopWidth = startWidth + popupWidth

        self.titlePos = [[1,1],[12,49]]
        self.cursesObj = curses.newwin(popupHeight,popupWidth,startHeight,startWidth)
        self.panel = curses.panel.new_panel(self.cursesObj)
        self.cursesObj.border(0)


    def showPanel(self):

        global windowStack
        
        self.panel.show()
        #self.panel.top()
        windowStack.append(self)


    def popStack(self):

        global windowStack

        self.cursesObj.clear()
        self.cursesObj.refresh()
        self.userPos = [0,0]
        self.panel.hide()
        windowStack.pop()
        mainWindow.refresh()


    def popupViewOrderbook(self, baseAsset, relAsset):

        self.cursesObj.addstr(1,18,"View orderbook")
        self.initTitle([[2,0],[2,50]], "{0}/{1}".format(baseAsset['name'],relAsset['name']))
        self.cursesObj.addstr(5,7,"{0:15} {1}".format("Base Name:",baseAsset['name']))
        self.cursesObj.addstr(6,7,"{0:15} {1}".format("Base ID:",baseAsset['asset']))
        self.cursesObj.addstr(8,7,"{0:15} {1}".format("Rel Name:",relAsset['name']))
        self.cursesObj.addstr(9,7,"{0:15} {1}".format("Rel ID:",relAsset['asset']))

        #centerPos = self.centerText([[13,10],[13,40]], 
        self.menu = menu(self, [[1,30],[13,16]], [1,5], [1,11], ["Confirm", "Cancel"])
        self.menu.initDataFormat()
        self.cursesObj.refresh()


    def popupErrorMessage(self, errorMessage):

        self.cursesObj.addstr(1,22,"Error!")
        self.cursesObj.addstr(5,3,"{0}".format(errorMessage))
        self.menu = menu(self, [[1,30],[13,21]], [1,5], [1,10], ["   OK   "])
        self.menu.initDataFormat()
        self.cursesObj.refresh()


    ######## MERGE THESE??  ########
    def popupAddAsset(self):

        self.cursesObj.addstr(1,18,"Add an asset")
        self.menu = menu(self, [[3,30],[5,5]], [3,1], [1,0], ["Asset ID:", "Asset Name:", "Confirm"])
        self.assetIDInputWin = self.cursesObj.derwin(1,25,5,20)
        self.assetNameInputWin = self.cursesObj.derwin(1,15,6,20)
        self.menu.specials = {}
        self.menu.specials['Confirm'] = [13, 21]
        self.menu.initDataFormat()
        self.cursesObj.refresh()

    def popupPlaceOrder(self, typeOrder):

        titleStr = "Place a bid" if typeOrder == "placebid" else "Place an ask"
        self.cursesObj.addstr(1,18,"{0}".format(titleStr))
        self.menu = menu(self, [[3,30],[5,5]], [3,1], [1,0], ["Price", "Amount", "Confirm"])
        self.priceInputWin = self.cursesObj.derwin(1,25,5,20)
        self.amountInputWin = self.cursesObj.derwin(1,15,6,20)
        self.menu.specials = {}
        self.menu.specials['Confirm'] = [13, 21]
        self.menu.initDataFormat()
        self.cursesObj.refresh()
    #################################

########   MENU   #########

class menu(object):
    def __init__(self, parent=None, menuPos=None, maxRowsAndCols=[1,10], rowAndColSize=[1,20], data=None, href=None, dataKeys=None):

        self.parent = parent
        self.menuPos = menuPos
        if menuPos:
            height, width = menuPos[0]
            startPosY = menuPos[1][0]
            startPosX = menuPos[1][1]
            endPosY = startPosY+height - 1
            endPosX = startPosX+width - 1
            self.menuPos = [[startPosY,startPosX], [endPosY, endPosX]]

        self.maxRows = maxRowsAndCols[0]
        self.maxCols = maxRowsAndCols[1]
        self.rowSize = rowAndColSize[0]
        self.colSize = rowAndColSize[1]

        self.data = data
        self.dataKeys = dataKeys
        self.dataHref = href
        self.displayedSection = None


    def initDataFormat(self):

        numData = len(self.data)
        self.maxCols = numData/self.maxRows
        lastRowPos = numData % self.maxRows

        if lastRowPos != 0:
            self.maxCols += 1
        else:
            if numData > 0:
                lastRowPos = self.maxRows

        self.lastPos = [lastRowPos-1, self.maxCols-1]


    def updateMenu(self):

        formatPos = [0,0]

        for counter in range(0,len(self.data)):

            tempString = ""
            textStyle = h if formatPos == self.parent.userPos else n

            ## Get rid of this after data is auto formatted ##
            if self.dataKeys is not None:
                for key in self.dataKeys:
                    tempString += "{0:20}".format(self.data[counter][key])
            else:
                tempString += "{0}".format(self.data[counter])
            ##                                              ##

            if hasattr(self, 'specials') and self.data[counter] in self.specials:
                self.parent.cursesObj.addstr(self.specials[self.data[counter]][0],self.specials[self.data[counter]][1], tempString, textStyle)
            else:
                self.parent.cursesObj.addstr(self.menuPos[0][0]+formatPos[0],formatPos[1]+self.menuPos[0][1]+self.colSize*counter, tempString, textStyle)

            formatPos[0] += 1
            if formatPos[0] == self.maxRows:
                formatPos[0] = 0; formatPos[1] += 1

        self.parent.cursesObj.refresh()


############ PAD MENU  #################

class padMenu(menu):
    def __init__(self, parent=None, menuPos=None, maxRowsAndCols=[1,10], rowAndColSize=[1,20], data=None, href=None, dataKeys=None):
        menu.__init__(self, parent, menuPos, maxRowsAndCols, rowAndColSize, data, href, dataKeys)

        height, width = menuPos[0]
        pStartY, pStartX, = self.parent.windowPos[0]
        startPosY = menuPos[1][0]+pStartY
        startPosX = menuPos[1][1]+pStartX
        endPosY = startPosY+height - 1
        endPosX = startPosX+width - 1
        self.menuPos = [[startPosY,startPosX], [endPosY, endPosX]]

        self.numDisplayedRows = ((self.menuPos[1][0] - self.menuPos[0][0]) / self.rowSize)
        self.numDisplayedCols = ((self.menuPos[1][1] - self.menuPos[0][1]) / self.colSize)
        self.displayedSection = [[0,0], [self.numDisplayedRows, self.numDisplayedCols]]


    def updateMenu(self):

        formatPos = [0,0]

        for counter in range(0,len(self.data)):

            tempString = ""
            textStyle = h if formatPos == self.parent.userPos else n

            ##  Get rid of this ##
            if self.dataKeys is not None:
                for key in self.dataKeys:
                    try: # BAD
                        tempString += "{0:20}".format(str(self.data[counter][key]))
                    except:
                        tempString = "--------ERROR: DONT CLICK ME--------"
                        break
            else:
                tempString += "{0:20}".format(self.data[counter])
            ##                  ##

            try: # fix encoding
                self.parent.cursesObj.addstr(formatPos[0],formatPos[1]*self.colSize, tempString, textStyle)
            except:
                pass
            formatPos[0] += 1
            if formatPos[0] == self.maxRows:
                formatPos[0] = 0; formatPos[1] += 1

        if self.parent.userPos[0] > self.displayedSection[1][0]: # down
            self.displayedSection[1][0] = self.parent.userPos[0]
            self.displayedSection[0][0] = self.displayedSection[1][0] - self.numDisplayedRows
        elif self.parent.userPos[0] < self.displayedSection[0][0]: # up
            self.displayedSection[0][0] = self.parent.userPos[0]
            self.displayedSection[1][0] = self.displayedSection[0][0] + self.numDisplayedRows
        elif self.parent.userPos[1] > self.displayedSection[1][1]: # right
            self.displayedSection[1][1] = self.parent.userPos[1]
            self.displayedSection[0][1] = self.displayedSection[1][1] - self.numDisplayedCols
        elif self.parent.userPos[1] < self.displayedSection[0][1]: # left
            self.displayedSection[0][1] = self.parent.userPos[1]
            self.displayedSection[1][1] = self.displayedSection[0][1] + self.numDisplayedCols

        self.parent.cursesObj.refresh(self.displayedSection[0][0],self.displayedSection[0][1]*self.colSize, self.menuPos[0][0],self.menuPos[0][1], self.menuPos[1][0], self.menuPos[1][1])


####### OPEN ORDERS MENU?? #########

class openOrdersMenu(padMenu):
    def __init__(self, parent=None, menuPos=None, maxRowsAndCols=[1,10], rowAndColSize=[1,20], data=None, href=None, dataKeys=None):
        padMenu.__init__(self, parent, menuPos, maxRowsAndCols, rowAndColSize, data, href, dataKeys)

    def initDataFormat(self):

        numData = len(self.data)
        self.maxRows = numData/self.maxCols*2
        lastColPos = numData % self.maxCols

        if lastColPos != 0:
            self.maxRows += 2
        else:
            if numData > 0:
                lastColPos = self.maxCols

        self.lastPos = [self.maxRows-1, lastColPos-1]

        self.numDisplayedRows = ((self.menuPos[1][0] - self.menuPos[0][0]) / 4)
        self.numDisplayedCols = ((self.menuPos[1][1] - self.menuPos[0][1]) / self.colSize)
        self.displayedSection = [[0,0], [self.numDisplayedRows, self.numDisplayedCols]]


    def updateMenu(self):

        formatPos = [0,0]
        topPadding = 2
        leftPadding = 10
        colWidth = 30
        rowHeight = 4

        for counter in range(0,len(self.data)):

            keyCount = 0
            for key in self.data[counter]:
                if key == "asset" or key == "name":
                    textStyle = h if [keyCount+2*formatPos[0],formatPos[1]] == self.parent.userPos else n
                    self.parent.cursesObj.addstr(keyCount+topPadding+formatPos[0]*rowHeight,formatPos[1]*colWidth+leftPadding, self.data[counter][key], textStyle)
                    keyCount+=1

            formatPos[1] += 1
            if formatPos[1] == self.maxCols:
                formatPos[1] = 0; formatPos[0] += 1

        format = 0
        temp1 = self.parent.userPos[0]/2
        temp2 = self.parent.userPos[0] % 2
        if temp2 == 0:
            format = 1

        #print(self.parent.userPos[0])
        if self.parent.userPos[0] > self.displayedSection[1][0]+6: # down
            self.displayedSection[1][0] = self.parent.userPos[0]-4
            self.displayedSection[0][0] = self.displayedSection[1][0] - self.numDisplayedRows
        elif self.parent.userPos[0] < self.displayedSection[0][0]: # up
            self.displayedSection[0][0] = self.parent.userPos[0]
            self.displayedSection[1][0] = self.displayedSection[0][0] + self.numDisplayedRows
        elif self.parent.userPos[1] > self.displayedSection[1][1]: # right
            self.displayedSection[1][1] = self.parent.userPos[1]
            self.displayedSection[0][1] = self.displayedSection[1][1] - self.numDisplayedCols
        elif self.parent.userPos[1] < self.displayedSection[0][1]: # left
            self.displayedSection[0][1] = self.parent.userPos[1]
            self.displayedSection[1][1] = self.displayedSection[0][1] + self.numDisplayedCols

        self.parent.cursesObj.refresh(self.displayedSection[0][0],self.displayedSection[0][1]*self.colSize, self.menuPos[0][0],self.menuPos[0][1], self.menuPos[1][0], self.menuPos[1][1])



############ PAD  ##############

class cPad(cWindow):

    def __init__(self,parent=None, typeWin=None, window=None, title=None, content=None):
        cWindow.__init__(self)

        self.parent = parent
        self.cursesObj = curses.newpad(window[0][0],window[0][1])
        self.typeWin = typeWin

        height, width = window[1]
        pStartY, pStartX, = self.parent.windowPos[0]
        startPosY = window[2][0]+pStartY
        startPosX = window[2][1]+pStartX
        endPosY = startPosY+height - 1
        endPosX = startPosX+width - 1
        self.windowPos = [[startPosY,startPosX], [endPosY, endPosX]]


    def drawRectangle(self, cursesObj=None, pos=None):
        if pos == None:
            pos = self.windowPos 
        rectangle(cursesObj, pos[0][0],pos[0][1], pos[1][0], pos[1][1])
        self.parent.cursesObj.refresh()


    def popStack(self):
        self.cursesObj.clear()
        #self.pad.refresh(0,0,0,0,0,0)
        self.userPos = [0,0]
        self.parent.cursesObj.clear()
        self.parent.cursesObj.refresh()
        windowStack.pop()
        #mainWindow.refresh()


#############   ONE ORDERBOOK  ################

class orderbook(cWindow):
    def __init__(self, windowFormat=None, typeWin=None, parent=None, title=None, content=None):
        cWindow.__init__(self)

        ###### GET RID OF THIS #######
        height, width = windowFormat[0]
        startPosY = windowFormat[1][0]
        startPosX = windowFormat[1][1]
        endPosY = startPosY+height - 1
        endPosX = startPosX+width - 1

        self.cursesObj = curses.newwin(height, width, startPosY, startPosX)   # height, width, startPosY, 
        self.windowPos = [[startPosY, startPosX], [endPosY, endPosX]]
        self.typeWin = typeWin
        self.parent = parent
        ###############################

        self.baseAsset = None
        self.relAsset = None
        self.orderbookData = None
        self.twin = None
        self.bothOrderbooks = []


    def initBook(self, baseAsset, relAsset):

        self.getBook(baseAsset, relAsset)
        #self.getBook(relAsset, baseAsset)

        bidPad = self.children["pads"]["bidPad"]
        askPad = self.children["pads"]["askPad"]

        bidPad.cursesObj.clear()
        askPad.cursesObj.clear()
        try:
            self.bothOrderbooks[0].asks.reverse()
            if len(self.bothOrderbooks[0].bids):
                bidPad.menu = padMenu(bidPad, [[8,67],[0,0]], [len(self.bothOrderbooks[0].bids),1], [1,20], self.bothOrderbooks[0].bids, None, ["price","volume","other","exchange"])
            else:
                bidPad.menu = padMenu(bidPad, [[8,67],[0,0]], [1,1], [1,20], ['No bids available'])
            if len(self.bothOrderbooks[0].asks):
                askPad.menu = padMenu(askPad, [[8,67],[0,0]], [len(self.bothOrderbooks[0].asks),1], [1,20], self.bothOrderbooks[0].asks, None, ["price","volume","other","exchange"])
            else:
                askPad.menu = padMenu(askPad, [[8,67],[0,0]], [1,1], [1,20], ['No asks available'])
        except:
            bidPad.menu = padMenu(bidPad, [[8,67],[0,0]], [1,1], [1,20], ['ERROR!'])
            askPad.menu = padMenu(askPad, [[8,67],[0,0]], [1,1], [1,20], ['ERROR!'])
            return

        bidPad.menu.initDataFormat()
        askPad.menu.initDataFormat()
        self.children['windows']['orderbookBar'].initTitle([[0,4],[1,curses.COLS-2]], baseAsset['name']+"/"+relAsset['name'])

    def getBook(self, baseAsset, relAsset):
        self.bothOrderbooks = []
        self.baseAsset = baseAsset; self.relAsset = relAsset
        oneObook = Orders()
        oneObook.FromOrderbook(getOrderbook(bit, baseAsset['asset'], relAsset['asset']))
        self.bothOrderbooks.append(oneObook)

    #def initBookMenu():

    #    if len(data):
    #        book.menu = padMenu(book, [[8,67],[0,0]], [len(data),1], [1,20], data, None, ["price","amount"])


#########   LAZY HACKS   ################

def drawOrderbookDefaults(window):

    rectangle(window.cursesObj, 3,3,12,72)
    rectangle(window.cursesObj, 14,3,23,72)
    window.cursesObj.addstr(12,34," Asks ")
    window.cursesObj.addstr(14,34," Bids ")
    window.cursesObj.addstr(13,5,"{0:20}{1:20}{2:20}{3}".format("Price", "Amount", "Seller", "Exchang-"))
    window.cursesObj.refresh()
    window.children["windows"]["placeOrderWindow"].initTitle([[1,1],[1,22]],"Market Info")
    window.children["windows"]["placeOrderWindow"].cursesObj.border()
    window.children["windows"]["orderbookBar"].cursesObj.hline(1,0,'-',curses.COLS-1)
    childLoop(window.childrenList)


def drawAllOrderbooksDefaults(window):

    window.children["windows"]["allOrderbooksBar"].cursesObj.hline(1,0,'-',curses.COLS-1) # merge
    childLoop(window.childrenList)


def drawActiveOrderbooksDefaults(window):

    bar = window.children["windows"]["activeOrderbooksBar"]
    window.children["windows"]["activeOrderbooksBar"].cursesObj.hline(2,0,'-',curses.COLS-1)
    bar.cursesObj.addstr(1,1,"{0:20}{1:20}{2:20}{3:20}".format("Base", "Rel", "#Quotes","Exchange"))
    childLoop(window.childrenList)


def drawOpenOrdersDefaults(window):

    window.cursesObj.refresh()
    window.children["windows"]["openOrdersBar"].cursesObj.hline(1,0,'-',curses.COLS-1)
    childLoop(window.childrenList)

def childLoop(childrenList):

    for childWin in childrenList:
        childWin.prevUserPos = [0,0]
        #childWin.userPos = [0,0]
        childWin.userPos = [-1,0]
        try:
            childWin.menu.updateMenu()
        except:
            childWin.cursesObj.refresh()


##########  INIT WINDOWS   #############


def initWindows():
    
    global allWindows
    global windowStack

############# MAIN MENU ###############


    mainMenu = cWindow.initWindow([[5,curses.COLS],[0,0]], "menu", None, [[[1,1],[1,curses.COLS-2]],"CryptoSleuth v1.0.0b"], None)
    mainMenu.menu = menu(mainMenu, [[1,curses.COLS-1],[3,1]], [1,5], [1,15], ["Orderbooks", "Open Orders", "Settings"], ["subMenu", "openOrders", "Settings"])
    mainMenu.menu.initDataFormat()


###########    SUB MENU    ##########


    subMenu = cWindow.initWindow([[3,curses.COLS],[4,0]], "menu", None, None, None)
    subMenu.menu = menu(subMenu, [[1,curses.COLS-1],[1,1]], [1,5], [1,19], ["All Orderbooks", "Active Orderbooks", "Find Orderbook"], ["allOrderbooks", "activeOrderbooks", "Settings"])
    subMenu.menu.initDataFormat()

##########   ALL ORDERBOOKS  ###############


    allOrderbooks = cWindow.initWindow([[curses.LINES-7,curses.COLS],[7,0]], "allOrderbooks", None, None, None)

    allOrderbooksBar = cWindow.initWindow([[2,curses.COLS-1],[7,1]], "allOrderbooksBar", allOrderbooks, None, None)
    allOrderbooksBar.menu = menu(allOrderbooksBar, [[1,curses.COLS-1],[0,1]], [1,1], [1,15], ["All", "Favorites", "Add"])
    allOrderbooksBar.menu.initDataFormat()

    allOrderbooksPad = cPad(allOrderbooks, "allOrderbooksList", [[26,800],[21,curses.COLS-1],[2,1]], None, None)

    allOrderbooks.addChild("pads","menu", allOrderbooksPad)
    allOrderbooks.addChild("windows","allOrderbooksBar", allOrderbooksBar)

#########   ONE ORDERBOOK   ################


    obook = orderbook([[curses.LINES-7,curses.COLS],[7,0]], "orderbook", None, None, None)

    orderbookBar = cWindow.initWindow([[2,curses.COLS-1],[7,1]], "orderbookBar", obook, None, None)
    orderbookBar.menu = menu(orderbookBar, [[1,curses.COLS-1],[0,1]], [1,1], [1,15], ["Refresh", "Flip"])
    orderbookBar.menu.initDataFormat()

    placeOrderWindow = cWindow.initWindow([[17,20],[12,curses.COLS-23]], "placeOrderWindow", obook, [[[1,1],[1,22]],"Market Info"], None)
    placeOrderWindow.menu = menu(placeOrderWindow, [[3,8],[11,6]], [2,1], [1,0], ["placebid", "placeask"])
    placeOrderWindow.menu.initDataFormat()

    bidPad =  cPad(obook, "bidPad", [[200,800],[7,65],[15,5]], None, None)

    askPad = cPad(obook, "askPad", [[200,800],[7,65],[4,5]], None, None)

    obook.addChild('windows','placeOrderWindow', placeOrderWindow)
    obook.addChild("pads","bidPad", bidPad)
    obook.addChild("pads","askPad", askPad)
    obook.addChild('windows','orderbookBar', orderbookBar)


#########   ACTIVE ORDERBOOKS   ################


    activeOrderbooks = cWindow.initWindow([[curses.LINES-8,curses.COLS],[7,0]], "activeOrderbooks", None, None, None)

    activeOrderbooksBar = cWindow.initWindow([[3,curses.COLS-1],[7,1]], "activeOrderbooksBar", activeOrderbooks, None, None)
    activeOrderbooksBar.menu = menu(activeOrderbooksBar, [[1,curses.COLS-1],[0,1]], [1,1], [1,15], ["Sort"])
    activeOrderbooksBar.menu.initDataFormat()

    activeOrderbooksPad = cPad(activeOrderbooks, "activeOrderbooksPad", [[300,300],[21,curses.COLS-1],[3,1]], None, None)

    activeOrderbooks.addChild("pads","activeOrderbooksPad", activeOrderbooksPad)
    activeOrderbooks.addChild("windows","activeOrderbooksBar", activeOrderbooksBar)

##############   OPEN ORDERS   ###################


    openOrders = cWindow.initWindow([[curses.LINES-6,curses.COLS],[5,0]], "openOrders", None, None, None)

    openOrdersBar = cWindow.initWindow([[2,curses.COLS-1],[5,1]], "openOrdersBar", openOrders, None, None)
    openOrdersBar.menu = menu(openOrdersBar, [[1,curses.COLS-1],[0,1]], [1,1], [1,15], ["All", "Favorites", "Add"])
    openOrdersBar.menu.initDataFormat()

    openOrdersPad = cPad(openOrders, "openOrdersPad", [[99,1000],[23,curses.COLS-1],[0,1]], None, None)

    openOrders.addChild("pads","openOrdersPad", openOrdersPad)
    openOrders.addChild("windows","openOrdersBar", openOrdersBar)


#########   GLOBAL WINDOW LIST  ###################


    allWindows["mainMenu"] = mainMenu
    allWindows["subMenu"] = subMenu
    allWindows["allOrderbooks"] = allOrderbooks
    allWindows["activeOrderbooks"] = activeOrderbooks
    allWindows["orderbook"] = obook
    allWindows["openOrders"] = openOrders
    
############### END INIT WINDOWS  ###############3



##################    MAIN    ###########################


def processWindow(window):

    global windowStack
    global allWindows
    global assetInfo

    mainWindow.refresh()


    if window.typeWin == "menu":

        window.cursesObj.border()
        fourArrowUI(window)
        ignore = window.menu.data[window.userPos[1]]
        if ignore == "Settings" or ignore == "Find Orderbook":
            processWindow(window)
        windowStack.append(allWindows[window.menu.dataHref[window.userPos[1]]])
        processWindow(windowStack[len(windowStack)-1])


    elif window.typeWin == "allOrderbooks":

        #allOrderbooksBar.userPos=[-1,0]
        #allOrderbooksBar.menu.updateMenu()

        popupSelection = None
        pad = window.children["pads"]["menu"]
        pad.menu = padMenu(pad, [[22,95],[0,1]], [22,0], [1,48], assetInfo, None, ["name","asset"])
        pad.menu.initDataFormat()


        while popupSelection != "Confirm": # get rid of this

            drawAllOrderbooksDefaults(window)
            baseRel = []
            assetCounter = 0
            counter = 0
            while len(baseRel) < 2: # get rid of
                currentChild = window.childrenList[counter]
                currentChild.userPos = currentChild.prevUserPos
                if fourArrowUI(currentChild) == -2: # handle this somewhere else
                    currentChild.prevUserPos = currentChild.userPos
                    currentChild.userPos = [-1,0]
                    currentChild.menu.updateMenu()
                    counter = counter+1 if counter < len(window.childrenList)-1 else 0
                elif currentChild.typeWin == "allOrderbooksBar":
                    barSelection = currentChild.menu.data[currentChild.userPos[1]]
                    if barSelection == "Add":
                        popup = cPopup() # merge popup calls
                        popup.popupAddAsset()
                        popup.showPanel()
                        assetIDBox = Textbox(popup.assetIDInputWin)
                        assetNameBox = Textbox(popup.assetNameInputWin)
                        while True:
                            curses.curs_set(0) # merge
                            fourArrowUI(popup)
                            curses.curs_set(1)
                            popupSelection = popup.menu.data[popup.userPos[0]]
                            if popupSelection == "Asset ID:":
                                assetIDBox.edit()
                            elif popupSelection == "Asset Name:":
                                assetNameBox.edit()
                            else:
                                assetID = assetIDBox.gather()
                                assetName = assetNameBox.gather()
                                popup.popStack()
                                curses.curs_set(0)
                                if len(assetID) and len(assetName):
                                    assetInfo.append({"name":assetName,"asset":assetID})
                                    tempList = sorted(assetInfo, key=operator.itemgetter('name'))
                                    assetInfo = tempList
                                    with io.open("assetInfo2.txt", "w", encoding="utf-8") as f:
                                        f.write(unicode(json.dumps(assetInfo,sort_keys=True,indent=4,ensure_ascii=False)))
                                    curses.flash()
                                processWindow(window)

                elif currentChild.typeWin == "allOrderbooksList":
                    baseRel.append(currentChild.menu.data[currentChild.userPos[1]*currentChild.menu.maxRows+currentChild.userPos[0]])

            if baseRel[0] == baseRel[1]:
                popup = cPopup()
                popup.popupErrorMessage("Base Asset and Rel Asset must be different!")
            else:
                popup = cPopup()
                popup.popupViewOrderbook(baseRel[0], baseRel[1])

            popup.showPanel()
            fourArrowUI(popup)
            popupSelection = popup.menu.data[popup.userPos[1]]
            popup.popStack()

        window.cursesObj.clear()
        window.cursesObj.refresh()
        windowStack.pop()
        orderbook = allWindows["orderbook"]
        orderbook.initBook(baseRel[0],baseRel[1])
        windowStack.append(orderbook)
        processWindow(windowStack[len(windowStack)-1])


    elif window.typeWin == "activeOrderbooks":

        popupSelection = None
        pad = window.children["pads"]["activeOrderbooksPad"]

        retdata = getAllOrderbooks(bit)
        if not 'orderbooks' in retdata or not len(retdata['orderbooks']):
            pad.menu = padMenu(pad, [[20,98],[0,1]], [1,1], [1,25], ['No active orderbooks'])
        else:
            allObooks = retdata['orderbooks']
            tempSort = sorted(allObooks, key=operator.itemgetter('exchange'))
            allObooks = tempSort
            pad.menu = padMenu(pad, [[21,98],[0,1]], [len(allObooks),1], [1,25], allObooks, None, ["base","rel","numquotes","exchange"])
        pad.menu.initDataFormat()

        drawActiveOrderbooksDefaults(window)
        counter = 0
        while True:
            currentChild = window.childrenList[counter]
            currentChild.userPos = currentChild.prevUserPos
            if fourArrowUI(currentChild) == -2:
                currentChild.prevUserPos = currentChild.userPos
                currentChild.userPos = [-1,0]
                currentChild.menu.updateMenu()
                counter = counter+1 if counter < len(window.childrenList)-1 else 0
            elif currentChild.typeWin == "activeOrderbooksBar":
                continue
            elif currentChild.typeWin == "activeOrderbooksPad":
                menuData = currentChild.menu.data[currentChild.userPos[0]]
                baseAsset = {'name':menuData['base'],'asset':menuData['baseid']}
                relAsset = {'name':menuData['rel'],'asset':menuData['relid']}
                popup = cPopup() # merge
                popup.popupViewOrderbook(baseAsset, relAsset)
                popup.showPanel()
                fourArrowUI(popup)
                popupSelection = popup.menu.data[popup.userPos[1]]
                popup.popStack()
                if popupSelection == "Confirm":
                    window.cursesObj.clear()
                    window.cursesObj.refresh()
                    windowStack.pop()
                    orderbook = allWindows["orderbook"]
                    orderbook.initBook(baseAsset,relAsset)
                    windowStack.append(orderbook)
                    processWindow(windowStack[len(windowStack)-1])
                else:
                    processWindow(window)

    elif window.typeWin == "orderbook":

        drawOrderbookDefaults(window)

        counter = 0
        while True:
            currentChild = window.childrenList[counter]
            currentChild.userPos = currentChild.prevUserPos
            if fourArrowUI(currentChild) == -2: # merge
                currentChild.prevUserPos = currentChild.userPos
                currentChild.userPos = [-1,0]
                currentChild.menu.updateMenu()
                counter = counter+1 if counter < len(window.childrenList)-1 else 0
            elif currentChild.typeWin == "orderbookBar":
                barSelection = currentChild.menu.data[currentChild.userPos[1]]
                if barSelection == "Refresh":
                    window.initBook(window.baseAsset, window.relAsset)
                    curses.flash()
                    processWindow(window)
                elif barSelection == "Flip":
                    window.initBook(window.relAsset, window.baseAsset)
                    curses.flash()
                    processWindow(window)
            elif currentChild.typeWin == "placeOrderWindow":
                placeOrderType = currentChild.menu.data[currentChild.userPos[0]]
                popup = cPopup() # merge popup calls
                popup.popupPlaceOrder(placeOrderType)
                popup.showPanel()
                priceBox = Textbox(popup.priceInputWin)
                amountBox = Textbox(popup.amountInputWin)
                while True:
                    curses.curs_set(0) # merge
                    fourArrowUI(popup)
                    curses.curs_set(1)
                    popupSelection = popup.menu.data[popup.userPos[0]]
                    successFlash = False
                    if popupSelection == "Price":
                        priceBox.edit()
                    elif popupSelection == "Amount":
                        amountBox.edit()
                    else:
                        price = priceBox.gather()
                        amount = amountBox.gather()
                        curses.curs_set(0)
                        if len(price) and len(amount):
                            retdata = placeOrder(bit, window.baseAsset['asset'], window.relAsset['asset'], price, amount, placeOrderType)
                            if 'result' in retdata and retdata['result'] is not None:
                                successFlash = True # success?
                            else:
                                pass # error?
                        window.initBook(window.baseAsset, window.relAsset)
                        popup.popStack()
                        if successFlash:
                            curses.flash()
                        processWindow(window)
            elif currentChild.typeWin == "bidPad":
                continue
            elif currentChild.typeWin == "askPad":
                continue

    elif window.typeWin == "openOrders":

        pad = window.children["pads"]["openOrdersPad"]
        pad.menu = openOrdersMenu(pad, [[24,95],[0,1]], [10,10], [7,70], assetInfo, None, ["name","asset"])
        pad.menu.initDataFormat()

        #rectangle(window.cursesObj, 3,3,12,72)
        #rectangle(window.cursesObj, 14,3,23,72)

        drawOpenOrdersDefaults(window)

        while True:
            fourArrowUI(pad)
        
if __name__ == '__main__':

    #global windowStack
    #global allWindows

    signal.signal(signal.SIGINT, signal_handler)

    initWindows()
    windowStack.append(allWindows["mainMenu"])
    processWindow(windowStack[0])


    curses.echo()
    curses.nocbreak(False)
    curses.endwin()



