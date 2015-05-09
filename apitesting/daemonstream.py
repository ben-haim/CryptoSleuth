#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Thread, Lock
from subprocess import Popen, PIPE, call, check_call
from Queue import Queue, Empty
import time
from utils import *

class DaemonStream(object):

    def __init__(self, obj):

        self.isRunning = True
        self.queue = {"q":Queue(), "lock":Lock(), "name":obj['name']}
        self.streamData = []
        self.streamThread = None
        self.snDaemon = obj['snDaemon']
        
    def start(self):
        self.snDaemon.subscribeToDaemonLogs(self.queue)
        self.streamThread = Thread(target=self.readStream)
        self.streamThread.daemon = True
        self.streamThread.start()
        #while self.isRunning:
        #    self.readStream()
        #    time.sleep(3)


    def stop(self):
        self.isRunning = False


    def readStream(self):
        while self.isRunning:
            with self.queue['lock']:
                while not self.queue['q'].empty():
                    self.streamData.append(self.queue['q'].get(False))


class PadRefresher(object):

    def __init__(self, obj):

        self.isRunning = False
        self.refreshThread = None
        self.daemonStream = obj['daemonStream']
        self.pad = obj['pad']
        self.timer = obj['timer']

    def start(self):
        if not self.isRunning:
            self.isRunning = True
            self.refreshThread = Thread(target=self.refreshPad)
            self.refreshThread.daemon = True
            self.refreshThread.start()

    def stop(self):
        self.isRunning = False

    def refreshPad(self):

        while self.isRunning:
            data = self.formatStreamData()
            if len(data):
                self.pad.menu.updateData(data)
                self.pad.menu.menuToBottom() 
            time.sleep(self.timer)


    def formatStreamData(self):

        formatted = []

        for i in range(len(self.daemonStream.streamData)):
            data = self.daemonStream.streamData[i]
            s = getDate(data['ts'])+": "+data['line']
            if len(s) > 84:
                s = s[:84]
            formatted.append(s)

        return formatted

    #def updatePad(self):
    #    self.pad.menu.updateData(self.daemonStream.streamData)
    #    self.pad.menu.menuToBottom()
    #for i in range(len(snLogs)):
    #    if len(snLogs[i]['line']) > 84:
    #        snLogs[i]['line'] = snLogs[i]['line'][:84]
    #    s.append(getDate(snLogs[i]['ts'])+": "+snLogs[i]['line'])









