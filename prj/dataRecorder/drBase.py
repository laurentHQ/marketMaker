# encoding: UTF-8

'''
The data formats included in this file are common to the CTA module, and it is necessary for users to add their own formats.
'''

from __future__ import division


# Add the vn.trader root directory to the python environment variable
import sys
sys. path. append('..')


# Database name
SETTING_DB_NAME = 'VnTrader_Setting_Db'
TICK_DB_NAME = 'VnTrader_Tick_Db'
DAILY_DB_NAME = 'VnTrader_Daily_Db'
MINUTE_DB_NAME = 'VnTrader_1Min_Db'


# Data class definitions involved in the CTA engine
from common. vtConstant import EMPTY_UNICODE, EMPTY_STRING, EMPTY_FLOAT, EMPTY_INT


########################################################################
class DrBarData(object):
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

        self. highTime = EMPTY_STRING # the time happening the highest close during the bar
        self. lowTime = EMPTY_STRING # the time happening the lowest close during the bar

        self. volume = EMPTY_INT # volume
        self. openInterest = EMPTY_INT # open interest

        self. turnover = EMPTY_FLOAT # turnover
        self. closePrice = EMPTY_FLOAT # today closePrice

########################################################################
class DrTickData(object):
    """Tick Data"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""       
        self. vtSymbol = EMPTY_STRING # vt system code
        self. symbol = EMPTY_STRING # contract code
        self.  exchange = EMPTY_STRING # exchange code

        # Deal data
        self. lastPrice = EMPTY_FLOAT # Latest Transaction Price
        self. volume = EMPTY_INT # Latest volume
        self. turnover = EMPTY_FLOAT # turnover
        self. openInterest = EMPTY_INT # open interest

        self. openPrice = EMPTY_FLOAT # Today's Open price
        self. closePrice = EMPTY_FLOAT # today closePrice
        self. preClosePrice = EMPTY_FLOAT # Last Close
        self. preSettlementPrice = EMPTY_FLOAT # Yesterday's settlement price
        self. preOpenInterest = EMPTY_FLOAT # Previous Open Positions
        
        self. upperLimit = EMPTY_FLOAT # up and down price
        self. lowerLimit = EMPTY_FLOAT # Stop Price
        
        # tick time
        self.  date = EMPTY_STRING # date
        self.  time = EMPTY_STRING# time
        self. datetime = None #of the datetime objects of the python
        
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
