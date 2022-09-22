# encoding: UTF-8

import hashlib
import zlib
import json
from time import sleep
from threading import Thread

import websocket

# OKCOIN website
OKCOIN_CNY = 'wss://real.okcoin.cn:10440/websocket/okcoinapi'
OKCOIN_USD = 'wss://real.okcoin.com:10440/websocket/okcoinapi'

# Account currency code
CURRENCY_CNY = 'cny'
CURRENCY_USD = 'usd'

# E-money code
SYMBOL_BTC = 'btc'
SYMBOL_LTC = 'ltc'
SYMBOL_ETH = 'eth'

# Market depth
DEPTH_20 = 20
DEPTH_60 = 60

# K-line time interval
INTERVAL_1M = '1min'
INTERVAL_3M = '3min'
INTERVAL_5M = '5min'
INTERVAL_15M = '15min'
INTERVAL_30M = '30min'
INTERVAL_1H = '1hour'
INTERVAL_2H = '2hour'
INTERVAL_4H = '4hour'
INTERVAL_6H = '6hour'
INTERVAL_1D = 'day'
INTERVAL_3D = '3day'
INTERVAL_1W = 'week'

# Transaction code, requires suffix currency name to be complete
TRADING_SYMBOL_BTC = 'btc_'
TRADING_SYMBOL_LTC = 'ltc_'
TRADING_SYMBOL_ETH = 'eth_'

# Delegate type
TYPE_BUY = 'buy'
TYPE_SELL = 'sell'
TYPE_BUY_MARKET = 'buy_market'
TYPE_SELL_MARKET = 'sell_market'

# Futures contract expiration type
FUTURE_EXPIRY_THIS_WEEK = 'this_week'
FUTURE_EXPIRY_NEXT_WEEK = 'next_week'
FUTURE_EXPIRY_QUARTER = 'quarter'

# Futures Order Type
FUTURE_TYPE_LONG = 1
FUTURE_TYPE_SHORT = 2
FUTURE_TYPE_SELL = 3
FUTURE_TYPE_COVER = 4

# Whether the futures use the current price
FUTURE_ORDER_MARKET = 1
FUTURE_ORDER_LIMIT = 0

# Futures leverage
FUTURE_LEVERAGE_10 = 10
FUTURE_LEVERAGE_20 = 20

# Delegate status
ORDER_STATUS_NOTTRADED = 0
ORDER_STATUS_PARTTRADED = 1
ORDER_STATUS_ALLTRADED = 2
ORDER_STATUS_CANCELLED = -1
ORDER_STATUS_CANCELLING = 4


########################################################################
class OkCoinApi(object):
	"""Websocket-based API objects"""

	# ----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		self. apiKey = ''# username
		self. secretKey = ''# password 
		self. host = '' # server address

		self. currency = ''# Currency type (usd or cny).

		self. ws = None # websocket application object
		self. thread = None # worker thread

	#######################
	## Generic functions
	#######################

	# ----------------------------------------------------------------------
	def readData(self, evt):
		"""Unzip the data received by the push"""
		try:
			# Create a decompressionr
			decompress = zlib. decompressobj(-zlib. MAX_WBITS)
			# Unzip the raw data into strings
			inflated = decompress. decompress(evt) + decompress. flush()
			# Parse strings by json
			data = json. loads(inflated)
			return data

		except zlib. error as err:
			# print err
			# # Create a decompressionr
			# decompress = zlib.decompressobj(16+zlib. MAX_WBITS)
			# # Unzip the raw data into a string
			# inflated = decompress.decompress(evt) + decompress.flush()
			# Parse strings by json
			data = json. loads(evt)
			return data


	# ----------------------------------------------------------------------
	def generateSign(self, params):
		"""Generate Signature"""
		l = []
		for key in sorted(params. keys()):
			l. append('%s=%s' % (key, params[key]))
		l. append('secret_key=%s' % self. secretKey)
		sign = '&'. join(l)
		return hashlib. md5(sign. encode('utf-8')). hexdigest(). upper()

	# ----------------------------------------------------------------------
	def onMessage(self, ws, evt):
		"""Information push"""
		print 'onMessage'
		data = self. readData(evt)
		print data[0]['channel'], data

	# ----------------------------------------------------------------------
	def onError(self, ws, evt):
		"""Error push"""
		print 'onError'
		print if necessary

	# ----------------------------------------------------------------------
	def onClose(self, ws):
		"""Interface disconnected"""
		print 'onClose'

	# ----------------------------------------------------------------------
	def onOpen(self, ws):
		"""Interface Open"""
		print 'onOpen'

	# ----------------------------------------------------------------------
	def connect(self, host, apiKey, secretKey, trace=False):
		"""Connection Server"""
		self. host = host
		self. apiKey = apiKey
		self. secretKey = secretKey

		if self. host == OKCOIN_CNY:
			self. currency = CURRENCY_CNY
		else:
			self. currency = CURRENCY_USD

		websocket. enableTrace(trace)

		self. ws = websocket. WebSocketApp(host,
										 on_message=self. onMessage,
										 on_error=self. onError,
										 on_close=self. onClose,
										 on_open=self. onOpen)

		self. thread = Thread(target=self. ws. run_forever)
		self. thread. start()

	# ----------------------------------------------------------------------
	def reconnect(self):
		"""Reconnect"""
		# Close the previous connection first
		self. close()

		# Perform the reconnect task again
		self. ws = websocket. WebSocketApp(self. host,
										 on_message=self. onMessage,
										 on_error=self. onError,
										 on_close=self. onClose,
										 on_open=self. onOpen)

		self. thread = Thread(target=self. ws. run_forever)
		self. thread. start()

	# ----------------------------------------------------------------------
	def close(self):
		"""Close Interface"""
		if self. thread and self. thread. isAlive():
			self. ws. close()
			self. thread. join()

	# ----------------------------------------------------------------------
	def sendMarketDataRequest(self, channel):
		"""Send quote request"""
		# Generate a request
		d = {}
		d['event'] = 'addChannel'
		d['binary'] = True
		d['channel'] = channel

		# Package and send using json
		j = json. dumps(d)

		# Reconnect if an exception is triggered
		try:
			self. ws. send(j)
		except websocket. WebSocketConnectionClosedException:
			pass

	# ----------------------------------------------------------------------
	def sendTradingRequest(self, channel, params):
		"""Send a trade request"""
		# Add api_key and signature fields to the parameter dictionary
		params['api_key'] = self. apiKey
		params['sign'] = self. generateSign(params)

		# Generate a request
		d = {}
		d['event'] = 'addChannel'
		d['binary'] = True
		d['channel'] = channel
		d['parameters'] = params

		# Package and send using json
		j = json. dumps(d)

		# Reconnect if an exception is triggered
		try:
			self. ws. send(j)
		except websocket. WebSocketConnectionClosedException:
			pass

			#######################

	## Spot related
	#######################

	# ----------------------------------------------------------------------
	def subscribeSpotTicker(self, symbol):
		"""Subscribe to the regular quote in stock"""
		self. sendMarketDataRequest('ok_sub_spot%s_%s_ticker' % (self. currency, symbol))

	# ----------------------------------------------------------------------
	def subscribeSpotDepth(self, symbol, depth):
		"""Subscribe to Spot Depth Quotes"""
		self. sendMarketDataRequest('ok_sub_spot%s_%s_depth_%s' % (self. currency, symbol, depth))

		# ----------------------------------------------------------------------

	def subscribeSpotTradeData(self, symbol):
		"""Subscribe to spot deals"""
		self. sendMarketDataRequest('ok_sub_spot%s_%s_trades' % (self. currency, symbol))

	# ----------------------------------------------------------------------
	def subscribeSpotKline(self, symbol, interval):
		"""Subscribe to spot candlesticks"""
		self. sendMarketDataRequest('ok_sub_spot%s_%s_kline_%s' % (self. currency, symbol, interval))

	# ----------------------------------------------------------------------
	def spotTrade(self, symbol, type_, price, amount):
		"""Spot order"""
		params = {}
		params['symbol'] = str(symbol + self. currency)
		params['type'] = str(type_)
		params['price'] = str(price)
		params['amount'] = str(amount)
		# print params
		channel = 'ok_spot%s_trade' % (self. currency)

		self. sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def spotCancelOrder(self, symbol, orderid):
		"""Spot Withdrawal"""
		params = {}
		params['symbol'] = str(symbol + self. currency)
		params['order_id'] = str(orderid)

		channel = 'ok_spot%s_cancel_order' % (self. currency)

		self. sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def spotUserInfo(self):
		"""Enquiry Spot Account"""
		channel = 'ok_spot%s_userinfo' % (self. currency)

		self. sendTradingRequest(channel, {})

	# ----------------------------------------------------------------------
	def spotOrderInfo(self, symbol, orderid):
		"""Query Spot Order Information"""
		params = {}
		params['symbol'] = str(symbol + self. currency)
		params['order_id'] = str(orderid)

		channel = 'ok_spot%s_orderinfo' % (self. currency)

		self. sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def subscribeSpotTrades(self):
		"""Subscribe to spot deal information"""
		channel = 'ok_sub_spot%s_trades' % (self. currency)

		self. sendTradingRequest(channel, {})

	# ----------------------------------------------------------------------
	def subscribeSpotUserInfo(self):
		"""Subscribe to Spot Account Information"""
		channel = 'ok_sub_spot%s_userinfo' % (self. currency)

		self. sendTradingRequest(channel, {})

	#######################
	## Futures related
	#######################

	# ----------------------------------------------------------------------
	def subscribeFutureTicker(self, symbol, expiry):
		"""Subscribe to regular futures quotes"""
		self. sendMarketDataRequest('ok_sub_future%s_%s_ticker_%s' % (self. currency, symbol, expiry))

	# ----------------------------------------------------------------------
	def subscribeFutureDepth(self, symbol, expiry, depth):
		"""Subscribe to futures depth quotes"""
		self. sendMarketDataRequest('ok_sub_future%s_%s_depth_%s_%s' % (self. currency, symbol,
																	   expiry, depth))

		# ----------------------------------------------------------------------

	def subscribeFutureTradeData(self, symbol, expiry):
		"""Subscribe to futures deal history"""
		self. sendMarketDataRequest('ok_sub_future%s_%s_trade_%s' % (self. currency, symbol, expiry))

	# ----------------------------------------------------------------------
	def subscribeFutureKline(self, symbol, expiry, interval):
		"""Subscribe to futures candlesticks"""
		self. sendMarketDataRequest('ok_sub_future%s_%s_kline_%s_%s' % (self. currency, symbol,
																	   expiry, interval))

	# ----------------------------------------------------------------------
	def subscribeFutureIndex(self, symbol):
		"""Subscribe to futures index"""
		self. sendMarketDataRequest('ok_sub_future%s_%s_index' % (self. currency, symbol))

	# ----------------------------------------------------------------------
	def futureTrade(self, symbol, expiry, type_, price, amount, order, leverage):
		"""Futures Order"""
		params = {}
		params['symbol'] = str(symbol + self. currency)
		params['type'] = str(type_)
		params['price'] = str(price)
		params['amount'] = str(amount)
		params['contract_type'] = str(expiry)
		params['match_price'] = str(order)
		params['lever_rate'] = str(leverage)

		channel = 'ok_future%s_trade' % (self. currency)

		self. sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def futureCancelOrder(self, symbol, expiry, orderid):
		"""Futures Cancellation"""
		params = {}
		params['symbol'] = str(symbol + self. currency)
		params['order_id'] = str(orderid)
		params['contract_type'] = str(expiry)

		channel = 'ok_future%s_cancel_order' % (self. currency)

		self. sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def futureUserInfo(self):
		"""Enquiry Futures Account"""
		channel = 'ok_future%s_userinfo' % (self. currency)

		self. sendTradingRequest(channel, {})

	# ----------------------------------------------------------------------
	def futureOrderInfo(self, symbol, expiry, orderid, status, page, length):
		"""Inquiry of futures order information"""
		params = {}
		params['symbol'] = str(symbol + self. currency)
		params['order_id'] = str(orderid)
		params['contract_type'] = expiry
		params['status'] = status
		params['current_page'] = page
		params['page_length'] = length

		channel = 'ok_future%s_orderinfo' % (self. currency)

		self. sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def subscribeFutureTrades(self):
		"""Subscribe to futures deal information"""
		channel = 'ok_sub_future%s_trades' % (self. currency)

		self. sendTradingRequest(channel, {})

	# ----------------------------------------------------------------------
	def subscribeFutureUserInfo(self):
		"""Subscribe to futures account information"""
		channel = 'ok_sub_future%s_userinfo' % (self. currency)

		self. sendTradingRequest(channel, {})

	# ----------------------------------------------------------------------
	def subscribeFuturePositions(self):
		"""Subscribe to futures position information"""
		channel = 'ok_sub_future%s_positions' % (self. currency)

		self. sendTradingRequest(channel, {})


if __name__ == '__main__':
	api = OkCoinApi()
	host = OKCOIN_CNY
	apiKey = "f1c5d942-beab-448a-8996-4d502e42cd96"
	secretKey = "8E0C2C77443BB43C1034E016055DC545"

	api. currency = CURRENCY_CNY

	while 1:
		input = raw_input ('0.Connect 1:Subscribe to tick 2.Subscribe to depth 3.Subscribe to deal history 4.Subscribe to candlesticks 5.Place orders 6.Cancel orders 7.Check account 8.Check orders 9.Subscribe to transaction data 10.Subscribe to accounts 20.Disconnect\n')
		if input == '0':
			api. connect(host, apiKey, secretKey, trace=False)
			sleep(2)
		elif input == '1':
			api. subscribeSpotTicker('btc')
		elif input == '2':
			api. subscribeSpotDepth('btc', 20)
		elif input == '3':
			api. subscribeSpotTrades()
		elif input == '4':
			api. subscribeSpotKline('btc', INTERVAL_1M)
		elif input == '5':
			# api.spotTrade('btc_', 'buy', str(17000), str(0.01))
			# api.spotTrade('btc_', 'buy', str(16000), str(0.01))
			pass
		elif input == '6':
			pass
		elif input == '7':
			api. spotUserInfo()
		elif input == '8':
			api. spotOrderInfo('btc', '-1')
		elif input == '9':
			api. subscribeSpotTrades()
		elif input == '10':
			api. subscribeSpotUserInfo()
		elif input == '20':
			api. close()
		else:
			break
