# encoding: UTF-8

'''
vn.okcoin's gateway access
Note:
1. Previously, only spot trading of USD and CNY was supported, and trading of futures contracts of USD was not supported
'''

import the
import json
from datetime import datetime
from copy import copy
from threading import Condition
from Queue import Queue
from threading import Thread

import sys
sys. path. append('..')
from api import vnokcoin
from common. vnlog import *
from vtGateway import *

# Price type mapping
priceTypeMap = {}
priceTypeMap['buy'] = (DIRECTION_LONG, PRICETYPE_LIMITPRICE)
priceTypeMap['buy_market'] = (DIRECTION_LONG, PRICETYPE_MARKETPRICE)
priceTypeMap['sell'] = (DIRECTION_SHORT, PRICETYPE_LIMITPRICE)
priceTypeMap['sell_market'] = (DIRECTION_SHORT, PRICETYPE_MARKETPRICE)
priceTypeMapReverse = {v: k for k, v in priceTypeMap. items()}

# Direction type mapping
directionMap = {}
directionMapReverse = {v: k for k, v in directionMap. items()}

# Delegate status imprint
statusMap = {}
statusMap[-1] = STATUS_CANCELLED
statusMap[0] = STATUS_NOTTRADED
statusMap[1] = STATUS_PARTTRADED
statusMap[2] = STATUS_ALLTRADED
statusMap[4] = STATUS_UNKNOWN

############################################
## Trading contract code
############################################

# USD
BTC_USD_SPOT = 'BTC_USD_SPOT'
BTC_USD_THISWEEK = 'BTC_USD_THISWEEK'
BTC_USD_NEXTWEEK = 'BTC_USD_NEXTWEEK'
BTC_USD_QUARTER = 'BTC_USD_QUARTER'

LTC_USD_SPOT = 'LTC_USD_SPOT'
LTC_USD_THISWEEK = 'LTC_USD_THISWEEK'
LTC_USD_NEXTWEEK = 'LTC_USD_NEXTWEEK'
LTC_USD_QUARTER = 'LTC_USD_QUARTER'

ETH_USD_SPOT = 'ETH_USD_SPOT'
ETH_USD_THISWEEK = 'ETH_USD_THISWEEK'
ETH_USD_NEXTWEEK = 'ETH_USD_NEXTWEEK'
ETH_USD_QUARTER = 'ETH_USD_QUARTER'

# CNY
# BTC_CNY_SPOT = 'BTC_CNY_SPOT'
# LTC_CNY_SPOT = 'LTC_CNY_SPOT'
# ETH_CNY_SPOT = 'ETH_CNY_SPOT'

# Printing dictionary
spotSymbolMap = {}
# spotSymbolMap['ltc_usd'] = LTC_USD_SPOT
# spotSymbolMap['btc_usd'] = BTC_USD_SPOT
# spotSymbolMap['eth_usd'] = ETH_USD_SPOT
spotSymbolMap[SYMBOL_BTC_CNY] = 'btc'
spotSymbolMap[SYMBOL_LTC_CNY] = 'ltc'
spotSymbolMap[SYMBOL_ETH_CNY] = 'eth'
spotSymbolMapReverse = {v: k for k, v in spotSymbolMap. items()}

############################################
## Channel and Symbol printing
############################################
channelSymbolMap = {}

# USD
channelSymbolMap['ok_sub_spotusd_btc_ticker'] = BTC_USD_SPOT
channelSymbolMap['ok_sub_spotusd_ltc_ticker'] = LTC_USD_SPOT
channelSymbolMap['ok_sub_spotusd_eth_ticker'] = ETH_USD_SPOT

channelSymbolMap['ok_sub_spotusd_btc_depth_20'] = BTC_USD_SPOT
channelSymbolMap['ok_sub_spotusd_ltc_depth_20'] = LTC_USD_SPOT
channelSymbolMap['ok_sub_spotusd_eth_depth_20'] = ETH_USD_SPOT

# CNY
channelSymbolMap['ok_sub_spotcny_btc_ticker'] = SYMBOL_BTC_CNY
channelSymbolMap['ok_sub_spotcny_ltc_ticker'] = SYMBOL_LTC_CNY
channelSymbolMap['ok_sub_spotcny_eth_ticker'] = SYMBOL_ETH_CNY

channelSymbolMap['ok_sub_spotcny_btc_depth_20'] = SYMBOL_BTC_CNY
channelSymbolMap['ok_sub_spotcny_ltc_depth_20'] = SYMBOL_LTC_CNY
channelSymbolMap['ok_sub_spotcny_eth_depth_20'] = SYMBOL_ETH_CNY



########################################################################
class OkcoinGateway(VtGateway):
	"""OkCoin interface"""

	# ----------------------------------------------------------------------
	def __init__(self, eventEngine, gatewayName='OKCOIN'):
		"""Constructor"""
		super(OkcoinGateway, self). __init__(eventEngine, gatewayName)

		self. api = Api(self)

		self. leverage = 0
		self. connected = False
		self. qryEnabled = False

	# ----------------------------------------------------------------------
	def connect(self):
		"""Connection"""
		# Load json files
		fileName = self. gatewayName + '_connect.json'
		fileName = os. path. join(getRootPath(), 'cfg', fileName)

		try:
			f = file(fileName)
		except IOError:
			log = VtLogData()
			log. gatewayName = self. gatewayName
			log. logContent = u'Read connection configuration error, please check'
			self. onLog(log)
			return

		# Parse json file
		setting = json. load(f)
		try:
			host = str(setting['host'])
			apiKey = str(setting['apiKey'])
			secretKey = str(setting['secretKey'])
			trace = setting['trace']
			leverage = setting['leverage']
		except KeyError:
			log = VtLogData()
			log. gatewayName = self. gatewayName
			log. logContent = u'Connection configuration missing field, please check'
			self. onLog(log)
			return

			# Initialize the interface
		self. leverage = leverage

		if host == 'CNY':
			host = vnokcoin. OKCOIN_CNY
		else:
			host = vnokcoin. OKCOIN_USD

		self. api. active = True
		self. api. connect(host, apiKey, secretKey, trace)


		self. api. writeLog(u'Interface initialization successful')

		# Start the query
		self. initQuery()

	# ----------------------------------------------------------------------
	def subscribe(self, subscribeReq):
		self. api. _subscribe(subscribeReq. symbol)

	# ----------------------------------------------------------------------
	def sendOrder(self, orderReq):
		"""Billing"""
		return self. api. spotSendOrder(orderReq)

	# ----------------------------------------------------------------------
	def cancelOrder(self, cancelOrderReq):
		"""Withdraw"""
		self. api. spotCancel(cancelOrderReq)

	# ----------------------------------------------------------------------
	def qryAccount(self):
		"""Check Account Funds"""
		self. api. spotUserInfo()

	# ----------------------------------------------------------------------
	def qryPosition(self):
		"""Query Positions"""
		pass

	# ----------------------------------------------------------------------
	def close(self):
		"""Close"""
		self. api. active = False
		self. api. close()

	# ----------------------------------------------------------------------
	def initQuery(self):
		"""Initialize continuous query"""
		if self. qryEnabled:
			# A list of query functions that require a loop
			self. qryFunctionList = [self. qryAccount]

			self. qryCount = 0 # The query triggers a countdown
			self. qryTrigger = 1 # Query trigger point
			self. qryNextFunction = 0# Index of the last run query function

			self. startQuery()

	# ----------------------------------------------------------------------
	def query(self, event):
		"""Query function registered with the event processing engine"""
		self. qryCount += 1

		if self. qryCount > self. qryTrigger:
			# Empty the countdown
			self. qryCount = 0

			# Execute the query function
			function = self. qryFunctionList[self. qryNextFunction]
			function()

			# Calculate the index of the next query function, and if the list length is exceeded, set again to 0
			self. qryNextFunction += 1
			if self. qryNextFunction == len(self. qryFunctionList):
				self. qryNextFunction = 0

	# ----------------------------------------------------------------------
	def startQuery(self):
		"""Start continuous query"""
		self. eventEngine. register(EVENT_TIMER, self. query)

	# ----------------------------------------------------------------------
	def setQryEnabled(self, qryEnabled):
		"""Set whether to start a circular query """
		self. qryEnabled = qryEnabled


########################################################################
class Api(vnokcoin. OkCoinApi):
	"""API implementation of OkCoin"""

	# ----------------------------------------------------------------------
	def __init__(self, gateway):
		"""Constructor"""
		super(Api, self). __init__()

		self. gateway = gateway # gateway对象
		self. gatewayName = gateway. gatewayName # gateway object name

		self. active = False # If True, it will be automatically reconnected after disconnection

		self. cbDict = {}
		self. tickDict = {}
		self. orderDict = {}

		self. localNo = 0# Local delegate number
		self. localNoQueue = Queue() # The local delegation number queue for which the system delegation number was not received
		self. localNoDict = {} # key is the local delegation number and value is the system delegation number
		self. orderIdDict = {} # key is the system delegate number and value is the local delegate number
		self. cancelDict = {} # key is the local delegate number and value is the withdrawal request

		self. initCallback()

	def _subscribe(self, symbol):
		log = "okcoin_gateway _subscribe %s" % symbol
		self. writeLog(log)
		#从系统定义的合约名转为okcoin的合约名

		tick = VtTickData()
		tick. exchange = EXCHANGE_OKCOIN
		tick. symbol = symbol
		tick. vtSymbol = '.'. join([tick. symbol, tick. exchange])
		tick. gatewayName = self. gatewayName
		self. tickDict[symbol] = tick

	# ----------------------------------------------------------------------
	def onMessage(self, ws, evt):
		"""Information push"""
		data = self. readData(evt)[0]
		channel = data['channel']
		# print '%s %s' % (channel, data)
		callback = self. cbDict[channel]
		callback(data)

	# ----------------------------------------------------------------------
	def onError(self, ws, evt):
		"""Error push"""
		error = VtErrorData()
		error. gatewayName = self. gatewayName
		error. errorMsg = str(evt)
		self. gateway. onError(error)

	# ----------------------------------------------------------------------
	def onClose(self, ws):
		self. writeLog("okcoin_gateway disconnected")
		# If it is not already connected, the disconnect prompt is ignored
		if not self. gateway. connected:
			return

		self. gateway. connected = False


		# Reconnect
		if self. active:

			def reconnect():
				while not self. gateway. connected:
					self. writeLog(u'Wait 10 seconds and reconnect')
					sleep(10)
					if not self. gateway. connected:
						self. reconnect()

			t = Thread(target=reconnect)
			t. start()

	# ----------------------------------------------------------------------
	def onOpen(self, ws):
		self. writeLog("okcoin_gateway Connect")
		self. gateway. connected = True

		# Query account and delegate data after connection
		self. spotUserInfo()

		# self.spotOrderInfo(vnokcoin. TRADING_SYMBOL_BTC, '-1')
		# self.spotOrderInfo(vnokcoin. TRADING_SYMBOL_LTC, '-1')
		# self.spotOrderInfo(vnokcoin. TRADING_SYMBOL_ETH, '-1')

		# Subscribe to spot deal and account data after connecting
		# self.subscribeSpotTrades()
		# self.subscribeSpotUserInfo()


		for symbol in self. tickDict. keys():
			self. subscribeSpotTicker(spotSymbolMap[symbol])
			self. subscribeSpotDepth(spotSymbolMap[symbol], vnokcoin. DEPTH_20)

		# If the connection is to the USD website, subscribe to the futures-related return data
		if self. currency == vnokcoin. CURRENCY_USD:
			self. subscribeFutureTrades()
			self. subscribeFutureUserInfo()
			self. subscribeFuturePositions()

		# Returns contract information
		if self. currency == vnokcoin. CURRENCY_CNY:
			l = self. generateCnyContract()
		else:
			l = self. generateUsdContract()

		for contract in l:
			contract. gatewayName = self. gatewayName
			self. gateway. onContract(contract)

	# ----------------------------------------------------------------------
	def writeLog(self, content):
		"""Fast logging"""
		log = VtLogData()
		log. gatewayName = self. gatewayName
		log. logContent = content
		self. gateway. onLog(log)

	# ----------------------------------------------------------------------
	def initCallback(self):
		"""Initialization callback function"""
		# USD_SPOT
		self. cbDict['ok_sub_spotusd_btc_ticker'] = self. onTicker
		self. cbDict['ok_sub_spotusd_ltc_ticker'] = self. onTicker
		self. cbDict['ok_sub_spotusd_eth_ticker'] = self. onTicker

		self. cbDict['ok_sub_spotusd_btc_depth_20'] = self. onDepth
		self. cbDict['ok_sub_spotusd_ltc_depth_20'] = self. onDepth
		self. cbDict['ok_sub_spotusd_eth_depth_20'] = self. onDepth

		self. cbDict['ok_spotusd_userinfo'] = self. onSpotUserInfo
		self. cbDict['ok_spotusd_orderinfo'] = self. onSpotOrderInfo

		self. cbDict['ok_sub_spotusd_userinfo'] = self. onSpotSubUserInfo
		self. cbDict['ok_sub_spotusd_trades'] = self. onSpotSubTrades

		self. cbDict['ok_spotusd_trade'] = self. onSpotTrade
		self. cbDict['ok_spotusd_cancel_order'] = self. onSpotCancelOrder

		# CNY_SPOT
		self. cbDict['ok_sub_spotcny_btc_ticker'] = self. onTicker
		self. cbDict['ok_sub_spotcny_ltc_ticker'] = self. onTicker
		self. cbDict['ok_sub_spotcny_eth_ticker'] = self. onTicker

		self. cbDict['ok_sub_spotcny_btc_depth_20'] = self. onDepth
		self. cbDict['ok_sub_spotcny_ltc_depth_20'] = self. onDepth
		self. cbDict['ok_sub_spotcny_eth_depth_20'] = self. onDepth

		self. cbDict['ok_spotcny_userinfo'] = self. onSpotUserInfo
		self. cbDict['ok_spotcny_orderinfo'] = self. onSpotOrderInfo

		self. cbDict['ok_sub_spotcny_userinfo'] = self. onSpotSubUserInfo
		self. cbDict['ok_sub_spotcny_trades'] = self. onSpotSubTrades

		self. cbDict['ok_spotcny_trade'] = self. onSpotTrade
		self. cbDict['ok_spotcny_cancel_order'] = self. onSpotCancelOrder

		self. cbDict['login'] = self. onPass
		self. cbDict['addChannel'] = self. onPass
		# USD_FUTURES

	# ----------------------------------------------------------------------
	def onTicker(self, data):
		if 'data' not in data:
			return

		channel = data['channel']
		symbol = channelSymbolMap[channel]

		tick = self. tickDict[symbol]

		rawData = data['data']
		tick. highPrice = float(rawData['high'])
		tick. lowPrice = float(rawData['low'])
		tick. lastPrice = float(rawData['last'])
		tick. volume = float(rawData['vol'])
		tick. date, tick. time = generateDateTime(rawData['timestamp'])
		# newtick = copy(tick)
		self. gateway. onTick(tick)

	# ----------------------------------------------------------------------
	def onPass(self, data):
		""""""
		pass

	# ----------------------------------------------------------------------
	def onDepth(self, data):
		if 'data' not in data:
			return

		channel = data['channel']
		symbol = channelSymbolMap[channel]

		tick = self. tickDict[symbol]
		rawData = data['data']

		tick. bids = []
		tick. asks = []
		for i in range(0,5):
			tick. bids. append(rawData['bids'][i])
			tick. asks. append(rawData['asks'][-i-1])
		tick. bidPrice1, tick. bidVolume1 = [float(i) for i in rawData['bids'][0]]
		tick. bidPrice2, tick. bidVolume2 = [float(i) for i in rawData['bids'][1]]
		tick. bidPrice3, tick. bidVolume3 = [float(i) for i in rawData['bids'][2]]
		tick. bidPrice4, tick. bidVolume4 = [float(i) for i in rawData['bids'][3]]
		tick. bidPrice5, tick. bidVolume5 = [float(i) for i in rawData['bids'][4]]

		tick. askPrice1, tick. askVolume1 = [float(i) for i in rawData['asks'][-1]]
		tick. askPrice2, tick. askVolume2 = [float(i) for i in rawData['asks'][-2]]
		tick. askPrice3, tick. askVolume3 = [float(i) for i in rawData['asks'][-3]]
		tick. askPrice4, tick. askVolume4 = [float(i) for i in rawData['asks'][-4]]
		tick. askPrice5, tick. askVolume5 = [float(i) for i in rawData['asks'][-5]]

		tick. date, tick. time = generateDateTime(rawData['timestamp'])
		self. gateway. onTick(tick)

	# ----------------------------------------------------------------------
	def onSpotUserInfo(self, data):
		"""Spot Account Funds Push"""
		rawData = data['data']
		info = rawData['info']
		funds = rawData['info']['funds']

		# Position information
		for symbol in ['btc', 'ltc', self. currency]:
			if symbol in funds['free']:
				pos = VtPositionData()
				pos. gatewayName = self. gatewayName

				pos. exchange = EXCHANGE_OKCOIN
				pos. symbol = symbol
				pos. vtSymbol = '.'. join([pos. symbol, pos. exchange])
				# pos.vtSymbol = symbol
				pos. vtPositionName = symbol
				pos. direction = DIRECTION_NET

				pos. frozen = float(funds['freezed'][symbol])
				pos. position = pos. frozen + float(funds['free'][symbol])

				self. gateway. onPosition(pos)

		# Account funds
		account = VtAccountData()
		account. gatewayName = self. gatewayName
		account. accountID = self. gatewayName
		account. vtAccountID = account. accountID
		account. balance = float(funds['asset']['net'])
		self. gateway. onAccount(account)

	# ----------------------------------------------------------------------
	def onSpotSubUserInfo(self, data):
		"""Spot Account Funds Push"""
		if 'data' not in data:
			return

		rawData = data['data']
		info = rawData['info']

		# Position information
		for symbol in ['btc', 'ltc', self. currency]:
			if symbol in info['free']:
				pos = VtPositionData()
				pos. gatewayName = self. gatewayName

				pos. exchange = EXCHANGE_OKCOIN
				pos. symbol = symbol
				pos. vtSymbol = '.'. join([pos. symbol, pos. exchange])
				# pos.vtSymbol = symbol
				pos. vtPositionName = symbol
				pos. direction = DIRECTION_NET

				pos. frozen = float(info['freezed'][symbol])
				pos. position = pos. frozen + float(info['free'][symbol])

				self. gateway. onPosition(pos)

	# ----------------------------------------------------------------------
	def onSpotSubTrades(self, data):
		"""Deal and Order Push"""
		if 'data' not in data:
			return
		rawData = data['data']
		# print 'onSpotSubTrades %s' % rawData
		# Local and system delegate numbers
		orderId = str(rawData['orderId'])
		# orderId = rawData['orderId']
		localNo = self. orderIdDict[orderId]
		# Delegate information
		if orderId not in self. orderDict:
			order = VtOrderData()
			order. gatewayName = self. gatewayName
			order. exchange = EXCHANGE_OKCOIN

			order. symbol = spotSymbolMap[rawData['symbol']]
			order. vtSymbol = '.'. join([order. symbol, order. exchange])
			# order.vtSymbol = order.symbol

			order. orderID = localNo
			# order.vtOrderID = '.'. join([self.gatewayName, order.orderID])
			order. vtOrderID = '.'. join([order. orderID, self. gatewayName])

			order. price = float(rawData['tradeUnitPrice'])
			order. totalVolume = float(rawData['tradeAmount'])
			order. direction, priceType = priceTypeMap[rawData['tradeType']]

			self. orderDict[orderId] = order
		else:
			order = self. orderDict[orderId]

		order. tradedVolume = float(rawData['completedTradeAmount'])
		order. status = statusMap[rawData['status']]
		# print order.__dict__
		self. gateway. onOrder(copy(order))

		# Deal information
		if 'sigTradeAmount' in rawData and float(rawData['sigTradeAmount']) > 0:
			trade = VtTradeData()
			trade. gatewayName = self. gatewayName
			trade. exchange = EXCHANGE_OKCOIN

			trade. symbol = spotSymbolMap[rawData['symbol']]
			trade. vtSymbol = '.'. join([order. symbol, order. exchange])
			# trade.vtSymbol = order.symbol

			trade. tradeID = str(rawData['id'])
			trade. vtTradeID = '.'. join([self. gatewayName, trade. tradeID])

			trade. orderID = localNo
			# trade.vtOrderID = '.'. join([self.gatewayName, trade.orderID])
			trade. vtOrderID = '.'. join([order. orderID, self. gatewayName])

			trade. price = float(rawData['sigTradePrice'])
			trade. volume = float(rawData['sigTradeAmount'])

			trade. direction, priceType = priceTypeMap[rawData['tradeType']]

			trade. tradeTime = datetime. now(). strftime('%H:%M:%S')

			self. gateway. onTrade(trade)

	# ----------------------------------------------------------------------
	def onSpotOrderInfo(self, data):
		"""Delegate information query callback"""
		rawData = data['data']

		for d in rawData['orders']:
			self. localNo += 1
			localNo = str(self. localNo)
			orderId = str(d['order_id'])

			self. localNoDict[localNo] = orderId
			self. orderIdDict[orderId] = localNo

			if orderId not in self. orderDict:
				order = VtOrderData()
				order. gatewayName = self. gatewayName
				order. exchange = EXCHANGE_OKCOIN

				order. symbol = spotSymbolMap[d['symbol']]
				order. vtSymbol = '.'. join([order. symbol, order. exchange])
				# order.vtSymbol = order.symbol

				order. orderID = localNo
				# order.vtOrderID = '.'. join([self.gatewayName, order.orderID])
				order. vtOrderID = '.'. join([order. orderID, self. gatewayName])

				order. price = d['price']
				order. totalVolume = d['amount']
				order. direction, priceType = priceTypeMap[d['type']]

				self. orderDict[orderId] = order
			else:
				order = self. orderDict[orderId]

			order. tradedVolume = d['deal_amount']
			order. status = statusMap[d['status']]

			self. gateway. onOrder(copy(order))

	# ----------------------------------------------------------------------
	def generateSpecificContract(self, contract, symbol):
		"""Generate Contract"""
		new = copy(contract)
		new. symbol = symbol
		new. vtSymbol = '.'. join([symbol, EXCHANGE_OKCOIN])
		new. name = symbol
		return new

	# ----------------------------------------------------------------------
	def generateCnyContract(self):
		"""Generate CNY contract information"""
		contractList = []

		contract = VtContractData()
		contract. exchange = EXCHANGE_OKCOIN
		contract. productClass = PRODUCT_SPOT
		contract. size = 1
		contract. priceTick = 0.01

		contractList. append(self. generateSpecificContract(contract, SYMBOL_BTC_CNY))
		contractList. append(self. generateSpecificContract(contract, SYMBOL_LTC_CNY))
		contractList. append(self. generateSpecificContract(contract, SYMBOL_ETH_CNY))

		return contractList

	# ----------------------------------------------------------------------
	def generateUsdContract(self):
		"""Generate USD contract information"""
		contractList = []

		# Off-the-shelf
		contract = VtContractData()
		contract. exchange = EXCHANGE_OKCOIN
		contract. productClass = PRODUCT_SPOT
		contract. size = 1
		contract. priceTick = 0.01

		contractList. append(self. generateSpecificContract(contract, BTC_USD_SPOT))
		contractList. append(self. generateSpecificContract(contract, LTC_USD_SPOT))
		contractList. append(self. generateSpecificContract(contract, ETH_USD_SPOT))

		# Futures
		contract. productClass = PRODUCT_FUTURES

		contractList. append(self. generateSpecificContract(contract, BTC_USD_THISWEEK))
		contractList. append(self. generateSpecificContract(contract, BTC_USD_NEXTWEEK))
		contractList. append(self. generateSpecificContract(contract, BTC_USD_QUARTER))
		contractList. append(self. generateSpecificContract(contract, LTC_USD_THISWEEK))
		contractList. append(self. generateSpecificContract(contract, LTC_USD_NEXTWEEK))
		contractList. append(self. generateSpecificContract(contract, LTC_USD_QUARTER))
		contractList. append(self. generateSpecificContract(contract, ETH_USD_THISWEEK))
		contractList. append(self. generateSpecificContract(contract, ETH_USD_NEXTWEEK))
		contractList. append(self. generateSpecificContract(contract, ETH_USD_QUARTER))

		return contractList

	# ----------------------------------------------------------------------
	def onSpotTrade(self, data):
		"""Return on commission"""
		rawData = data['data']
		orderId = str(rawData['order_id'])

		Although the delegate number return of the websocket interface is asynchronous, it has been tested
		# It conforms to the first-mover rule, so here you can get the previous one sent by queue
		# Local delegate number, and map it to the pushed system delegate number
		localNo = self. localNoQueue. get_nowait()

		self. localNoDict[localNo] = orderId
		self. orderIdDict[orderId] = localNo

		# Check if there is a cancellation request issued before the system delegate number returns, and if so, enter
		# Line cancellation operation
		if localNo in self. cancelDict:
			req = self. cancelDict[localNo]
			self. spotCancel(req)
			del self. cancelDict[localNo]

	# ----------------------------------------------------------------------
	def onSpotCancelOrder(self, data):
		"""Withdrawal return"""
		pass

	# ----------------------------------------------------------------------
	def spotSendOrder(self, req):
		"""Billing"""
		symbol = spotSymbolMapReverse[req. symbol][:4]
		type_ = priceTypeMapReverse[(req. direction, req. priceType)]
		self. spotTrade(symbol, type_, str(req. price), str(req. volume))

		# The local delegate number is added to 1, and the corresponding string is saved to the queue, returning the vtOrderID based on the local delegate number
		self. localNo += 1
		self. localNoQueue. put(str(self. localNo))
		# vtOrderID = '.'. join([self.gatewayName, str(self.localNo)])
		vtOrderID = '.'. join([str(self. localNo), self. gatewayName])
		return vtOrderID

	# ----------------------------------------------------------------------
	def spotCancel(self, req):
		"""Withdraw"""
		symbol = spotSymbolMapReverse[req. symbol][:4]
		localNo = req. orderID

		if localNo in self. localNoDict:
			orderID = self. localNoDict[localNo]
			self. spotCancelOrder(symbol, orderID)
		else:
			# If the customer sends a cancellation request before the system delegate number returns, it is saved
			# In the cancelDict dictionary, wait for the return to perform the withdrawal task
			self. cancelDict[localNo] = req


# ----------------------------------------------------------------------
def generateDateTime(s):
	"""Build Time"""
	dt = datetime. fromtimestamp(float(s) / 1e3)
	time = dt. strftime("%H:%M:%S.%f")
	date = dt. strftime("%Y%m%d")
	return date, time



if __name__ == '__main__':
	import sys
	# from PyQt4.QtCore import QCoreApplication

	logger = vnLog('test_okcoin_gateway.log')

	# app = QCoreApplication(sys.argv)

	ee = EventEngine2()
	ee. start()

	def print_data(event):
		data = event. dict_['data']
		log = '%s %s' %(event. type_, data. vtSymbol)
		logger. write(log)

	def print_log(event):
		data = event. dict_['data']
		log = '%s %s' % (event. type_, data. logContent)
		logger. write(log)

	ee. register(EVENT_TICK, print_data)
	ee. register(EVENT_LOG, print_log)

	okcoin_gateway = OkcoinGateway(ee, 'OKCOIN')

	req = VtSubscribeReq()
	req. symbol = SYMBOL_BTC_CNY
	okcoin_gateway. subscribe(req)
	req. symbol = SYMBOL_LTC_CNY
	okcoin_gateway. subscribe(req)
	req. symbol = SYMBOL_ETH_CNY
	okcoin_gateway. subscribe(req)


	okcoin_gateway. connect()

	while True:
		sleep(100)

	# app.exec_()
