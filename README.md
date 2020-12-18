#absolutePython

**Python Version**
This module was built and tested against Python 3.5

**Installation**

Copy the absolutePython folder to your python modules folder, for example %appdata%/programs/python/python35/lib/site-packages on windows.
At the start of your script use 'from absolute import absolutePython' without the quotes to add the module.


**Authentication**

Create an object that will contain the api authentication and make requests by adding the following to your script.  Replace the <tokens> with your api details

abtApi = absolutePython.absolutePython('<apiToken>','<apiSecret>')  Optional apiHost='' to specifiy non CADC data center

once you have created your object you can make the following calls using that object, for example abtAPI.getActiveDevices


**Commands Available**


**.getDevice** - Gets the full api output for that device, max 100 devices per call.

	Parameters:

	DeviceList -Comma seperated list of device ESN's or Serial numbers used to find the devices
	SerialNumbers=True -Specifies if the list of devices are serial numbers (default is ESN's) Can be ommited if using ESN
	
	Example: abtApi.getDevice('abc123,def456', SerialNumbers=True) - Will get the data for 2 devices with these serial numbers


**.getActiveDevices** - gets basic info for all active devices.  By defult only collects id, ESN, SystemName, systemManufacturer, systemodel, serial, username, domain, lastConnected UTC

	Parameters:
	
	-FieldList -Comma seperated list of additional fields to collect when the fetch is executed.

	Example: abtApi.getActiveDevices('os,bios') - Will get all devices with OS and BIOS data in addition to the default fields


**.invokeFreezeDevice** - Causes a device freeze

	Parameters:

	DeviceList -Comma seperated list of device ESN's or Serial numbers used to find the devices
	SerialNumbers=True -Specifies if the list of devices are serial numbers (default is ESN's) Can be ommited if using ESN
	RequestName -Name for the Request in the console
	Passcode - 4 to 8 digit unlock pin
	MessageName -(Optional) Name of the Message
	Message -message to disply on the users screen when frozen
	NotifyeMails -list of email addresses to be sent status updates of the freeze
	
	Example: abtApi.invokeFreezeDevice('75752633XHXXXXXXX',"Freeze From Python",1234,"This was Frozen from python","me@acme.net"))


**.invokeUnFreezeDevice** - Unfreezes a frozen Device

	Parameters:

	DeviceList -Comma seperated list of device ESN's or Serial numbers used to find the devices
	SerialNumbers=True -Specifies if the list of devices are serial numbers (default is ESN's) Can be ommited if using ESN

	Example: abtApi.invokeUnFreezeDevice('75752633XHXXXXXXX')

**.invokeUnEnrollDevice** - Removes a device permanantly from the Absolute system.

	Parameters:

	DeviceList -Comma seperated list of device ESN's or Serial numbers used to find the devices
	SerialNumbers=True -Specifies if the list of devices are serial numbers (default is ESN's) Can be ommited if using ESN

	Example: abtApi.invokeUnEnrollDevice('75752633XHXXXXXXX')