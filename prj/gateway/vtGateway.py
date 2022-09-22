# encoding: UTF-8

import time

import sys
sys. path. append('.. /common')

from eventEngine import *

from vtConstant import *


########################################################################
class VtGateway(object):
	"""Transaction interface"""

	#----------------------------------------------------------------------
	def __init__(self, eventEngine, gatewayName):
		"""Constructor"""
		self. eventEngine = eventEngine
		self. gatewayName = gatewayName
		
	#----------------------------------------------------------------------
	def onTick(self, tick):
		"""Market Push """
		# Incidents
		event1 = Event(type_=EVENT_TICK)
		event1. dict_['data'] = tick
		self. eventEngine. put(event1)
		
		# Events for a specific contract code
		event2 = Event(type_=EVENT_TICK+tick. vtSymbol)
		event2. dict_['data'] = tick
		self. eventEngine. put(event2)

	#----------------------------------------------------------------------
	def onTrade(self, trade):
		"""Deal Information Push"""
		# Incidents
		event1 = Event(type_=EVENT_TRADE)
		event1. dict_['data'] = trade
		self. eventEngine. put(event1)
		
		# Deal events for a specific contract
		event2 = Event(type_=EVENT_TRADE+trade. vtSymbol)
		event2. dict_['data'] = trade
		self. eventEngine. put(event2)        

	#----------------------------------------------------------------------
	def onOrder(self, order):
		"""Order Change Push"""
		# Incidents
		event1 = Event(type_=EVENT_ORDER)
		event1. dict_['data'] = order
		self. eventEngine. put(event1)
		
		# Events for a specific order number
		event2 = Event(type_=EVENT_ORDER+order. vtOrderID)
		event2. dict_['data'] = order
		self. eventEngine. put(event2)

	#----------------------------------------------------------------------
	def onPosition(self, position):
		"""Position information push"""
		# Incidents
		event1 = Event(type_=EVENT_POSITION)
		event1. dict_['data'] = position
		self. eventEngine. put(event1)
		
		# Events for a specific contract code
		event2 = Event(type_=EVENT_POSITION+position. vtSymbol)
		event2. dict_['data'] = position
		self. eventEngine. put(event2)

	#----------------------------------------------------------------------
	def onAccount(self, account):
		"""Account Information Push"""
		# Incidents
		event1 = Event(type_=EVENT_ACCOUNT)
		event1. dict_['data'] = account
		self. eventEngine. put(event1)
		
		# Events for a specific contract code
		event2 = Event(type_=EVENT_ACCOUNT+account. vtAccountID)
		event2. dict_['data'] = account
		self. eventEngine. put(event2)

	#----------------------------------------------------------------------
	def onError(self, error):
		"""Error message push"""
		# Incidents
		event1 = Event(type_=EVENT_ERROR)
		event1. dict_['data'] = error
		self. eventEngine. put(event1)
		
	#----------------------------------------------------------------------
	def onLog(self, log):
		"""Log push"""
		# Incidents
		event1 = Event(type_=EVENT_LOG)
		event1. dict_['data'] = log
		self. eventEngine. put(event1)
		
	#----------------------------------------------------------------------
	def onContract(self, contract):
		"""Contract base information push"""
		# Incidents
		event1 = Event(type_=EVENT_CONTRACT)
		event1. dict_['data'] = contract
		self. eventEngine. put(event1)        

	#----------------------------------------------------------------------
	def connect(self):
		"""Connection"""
		pass

	#----------------------------------------------------------------------
	def subscribe(self, subscribeReq):
		"""Subscribe to quotes"""
		pass

	#----------------------------------------------------------------------
	def sendOrder(self, orderReq):
		"""Billing"""
		pass

	#----------------------------------------------------------------------
	def cancelOrder(self, cancelOrderReq):
		"""Withdraw"""
		pass

	#----------------------------------------------------------------------
	def qryAccount(self):
		"""Check Account Funds"""
		pass

	def qryOrder(self):
		#查可撤单
		pass

	def qryTrade(self):
		pass

	#----------------------------------------------------------------------
	def qryPosition(self):
		"""Query Positions"""
		pass

	#----------------------------------------------------------------------
	def close(self):
		"""Close"""
		pass


########################################################################
class VtBaseData(object):
	"""The callback function pushes the underlying class of the data, and other data classes inherit from this """

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		self. gatewayName = EMPTY_STRING # GatewayName 
		self. rawData = None # raw data
		
		
########################################################################
class VtTickData(VtBaseData):
	"""Tick Quotes Data Class"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		super(VtTickData, self). __init__()
		
		# Code dependent
		self. symbol = EMPTY_STRING # contract code
		self.  exchange = EMPTY_STRING # exchange code
		self. vtSymbol = EMPTY_STRING # The unique code of the contract in the vt system, usually the contract code. Exchange code
		
		# Deal data
		self. lastPrice = EMPTY_FLOAT # Latest Transaction Price
		self. lastVolume = EMPTY_INT # Latest volume
		self. volume = EMPTY_INT # Total volume for today
		self. openInterest = EMPTY_INT # open interest
		self. turnover = EMPTY_INT # turnover
		self. time = EMPTY_STRING # Time 11:20:56.5
		self. date = EMPTY_STRING # Date 20151009

		# General quotes
		self. openPrice = EMPTY_FLOAT # Today's Open price
		self. closePrice = EMPTY_FLOAT # today closePrice
		self. highPrice = EMPTY_FLOAT # Today's High
		self. lowPrice = EMPTY_FLOAT # Today's low
		self. preClosePrice = EMPTY_FLOAT # Last Close
		self. preSettlementPrice = EMPTY_FLOAT # Yesterday's settlement price
		self. preOpenInterest = EMPTY_FLOAT # Previous Open Positions

		self. upperLimit = EMPTY_FLOAT # up and down price
		self. lowerLimit = EMPTY_FLOAT # Stop Price

		self. bids = []
		self. asks = []
		# Five levels of quotes
		self. bidPrice1 = EMPTY_FLOAT
		self. bidPrice2 = EMPTY_FLOAT
		self. bidPrice3 = EMPTY_FLOAT
		self. bidPrice4 = EMPTY_FLOAT
		self. bidPrice5 = EMPTY_FLOAT
		
		self. askPrice1 = EMPTY_FLOAT
		self. askPrice2 = EMPTY_FLOAT
		self. askPrice3 = EMPTY_FLOAT
		self. askPrice4 = EMPTY_FLOAT
		self. askPrice5 = EMPTY_FLOAT        
		
		self. bidVolume1 = EMPTY_INT
		self. bidVolume2 = EMPTY_INT
		self. bidVolume3 = EMPTY_INT
		self. bidVolume4 = EMPTY_INT
		self. bidVolume5 = EMPTY_INT
		
		self. askVolume1 = EMPTY_INT
		self. askVolume2 = EMPTY_INT
		self. askVolume3 = EMPTY_INT
		self. askVolume4 = EMPTY_INT
		self. askVolume5 = EMPTY_INT         
    
    
########################################################################
class VtTradeData(VtBaseData):
	"""Deal data class"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		super(VtTradeData, self). __init__()
		
		# Code number dependent
		self. symbol = EMPTY_STRING # contract code
		self.  exchange = EMPTY_STRING # exchange code
		self. vtSymbol = EMPTY_STRING # The unique code of the contract in the vt system, usually the contract code. Exchange code
		
		self. tradeID = EMPTY_STRING # deal number
		self. vtTradeID = EMPTY_STRING # The unique number of deals in the vt system, usually the Gateway name. Deal number
		
		self. orderID = EMPTY_STRING # order number
		self. vtOrderID = EMPTY_STRING # The unique number of the order in the vt system, usually the Gateway name. The order number
		
		# Deal related
		self.  direction = EMPTY_UNICODE # deal direction
		self. offset = EMPTY_UNICODE # Deal Open and Close Position
		self.  price = EMPTY_FLOAT # Deal price
		self. volume = EMPTY_INT # number of deals
		self. tradeTime = EMPTY_STRING # Deal time
   

########################################################################
class VtOrderData(VtBaseData):
	"""Order data class"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		super(VtOrderData, self). __init__()
		
		# Code number dependent
		self. symbol = EMPTY_STRING # contract code
		self.  exchange = EMPTY_STRING # exchange code
		self. vtSymbol = EMPTY_STRING # The unique code of the contract in the vt system, usually the contract code. Exchange code
		
		self. orderID = EMPTY_STRING # order number
		self. vtOrderID = EMPTY_STRING # The unique number of the order in the vt system, usually the Gateway name. The order number
		
		# Bill-related
		self.  direction = EMPTY_UNICODE # reports a single direction
		self. offset = EMPTY_UNICODE # Open and close a position
		self.  price = EMPTY_FLOAT # Quote price
		self. totalVolume = EMPTY_FLOAT # Total number of orders
		self. tradedVolume = EMPTY_FLOAT # number of deal orders
		self.  status = EMPTY_UNICODE # Reporting status

		# self.orderDate = EMPTY_STRING           # sendOrder Date
		self. orderTime = EMPTY_STRING # Billing time
		self. cancelTime = EMPTY_STRING # Cancellation time
		
		# CTP/LTS related
		self. frontID = EMPTY_INT# Frontage number
		self. sessionID = EMPTY_INT # connection number

    
########################################################################
class VtPositionData(VtBaseData):
	"""Position data class"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		super(VtPositionData, self). __init__()
		
		# Code number dependent
		self. symbol = EMPTY_STRING # contract code
		self.  exchange = EMPTY_STRING # exchange code
		self. vtSymbol = EMPTY_STRING # The unique code of the contract in the vt system, the contract code. Exchange code 
		
		# Position related
		self.  direction = EMPTY_STRING # position direction
		self. position = EMPTY_INT # Open Position
		self. frozen = EMPTY_INT # number of freezes
		self. price = EMPTY_FLOAT # Average price of the position
		self. vtPositionName = EMPTY_STRING # The unique code for positions held in the vt system, usually in the vtSymbol.direction direction
		
		# 20151020 add
		self. ydPosition = EMPTY_INT # Previous position
		self. positionProfit = EMPTY_FLOAT


########################################################################
class VtAccountData(VtBaseData):
	"""Account Data Class"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		super(VtAccountData, self). __init__()
		
		# Account code related
		self. accountID = EMPTY_STRING # account code
		self. vtAccountID = EMPTY_STRING # The unique code of the account in vt, usually the Gateway name. Account code
		self. currency = EMPTY_STRING
		
		# Numerical correlation
		self. preBalance = EMPTY_FLOAT # Yesterday's account settlement equity
		self. balance = EMPTY_FLOAT # Account equity
		self. available = EMPTY_FLOAT # Available funds
		self. commission = EMPTY_FLOAT # Today's commission
		self. margin = EMPTY_FLOAT # margin occupancy
		self. closeProfit = EMPTY_FLOAT # Close P&L
		self. positionProfit = EMPTY_FLOAT # P&L of open positions
        

########################################################################
class VtErrorData(VtBaseData):
	"""Error data class"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		super(VtErrorData, self). __init__()
		
		self. errorID = EMPTY_STRING# error code
		self. errorMsg = EMPTY_UNICODE# error message
		self. additionalInfo = EMPTY_UNICODE # Supplemental information
		
		self. errorTime = time. strftime('%X', time. localtime()) # Error generation time


########################################################################
class VtLogData(VtBaseData):
	"""Log data class"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		super(VtLogData, self). __init__()
		
		self. logTime = time. strftime('%X', time. localtime()) # Log generation time
		self. logContent = EMPTY_UNICODE # log information


########################################################################
class VtContractData(VtBaseData):
	"""Contract Detail Class"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		super(VtContractData, self). __init__()
		
		self. symbol = EMPTY_STRING # code
		self.  exchange = EMPTY_STRING # exchange code
		self. vtSymbol = EMPTY_STRING # The unique code of the contract in the vt system, usually the contract code. Exchange code
		self.  name = EMPTY_UNICODE # Contract Chinese name
		
		self. productClass = EMPTY_UNICODE# contract type
		self.  size = EMPTY_INT # contract size
		self. priceTick = EMPTY_FLOAT # Contract minimum price TICK
		
		# Options related
		self. strikePrice = EMPTY_FLOAT # option strike price
		self. underlyingSymbol = EMPTY_STRING # Underlying contract code
		self. optionType = EMPTY_UNICODE# option type


########################################################################
class VtSubscribeReq(object):
	"""Object class passed in when subscribing to quotes"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		self. symbol = EMPTY_STRING # code
		self.  exchange = EMPTY_STRING # exchange
		
		# The following are IB related
		self. productClass = EMPTY_UNICODE# contract type
		self.  currency = EMPTY_STRING # contract currency
		self. expiry = EMPTY_STRING# expiration date
		self. strikePrice = EMPTY_FLOAT # Strike price
		self. optionType = EMPTY_UNICODE# option type


########################################################################
class VtOrderReq(object):
	"""Object class passed in when billing"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		self. symbol = EMPTY_STRING # code
		self.  exchange = EMPTY_STRING # exchange
		self.  price = EMPTY_FLOAT # price
		self. volume = EMPTY_INT # 数量

		self. priceType = EMPTY_STRING # price type
		self. direction = EMPTY_STRING # buy and sell
		self. offset = EMPTY_STRING # open level
		
		# The following are IB related
		self. productClass = EMPTY_UNICODE# contract type
		self.  currency = EMPTY_STRING # contract currency
		self. expiry = EMPTY_STRING# expiration date
		self. strikePrice = EMPTY_FLOAT # Strike price
		self. optionType = EMPTY_UNICODE# option type 
		

########################################################################
class VtCancelOrderReq(object):
	"""Object class passed in when unblocking"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		self. symbol = EMPTY_STRING # code
		self.  exchange = EMPTY_STRING # exchange
		
		# The following fields are mainly related to CTP and LTS class interfaces
		self. orderID = EMPTY_STRING # Billing number
		self. frontID = EMPTY_STRING # Previous machine number
		self. sessionID = EMPTY_STRING # session number
