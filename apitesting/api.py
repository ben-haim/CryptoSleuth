#!/usr/bin/env python
# -*- coding: utf-8 -*-


#import bitcoinrpc, bitcoinrpc.authproxy

import requests
from params import snPostParams


class API(object):


    def __init__(self, config={}):

        self.snDir = None

        self.btcdUser = None
        self.btcdPass = None
        self.btcdPort = None
        #self.rpc = 'http://'+rpcuser+':'+rpcpass+'@127.0.0.1:'+rpcport
        #self.bit = bitcoinrpc.authproxy.AuthServiceProxy(rpc)

        self.nxturl = "http://127.0.0.1:7876/nxt?"
        self.snurl = "http://127.0.0.1:7777"


    def buildParams(self, method, params):
        obj = {}

        postParams = snPostParams[method]
        for key in postParams:
            if key in params:
                obj[key] = params

        return obj


    def doAPICall(self, method, params, isNXT):

        if isNXT:
            url = self.nxturl
        else:
            url = self.snurl
            params = self.buildParams(method, params)
            params = json.dumps(params)

        try:
            r = requests.post(url, data=params)
            data = r.json()
        except Exception as e:
            data = {}
            raise

        return data



