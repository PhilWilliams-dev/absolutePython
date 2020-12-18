class absolutePython:
    import hashlib as __hashlib
    import hmac as __hmac
    import requests as __requests
    import datetime as __datetime
    import json as __json
    import time as __time
    from collections import OrderedDict

    def __init__(self, apiToken, apiSecret, apiHost="api.absolute.com"):
        self.__apiToken=apiToken
        self.__apiSecret=apiSecret
        self.__apiHost=apiHost

    @staticmethod
    def __makeFreezeBody(uidList, passCode, message, emailList, messageName, requestName):
        body = '{"name" : "'+ requestName +'","message" : "'+ message +'","messageName" : "'+ messageName +'","deviceUids" : "","freezeDefinition" : {"deviceFreezeType" : "OnDemand"},"passcodeDefinition" : {"option" : "UserDefined","passcode" : ""},"notificationEmails": ""}'
        bodyObject = absolutePython.__json.loads(body, object_pairs_hook=absolutePython.OrderedDict)
        bodyObject['deviceUids'] = uidList
        bodyObject['passcodeDefinition']['passcode'] = passCode
        bodyObject['notificationEmails'] = emailList
        #return '{"name":"Device Freeze Name","message":"You have a geo-location event","messageName":"ServiceNow Freeze","freezeDefinition":{"deviceFreezeType":"OnDemand"},"deviceUids":["cdf975c0-af00-4a6e-88da-0cf4ce82ec63"],"passcodeDefinition":{"option":"UserDefined","passcode":"1234"},"notificationEmails":["demo2dlevine@absolute.com"]}'
        return absolutePython.__json.dumps(bodyObject, sort_keys=False)

    @staticmethod
    def __makeUnFreezeBody(uidList):
        body = '{"deviceUids" : "", "unfreeze" : "true"}'
        bodyObject = absolutePython.__json.loads(body, object_pairs_hook=absolutePython.OrderedDict)
        bodyObject['deviceUids'] = uidList
        return absolutePython.__json.dumps(bodyObject, sort_keys=False)

    @staticmethod
    def __makeUnerollBody(uidList):
        body = '[]'
        bodyObject = absolutePython.__json.loads(body)
        for i in uidList:
            newitem = '{"deviceUid" : "' + i +'"}'
            newItemObject = absolutePython.__json.loads(newitem)
            bodyObject.append(newItemObject)
        return absolutePython.__json.dumps(bodyObject, sort_keys=False)

    @staticmethod
    def __urlEncode(value):
        #Built in URL encode does not work well with the Absolute API so specific chars aare encoded for the time being
        value = value.replace("$", "%24")
        value = value.replace(" ", "%20")
        value = value.replace("'", "%27")
        value = value.replace("(", "%28")
        value = value.replace(")", "%29")
        value = value.replace(",", "%2C")
        #value = value.replace("=", "%3D")
        value = value.replace(":", "%3A")
        return value

    def __makeApiRequest(self, path, query='', method='GET', body=''):
        #vars
        httpRequestMethod = method.upper()
        apiHost = self.__apiHost
        contentType = 'application/json;charset=utf-8'
        date = self.__datetime.datetime.utcnow()
        date_yyyyMMdd = date.strftime("%Y") + date.strftime("%m") + date.strftime("%d")
        date_HHmmss = date.strftime("%H") + date.strftime("%M") + date.strftime("%S")
        xAbsDate = date_yyyyMMdd + "T" + date_HHmmss + "Z"
        #xAbsDate = "20171122T162253Z"

        #Create a canonical request
        canonicalRequest = ""
        canonicalRequest += httpRequestMethod.upper() + "\n"
        canonicalRequest += path + "\n"
        canonicalRequest += self.__urlEncode(query) + "\n"
        canonicalRequest += "host:" + apiHost + "\n"
        canonicalRequest += "content-type:" + contentType + "\n"
        canonicalRequest += "x-abs-date:" + xAbsDate + "\n"    
        canonicalRequest += self.__hashlib.sha256(body.encode("UTF-8")).hexdigest()

        #Create Signing String
        reqHash = self.__hashlib.sha256(canonicalRequest.encode("UTF-8")).hexdigest()
        if(apiHost == 'api.us.absolute.com'):
            credentialScope = str(date_yyyyMMdd) + '/usdc/abs1'
        elif(apiHost == 'api.eu.absolute.com'):
            credentialScope = str(date_yyyyMMdd) + '/eudc/abs1'
        else:
            credentialScope = str(date_yyyyMMdd) + '/cadc/abs1'
        stringToSign = "ABS1-HMAC-SHA-256" + "\n" + xAbsDate + "\n" + credentialScope + "\n" + reqHash

        #Create Signing Key
        ksecret = ("ABS1" + self.__apiSecret).encode("UTF-8")
        kdate = self.__hmac.new(ksecret, date_yyyyMMdd.encode("UTF-8"), self.__hashlib.sha256).digest()
        signingKey = self.__hmac.new(kdate, "abs1_request".encode("UTF-8"), self.__hashlib.sha256).digest()

        #Create Signature
        signature = self.__hmac.new(signingKey, stringToSign.encode("UTF-8"), self.__hashlib.sha256).hexdigest()

        #Create Headers
        credentials = self.__apiToken + '/' + credentialScope
        headers = {}
        headers['host'] = apiHost
        headers['Content-Type'] = contentType
        headers['x-abs-date'] = xAbsDate
        headers['Authorization'] = "ABS1-HMAC-SHA-256 Credential=" + credentials + ", SignedHeaders=host;content-type;x-abs-date, Signature=" + signature

        #Make Request
        url = "https://" + apiHost + path + "?" + self.__urlEncode(query)
        print("URL we are using is: " + url)
        try:
            if(httpRequestMethod == 'GET'):
                response = self.__requests.get(url, headers=headers)
            elif(httpRequestMethod == 'POST'):
                response =self. __requests.post(url, data=body, headers=headers)
            elif(httpRequestMethod == 'PUT'):
                response = self.__requests.put(url, data=body, headers=headers)
            #elif(httpRequestMethod == 'DELETE'):
                #response = __requests.get(url, headers=headers)
            else:
                raise Exception('Invalid HTTP Method Used')
            
        
        except self.__requests.exceptions.ConnectionError as conError:
            raise Exception('Connection error, possibly incorrect api host')

        except self.__requests.exceptions.HTTPError as conError:
            #Something Wrong with the request
            raise Exception('Something Wrong with the request, HTTP: ' + str(conError.errno))
            
        except self.__requests.exceptions.InvalidURL as conError:
            #Something wrong with the url or network possibly
            raise Exception("Something wrong with the url or network possibly ")

        except:
            raise Exception("Something went wrong")
        
        else:
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 201:
                return response.json()
            elif response.status_code == 204:
                return "Ok"
            else:
                return response.status_code

    def __getDevicesByESN(self, esnList:list):
        filter = '$filter='
        for e in esnList:
            filter += "esn eq '" + e + "' or "
        filter = filter[0:len(filter)-4]
        return self.__makeApiRequest("/v2/reporting/devices", filter , "GET", "")

    def __getDevicesBySerial(self, serialList:list):
        filter = '$filter='
        for e in serialList:
            filter += "serial eq '" + e + "' or "
        filter = filter[0:len(filter)-4]
        return self.__makeApiRequest("/v2/reporting/devices", filter , "GET", "")

    def __getDeviceUIDfromESN(self, esn:str):
        d = self.__getDevicesByESN([esn])
        return str(d[0]['id'])

    def __getDeviceUIDfromSerial(self, serial:str):
        d = self.__getDevicesBySerial([serial])
        return str(d[0]['id'])

    def getActiveDevices(self, fieldList = []):
        if not isinstance(fieldList, list):
            internalFieldList = str.split(fieldList, ',')
        else:
            internalFieldList = fieldList

        try:
            batchSize = 300
            top = batchSize
            skip = 0

            requestFilter = "$filter=agentStatus eq 'A'"
            requestSelect = "$select=esn,lastConnectedUtc,domain,username,systemName,serial,systemModel,systemManufacturer"

            if(len(internalFieldList) > 0):
                for p in internalFieldList:
                    requestSelect += "," + p

            requestQuery = requestFilter + "&" + requestSelect + "&$skip=" + str(skip) + "&$top=" + str(top)

            devices = self.__makeApiRequest("/v2/reporting/devices", requestQuery, "GET", "")

            fetchedCount = len(devices)

            while fetchedCount == batchSize:
                skip = skip + batchSize
                batchDevices =  self.__makeApiRequest("/v2/reporting/devices", requestFilter + "&" + requestSelect + "&$skip=" + str(skip) + "&$top=" + str(top), "GET", "")
                devices += batchDevices
                fetchedCount = len(batchDevices) 

        except Exception as e:
            print(e)
        else:
            return devices

    def getDevice(self, deviceList, SerialNumbers = False):
        if len(deviceList) == 0:
            raise Exception("No devices were specified")

        if not isinstance(deviceList, list):
            internalDeviceList = str.split(deviceList, ',')
        else:
            internalDeviceList = deviceList

        try:
            if SerialNumbers:
                response = self.__getDevicesBySerial(internalDeviceList)
            else:
                response = self.__getDevicesByESN(internalDeviceList)

        except Exception as e:
            print(e)
        else:
            return response

    def invokeFreezeDevice(self, deviceList, requestName, passCode, message, notifyEmailList, serialNumbers = False, messageName = "This is a freeze Mesage"):
        
        if len(deviceList) == 0:
            raise Exception("No devices were specified")

        if not isinstance(deviceList, list):
            internalDeviceList = str.split(deviceList, ',')
        else:
            internalDeviceList = deviceList

        if not isinstance(notifyEmailList, list):
            internalnotifyEmailList = str.split(notifyEmailList, ',')
        else:
            internalnotifyEmailList = notifyEmailList

        if not isinstance(passCode, int):
            raise Exception("Passcode must be a number")

        if len(str(passCode)) > 8 or len(str(passCode)) < 4:
            raise Exception("Passcode must be between 4 and 8 numbers in lengeth")

        uidList = []
        if serialNumbers:
            for i in internalDeviceList:
                uidList.append(self.__getDeviceUIDfromSerial(i))
        else:
            for i in internalDeviceList:
                uidList.append(self.__getDeviceUIDfromESN(i))
            
        
        body = absolutePython.__makeFreezeBody(uidList,passCode, message, internalnotifyEmailList, messageName, requestName)

        try:
            response = self.__makeApiRequest('/v2/device-freeze/requests','','POST', body)
        
        except Exception as e:
            print(e)
        else:
            return response

    def invokeUnFreezeDevice(self, deviceList, serialNumbers = False):
        
        if len(deviceList) == 0:
            raise Exception("No devices were specified")

        if not isinstance(deviceList, list):
            internalDeviceList = str.split(deviceList, ',')
        else:
            internalDeviceList = deviceList

        uidList = []
        if serialNumbers:
            for i in internalDeviceList:
                uidList.append(self.__getDeviceUIDfromSerial(i))
        else:
            for i in internalDeviceList:
                uidList.append(self.__getDeviceUIDfromESN(i))
            
        
        body = absolutePython.__makeUnFreezeBody(uidList)

        try:
            response = self.__makeApiRequest('/v2/device-freeze/requests','','PUT', body)
        
        except Exception as e:
            print(e)
        else:
            return response

    def invokeUnEnrollDevice(self, deviceList, serialNumbers = False):
       
        if len(deviceList) == 0:
            raise Exception("No devices were specified")

        if not isinstance(deviceList, list):
            internalDeviceList = str.split(deviceList, ',')
        else:
            internalDeviceList = deviceList

        uidList = []
        if serialNumbers:
            for i in internalDeviceList:
                uidList.append(self.__getDeviceUIDfromSerial(i))
        else:
            for i in internalDeviceList:
                uidList.append(self.__getDeviceUIDfromESN(i))
            
        
        body = absolutePython.__makeUnerollBody(uidList)

        try:
            response = self.__makeApiRequest('/v2/device-unenrollment/unenroll','','POST', body)
        
        except Exception as e:
            print(e)
        else:
            return response
