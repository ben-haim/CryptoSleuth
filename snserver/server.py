import sys
import base64
import ConfigParser
import json
import SimpleXMLRPCServer
import requests


Config = ConfigParser.ConfigParser()

try:
    Config.read('server.conf')
    serverPort = Config.get('Server', 'port')
    serverUser = Config.get('Server', 'user')
    serverPass = Config.get('Server', 'pass')
    rpcuser = Config.get('BitcoinDark', 'rpcuser')
    rpcpass = Config.get('BitcoinDark', 'rpcpass')
    rpcport = Config.get('BitcoinDark', 'rpcport')
except:
    sys.exit("Invalid server.conf")


btcdurl = "http://127.0.0.1:" + rpcport
nxturl = "http://127.0.0.1:7876/nxt?"

pair = rpcuser + ":" + rpcpass
authPair = base64.b64encode(pair)


class retVal(object):
    def __init__(self):
        self.retstat = ''
        self.retval = {}
        self.retbool = None



class SleuthSimpleJSONRPCRequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', "null")
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', "Authorization, content-type, accept")
        self.end_headers()
        self.wfile.flush()

    def do_POST(self):
        if not self.is_rpc_path_valid():
            self.report_404()
            return

        if self.authenticate(self.headers):
            pass
        else:
            self.send_error(401, 'Authentication failed')
            return

        try:
            max_chunk_size = 10*1024*1024
            size_remaining = int(self.headers["content-length"])
            L = []
            while size_remaining:
                chunk_size = min(size_remaining, max_chunk_size)
                L.append(self.rfile.read(chunk_size))
                size_remaining -= len(L[-1])
            data = ''.join(L)
            response = self.server._marshaled_dispatch(data)
            self.send_response(200)
        except Exception, e:
            self.send_response(500)
            err_lines = traceback.format_exc().splitlines()
            trace_string = '%s | %s' % (err_lines[-3], err_lines[-1])
            fault = jsonrpclib.Fault(-32603, 'Server error: %s' % trace_string)
            response = fault.response()

        if response == None:
            response = ''
        self.send_header('Access-Control-Allow-Origin', "null")
        self.send_header("Content-type", "application/json-rpc")
        self.send_header("Content-length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)
        self.wfile.flush()
        self.connection.shutdown(1)


    
    def authenticate(self, headers):
        from base64 import b64decode

        (basic, _, encoded) = headers.get('Authorization').partition(' ')
        assert basic == 'Basic', 'Only basic authentication supported'

        encodedByteString = encoded.encode()
        decodedBytes = b64decode(encodedByteString)
        decodedString = decodedBytes.decode()
        (username, _, password) = decodedString.partition(':')

        if username == serverUser and password == serverPass:
            return True

        return False
    
        
        
def convert_to_json_obj(obj):

    jsons = json.dumps(obj)

    return json.loads(jsons)
    
        
def server_thread():

    from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

    host = "127.0.0.1"
    port = int(serverPort)
    #http://user:pass@127.0.0.1:12345
    server = SimpleJSONRPCServer((host, port), requestHandler=SleuthSimpleJSONRPCRequestHandler, logRequests=True)
    server.register_function(handleRequest, 'sendPost')

    server.serve_forever()


def parseHack(string):

    startIndex = string.find('{"result"')
    startIndex = startIndex + 10
    
    endIndex = string.find(',"error"')
    sub = string[startIndex:endIndex]
    obj = json.loads(sub)
    
    return obj

    
def handleRequest(**req):

    print req
    receivedParams = req
    plugin = receivedParams['plugin']
    
    retObj = retVal()
    retObj.retbool = True
    retObj.retstat = "alive"

    
    if plugin == "nxt":

        params = {}

        for key in receivedParams:
            if key == "plugin":
                continue
            params[key] = receivedParams[key]

        r = requests.post(nxturl, data=params)
        ret = r.json()

        retObj.retbool = True
        retObj.retstat = "alive"
        retObj.retval = ret
        
    elif plugin == "InstantDEX":

        receivedParamsString = json.dumps(receivedParams, separators=(',', ':'))

        headers = {}
        headers['Authorization'] = b'Basic ' + authPair
        headers['Content-Type'] = "application/json"

        params = {}
        params['id'] = "777"*100
        params['method'] = "SuperNET"
        params['params'] = [receivedParamsString]
        params = json.dumps(params, separators=(',', ':'))
    
        r = requests.post(btcdurl, data=params, headers=headers)
    
        ret = r.text
        parsed = parseHack(ret)

        retObj.retbool = True
        retObj.retstat = "alive"
        retObj.retval = parsed


    retObj.retval = convert_to_json_obj(retObj.retval)


    return retObj

    
if __name__ == '__main__':
    

    server_thread()
	
