#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import signal
from threading import Thread, Lock
import time
import json
import ConfigParser

from tui import * 
from sndaemon import SNDaemon
from daemonstream import DaemonStream, PadRefresher
#from APIcalls import API



windowStack = []

allWindows = {
    "mainMenu":None,
    "supernet":None
}


def exit_handler(message=None):

    global mainPadRefresher
    global snDaemon

    mainPadRefresher.stop()
    mainPadRefresher.daemonStream.stop()

    unloadCurses()

    
    snDaemon.stopSN()

    if message:
        print(message)
    
    sys.exit(0)


def signal_handler(signal, frame):
    exit_handler()



def initWindows():
    
    global allWindows

    mainMenu = cWindow.initWindow([[5,getCursesCols()],[0,0]], "menu", None, [[[1,1],[1,getCursesCols()-2]],"CryptoSleuth v1.0.0b"], None)
    mainMenu.menu = menu(mainMenu, [[1,getCursesCols()-1],[3,1]], [1,5], [1,15], ["SuperNET"], ["supernet"])
    mainMenu.menu.initDataFormat()

    ########## SN #####################

    supernet = cWindow.initWindow([[curses.LINES-7,getCursesCols()],[5,0]], "supernet", None, None, None)

    supernetPad = cPad(supernet, "supernetPad", [[3500,1000],[20,90],[4,88]], None, None)
    supernetPad.menu = padMenu(supernetPad, [[19,87],[0,0]], [1,1], [1,1], [" "], None)
    supernetPad.menu.initDataFormat()

    testsWin = cWindow.initWindow([[17,85],[9,1]], "testsWin", supernet, None, None)
    #testsPad = cPad(supernet, "snTestPad", [[500,400],[20,86],[4,1]], None, None)
    testsWin.menu = menu(testsWin, [[1,84],[0,3]], [1,5], [1,15], ["Sequence", "Cases", "Results"])
    testsWin.menu.initDataFormat()

    progressPad = cPad(supernet, "progressPad", [[500,400],[14,90],[25,44]], None, None)
    progressPad.menu = padMenu(progressPad, [[13,89],[0,0]], [1,1], [1,1], [" "], None)
    progressPad.menu.initDataFormat()

    supernet.addChild("pads","progressPad", progressPad)
    supernet.addChild("pads","menu", supernetPad)
    supernet.addChild("windows","testsWin", testsWin)

    #####################################

    allWindows["mainMenu"] = mainMenu
    allWindows["supernet"] = supernet


##################    MAIN    ###########################


def processWindow(window):

    global windowStack
    global allWindows
    global mainPadRefresher

    getMainWindow().refresh()


    if window.typeWin == "menu":

        window.cursesObj.border()
        ret = fourArrowUI(window)
        if ret == -1 or ret == -2:
                processWindow(window)
        windowStack.append(allWindows[window.menu.dataHref[window.userPos[1]]])
        processWindow(windowStack[len(windowStack)-1])


    elif window.typeWin == "supernet":

        #pad = window.children["pads"]["menu"]
        #snPadRefresher = Looping()
        #t = Thread(target=snPadRefresher.runForever)
        #t.daemon = True
        #t.start()

        drawSuperNETDefaults(window)
        mainPadRefresher.start()
        counter = 0
        while True: # get rid of this
            currentChild = window.childrenList[counter]
            currentChild.userPos = currentChild.prevUserPos
            ret = fourArrowUI(currentChild)
            if ret == -2: # handle this somewhere else
                currentChild.prevUserPos = currentChild.userPos
                currentChild.userPos = [-1,0]
                currentChild.menu.updateMenu()
                counter = counter+1 if counter < len(window.childrenList)-1 else 0
            elif ret == -1:
                mainPadRefresher.stop()
                if len(windowStack) > 1:
                    window.children["pads"]["menu"].popStack()
                    windowStack.pop()
                    processWindow(windowStack[len(windowStack)-1])
                else:
                    processWindow(window)
            elif currentChild.typeWin == "testsWin":
                barSelection = currentChild.menu.data[currentChild.userPos[1]]
                if barSelection == "Sequence":
                    makeSeq()
                elif barSelection == "Cases":
                    processWindow(window)
                elif barSelection == "Results":
                    processWindow(window)


if __name__ == '__main__':

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

    signal.signal(signal.SIGINT, signal_handler)

    initCurses()
    initWindows()

    snDaemon = SNDaemon({"sndir":sndir})
    snDaemon.start()
    mainDaemonStream = DaemonStream({'snDaemon':snDaemon, 'name':'main'})
    mainDaemonStream.start()
    mainPadRefresher = PadRefresher({'daemonStream':mainDaemonStream, 'pad':allWindows['supernet'].children["pads"]["menu"], 'timer':3})

    windowStack.append(allWindows["mainMenu"])
    processWindow(windowStack[0])






