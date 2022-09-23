# encoding: UTF-8

"""
A trading strategy that combines the ATR-RSI indicator and is suitable for use on the 1-minute and 5-minute lines of the stock index.
Notes:
1. The author does not make any guarantee of trading profitability, the strategy code is for reference only
2. This policy requires talib, if you do not have it installed, please refer to the tutorial on the www.vnpy.org to install it first
3. After importing the IF0000_1min.csv ctaHistoryData.py into MongoDB, run this file directly to test the policy
"""

from MMBase import *
from MMTemplate import MMTemplate
from collections import OrderedDict
import numpy as np
from vtGateway import *
from datetime import datetime
import random
from operator import itemgetter, attrgetter
import  logging
import copy
from vnlog import vnLog
from vtFunction import *

DIRECTION_LONG = u'buy'
DIRECTION_SHORT = u'sell'


########################################################################
class MarketBalance(MMTemplate):
    """BitCoin Market Making Balanced Market Trading Strategy"""
    className = 'MMStrategy'
    author = u'CYX'

    # Policy parameters
    initDays = 10 # The number of days it took to initialize the data

    # Policy variables
    bar = None # candlestick object
    barMinute = EMPTY_STRING # K line current minute

    bufferSize = 100 # The size of the data that needs to be cached
    bufferCount = 0 # Count of data that is currently cached
    highArray = np. zeros(bufferSize) # array of candlestick highs
    lowArray = np. zeros(bufferSize) # array of candlestick lows
    closeArray = np. zeros(bufferSize) # An array of candlestick closing prices

    orderList = [] # Saves a list of delegate codes
    EntryOrder = []

    # Parameter list, the name of the parameter is saved
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']

    # A list of variables that hold the name of the variable
    varList = ['inited',
               'trading',
               'pos']

    # orderbook_prc = {} # Record the order book price on a tick
    # orderbook_vol = {} # Record the order book volume on a tick
    # tick_old = VtTickData() # Record the last tick
    orderbook1 = []
    orderbook2 = []
    tunepct = 0.5
    tickcount = 0
    tickcount1 = 0
    # print fields

    orderbook_buy = {}
    orderbook_sell = {}

    # ----------------------------------------------------------------------
    def __init__(self, mmEngine, setting):
        """Constructor"""
        # the mmEngine here could be either MMEngine for real-trading, or backtestingEngine for backtesting.
        super(MarketBalance, self). __init__(mmEngine, setting)

        # Note that the mutable object properties in the policy class (usually list and dict, etc.) need to be recreated when the policy is initialized.
        # Otherwise, data sharing between multiple policy instances may occur, which may lead to potential policy logic errors.
        # These mutable object properties in the policy class can be chosen not to write, all placed under the __init__, written mainly for reading
        # Convenient strategy (more of a programming habit choice)
        # order_id -> order
        self. idOrderDict = {}
        # price -> list(order_id)
        self. priceOrderIdsDict = {}

        self. orderUpdate = False
        self. tickUpdate = False
        self. OKtickUpdate = False

        self. logger = vnLog('marketMaker.log')
    # ----------------------------------------------------------------------
    def onInit(self):
        """Initialization policy (must be implemented by user inheritance)"""
        self. writeCtaLog(u'%s policy initialization' % self.name)

        # # Load historical data and initialize the policy value by means of playback calculation
        # initData = self.loadBar(self.initDays)
        # for bar in initData:
        #     self.onBar(bar)

        self. putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """Startup policy (must be implemented by user inheritance)"""
        self. writeCtaLog(u'The %s policy starts' % self. name)
        self. putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """Stop policy (must be implemented by user inheritance)"""
        self. writeCtaLog(u'The %s policy stops' % self. name)
        self. putEvent()


    # Market making strategy: According to the orderbook of okcoin, flexibly adjust the orderbook of zhcoin. The price is required to be consistent, and the amount of pending orders has a certain correlation
    def onTick(self, tick):
        if 'OKCOIN' in tick. vtSymbol:
            def get_orderbook1():
                bids1 = copy. deepcopy(tick. bids)
                asks1 = copy. deepcopy(tick. asks)
                bids1vol = [0]*len(bids1)
                asks1vol = [0]*len(bids1)
                for i in range(len(bids1)):
                    bids1[i][0] = priceUniform(bids1[i][0]) # The order price takes two decimal places
                    bids1vol[i] = (float(bids1[i][1])) # Record the amount of delegate separately for subsequent calculation of the total and proportion
                    asks1[i][0] = priceUniform(asks1[i][0])
                    asks1vol[i] = (float(asks1[i][1]))

                bids1volpct = [x / sum(bids1vol) for x in bids1vol] # The proportion of the number of orders paid by the General Committee accounts for the number of orders paid by the General Committee
                asks1volpct = [x / sum(asks1vol) for x in asks1vol] # The number of orders sold by the commission accounts for the proportion of the number of orders sold by the general committee
                if not bids1vol:
                    return
                PCT = sum(asks1vol) / sum(bids1vol) # The ratio of the amount of sell orders to the amount of orders of the General Committee of the General Committee
                BuyTotalVol = 5 # ZHCOIN General Committee Buy Order Volume (determined based on the number of RMB account funds converted into Bitcoin).
                SellTotalVol = int(round(BuyTotalVol * PCT * 10)) / 10.0  # According to the ratio of the volume of buyers and sellers in the market, one decimal place is retained
                for i in range(len(bids1)):
                    bids1[i][1] = priceUniform(bids1volpct[i] * BuyTotalVol) # The proportion of orders at a certain price to the total number of orders is consistent
                    asks1[i][1] = - priceUniform(asks1volpct[i] * SellTotalVol)
                tmp1 = bids1
                tmp1[len(bids1):] = asks1
                self. orderbook1 = tmp1 # target orderbook, order amount is negative to sell
            get_orderbook1()
            self. OKtickUpdate = True

        elif 'ZHCOIN' in tick. vtSymbol:
            def get_orderbook2():
                bids2 = copy. deepcopy(tick. bids)
                asks2 = copy. deepcopy(tick. asks)
                for i in range(len(bids2)):
                    bids2[i][0] = priceUniform(bids2[i][0])
                    bids2[i][1] = volumeUniform(bids2[i][1])
                for i in range(len(asks2)):
                    asks2[i][0] = priceUniform(asks2[i][0])
                    asks2[i][1] = - volumeUniform(asks2[i][1])
                tmp2 = bids2
                tmp2[len(bids2):] = asks2
                self. orderbook2 = tmp2
            get_orderbook2()
            self. tickUpdate = True

        # Operate every n ticks
        self. tickcount += 1
        if not self. OKtickUpdate or not self. tickUpdate or not self. orderUpdate or self. tickcount <= 2:
            return
        else:
            self. tickcount = 0

        print ('OKCOIN')
        print (self. orderbook1)
        print ('ZHCOIN')
        print (self. orderbook2)
        def trade_in_lastPrice():
            n = random. randint(1, 10)
            pri = priceUniform(tick. lastPrice)
            v = 0.0001
            if n % 2 == 0:
                self. buy('BTC_CNY. ZHCOIN', pri, v)
                self. sell('BTC_CNY. ZHCOIN', pri - 0.1, v)
            else:
                self. sell('BTC_CNY. ZHCOIN', pri, v)
                self. buy('BTC_CNY. ZHCOIN', pri + 0.1, v)

            # buyVol = 0.
            # sellVol = 0.
            # for pri_vol in self.orderbook2:
            #     if pri_vol[1] > 0:
            #         buyVol += pri_vol[1]
            #     else:
            #         sellVol += pri_vol[1]
            # print 'buyVol:',buyVol, 'sellVol:',sellVol
            # if buyVol > 2:
            # self.sell('BTC_CNY. ZHCOIN', pri-1000, 2)
            # elif sellVol > 2:
            # self.buy('BTC_CNY. ZHCOIN', pri + 1000, 2)

        trade_in_lastPrice()

        self. orderUpdate = False


    # ----------------------------------------------------------------------
    def onBar(self, bar):
        pass

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        if order. status in [STATUS_PARTTRADED, STATUS_PENDING]:
            if not self. idOrderDict. has_key(order. vtOrderID):
                self. idOrderDict[order. vtOrderID] = order
                if order. status == STATUS_PENDING:
                    print ('Queue List', order. vtOrderID)
                else:
                    print ('Partial Deal', order. vtOrderID)
        else:
            if order. vtOrderID in self. idOrderDict:
                del self. idOrderDict[order. vtOrderID]
                if order. status == STATUS_ALLTRADED:
                    print ('All Deal', order. vtOrderID)
                else:
                    print ('Cancel All', order. vtOrderID)

        price = priceUniform(order. price)

        # Withdrawable order and is not in the list, then insert # Deal or Undo, then delete
        if order. status in [STATUS_PARTTRADED, STATUS_PENDING]:
            if not self. priceOrderIdsDict. has_key(price):
                self. priceOrderIdsDict[price] = []
                print ('append ', price)
            orderList = self. priceOrderIdsDict[price]
            if orderList. count(order. vtOrderID) == 0:
                orderList. append(order. vtOrderID)
        # elif order.status in [STATUS_ALLTRADED, STATUS_CANCELLED]:
        else:
            if self. priceOrderIdsDict. has_key(price):
                orderList = self. priceOrderIdsDict[price]
                if orderList. count(order. vtOrderID) > 0:
                    orderList. remove(order. vtOrderID)
                if len(orderList) == 0:
                    del self. priceOrderIdsDict[price]
                    print ('del ', price)

        self. orderUpdate = True


    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        pass


if __name__ == '__main__':
    # Provides the function of direct double-click backtesting
    #The package for PyQt4 is imported to ensure that matplotlib uses PyQt4 instead of PySide, preventing initialization errors
    from ctaBacktesting_tick import *
    from PyQt5 import QtCore, QtGui

    # Create a backtest engine
    engine = BacktestingEngine()

    # Set the backtesting mode of the engine to K line
    engine. setBacktestingMode(engine. BAR_MODE)

    # Set the data start date for backtesting
    engine. setStartDate('20161101')
    # engine.setStartDate('20110101')

    # Set the history database used
    engine. setDatabase(TICK_DB_NAME, 'EUR_USD. OANDA')
    # engine.setDatabase(MINUTE_DB_NAME, 'IF0000')

    # Set product-related parameters
    # engine.setSlippage(0.02) # Stock index 1 hop
    engine. setSlippage(0.0001) # Stock index 1 hop
    engine. setRate(0.3 / 10000) # 万0.3
    engine. setSize(300) # Stock index contract size
    engine. setFreq(5)

    ## Create a policy object in the engine
    # setting = {'atrLength': 11}
    engine. initStrategy(MarketBalance)

    ## Start running backtest
    engine. runBacktesting()

    ## Display backtesting results
    engine. showBacktestingResult()

    # Run optimization
    # setting = OptimizationSetting() # Create a new optimization task settings object
    # setting.setOptimizeTarget('capital') # Set the goal of optimization ordering to the net profit of the strategy
    # setting.addParameter('atrLength', 11, 20, 1) # Add the first optimization parameter, atrLength, start 11, end 12, step 1
    # setting.addParameter('atrMa', 20, 30, 5) # Add a second optimization parameter, atrMa, start 20, end 30, step 1

    # Performance test environment: I7-3770, frequency 3.4G, 8 cores, memory 16G, Windows 7 Pro
    # There are a bunch of other programs running during the test, and the performance is for reference only
    import time

    start = time. time()

    # Run the single-process optimization function and automatically output the result, time-consuming: 359 seconds
    # engine.runOptimization(AtrRsiStrategy, setting)

    # Multi-process optimization, time-consuming: 89 seconds
    # engine.runParallelOptimization(AtrRsiStrategy, setting)

    # print u'耗时：%s' %(time.time()-start)
