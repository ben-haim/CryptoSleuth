#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# CryptoSleuth 
# TUI for sleuthing around the cryptocurrency world
# Powered by SuperNET
# Created by CryptoSleuth

import sys
import signal
import threading
import time
import requests

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
from tui import * 


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
    
    try:
        a = authService.SuperNET('{"requestType":"orderbook","baseid":"'+baseid+'","relid":"'+relid+'","allfields":1}')
    except Exception as e:
        raise

    return json.loads(a)


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





#########   LAZY HACKS   ################



def drawSuperNETDefaults(window):

    try:
        window.initTitle([[2,curses.COLS/2],[2,curses.COLS-1]],"Tests")
    except:
        pass

    rectangle(window.cursesObj, 3,87,23,179)
    rectangle(window.cursesObj, 24,41,40,135)
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

    supernetPad = cPad(supernet, "supernetPad", [[3500,2000],[20,90],[4,88]], None, None)

    testsWin = cWindow.initWindow([[17,85],[9,1]], "testsWin", supernet, None, None)
    #testsPad = cPad(supernet, "snTestPad", [[500,400],[20,86],[4,1]], None, None)
    testsWin.menu = menu(testsWin, [[1,84],[0,3]], [1,5], [1,15], ["Sequence", "Cases", "Results"])
    testsWin.menu.initDataFormat()


    supernet.addChild("pads","menu", supernetPad)
    supernet.addChild("windows","testsWin", testsWin)
    supernet.addChild("windows","supernetBar", supernetBar)

#########    PROGRESS WINDOW    ###################


    progressPad = cPad(supernet, "progressPad", [[500,400],[14,90],[25,44]], None, None)
    progressPad.menu = padMenu(progressPad, [[13,89],[0,0]], [1,1], [1,1], [" "], None)
    progressPad.menu.initDataFormat()
    supernet.addChild("pads","progressPad", progressPad)



#########   GLOBAL WINDOW LIST  ###################


    allWindows["mainMenu"] = mainMenu
    allWindows["subMenu"] = subMenu
    allWindows["supernet"] = supernet

############### END INIT WINDOWS  ###############3



################ SUPERNET #####################

from threading import Lock
lock = Lock()
readers = []

def loop1(stream):
    global q
    global readers
    while True:
        line = stream.readline()
        if line:
            obj = {"ts":time.time(), "line":line}
            q.put(obj, False)

            with lock:
                for i in range(len(readers)):
                    readers[i]['q'].put(obj, False)
    pass

def loop2(stream):
    global q2
    global readers
    while True:
        line = stream.readline()
        if line:
            obj = {"ts":time.time(), "line":line}
            q.put(obj, False)
            with lock:
                for i in range(len(readers)):
                    readers[i]['q'].put(obj, False)
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
    global pro
    global snLogs

    s = []
    window = allWindows['supernet']
    pad = window.children["pads"]["menu"]

    if pro:
        while not q.empty():
            snLogs.append(q.get(False))


    for i in range(len(snLogs)):
        if len(snLogs[i]['line']) > 84:
            snLogs[i]['line'] = snLogs[i]['line'][:84]
        s.append(getDate(snLogs[i]['ts'])+": "+snLogs[i]['line'])

    if len(s):
        pad.menu.updateData(s)
        pad.menu.menuToBottom()

clogs = []
progress = []
def caseRefresher():
    global readers
    global pro
    global clogs
    global progress

    for i in range(len(progress)):
        clogs.append(progress[i])

    with lock:
        readers.append({'q':Queue()})

    window = allWindows['supernet']
    pad = window.children["pads"]["progressPad"]

    while True:
        with lock:

            s = []
            while not readers[0]['q'].empty():
                s.append(readers[0]['q'].get(False))


            for i in range(len(s)):
                if len(s[i]['line']) > 84:
                    s[i]['line'] = s[i]['line'][:84]
                clogs.append(getDate(s[i]['ts'])+": "+s[i]['line'])

            if len(s):
                pad.menu.updateData(clogs)
                pad.menu.menuToBottom()


def getDate(ts):
    import datetime
    return datetime.datetime.fromtimestamp(int(ts)).strftime("%H:%M:%S")

def makeoffer(authService, obj):
    
    try:
        a = authService.SuperNET(json.dumps(obj))
    except:
        raise

    return json.loads(a)

def getBal(asset):

    nxturl = "http://127.0.0.1:7876/nxt?"
    nxtid = "9572159016638540187"

    ret = {}
    obj = {'requestType':"getAccountAssets",'account':nxtid, 'asset':asset}

    try:
        r = requests.post(nxturl, data=obj)
        info = r.json()
        if "errorCode" in info:
            return {}
        return info
    except:
        pass

    return {}



def makeBal(assetID):

    asset = getBal(assetID)
    aStr = "NAME: "+asset['name'] + ", BAL: " + str(asset['unconfirmedQuantityQNT']) + ", DEC: " + str(asset['decimals'])
    return aStr


def update(pad, menuData):
    pad.menu.updateData(menuData)
    pad.menu.menuToBottom()


def makeSeq():

    window = allWindows['supernet']
    pad = window.children["pads"]["progressPad"]

    global progress
    jl = "6932037131189568014"
    #skyn = "6854596569382794790"
    skyn ="11060861818140490423"

    #   CASE INIT  #
    caseType = "makeoffer3"
    typeOffer = "Sell"
    exchangeType = "any"
    
    progress.append("CASE: " + caseType + ", OFFER TYPE: " + typeOffer + ", EXCHANGE: " + exchangeType + "\n")
    #           #

    progress.append(" \n")
    update(pad, progress)

    #   CHECK BALANCES  #
    progress.append("Checking balances...\n")
    update(pad, progress)
    progress.append(makeBal(jl))
    progress.append(makeBal(skyn))
    update(pad, progress)
    #                   #

    progress.append(" \n")
    update(pad, progress)

    #   GET ORDERBOOK   #
    progress.append("Loading orderbook...\n")
    update(pad, progress)

    try:
        a = getOrderbook(bit, jl, skyn)
    except:
        a = {}

    needed = "bids" if typeOffer == "Sell" else "asks"
    if needed in a:
        a = a[needed]
    else:
        a = []

    for i in range(len(a)):
        try:
            progress.append(json.dumps(a[i]))
        except:
            progress.append(a[i])

    if len(a):
        update(pad, progress)
    else:
        progress.append("Could not load orderbook\n")
        update(pad, progress)
    #                  #

    progress.append(" \n")
    update(pad, progress)

    #   SELECT ORDER   #
    progress.append("Selecting order...\n")

    if len(a):
        order = a[0]
        try:
            progress.append(json.dumps(order))
        except:
            progress.append(order)
        update(pad, progress)
    else:
        order = None
        progress.append("No orders to choose from\n")
        update(pad, progress)
    #                  #
    
    progress.append(" \n")
    update(pad, progress)

    #   DO MAKEOFFER CALL  #
    time.sleep(1)
    progress.append("Sending makeoffer...\n")

    if order:
        obj = {}
        obj['requestType'] = "makeoffer3"
        for key in order:
            obj[key] = order[key]
        obj['perc'] = 4
        try:
            ret = makeoffer(bit, obj)
        except:
            ret = "Failed"

        try:
            ret = json.dumps(ret)
        except:
            pass

        progress.append(ret)
        update(pad, progress)
    else:
        progress.append("No orders to choose from\n")
        update(pad, progress)

    progress.append(" \n")
    progress.append("Done\n")
    update(pad, progress)
    #                  #


    #   DUMP RESULTS  #
    f = open('dump', 'w')
    for i in range(len(progress)):
        try:
            f.write(json.dumps(progress[i])+'\n')
        except:
            try:
                f.write(str(progress[i])+'\n')
            except:
                f.write('fail\n')
    f.close()

    t = Thread(target=caseRefresher)
    t.daemon = True
    t.start()
    #                 #

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
        pad.menu = padMenu(pad, [[19,89],[0,0]], [1,1], [1,1], [" "], None)
        pad.menu.initDataFormat()
        snPadRefresher = Looping()
        t = Thread(target=snPadRefresher.runForever)
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
                    makeSeq()
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



