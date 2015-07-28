import SimpleXMLRPCServer
import json
import requests
import base64


url = "http://127.0.0.1:14632"
nxturl = "http://127.0.0.1:7876/nxt?"
pair = "user:pass"
authPair = b'Basic ' + base64.b64encode(pair)

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
        self.send_header('Access-Control-Allow-Headers', "content-type, accept")
        self.end_headers()
        self.wfile.flush()

    def do_POST(self):
        if not self.is_rpc_path_valid():
            self.report_404()
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
        
        
        
def convert_to_json_obj(obj):

    jsons = json.dumps(obj)

    return json.loads(jsons)
    
        
def server_thread():

    from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
    host = "localhost"
    port = 12345
    server = SimpleJSONRPCServer(( host, port), requestHandler=SleuthSimpleJSONRPCRequestHandler, logRequests=True)
    server.register_function(handleRequest, 'sendPost')

    server.serve_forever()



def parseHack(str):
    startIndex = str.find('{"result"')
    startIndex = startIndex + 10
    
    endIndex = str.find(',"error"')
    sub = str[startIndex:endIndex]
    obj = json.loads(sub)
    
    return obj

    
def handleRequest(**req):

    print req
    receivedParams = req
    plugin = receivedParams['plugin']
    
    retObj = retVal()
    retObj.retbool = True
    retObj.retstat = "alive"
    #retObj.retval = {}


    
    if plugin == "nxt":
        #headers = {}
        #headers['Content-Type'] = "application/json"

        params = {}
        for key in receivedParams:
            if key == "plugin":
                continue
            params[key] = receivedParams[key]
        #params = json.dumps(params)
        #print params
        r = requests.post(nxturl, data=params)
        ret = r.json()
        retObj.retbool = True
        retObj.retstat = "alive"
        retObj.retval = ret
        
    elif plugin == "InstantDEX":

        headers = {}
        headers['Authorization'] = authPair
        #headers['User-Agent'] = "AuthServiceProxy/0.1"
        #headers['Content-Type'] = "application/x-www-form-urlencoded"
        headers['Content-Type'] = "application/json"

        receivedParamsString = json.dumps(receivedParams, separators=(',', ':'))
        params = {}
        params['id'] = "777"*100
        params['method'] = "SuperNET"
        params['params'] = [receivedParamsString]
        params = json.dumps(params, separators=(',', ':'))
    
        r = requests.post(url, data=params, headers=headers)
        #print r
    
        ret = r.text
        parsed = parseHack(ret)
        
        #print r.text
    
        retObj.retbool = True
        retObj.retstat = "alive"
        retObj.retval = parsed

    retObj.retval = convert_to_json_obj(retObj.retval)
    return retObj
    
if __name__ == '__main__':
    

    
    server_thread()
	
