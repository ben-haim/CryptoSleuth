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
import thread

import curses
from curses.textpad import Textbox, rectangle
import curses.panel

import json
import bitcoinrpc, bitcoinrpc.authproxy
import ConfigParser

from subprocess import Popen, PIPE
from Queue import Queue, Empty
from threading import Thread
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

from subprocess import call
from subprocess import check_call
snthread = None

def exit_handler(message=None):
    global pro
    global snPadRefresher

    if snPadRefresher:
        snPadRefresher.isRunning = False
    curses.echo()
    curses.curs_set(1)
    curses.nocbreak()
    curses.endwin()
    if message:
        print(message)

    #check_call(["/home/sleuth/Desktop/git/CryptoSleuth/exit"], shell=True)
    try:
        check_call([sndir+"BitcoinDarkd", "SuperNET", json.dumps({"requestType":"stop"})], shell=False)
    except:
        pass    
    time.sleep(2)
    try:
        check_call([sndir+"BitcoinDarkd", "stop"], shell=False)
    except:
        pass
    time.sleep(1)
    sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=24, cols=80))
    #pro.kill()
    #snthread
    sys.exit(0)


##########  CONFIG  ##############

Config = ConfigParser.ConfigParser()
try:
    Config.read('cryptosleuth.conf')
    rpcuser = Config.get('BitcoinDark', 'rpcuser')
    rpcpass = Config.get('BitcoinDark', 'rpcpass')
    rpcport = Config.get('BitcoinDark', 'rpcport')
    sndir = Config.get('SuperNET', 'sndir')
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
    "supernet":None
}


#################   RPC    ######################


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

    def popupErrorMessage(self, errorMessage):

        self.cursesObj.addstr(1,22,"Error!")
        self.cursesObj.addstr(5,3,"{0}".format(errorMessage))
        self.menu = menu(self, [[1,30],[13,21]], [1,5], [1,10], ["   OK   "])
        self.menu.initDataFormat()
        self.cursesObj.refresh()

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


    def menuToBottom(self):
    
        self.displayedSection[1][0] = self.lastPos[0]
        self.displayedSection[0][0] = self.displayedSection[1][0] - self.numDisplayedRows
        self.parent.cursesObj.refresh(self.displayedSection[0][0],self.displayedSection[0][1]*self.colSize, self.menuPos[0][0],self.menuPos[0][1], self.menuPos[1][0], self.menuPos[1][1])

    def updateData(self, data):
        
        self.data = data
        numData = len(self.data)
        self.maxRows = numData 
        self.maxCols = numData/self.maxRows
        lastRowPos = numData % self.maxRows

        if lastRowPos != 0:
            self.maxCols += 1
        else:
            if numData > 0:
                lastRowPos = self.maxRows

        self.lastPos = [lastRowPos-1, self.maxCols-1]

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
        rectangle(self.parent.cursesObj, pos[0][0],pos[0][1], pos[1][0], pos[1][1])
        self.parent.cursesObj.refresh()


    def popStack(self):
        self.cursesObj.clear()
        #self.pad.refresh(0,0,0,0,0,0)
        self.userPos = [0,0]
        self.parent.cursesObj.clear()
        self.parent.cursesObj.refresh()
        windowStack.pop()
        #mainWindow.refresh()


#########   LAZY HACKS   ################


def drawSuperNETDefaults(window):

    try:
        window.initTitle([[2,curses.COLS/2],[2,curses.COLS-1]],"Tests")
    except:
        pass
    rectangle(window.cursesObj, 3,87,23,179)
    rectangle(window.cursesObj, 3,0,23,86)
    #window.children["pads"]["menu"].drawRectangle()
    window.cursesObj.refresh()
    window.children["windows"]["supernetBar"].cursesObj.hline(1,0,'-',curses.COLS-1)
    window.children["windows"]["testsWin"].cursesObj.hline(1,0,'-',85)
    childLoop(window.childrenList)


def childLoop(childrenList):

    for childWin in childrenList:
        childWin.prevUserPos = [0,0]
        #childWin.userPos = [0,0]
        childWin.userPos = [-1,0]
        try:
            childWin.menu.updateMenu()
        except:
            try:
                childWin.cursesObj.refresh()
            except:
                pass


##########  INIT WINDOWS   #############


def initWindows():
    
    global allWindows
    global windowStack

############# MAIN MENU ###############


    mainMenu = cWindow.initWindow([[5,curses.COLS],[0,0]], "menu", None, [[[1,1],[1,curses.COLS-2]],"CryptoSleuth v1.0.0b"], None)
    mainMenu.menu = menu(mainMenu, [[1,curses.COLS-1],[3,1]], [1,5], [1,15], ["InstantDEX", "SuperNET", "Electrum"], ["subMenu", "supernet", "electrum"])
    mainMenu.menu.initDataFormat()


###########    SUB MENU    ##########


    subMenu = cWindow.initWindow([[3,curses.COLS],[4,0]], "menu", None, None, None)
    subMenu.menu = menu(subMenu, [[1,curses.COLS-1],[1,1]], [1,5], [1,19], ["All Orderbooks", "Active Orderbooks", "Find Orderbook"], ["allOrderbooks", "activeOrderbooks", "Settings"])
    subMenu.menu.initDataFormat()


##########   SUPERNET  ###############


    supernet = cWindow.initWindow([[curses.LINES-7,curses.COLS],[5,0]], "supernet", None, None, None)

    supernetBar = cWindow.initWindow([[2,curses.COLS-1],[5,1]], "supernetBar", supernet, None, None)
    supernetBar.menu = menu(supernetBar, [[1,curses.COLS-1],[0,1]], [1,1], [1,15], ["Refresh", "Clear", "Filter"])
    supernetBar.menu.initDataFormat()

    supernetPad = cPad(supernet, "supernetPad", [[500,400],[20,90],[4,88]], None, None)

    testsWin = cWindow.initWindow([[17,85],[9,1]], "testsWin", supernet, None, None)
    #testsPad = cPad(supernet, "snTestPad", [[500,400],[20,86],[4,1]], None, None)
    testsWin.menu = menu(testsWin, [[1,84],[0,3]], [1,5], [1,15], ["Sequence", "Cases", "Results"])
    testsWin.menu.initDataFormat()


    supernet.addChild("pads","menu", supernetPad)
    supernet.addChild("windows","testsWin", testsWin)
    supernet.addChild("windows","supernetBar", supernetBar)

#########    SEQUENCE WINDOW    ###################


#########   GLOBAL WINDOW LIST  ###################


    allWindows["mainMenu"] = mainMenu
    allWindows["subMenu"] = subMenu
    allWindows["supernet"] = supernet

############### END INIT WINDOWS  ###############3



################ SUPERNET #####################

def loop1(stream):
    global q
    while True:
        line = stream.readline()
        if line:
            q.put(line, False)
    pass

def loop2(stream):
    global q2
    while True:
        line = stream.readline()
        if line:
            q2.put(line, False)
    pass


def sn_thread():
    global pro
    global q
    global q2
    pro = Popen(sndir+"BitcoinDarkd", cwd=sndir, stderr=PIPE, stdout=PIPE, stdin=PIPE, shell=False)
    pro.wait()

    a = Thread(target=loop2, args=(pro.stderr,), name="loop2")
    a.daemon = True
    a.start()
    b = Thread(target=loop1, args=(pro.stdout,), name="loop1")
    b.daemon = True
    b.start()


snLogs = []
snPadRefresher = None

class Looping(object):
    def __init__(self):
        self.isRunning = True

    def runForever(self):
        while self.isRunning == True:
            snRefresher()
            time.sleep(3)

def snRefresher():
    global q
    global q2
    global pro
    global snLogs

    window = allWindows['supernet']

    if pro:
        a = []
        b = []
        while not q.empty():
            snLogs.append(q.get(False))
        while not q2.empty():
            snLogs.append(q2.get(False))
        try:
            for key in b:
                a.append(key)
                pass
        except:
            pass

    pad = window.children["pads"]["menu"]
    if len(snLogs):
        pad.menu.updateData(snLogs)
        pad.menu.updateMenu()
        pad.menu.menuToBottom()
        #pad.userPos[1] = pad.menu.lastPos[1]
        #pad.menu.updateMenu()


##################    MAIN    ###########################


def processWindow(window):

    global windowStack
    global allWindows
    global assetInfo
    global q
    global q2
    global pro
    global snPadRefresher

    mainWindow.refresh()


    if window.typeWin == "menu":

        window.cursesObj.border()
        fourArrowUI(window)
        ignore = window.menu.data[window.userPos[1]]
        if ignore == "Settings" or ignore == "Find Orderbook":
            processWindow(window)
    
        windowStack.append(allWindows[window.menu.dataHref[window.userPos[1]]])
        processWindow(windowStack[len(windowStack)-1])


    elif window.typeWin == "supernet":
        #window.cursesObj.border()
        pad = window.children["pads"]["menu"]
        pad.menu = padMenu(pad, [[19,89],[0,0]], [1,1], [1,25], [""], None)
        pad.menu.initDataFormat()
        snPadRefresher = Looping()
        t = Thread(target = snPadRefresher.runForever)
        t.daemon = True
        t.start()


        drawSuperNETDefaults(window)
        counter = 0
        while True: # get rid of this
            currentChild = window.childrenList[counter]
            currentChild.userPos = currentChild.prevUserPos
            if fourArrowUI(currentChild) == -2: # handle this somewhere else
                currentChild.prevUserPos = currentChild.userPos
                currentChild.userPos = [-1,0]
                currentChild.menu.updateMenu()
                counter = counter+1 if counter < len(window.childrenList)-1 else 0
            elif currentChild.typeWin == "supernetBar":
                barSelection = currentChild.menu.data[currentChild.userPos[1]]
                if barSelection == "Refresh":
                    pad.cursesObj.clear()
                    curses.flash()
                    processWindow(window)
            elif currentChild.typeWin == "testsWin":
                barSelection = currentChild.menu.data[currentChild.userPos[1]]
                if barSelection == "Sequence":

                    processWindow(window)
                elif barSelection == "Cases":

                    processWindow(window)
                elif barSelection == "Results":

                    processWindow(window)
            #elif currentChild.typeWin == "supernetPad":
                #baseRel.append(currentChild.menu.data[currentChild.userPos[1]*currentChild.menu.maxRows+currentChild.userPos[0]])


        
if __name__ == '__main__':

    #global windowStack
    #global allWindows

    q = Queue()
    q2 = Queue()
    pro = None  
    signal.signal(signal.SIGINT, signal_handler)

    snthread = Thread(target=sn_thread)
    snthread.daemon = True
    snthread.start()
    

    initWindows()
    windowStack.append(allWindows["mainMenu"])
    processWindow(windowStack[0])


    #curses.echo()
    #curses.nocbreak(False)
    #curses.endwin()



