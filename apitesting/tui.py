#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

import curses
from curses.textpad import Textbox, rectangle
import curses.panel

mainWindow = None
h = None
n = None

def getCursesCols():
    return curses.COLS

def getMainWindow():
    return mainWindow

def initCurses():
    global mainWindow
    global h
    global n

    #sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=50, cols=180))
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

def unloadCurses():
    curses.echo()
    curses.curs_set(1)
    curses.nocbreak()
    curses.endwin()
    sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=24, cols=80))



##########   WINDOW   ###################


def init():

    windowMap = []



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
        #windowStack.pop()
        #mainWindow.refresh()


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


    def addStr(self):

        formatPos = [0,0]

        for counter in range(len(self.data)):

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


    def updateMenu(self):

        self.addStr()

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

        try:
            self.parent.cursesObj.refresh(self.displayedSection[0][0],self.displayedSection[0][1]*self.colSize, self.menuPos[0][0],self.menuPos[0][1], self.menuPos[1][0], self.menuPos[1][1])
        except:
            self.parent.cursesObj.clear()


    def menuToBottom(self):

        self.addStr()

        self.displayedSection[1][0] = self.lastPos[0]
        self.displayedSection[0][0] = self.displayedSection[1][0] - self.numDisplayedRows

        try:
            self.parent.cursesObj.refresh(self.displayedSection[0][0],self.displayedSection[0][1]*self.colSize, self.menuPos[0][0],self.menuPos[0][1], self.menuPos[1][0], self.menuPos[1][1])
        except:
            self.parent.cursesObj.clear()

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
        #windowStack.pop()
        #mainWindow.refresh()



def drawSuperNETDefaults(window):

    try:
        window.initTitle([[2,curses.COLS/2],[2,curses.COLS-1]],"Tests")
    except:
        pass

    #for windowsThatNeedBorders in window.children:
    #    this.drawBorder()

    
    rectangle(window.cursesObj, 3,87,23,179)
    rectangle(window.cursesObj, 24,41,40,135)
    rectangle(window.cursesObj, 3,0,23,86)

    #window.children["pads"]["menu"].drawRectangle()
    window.cursesObj.refresh()
    #window.children["windows"]["supernetBar"].cursesObj.hline(1,0,'-',curses.COLS-1)
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



###############    FOUR ARROW UI    ########################
SQUIGGLY = 96
DOWN_ARROW = 258
UP_ARROW = 259
LEFT_ARROW = 260
RIGHT_ARROW = 261

def fourArrowUI(window):

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
            return -1

        elif userInput == SQUIGGLY and window.parent and len(window.parent.childrenList) > 0:
            return -2

    return





###########    LATER   ################

    #obj = {}
    #obj['width'] = "100%"
    #obj['height'] = "100%"
    #obj['parent'] = None
    #mainContainer = Container()

    #obj = {}
    #obj['width'] = "100%"
    #obj['height'] = "5"
    #mainMenuContainer = Container(obj)

class Container(object):

    def __init__(self, config={}):

        self.config = config
        self.display = self.checkObj("display", None)
        self.containerType = self.checkObj("containerType", None)

        self.height = self.checkObj("height", None)
        self.width = self.checkObj("width", None)
        self.absPos = []

        self.parent = self.checkObj("parent", None)
        self.children = []
        self.siblings = []

        self.sibIndex = 0


    def addChild(self, obj):

        obj['parent'] = self
        child = Container.__init__(obj)
        self.children.append(child)

        child.sibIndex = len(self.children) - 1
        child.getSiblings()


    def getSiblings(self):
        if self.parent:
            for i in range(len(self.parent.children)):
                if i != self.sibIndex:
                    self.siblings.append(self.parent.children[i])
        else:
            self.siblings = []


    def getHeightWidth(self):

        pHeight = self.parent.pixHeight
        pWidth = self.parent.pixWidth

        index = self.height.find("%")
        if index:
            mult = int(self.height[0:index])
            self.pixHeight = int(pHeight * (mult/100))
        else:
            self.pixHeight = int(self.height)

        index = self.width.find("%")
        if index:
            mult = int(self.width[0:index])
            self.pixWidth = int(pWidth * (mult/100))
        else:
            self.pixWidth = int(self.width)



    def getPos(self):

        pos = [0,0]

        for i in range(len(self.siblings)):
            if self.siblings[i].sibIndex < self.sibIndex:
                pos[0] += self.siblings[i].pixHeight


    def checkObj(self, key, default):
        
        a = None

        if key in self.config:
            a = self.config[key]
        else:
            a = default

        return a
            
