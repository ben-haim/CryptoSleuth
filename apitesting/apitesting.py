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
from userclass import User
from makeoffer import *
from utils import *
#from api import API


allControllers = []
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

    supernetPad = cPad(supernet, "supernetPad", [[6500,1000],[20,90],[4,88]], None, None)
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
    global user
    global snDaemon

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
        user.updateAssetBalances()

        while True:
            currentChild = window.childrenList[counter]
            currentChild.userPos = currentChild.prevUserPos
            ret = fourArrowUI(currentChild)
            if ret == -2:
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
                    makeofferTests()
                    #makeofferTest_nxtae()
                elif barSelection == "Cases":
                    processWindow(window)
                elif barSelection == "Results":
                    processWindow(window)


def makeofferTests():

    import random
    import itertools

    global snDaemon
    global user
    global allControllers


    config = {
        "baseAsset": None,
        "baseDecimals":None,
        "baseAmount": 0,
        "baseAmountDecimals": None,
        "minBaseAmount": 0,
        "relAsset": None,
        "relDecimals":None,
        "relAmount": 0,
        "minRelAmount": 0,
        "perc": 1,
        "offerType": "Sell",
        "exchangeType": "nxtae_nxtae"
        #"isExternalExchange": {"value":None, "default":None}
    }

    assets = []
    history = []
    assets.append(user.getAsset("assetID", "2677462001133444117")) #sleuth00
    assets.append(user.getAsset("assetID", "2892714921553533909")) #sleuth20
    assets.append(user.getAsset("assetID", "13995071746675094813")) #sleuth40
    assets.append(user.getAsset("assetID", "5483407135476088028")) #sleuth60
    pairs = itertools.permutations(assets, 2)

    for pair in pairs:
        baseAsset, relAsset = pair
        #if baseAsset['assetID'] != "2677462001133444117":
        #    continue
        config['baseAsset'] = baseAsset
        config['relAsset'] = relAsset
        config['baseDecimals'] = str(baseAsset['decimals'])
        config['relDecimals'] = str(relAsset['decimals'])

        config['offerType'] = "Sell"
        filename = "./makeoffer_tests/" + str(baseAsset['name']) + "-" + str(relAsset['name']) + "/" + config['offerType']
        baseAmountDecimalsLoop(config, filename)

        config['offerType'] = "Buy"
        filename = "./makeoffer_tests/" + str(baseAsset['name']) + "-" + str(relAsset['name']) + "/" + config['offerType']
        baseAmountDecimalsLoop(config, filename)


    for controller in allControllers:
        overview = controller.testSummary()
        with open("alloverviews", 'a+') as f:
            for line in overview:
                f.write(line)
            f.close()
    
    


def baseAmountDecimalsLoop(config, filename):

    import os

    global user
    global snDaemon
    global allControllers

    baseAmountDecimals = 0

    while baseAmountDecimals <= int(config['baseAsset']['decimals']):
        config['baseAmountDecimals'] = baseAmountDecimals
        addedFilename = filename + "/" + "baseDec-" + str(baseAmountDecimals) + ".txt"
        if not os.path.exists(os.path.dirname(addedFilename)):
            os.makedirs(os.path.dirname(addedFilename))
        controllerName = str(config['baseAsset']['name']) + "-" + str(config['relAsset']['name']) + "_" + config['offerType'] + "_" + "baseDec-" + str(baseAmountDecimals)
        makeoffer = Makeoffer(config=config, filename=addedFilename, user=user, snDaemon=snDaemon, controllerName=controllerName)
        makeoffer.initCases()
        controller = makeoffer.run()
        allControllers.append(controller)

        blockUntilNXTBal()
        baseAmountDecimals += 1
        time.sleep(1)


def blockUntilNXTBal():

    global allWindows
    global user

    pad = allWindows['supernet'].children["pads"]["progressPad"]

    while True:
        nxtBalance = user.api.doAPICall("getBalance", {"requestType":"getBalance","account":user.nxtID}, True)
        if int(nxtBalance['unconfirmedBalanceNQT']) < 40000000000:
            time.sleep(10)
            pad.menu.updateData([getDateNoMS(time.time()), nxtBalance], append=True)
            pad.menu.menuToBottom() 
        else:
            break


if __name__ == '__main__':

    Config = ConfigParser.ConfigParser()
    try:
        Config.read('cryptosleuth.conf')
        rpcuser = Config.get('BitcoinDark', 'rpcuser')
        rpcpass = Config.get('BitcoinDark', 'rpcpass')
        rpcport = Config.get('BitcoinDark', 'rpcport')
        nxtrs = Config.get('NXT', 'nxtrs')
        nxtid = Config.get('NXT', 'nxtid')
        sndir = Config.get('SuperNET', 'sndir')
        assetFile = Config.get('General', 'assetFile')
    except:
        exit_handler("Invalid sleuther.conf")

    try:
        assetInfo = json.load(open(assetFile))
        assetInfo = addAssetID(assetInfo)
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
    user = User({"allAssets":assetInfo, "nxtid":nxtid, "nxtrs":nxtrs})
    windowStack.append(allWindows["mainMenu"])
    processWindow(windowStack[0])






