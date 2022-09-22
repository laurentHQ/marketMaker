# encoding: UTF-8

import json
import shelve
from collections import OrderedDict

from pymongo import MongoClient
from pymongo. errors import ConnectionFailure

import sys
sys. path. append('.')
sys. path. append('..')
from common. vtFunction import *
from common. eventEngine import *
from gateway. vtGateway import *
from common. vtFunction import loadMongoSetting

# from ctaAlgo.ctaEngine import CtaEngine
from drEngine import DrEngine
# from riskManager.rmEngine import RmEngine


########################################################################
class MainEngine(object):
	"""Main Engine"""

	# ----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""

		def print_log(event):
			log = event. dict_['data']
			print (':'. join([log. logTime, log. logContent]))

		def print_classofclass(event):
			class_data = event. dict_['data']. __dict__
			print (json. dumps(class_data, encoding="UTF-8", ensure_ascii=False))

		# Create an event engine
		self. eventEngine = EventEngine2()
		# self.eventEngine.register(EVENT_LOG, print_log)
		# self.eventEngine.register(EVENT_DATARECORDER_LOG, print_log)
		# self.eventEngine.register(EVENT_ACCOUNT, print_classofclass)
		# self.eventEngine.register(EVENT_POSITION, print_classofclass)
		self. eventEngine. start()

		# Create a data engine
		# self.dataEngine = DataEngine(self.eventEngine)

		# MongoDB database related
		self. dbClient = None # MongoDB client object

		# Call the initialization functions one by one
		self. initGateway()
		
		#self._loadSetting()

		# Extension modules
		# self.ctaEngine = CtaEngine(self, self.eventEngine)
		self. drEngine = DrEngine(self, self. eventEngine)
		# self.rmEngine = RmEngine(self, self.eventEngine)

	# ----------------------------------------------------------------------
	def initGateway(self):
		"""Initialize Interface Object"""
		# The dictionary used to hold the interface object
		self. gatewayDict = OrderedDict()
		
		try:
			from okcoinGateway import OkcoinGateway
			self. addGateway(OkcoinGateway, 'OKCOIN')
			self. gatewayDict['OKCOIN']. setQryEnabled(False)
		except Exception as e:
			print (e)
			
		try:
			from btccGateway import BtccGateway
			self. addGateway(BtccGateway, 'BTCC')
			self. gatewayDict['BTCC']. setQryEnabled(False)
		except Exception, e:
			print e

		try:
			from huobiGateway import HuobiGateway
			self. addGateway(HuobiGateway, 'HUOBI')
			self. gatewayDict['HUOBI']. setQryEnabled(False)
		except Exception, e:
			print e

		try:
			from huobiGateway import HuobiETHGateway
			self. addGateway(HuobiETHGateway, 'HUOBIETH')
			self. gatewayDict['HUOBIETH']. setQryEnabled(False)
		except Exception, e:
			print e


	# DR_setting.json read which gateway to subscribe to which contract
	def _loadSetting(self):
		self. gatewaySymbolsDict = {}
		path = settingFileName = getRootPath() + '/cfg/' + 'DR_setting.json'
		with open(path) as f:
			drSetting = json. load(f)
			for gatewayName in self. gatewayDict. keys():
				if gatewayName in drSetting:
					gatewaySymbolsDict[gatewayName] = drSetting[gatewayName]
					
	# ----------------------------------------------------------------------
	# create separate objects from each gateway first
	def addGateway(self, gateway, gatewayName=None):
		"""Create interface"""
		self. gatewayDict[gatewayName] = gateway(self. eventEngine, gatewayName)

	# ----------------------------------------------------------------------
	def connect(self, gatewayName):
		"""Connect to a specific name of the interface"""
		if gatewayName in self. gatewayDict:
			gateway = self. gatewayDict[gatewayName]
			gateway. connect()
		else:
			self. writeLog(u' interface does not exist: %s' %  gatewayName)

	# ----------------------------------------------------------------------
	def subscribe(self, subscribeReq, gatewayName):
		"""Subscribe to quotes for a particular interface"""
		if gatewayName in self. gatewayDict:
			gateway = self. gatewayDict[gatewayName]
			gateway. subscribe(subscribeReq)
		else:
			self. writeLog(u' interface does not exist: %s' %  gatewayName)



	def sendOrder(self, orderReq, gatewayName):
		"""Billing a specific interface"""
		# If the risk control check fails, no order will be issued
		if not self. rmEngine. checkRisk(orderReq):
			return ''

		if gatewayName in self. gatewayDict:
			gateway = self. gatewayDict[gatewayName]
			return gateway. sendOrder(orderReq)
		else:
			self. writeLog(u' interface does not exist: %s' %  gatewayName)

			# ----------------------------------------------------------------------

	def cancelOrder(self, cancelOrderReq, gatewayName):
		"""Cancel order for specific interface"""
		if gatewayName in self. gatewayDict:
			gateway = self. gatewayDict[gatewayName]
			gateway. cancelOrder(cancelOrderReq)
		else:
			self. writeLog(u' interface does not exist: %s' %  gatewayName)

			# ----------------------------------------------------------------------

	def qryAccont(self, gatewayName):
		"""Query accounts for a specific interface"""
		if gatewayName in self. gatewayDict:
			gateway = self. gatewayDict[gatewayName]
			gateway. qryAccount()
		else:
			self. writeLog(u' interface does not exist: %s' %  gatewayName)

			# ----------------------------------------------------------------------

	def qryPosition(self, gatewayName):
		"""Query positions for a particular interface"""
		if gatewayName in self. gatewayDict:
			gateway = self. gatewayDict[gatewayName]
			gateway. qryPosition()
		else:
			self. writeLog(u' interface does not exist: %s' %  gatewayName)

			# ----------------------------------------------------------------------

	def exit(self):
		"""Call before exiting the program to ensure a normal exit"""
		# Safely shut down all interfaces
		for gateway in self. gatewayDict. values():
			gateway. close()

		# Stop the event engine
		self. eventEngine. stop()

		# Stop the data logging engine
		self. drEngine. stop()

		# Save the contract data in the data engine to the hard disk
		self. dataEngine. saveContracts()

	# ----------------------------------------------------------------------
	def writeLog(self, content):
		"""Fast Log Event"""
		log = VtLogData()
		log. logContent = content
		event = Event(type_=EVENT_LOG)
		event. dict_['data'] = log
		self. eventEngine. put(event)

		# ----------------------------------------------------------------------

	def dbConnect(self):
		"""Connect to MongoDB database"""
		if not self. dbClient:
			# Read MongoDB settings

			host, port = loadMongoSetting()
			try:
				# Set the timeout for MongoDB operations to 0.5 seconds
				self. dbClient = MongoClient(host, port, serverSelectionTimeoutMS=500)

				# Call server_info query the server status to prevent the server from abnormally connecting successfully
				self. dbClient. server_info()

				self. writeLog(u'MongoDB connection successful')
			except ConnectionFailure:
				self. writeLog(u'MongoDB connection failed')

	# ----------------------------------------------------------------------
	def dbInsert(self, dbName, collectionName, d):
		"""Insert data into MongoDB, d is specific data"""
		if self. dbClient:
			db = self. dbClient[dbName]
			collection = db[collectionName]
			collection. insert(d)


	# ----------------------------------------------------------------------
	def dbQuery(self, dbName, collectionName, d):
		"""Reading data from MongoDB, d is the query requirement, returning a pointer to the database query """
		if self. dbClient:
			db = self. dbClient[dbName]
			collection = db[collectionName]
			cursor = collection. find(d)
			return cursor
		else:
			return None

	# ----------------------------------------------------------------------
	def getContract(self, vtSymbol):
		"""Query Contract"""
		return self. dataEngine. getContract(vtSymbol)

	# ----------------------------------------------------------------------
	def getAllContracts(self):
		"""Query all contracts (return list)"""
		return self. dataEngine. getAllContracts()

	# ----------------------------------------------------------------------
	def getOrder(self, vtOrderID):
		"""Query Delegation"""
		return self. dataEngine. getOrder(vtOrderID)

	# ----------------------------------------------------------------------
	def getAllWorkingOrders(self):
		"""Query all active delegates (returned list)"""
		return self. dataEngine. getAllWorkingOrders()

	
########################################################################
class DataEngine(object):
	"""Data Engine"
	contractFileName = 'ContractData.vt'

	# ----------------------------------------------------------------------
	def __init__(self, eventEngine):
		"""Constructor"""
		self. eventEngine = eventEngine

		# A dictionary to save the contract details
		self. contractDict = {}

		# A dictionary that holds delegate data
		self. orderDict = {}

		# Dictionary to save activity delegation data (i.e. revoked)
		self. workingOrderDict = {}

		# Read the contract data saved on the hard disk
		self. loadContracts()

		# Register event listening
		self. registerEvent()

	# ----------------------------------------------------------------------
	def updateContract(self, event):
		"""Update contract data"""
		contract = event. dict_['data']
		self. contractDict[contract. vtSymbol] = contract
		self. contractDict[contract. symbol] = contract # Using a regular code (excluding exchanges) may result in duplication

	# ----------------------------------------------------------------------
	def getContract(self, vtSymbol):
		"""Query contract object"""
		try:
			return self. contractDict[vtSymbol]
		except KeyError:
			return None

	# ----------------------------------------------------------------------
	def getAllContracts(self):
		"""Query all contract objects (return list)"""
		return self. contractDict. values()

	# ----------------------------------------------------------------------
	def saveContracts(self):
		"""Save all contract objects to the hard disk"""
		f = shelve. open(self. contractFileName)
		f['data'] = self. contractDict
		f. close()

	# ----------------------------------------------------------------------
	def loadContracts(self):
		"""Read contract object from hard disk"""
		f = shelve. open(self. contractFileName)
		if 'data' in f:
			d = f['data']
			for key, value in d. items():
				self. contractDict[key] = value
		f. close()

	# ----------------------------------------------------------------------
	def updateOrder(self, event):
		"Update delegate data"""
		order = event. dict_['data']
		self. orderDict[order. vtOrderID] = order

		# If the status of the order is fully filled or cancelled, it needs to be removed from workingOrderDict
		if order. status == STATUS_ALLTRADED or order. status == STATUS_CANCELLED:
			if order. vtOrderID in self. workingOrderDict:
				del self. workingOrderDict[order. vtOrderID]
		# Otherwise, the data in the dictionary is updated
		else:
			self. workingOrderDict[order. vtOrderID] = order

	# ----------------------------------------------------------------------
	def getOrder(self, vtOrderID):
		"""Query Delegation"""
		try:
			return self. orderDict[vtOrderID]
		except KeyError:
			return None

	# ----------------------------------------------------------------------
	def getAllWorkingOrders(self):
		"""Query all active delegates (return list)"""
		return self. workingOrderDict. values()

	# ----------------------------------------------------------------------
	def registerEvent(self):
		"""Register Event Listening"""
		self. eventEngine. register(EVENT_CONTRACT, self. updateContract)
		self. eventEngine. register(EVENT_ORDER, self. updateOrder)



if __name__ == '__main__':

	from PyQt4 import QtCore
	import sys

	app = QtCore. QCoreApplication(sys. argv)

	me = MainEngine()

	me. dbConnect()


	for i in sys. argv[1:]:
		print "Connecting Gateway: %s ......" %i
		me. connect(str(i))

	sys. exit(app. exec_())
