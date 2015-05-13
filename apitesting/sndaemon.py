#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Thread, Lock
from subprocess import Popen, PIPE, call, check_call
from Queue import Queue, Empty
import json
import time

class SNDaemon(object):

    def __init__(self, config={}):

        self.snDir = config['sndir']

        self.snProcess = None
        self.snThread = None
        self.stderrThread = None
        self.stdoutThread = None

        self.printoutLock = Lock()
        self.printoutQ = Queue()
        self.printoutList = []
        self.printoutSubscribers = []


    def start(self):

        self.snThread = Thread(target=self.startProcess)
        self.snThread.daemon = True
        self.snThread.start()


    def startProcess(self):

        self.snProcess = Popen(self.snDir+"BitcoinDarkd", cwd=self.snDir, stderr=PIPE, stdout=PIPE, stdin=PIPE, shell=False)
        self.snProcess.wait()

        self.startReadline()

    
    def startReadline(self):

        self.stderrThread = Thread(target=self.readlineThread, args=(self.snProcess.stderr,), name="loop1")
        self.stderrThread.daemon = True
        self.stderrThread.start()

        self.stdoutThread = Thread(target=self.readlineThread, args=(self.snProcess.stdout,), name="loop2")
        self.stdoutThread.daemon = True
        self.stdoutThread.start()


    def readlineThread(self, stream):

        while True:
            ts = time.time()
            line = stream.readline()
            if line:
                obj = {"ts":ts, "line":line}

                with self.printoutLock:
                    self.printoutList.append(obj)

                #q.put(obj, False)
                for i in range(len(self.printoutSubscribers)):
                    with self.printoutSubscribers[i]['lock']:
                        self.printoutSubscribers[i]['q'].put(obj, False)


    def getPrintouts(self, index=None, startTime=None, endTime=None):

        parsed = []
        startIndex = -1
        endIndex = -1

        time.sleep(1)
        with self.printoutLock:
            for i in range(len(self.printoutList)):
                line = self.printoutList[i]
                #if index and i < index:
                #    continue
                if startIndex == -1 and line['ts'] >= startTime:
                    startIndex = i
                if endIndex == -1 and line['ts'] >= endTime:
                    endIndex = i

            if not endIndex:
                endIndex = len(self.printoutList) - 1
            parsed = self.printoutList[startIndex:]

        return parsed



    def subscribeToDaemonLogs(self, queue):
        self.printoutSubscribers.append(queue)


    def unsubscribeToDaemonLogs(self):
        with lock:
            self.printoutSubscribers.append({'q':Queue()})


    def restartSN(self):
        pass


    def stopSN(self):
        try:
            check_call([self.snDir+"BitcoinDarkd", "SuperNET", json.dumps({"requestType":"stop"})], shell=False)
        except Exception as e:
            print e
            pass    
        time.sleep(2)
        try:
            check_call([self.snDir+"BitcoinDarkd", "stop"], shell=False)
        except Exception as e:
            print e
            pass
        time.sleep(2)

        return True


