import hashlib as __hashlib
import hmac as __hmac
import requests as __requests
#from urllib import request as __request
#from urllib import parse as __parse
import datetime as __datetime
import json as __json
import time as __time

#Helpers
def __epocMsToDateTime(timeStamp):
    #Converts unix epoc in milliseconds to date time
    return __time.strftime('%Y-%m-%d %H:%M:%S', __time.localtime(timeStamp / 1000))

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
def __makeApiRequest(authObject, path, query='', method='GET', body=''):
    
    def __urlEncode(value):
        #Built in URL encode does not work well with the Absolute API so specific chars aare encoded for the time being
        value = value.replace("$", "%24")
        value = value.replace(" ", "%20")
        value = value.replace("'", "%27")
        value = value.replace("(", "%28")
        value = value.replace(")", "%29")
        value = value.replace(",", "%2C")
        return value

    #vars
    httpRequestMethod = method.upper()
    apiHost = authObject.host
    contentType = 'application/json'
    date = __datetime.datetime.utcnow()
    date_yyyyMMdd = date.strftime("%Y") + date.strftime("%m") + date.strftime("%d")
    date_HHmmss = date.strftime("%H") + date.strftime("%M") + date.strftime("%S")
    xAbsDate = date_yyyyMMdd + "T" + date_HHmmss + "Z"

    #Create a canonical request
    canonicalRequest = ""
    canonicalRequest += httpRequestMethod.upper() + "\n"
    canonicalRequest += path + "\n"
    canonicalRequest += __urlEncode(query) + "\n"
    canonicalRequest += "host:" + apiHost + "\n"
    canonicalRequest += "content-type:" + contentType + "\n"
    canonicalRequest += "x-abs-date:" + xAbsDate + "\n"    
    canonicalRequest += __hashlib.sha256(body.encode("UTF-8")).hexdigest()

    #Create Signing String
    reqHash = __hashlib.sha256(canonicalRequest.encode("UTF-8")).hexdigest()
    if(apiHost == 'api.us.absolute.com'):
        credentialScope = str(date_yyyyMMdd) + '/usdc/abs1'
    elif(apiHost == 'api.eu.absolute.com'):
        credentialScope = str(date_yyyyMMdd) + '/eudc/abs1'
    else:
        credentialScope = str(date_yyyyMMdd) + '/cadc/abs1'
    stringToSign = "ABS1-HMAC-SHA-256" + "\n" + xAbsDate + "\n" + credentialScope + "\n" + reqHash

    #Create Signing Key
    ksecret = ("ABS1" + authObject.secret).encode("UTF-8")
    kdate = __hmac.new(ksecret, date_yyyyMMdd.encode("UTF-8"), __hashlib.sha256).digest()
    signingKey = __hmac.new(kdate, "abs1_request".encode("UTF-8"), __hashlib.sha256).digest()

    #Create Signature
    signature = __hmac.new(signingKey, stringToSign.encode("UTF-8"), __hashlib.sha256).hexdigest()

    #Create Headers
    credentials = authObject.token + '/' + credentialScope
    headers = {}
    headers['host'] = apiHost
    headers['Content-Type'] = contentType
    headers['x-abs-date'] = xAbsDate
    headers['Authorization'] = "ABS1-HMAC-SHA-256 Credential=" + credentials + ", SignedHeaders=host;content-type;x-abs-date, Signature=" + signature

    #Make Request
    url = "https://" + apiHost + path + "?" + __urlEncode(query)
    
    try:
        if(httpRequestMethod == 'GET'):
            response = __requests.get(url, headers=headers)
        elif(httpRequestMethod == 'POST'):
            response = __requests.post(url, data=body, headers=headers)
        elif(httpRequestMethod == 'PUT'):
            response = __requests.put(url, data=body, headers=headers)
        #elif(httpRequestMethod == 'DELETE'):
            #response = __requests.get(url, headers=headers)
        else:
           print('Invalid HTTP Method Used')
           exit(3)

    except response.error.HTTPError as e:
        #Something Wrong with the request
        print('Something Wrong with the request, HTTP: ' + str(e.code))
        exit(1)
    except response.error.URLError as e:
        #Something wrong with the url or network possibly
        print("Something wrong with the url or network possibly")
        exit(2)
    else:
        devices = response.json()
        return devices

#Api Requests
def getDevicesByESN(authObject, esnList:list):
    filter = '$filter='
    for e in esnList:
        filter += "esn eq '" + e + "' or "
    filter = filter[0:len(filter)-4]
    return __makeApiRequest(authObject, "/v2/reporting/devices", filter , "GET", "")

def getDevicesBySerial(authObject, serialList:list):
    filter = '$filter='
    for e in serialList:
        filter += "serial eq '" + e + "' or "
    filter = filter[0:len(filter)-4]
    return __makeApiRequest(authObject, "/v2/reporting/devices", filter , "GET", "")

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

    devices = __makeApiRequest(authObject, "/v2/reporting/devices", requestQuery, "GET", "")

    fetchedCount = len(devices)

    while fetchedCount == batchSize:
        skip = skip + batchSize
        batchDevices =  __makeApiRequest(authObject, "/v2/reporting/devices", requestFilter + "&" + requestSelect + "&$skip=" + str(skip) + "&$top=" + str(top), "GET", "")
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

#auth = SetAbsoluteAuth('4e2d1917-ea93-4c24-8b76-d8cc1ea8145d','4279d3cf-6853-4fee-813b-a4f2d699d32e')

