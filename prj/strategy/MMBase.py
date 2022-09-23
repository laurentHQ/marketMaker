# encoding: UTF-8

'''
This file contains some of the basic settings, classes, constants, etc. used in the CTA module.
'''

from __future__ import division

# Constant definition
# Types of trade directions involved in the CTA engine
CTAORDER_BUY = u'buy'
CTAORDER_SELL = u'sell flat'
CTAORDER_SHORT = u'sell'
CTAORDER_COVER = u'buy flat'

# Local stop single state
STOPORDER_WAITING = u'pending'
STOPORDER_CANCELLED = u'Undone'
STOPORDER_TRIGGERED = u'fired'

# Local stop single prefix
STOPORDERPREFIX = 'CtaStopOrder.'

# Database name
SETTING_DB_NAME = 'VnTrader_Setting_Db'
TICK_DB_NAME = 'VnTrader_Tick_Db'
DAILY_DB_NAME = 'VnTrader_Daily_Db'
MINUTE_DB_NAME = 'VnTrader_1Min_Db'

# Engine type, which is used to distinguish the environment in which the current policy is run
ENGINETYPE_BACKTESTING = 'backtesting' # backtesting
ENGINETYPE_TRADING = 'trading' # Real

# Data class definitions involved in the CTA engine
from vtConstant import EMPTY_UNICODE, EMPTY_STRING, EMPTY_FLOAT, EMPTY_INT

########################################################################
class StopOrder(object):
    """Local stop order"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self. vtSymbol = EMPTY_STRING
        self. orderType = EMPTY_UNICODE
        self. direction = EMPTY_UNICODE
        self. offset = EMPTY_UNICODE
        self. price = EMPTY_FLOAT
        self. volume = EMPTY_INT
        
        self. strategy = None # The policy object for placing a stop order
        self. stopOrderID = EMPTY_STRING# Local number of the stop order 
        self. status = EMPTY_STRING # Stop order state


########################################################################
class CtaBarData(object):
    """K-line data"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self. vtSymbol = EMPTY_STRING # vt system code
        self. symbol = EMPTY_STRING # code
        self.  exchange = EMPTY_STRING # exchange
    
        self. open = EMPTY_FLOAT # OHLC
        self. high = EMPTY_FLOAT
        self. low = EMPTY_FLOAT
        self. close = EMPTY_FLOAT
        
        self.  date = EMPTY_STRING # bar start time, date
        self.  time = EMPTY_STRING# time
        self. datetime = None #of the datetime objects of the python
        
        self. volume = EMPTY_INT # volume
        self. openInterest = EMPTY_INT # open interest


########################################################################
class MMTickData(object):
    "Tick Data"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""       
        self. vtSymbol = EMPTY_STRING # vt system code
        self. symbol = EMPTY_STRING # contract code
        self.  exchange = EMPTY_STRING # exchange code

        # Deal data
        self. lastPrice = EMPTY_FLOAT # Latest Transaction Price
        self. volume = EMPTY_INT # Latest volume
        self. openInterest = EMPTY_INT # open interest
        
        self. upperLimit = EMPTY_FLOAT # up and down price
        self. lowerLimit = EMPTY_FLOAT # Stop Price
        
        # tick time
        self.  date = EMPTY_STRING # date
        self.  time = EMPTY_STRING# time
        # self.lastTradeTime = EMPTY_STRING

        self. datetime = None #of the datetime objects of the python

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
