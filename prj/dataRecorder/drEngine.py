# encoding: UTF-8

'''
This file implements the market data logging engine for summarizing TICK data and generating candlesticks for insertion into the database.
Use DR_setting.json to configure the contracts that need to be collected, as well as the main contract code.
'''

import json
import the
import copy
from collections import OrderedDict
from datetime import datetime, timedelta
from Queue import Queue
from threading import Thread

from eventEngine import *
from vtGateway import VtSubscribeReq, VtLogData
from drBase import *
from vtFunction import *
import vnlog

########################################################################
class DrEngine(object):
	"""Data Logging Engine"""
	settingFileName = 'DR_setting.json'
	settingFileName = getRootPath() + '/cfg/' + settingFileName

	#----------------------------------------------------------------------
	def __init__(self, mainEngine, eventEngine):
		"""Constructor"""
		self. mainEngine = mainEngine
		self. eventEngine = eventEngine
		
		# Current date
		self. today = todayDate()
		
		# Main contract code mapping dictionary, key is the specific contract code (such as IF1604), value is the main contract code (such as IF0000)
		self. activeSymbolDict = {}
		
		# Tick object dictionary
		self. tickDict = {}
		
		# Candlestick object dictionary
		self. barDict = {}
		
		# Associated with a separate thread responsible for performing database inserts
		self. active = False # Work status
		self. queue = Queue() # 队列
		self. thread = Thread(target=self. run) # 线程
		
		# Load the settings and subscribe to the market
		self. loadSetting()
		
		self. logger = vnlog. vnLog('vtDR.log')
		
	#----------------------------------------------------------------------
	def loadSetting(self):
		"""Loading settings"""
		with open(self. settingFileName) as f:
			drSetting = json. load(f)
			
			# If working is set to False, the market recording function is not enabled
			working = drSetting['working']
			if not working:
				return

			CTP_working = drSetting['CTP_working'] 

			if 'tick' in drSetting:
				l = drSetting['tick']
				
				for setting in l:
					symbol = setting[0]
					vtSymbol = symbol

					if setting[1] in ['OKCOIN', 'BTCC']:
						vtSymbol = '.'. join([symbol, setting[1]])

					req = VtSubscribeReq()
					req. symbol = setting[0]

					self. mainEngine. subscribe(req, setting[1])
					
					drTick = DrTickData() # This tick instance can be used to cache some of the data (currently unused).
					self. tickDict[vtSymbol] = drTick
					
			if 'bar' in drSetting:
				l = drSetting['bar']
				
				for setting in l:
					symbol = setting[0]
					vtSymbol = symbol
					
					req = VtSubscribeReq()
					req. symbol = symbol                    

					if len(setting)>=3:
						req. exchange = setting[2]
						vtSymbol = '.'. join([symbol, req. exchange])

					if len(setting)>=5:
						req. currency = setting[3]
						req. productClass = setting[4]                    
					
					self. mainEngine. subscribe(req, setting[1])  
					
					bar = DrBarData() 
					self. barDict[vtSymbol] = bar
					
			if 'active' in drSetting:
				d = drSetting['active']
				
				# Note that the vtSymbol here should be suffixed for IB and LTS interfaces. exchange
				for activeSymbol, vtSymbol in d. items():
					self. activeSymbolDict[vtSymbol] = activeSymbol
			
			# Start the data insertion thread
			self. start()
			
			# Register event listening
			self. registerEvent()    

	#----------------------------------------------------------------------
	def procecssTickEvent(self, event):
		"""Handle market push"""
		tick = event. dict_['data']
		# print tick.__dict__
		vtSymbol = tick. vtSymbol


		# Convert Tick format
		drTick = DrTickData()
		d = drTick. __dict__
		for key in d. keys():
			if key != 'datetime':
				d[key] = tick. __getattribute__(key)
		if tick. exchange in ["HUOBI", "BTCC", "HUOBIETH"]:
			drTick. datetime = datetime. strptime(' '. join([tick. date, tick. time]), '%Y%m%d %H:%M:%S')
		else:
			drTick. datetime = datetime. strptime(' '. join([tick. date, tick. time]), '%Y%m%d %H:%M:%S.%f')

		#print drTick.datetime, vtSymbol
		#self.logger.write(vtSymbol)
		# Update Tick data
		# if vtSymbol in self.tickDict:
		# record all data from API
		if 1:
			self. insertData(TICK_DB_NAME, vtSymbol, drTick)
			
			if vtSymbol in self. activeSymbolDict:
				activeSymbol = self. activeSymbolDict[vtSymbol]
				self. insertData(TICK_DB_NAME, activeSymbol, drTick)

			# print drTick.__dict__
			# Issue logs
			# self.writeDrLog(u'记录Tick数据%s，时间:%s, last:%s, bid1:%s, bid2:%s, bid3:%s, bid4:%s, bid5:%s, ask1:%s, ask2:%s, ask3:%s, ask4:%s, ask5:%s'
			#                 %(drTick.vtSymbol, drTick.time, drTick.lastPrice, drTick.bidPrice1, drTick.bidPrice2, drTick.bidPrice3, drTick.bidPrice4, drTick.bidPrice5
			#                   , drTick.askPrice1, drTick.askPrice2, drTick.askPrice3, drTick.askPrice4, drTick.askPrice5))
			self. writeDrLog(
				u'记录Tick数据%s，时间:%s, last:%s, bid1:%s, bid2:%s, bid3:%s, ask1:%s, ask2:%s, ask3:%s'
				% (drTick. vtSymbol, drTick. time, drTick. lastPrice, drTick. bidPrice1, drTick. bidPrice2, drTick. bidPrice3,
				   drTick. askPrice1, drTick. askPrice2, drTick. askPrice3))
			
		# Update minute line data
		if vtSymbol in self. barDict:
			bar = self. barDict[vtSymbol]
			
			# If the first tick or a new minute
			if not bar. datetime or bar. datetime. minute != drTick. datetime. minute: 
				if bar. vtSymbol:
					newBar = copy. copy(bar)
					self. insertData(MINUTE_DB_NAME, vtSymbol, newBar)
					
					if vtSymbol in self. activeSymbolDict:
						activeSymbol = self. activeSymbolDict[vtSymbol]
						self. insertData(MINUTE_DB_NAME, activeSymbol, newBar)                    
					
					self. writeDrLog(u'Record minute line data %s, Time: %s, O:%s, H:%s, L:%s, C:%s' 
									%(bar. vtSymbol, bar. time, bar. open, bar. high, 
									  bar. low, bar. close))
						 
				bar. vtSymbol = drTick. vtSymbol
				bar. symbol = drTick. symbol
				bar. exchange = drTick. exchange
				
				bar. open = drTick. lastPrice
				bar. high = drTick. lastPrice
				bar. low = drTick. lastPrice
				bar. close = drTick. lastPrice
				
				bar. date = drTick. date
				bar. time = drTick. time
				bar. datetime = drTick. datetime
				bar. volume = drTick. volume
				bar. openInterest = drTick. openInterest        
			# Otherwise continue to accumulate new candlesticks
			else:                               
				bar. high = max(bar. high, drTick. lastPrice)
				bar. low = min(bar. low, drTick. lastPrice)
				bar. close = drTick. lastPrice            

	#----------------------------------------------------------------------
	def registerEvent(self):
		"""Register Event Listening"""
		self. eventEngine. register(EVENT_TICK, self. procecssTickEvent)

	#----------------------------------------------------------------------
	def insertData(self, dbName, collectionName, data):
		"Insert data into the database (data here can be CtaTickData or CtaBarData)"
		self. queue. put((dbName, collectionName, data. __dict__))
		
	#----------------------------------------------------------------------
	def run(self):
		"""Run insertion thread"""
		while self. active:
			try:
				dbName, collectionName, d = self. queue. get(block=True, timeout=1)
				self. mainEngine. dbInsert(dbName, collectionName, d)
			except Empty:
				pass
	#----------------------------------------------------------------------
	def start(self):
		"""Start"""
		self. active = True
		self. thread. start()
		
	#----------------------------------------------------------------------
	def stop(self):
		"""Exit"""
		if self. active:
			self. active = False
			self. thread. join()
		
	#----------------------------------------------------------------------
	def writeDrLog(self, content):
		"""Fast Log Event"""
		log = VtLogData()
		log. logContent = content
		event = Event(type_=EVENT_DATARECORDER_LOG)
		event. dict_['data'] = log
		self. eventEngine. put(event)   
