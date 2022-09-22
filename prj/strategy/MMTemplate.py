# encoding: UTF-8

'''
This file contains templates for policy development in the CTA engine, and the CtaTemplate class needs to be inherited when developing policies.
'''

from MMBase import *
from vtConstant import *
from time import sleep

########################################################################
class MMTemplate(object):
    """CTA Policy Template"""
    
    # The name and author of the policy class
    className = 'MMTemplate'
    author = EMPTY_UNICODE
    
    # The name of the MongoDB database, the candlestick database defaults to 1 minute
    tickDbName = TICK_DB_NAME
    barDbName = MINUTE_DB_NAME
    
    # Basic parameters of the policy
    name = EMPTY_UNICODE # Policy instance name
    vtSymbol = EMPTY_STRING # Contract vt system code for trading 
    productClass = EMPTY_STRING # Product type (only required for IB interface).
     currency = EMPTY_STRING # currency (required only for IB interface).
    
    # The basic variables of the policy, managed by the engine
    inited = False # Whether initialized or not
    trading = False # Whether to initiate a transaction is managed by the engine
    pos = [0, 0] # Open Position
    
    # Parameter list, the name of the parameter is saved
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']
    
    # A list of variables that hold the name of the variable
    varList = ['inited',
               'trading',
               'pos']

    #----------------------------------------------------------------------
    def __init__(self, mmEngine, setting):
        """Constructor"""
        self. mmEngine = mmEngine

        # Set the parameters of the policy
        if setting:
            d = self. __dict__
            for key in self. paramList:
                if key in setting:
                    d[key] = setting[key]
    
    #----------------------------------------------------------------------
    def onInit(self):
        """Initialization policy (must be implemented by user inheritance)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStart(self):
        """Startup policy (must be implemented by user inheritance)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStop(self):
        """Stop policy (must be implemented by user inheritance)"""
        raise NotImplementedError

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """Received quote TICK push (must be implemented by user inheritance)"""
        raise NotImplementedError

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """Delegate change push received (must be implemented by user inheritance)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """Deal push received (must be implemented by user inheritance)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """Received Bar push (must be implemented by user inheritance)"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def buy(self, vtSymbol, price, volume, stop=False):
        """Buy it"""
        # print 'buy'
        return self. sendOrder(vtSymbol, CTAORDER_BUY, price, volume, stop)
    
    #----------------------------------------------------------------------
    def sell(self, vtSymbol, price, volume, stop=False):
        """Sell flat"""
        # print 'sell'
        return self. sendOrder(vtSymbol, CTAORDER_SELL, price, volume, stop)

    #----------------------------------------------------------------------
    def short(self, vtSymbol, price, volume, stop=False):
        """Sell out"""
        return self. sendOrder(vtSymbol, CTAORDER_SHORT, price, volume, stop)
 
    #----------------------------------------------------------------------
    def cover(self, vtSymbol, price, volume, stop=False):
        """Buy Flat"""
        return self. sendOrder(vtSymbol, CTAORDER_COVER, price, volume, stop)
        
    #----------------------------------------------------------------------
    def sendOrder(self, vtSymbol, orderType, price, volume, stop=False):
        """Send Delegate"""
        if self. trading:
            # If stop is True, it means that a local stop order is issued
            if stop:
                vtOrderID = self. mmEngine. sendStopOrder(vtSymbol, orderType, price, volume, self)
            else:
                vtOrderID = self. mmEngine. sendOrder(vtSymbol, orderType, price, volume, self)
            return vtOrderID
        else:
            # An empty string is returned when a transaction is stopped
            return ''        
        
    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """Withdraw"""
        # If the order number is an empty string, no subsequent action is taken
        if not vtOrderID:
            return

        if STOPORDERPREFIX in vtOrderID:
            self. mmEngine. cancelStopOrder(vtOrderID)
        else:
            self. mmEngine. cancelOrder(vtOrderID)

    # ----------------------------------------------------------------------
    def updateOrderStrategyDict(self, strategy):
        self. mmEngine. updateOrderStrategyDict(strategy)

    # ----------------------------------------------------------------------
    def getAllWorkingOrders(self, vtSymbol):
        """Query all working orders in target vtSymbol"""
        if self. trading:
            return self. mmEngine. getAllWorkingOrders(vtSymbol)

    # ----------------------------------------------------------------------
    def findVtSymbolWorkingOrders(self, vtSymbol):
        if self. trading:
            return self. mmEngine. findVtSymbolWorkingOrders(vtSymbol)

    # ----------------------------------------------------------------------
    def cancelAll(self, vtSymbol):
        """Cancel All Orders for target vtSymbol"""
        if self. trading:
            self. mmEngine. cancelAll(vtSymbol)

    #----------------------------------------------------------------------
    def insertTick(self, tick):
        """Insert tick data into the database"""
        self. mmEngine. insertData(self. tickDbName, self. vtSymbol, tick)
    
    #----------------------------------------------------------------------
    def insertBar(self, bar):
        """Insert bar data into the database """
        self. mmEngine. insertData(self. barDbName, self. vtSymbol, bar)
        
    #----------------------------------------------------------------------
    def loadTick(self, days):
        """Read tick data"""
        return self. mmEngine. loadTick(self. tickDbName, self. vtSymbol, days)
    
    #----------------------------------------------------------------------
    def loadBar(self, days):
        """Read bar data"""
        return self. mmEngine. loadBar(self. barDbName, self. vtSymbol, days)
    
    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """Record CTA logs"""
        content = self. name + ':' + content
        self. mmEngine. writeCtaLog(content)
        
    #----------------------------------------------------------------------
    def putEvent(self):
        """Emitting Policy State Change Event"""
        self. mmEngine. putStrategyEvent(self. name)
        
    #----------------------------------------------------------------------
    def getEngineType(self):
        """Query currently running environment"""
        return self. mmEngine. engineType
