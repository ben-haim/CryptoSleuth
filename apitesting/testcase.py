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


    def addFlow(self, method):
        method = getattr(handlers, method)
        self.flow.append(method)



    def initFlow(self):
        for i in range(len(commands)):
            method = getattr(server, command[i])
            data = method()



            
        
