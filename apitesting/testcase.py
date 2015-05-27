#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import *
from api import API
from daemonstream import DaemonStream
import time
import json
import types
import makeoffer



class TestCase(object):
    def __init__(self, config=None, typeCase=None, func=None, parent=None, mainHandler=None):

        self.typeCase = typeCase
        self.config = config

        self.progress = []
        self.percentComplete = 0
        self.status = None
        self.errors = []
        self.warnings = []
        self.startTime = None
        self.endTime = None

        self.titleText = ""
        self.name = ""

        self.childIndex = 0
        self.parent = parent
        self.siblings = []
        self.children = []
        self.mainHandler = mainHandler


    @classmethod
    def removeVariable(cls, name):
        return delattr(cls, name)


    @classmethod
    def addMethod(cls, func):
        return setattr(cls, func.__name__, types.MethodType(func, cls))


    def getTestPrints(self):
        temp = self.snDaemon.getPrintouts(None, self.startTime, endTime)
        for i in range(len(temp)):
            self.progress.append(getDate(temp[i]['ts'])+": "+temp[i]['line'])


    def addProgress(self, data, indent=0):
        filename = self.mainHandler.filename
        with open(filename, 'a+') as f:
        #for i in range(len(data)):
            f.write(" "*indent + toString(data))
            f.close()



class Runner(TestCase):

    def __init__(self, config=None, func=None, neededData=[], mainHandler=None, parent=None):
        TestCase.__init__(self, config=config, mainHandler=mainHandler)

        self.typeCase = "runner"

        self.func = func
        self.neededData = neededData


        self.finished = 0
        self.retLevel = 0
        self.retMsg = ""
        self.retData = []


    def run(self):
        #self.addMethod(globals()[self.func])
        #getattr(self, self.func)()
        prevCaseData = self.getNeededData()

        self.startingLogs(prevCaseData)

        #func = globals()[self.func]
        func = getattr(makeoffer, self.func)
        if prevCaseData:
            func(self, prevCaseData)
        else:
            func(self)

        self.endingLogs()

        for i in range(len(self.retData)):
            data = self.retData[i]
            for key in data:
                self.mainHandler.storeData(key, data[key])

        self.finished = 1

        if self.retLevel == -1:
            raise NameError("test")


    def startingLogs(self, prevCaseData):

        self.addProgress(" ")
        self.addProgress(" ")
        self.addProgress("RUNNER: " + self.func)
        self.addProgress("*"*20)

        if prevCaseData:
            self.addProgress("Using data: ")
            for key in prevCaseData:
                line = "    " + key + ": " + toString(prevCaseData[key])
                self.addProgress(line)

        if self.config:
            self.addProgress("Using config options: ")
            for key in self.config:
                line = "    " + key + ": " + toString(self.config[key])
                self.addProgress(line)

        self.addProgress("-"*20)
        self.addProgress(" ")

    
    def endingLogs(self):

        self.addProgress(" ")
        self.addProgress("-"*20)

        self.addProgress("Finished case: " + self.func)
        self.addProgress("retLevel: " + str(self.retLevel))
        self.addProgress("retMsg: " + self.retMsg)

        if len(self.retData):
            self.addProgress("Retrieved data: ")
            for i in range(len(self.retData)):
                data = self.retData[i]
                for key in data:
                    line = "    " + key + ": " + toString(data[key])
                    self.addProgress(line)

        self.addProgress("*"*20)
        self.addProgress(" ")
        self.addProgress(" ")


    def getNeededData(self):

        allData = {}

        for i in range(len(self.neededData)):
            data = self.mainHandler.getData(self.neededData[i])
            allData[self.neededData[i]] = data

        return allData



class Handler(TestCase):

    def __init__(self, config=None, mainHandler=None, parent=None):
        TestCase.__init__(self, config=config, mainHandler=mainHandler, parent=parent)

        self.typeCase = "handler"


    def run(self):
        for i in range(len(self.children)):
            testCase = self.children[i]

            try:
                testCase.run()
            except Exception as e:
                raise e


    def addChild(self, case):

        index = len(self.children)
        case.childIndex = index
        case.parent = self
        self.children.append(case)

        for i in range(len(self.children)):
            if i != index:
                self.children[i].siblings.append(case)


class HandlerLooper(TestCase):

    def __init__(self, config=None, mainHandler=None, parent=None):
        TestCase.__init__(self, config=config, mainHandler=mainHandler, parent=parent)

        self.typeCase = "handlerLooper"
        self.numLoops = 0
        self.sleepTime = 0
        self.breaker = 0


    def run(self):
        counter = 0
        isLooping = True

        while isLooping and counter < self.numLoops:
            for i in range(len(self.children)):
                testCase = self.children[i]

                try:
                    testCase.run()
                except Exception as e:
                    if i == self.breaker:
                        if counter == self.numLoops - 1:
                            raise e
                        else:
                            pass
                    else:
                        raise e
                else:
                    if i == self.breaker:
                        isLooping = False

            counter += 1
            if isLooping:
                time.sleep(self.sleepTime)


    def addChild(self, case):

        index = len(self.children)
        case.childIndex = index
        case.parent = self
        self.children.append(case)

        for i in range(len(self.children)):
            if i != index:
                self.children[i].siblings.append(case)



class Controller(Handler):

    def __init__(self, config={}, filename=None, user=None, snDaemon=None, controllerName=None):
        Handler.__init__(self)
        self.controllerName = controllerName
        self.data = {}
        self.user = user
        self.snDaemon = snDaemon
        self.api = API()
        self.filename = filename
        self.retLevel = 0
        self.retMsg = ""

        self.config = config



    def getData(self, key):

        data = None

        if key in self.data:
            data = self.data[key]

        return data


    def storeData(self, key, data):

        self.data[key] = data


    def countAllRunners(self, allRunners):

        numRunners = 0
        numFinished = 0
        numSuccess = 0
        numFailed = 0
        numWarnings = 0
        failedRunners = []
        warningRunners = []

        for runner in allRunners:

            if runner.finished == 1:
                numFinished += 1

                if runner.retLevel == 0:
                    numSuccess += 1
                elif runner.retLevel == -1:
                    numFailed += 1
                    failedRunners.append(runner)
                else:
                    numWarnings += 1
                    warningRunners.append(runner)

            numRunners += 1

        return {"numRunners":numRunners, "numFinished":numFinished, "numFailed":numFailed, "numSuccess":numSuccess, "numWarnings":numWarnings, "failedRunners":failedRunners, "warningRunners":warningRunners}


    def getAllRunners(self):

        allRunnersGen = self.getAllRunnersGen(self.children)
        allRunnersList = []

        for runner in allRunnersGen:
            #obj = {}
            #obj['caseName'] = runner.func
            #obj['retLevel'] = runner.retLevel
            #obj['retMsg'] = runner.retMsg
            #parsed.append(obj)
            #x = getattr(t,"attr1")

            allRunnersList.append(runner)

        return allRunnersList


    def getAllRunnersGen(self, children):

        for i in range(len(children)):
            child = children[i]
            if child.typeCase == "runner":
                yield child
            else:
                for j in self.getAllRunnersGen(child.children):
                    yield j



    def makeOverview(self):

        overview = []
        allRunners = self.getAllRunners()
        allRunnersCounts = self.countAllRunners(allRunners)

        overview.append("*"*30)

        overview.append("Test Name: " + self.controllerName)
        overview.append("Start time: " + getDateNoMS(int(self.startTime)))
        overview.append("End time: " + getDateNoMS(int(self.endTime)))
        #overview.append("Elapsed time: " + getTimer(int(self.endTime - self.startTime)))

        overview.append("Test Options: ")
        for key in self.config:
            overview.append("    " + key + ": " + toString(self.config[key]))

        overview.append("Num runners: " + str(allRunnersCounts['numRunners']))
        overview.append("Num finished: " + str(allRunnersCounts['numFinished']) + "/" + str(allRunnersCounts['numRunners']))
        overview.append("Num successful: " + str(allRunnersCounts['numSuccess']) + "/" + str(allRunnersCounts['numFinished']))
        overview.append("Num failed: " + str(allRunnersCounts['numFailed']) + "/" + str(allRunnersCounts['numFinished']))
        overview.append("Num warnings: " + str(allRunnersCounts['numWarnings']) + "/" + str(allRunnersCounts['numFinished']))

        overview.append("All runners: ")
        for runner in allRunners:
            overview.append("    " + "Case Name: " + runner.func)
            overview.append("        " + "Ret Level: " + str(runner.retLevel)) 
            overview.append("        " + "Ret Message: " + str(runner.retMsg))
            overview.append("        " + "Finished: " + str(runner.finished))

        overview.append("*"*30)
        overview.append(" ")
        overview.append(" ")

        prependToFile(self.filename, overview)

    
    def testSummary(self):

        overview = []
        allRunners = self.getAllRunners()
        allRunnersCounts = self.countAllRunners(allRunners)

        overview.append("Test Name: " + self.controllerName)
        overview.append("*"*30)
        overview.append("Start time: " + getDateNoMS(int(self.startTime)))
        overview.append("End time: " + getDateNoMS(int(self.endTime)))

        overview.append("Test Options: ")
        for key in self.config:
            overview.append("    " + key + ": " + toString(self.config[key]))

        overview.append("Num runners: " + str(allRunnersCounts['numRunners']))
        overview.append("Num finished: " + str(allRunnersCounts['numFinished']) + "/" + str(allRunnersCounts['numRunners']))
        overview.append("Num successful: " + str(allRunnersCounts['numSuccess']) + "/" + str(allRunnersCounts['numFinished']))
        overview.append("Num failed: " + str(allRunnersCounts['numFailed']) + "/" + str(allRunnersCounts['numFinished']))
        overview.append("Num warnings: " + str(allRunnersCounts['numWarnings']) + "/" + str(allRunnersCounts['numFinished']))
        overview.append("*"*30)
        overview.append(" ")
        overview.append(" ")

        return overview



    def finalStatusTest(self):

        allRunners = self.getAllRunners()
        allRunnersCounts = self.countAllRunners(allRunners)
        if allRunnersCounts['numFailed'] > 0:
            self.retLevel = -1
            self.retMsg = allRunnersCounts['failedRunners'][0].retMsg
        if allRunnersCounts['numWarnings'] > 0:
            self.retLevel = 1
            self.retMsg = allRunnersCounts['warningRunners'][0].retMsg
            


    def run(self):

        self.startTime = time.time()
        for i in range(len(self.children)):
            testCase = self.children[i]

            try:
                testCase.run()
            except Exception as e:
                break

        self.endTime = time.time()
        self.makeOverview()
        self.finalStatusTest()

        return self

            
        
