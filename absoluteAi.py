import hashlib
import hmac
import urllib.parse
import urllib.request
import urllib
import datetime
import json
import time

#Authentication
def _urlEncode(value):
    value = value.replace("$", "%24")
    value = value.replace(" ", "%20")
    value = value.replace("'", "%27")
    value = value.replace("(", "%28")
    value = value.replace(")", "%29")
    value = value.replace(",", "%2C")
    return value

def _getDate():
    cd = datetime.datetime.utcnow()
    return cd.strftime("%Y") + cd.strftime("%m") + cd.strftime("%d")

def _getTime():
    #Retards the time by 5 seconds to account for a local clock running a little fast
    cd = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    return cd.strftime("%H") + cd.strftime("%M") + cd.strftime("%S")

def _getAbtDateTime():
    return _getDate() + "T" + _getTime() + "Z"

def _getRequest(method, resourse, query, host, abtDT, body):
    request = ""
    request += method.upper() + "\n"
    request += resourse + "\n"
    request += _urlEncode(query) + "\n"
    request += "host:" + host + "\n"
    request += "content-type:application/json" + "\n"
    request += "x-abs-date:" + abtDT + "\n"    
    request += hashlib.sha256(body.encode("UTF-8")).hexdigest()
    
    return request

def _getSigningKey(secretKey, abtDate):
    ksecret = ("ABS1" + secretKey).encode("UTF-8")
    kdate = hmac.new(ksecret, abtDate.encode("UTF-8"), hashlib.sha256).digest()
    signingKey = hmac.new(kdate, "abs1_request".encode("UTF-8"), hashlib.sha256).digest()
    return signingKey

def _getAuthHeader(apiToken, apiSecret, abtDT, method, host, uri, query, body):
    abtDate = _getDate()
    abtDateTime = abtDT
    req = _getRequest(method, uri, query, host, abtDateTime, body)
    reqHash = hashlib.sha256(req.encode("UTF-8")).hexdigest()
    stringToSign = "ABS1-HMAC-SHA-256" + "\n" + abtDateTime + "\n" + abtDate + "/cadc/abs1" + "\n" + reqHash
    signingKey = _getSigningKey(apiSecret, abtDate)
    
    signature = hmac.new(signingKey, stringToSign.encode("UTF-8"), hashlib.sha256).hexdigest()
    header = "ABS1-HMAC-SHA-256 Credential=" + apiToken + "/" + abtDate + "/cadc/abs1, SignedHeaders=host;content-type;x-abs-date, Signature=" + signature
    return header

#Helpers
def _convertTime(timeStamp):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timeStamp / 1000))

#classes

class absoluteAuthData:
    def __init__(self, apiToken, apiSecret, apiHost):
        self.__apiToken=apiToken
        self.__apiSecret=apiSecret
        self.__apiHost=apiHost
    @property
    def token(self):
        return self.__apiToken
    @property
    def secret(self):
        return self.__apiSecret
    @property
    def host(self):
        return self.__apiHost

#Base Api Request
def makeApiRequest(authObject, path, query='', method='GET', body=''):
    
    apiSecret = authObject.secret
    apiToken = authObject.token
    host = authObject.host
                   
    abtDT = _getAbtDateTime()
    
    url = "https://" + host + path + "?" + _urlEncode(query)
    headers = {}
    headers['host'] = host
    headers['Content-Type'] = "application/json"
    headers['x-abs-date'] = abtDT
    headers['Authorization'] = _getAuthHeader(apiToken, apiSecret, abtDT, method, host, path, query, body)
    print(url)
    request = urllib.request.Request(url, headers=headers)
    
    try:
        response = urllib.request.urlopen(request)

    except urllib.error.HTTPError as e:
        #Something Wrong with the request
        print('Something Wrong with the request ' + str(e.code))
        #exit(1)
    except urllib.error.URLError as e:
        #Something wrong with the url or network possibly
        print("Something wrong with the url or network possibly")
        #exit(2)
    else:
        devices = json.loads(response.read())
        return devices

#Api Requests
def getDevicesByESN(authObject, esnList:list):
    filter = '$filter='
    for e in esnList:
        filter += "esn eq '" + e + "' or "
    filter = filter[0:len(filter)-4]
    return makeApiRequest(authObject, "/v2/reporting/devices", filter , "GET", "")

def getDevicesBySerial(authObject, serialList:list):
    filter = '$filter='
    for e in serialList:
        filter += "serial eq '" + e + "' or "
    filter = filter[0:len(filter)-4]
    return makeApiRequest(authObject, "/v2/reporting/devices", filter , "GET", "")

def getActiveDevices(authObject, additionalFields = []):
    batchSize = 300
    top = batchSize
    skip = 0

    requestFilter = "$filter=agentStatus eq 'A'"
    requestSelect = "$select=esn,lastConnectedUtc,domain,username,systemName,serial,systemModel,systemManufacturer"

    if(len(additionalFields) > 0):
        for p in additionalFields:
            requestSelect += "," + p

    requestQuery = requestFilter + "&" + requestSelect + "&$skip=" + str(skip) + "&$top=" + str(top)

    devices = makeApiRequest(authObject, "/v2/reporting/devices", requestQuery, "GET", "")

    fetchedCount = len(devices)

    while fetchedCount == batchSize:
        skip = skip + batchSize
        batchDevices =  makeApiRequest(authObject, "/v2/reporting/devices", requestFilter + "&" + requestSelect + "&$skip=" + str(skip) + "&$top=" + str(top), "GET", "")
        devices += batchDevices
        fetchedCount = len(batchDevices)      
    return devices

def getDeviceUIDfromESN(auth, esn:str):
    d = getDevicesByESN(auth, [esn])
    return str(d[0]['id'])

def getDeviceUIDfromSerial(auth, serial:str):
    d = getDevicesBySerial(auth, [serial])
    return str(d[0]['id'])
    

#Exposed

def SetAbsoluteAuth(apiToken, apiSecret, apiHost = 'api.absolute.com'):
    return absoluteAuthData(apiToken, apiSecret, apiHost)
