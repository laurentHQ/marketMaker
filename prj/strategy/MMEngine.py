# encoding: UTF-8

'''
This document implements the CTA policy engine, which abstracts and simplifies the functions of some of the underlying interfaces for CTA-type policies.
About the Rules of Peace and Yesterday Peace:
1. Ordinary closing OFFSET_CLOSET equal to closing last OFFSET_CLOSEYESTERDAY
2. Only the varieties of the previous period need to consider the difference between the present and the ordinary yesterday
3. When the futures of the previous period have this position, call Sell and Cover will use OFFSET_CLOSETODAY, otherwise
 OFFSET_CLOSE will be used
4. The above design means that if the number of Sell and Cover exceeds the current open position, it will lead to an error (i.e. the user
 Hope to pass a directive at the same time peace yesterday )
5. The reason for adopting the above design is to consider that vn.trader's users are mainly for TB, MC and pyramid platforms
 Users who feel inadequate (i.e. want to trade more frequently), trading strategies should not appear in the situation described in 4
6. For users who want to implement the situation described in 4, it is necessary to implement a separate strategy signal engine and a trading order engine
 Customized system structure (yes, you have to write it yourself)
'''

import json
import the
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta
from time import sleep

from MMBase import *
from MMSetting import STRATEGY_CLASS
import sys
sys. path. append('.')
sys. path. append('..')
from vtFunction import *
from eventEngine import *
from vtConstant import *
from vtGateway import VtSubscribeReq, VtOrderReq, VtCancelOrderReq, VtLogData



########################################################################
class MMEngine(object):
    """CTA Policy Engine"""
    settingFileName = 'MM_setting.json'
    settingFileName = os. path. join(ROOT_PATH, 'cfg', settingFileName)

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self. mainEngine = mainEngine
        self. eventEngine = eventEngine
        
        # Current date
        self. today = todayDate()
        
        # Save the dictionary of the policy instance
        # key is the policy name and value is the policy instance, note that the policy name is not allowed to be duplicated
        self. strategyDict = {}
        
        # Dictionary for saving vtSymbol and policy instance map (for pushing tick data)
        Since it is possible for multiple strategies to trade the same vtSymbol, the key is vtSymbol
        # value is the list that contains all related strategy objects
        self. tickStrategyDict = {}
        
        # Dictionary for saving vtOrderID and strategy object mappings (for pushing order and trade data)
        # key is vtOrderID and value is the strategy object
        self. orderStrategyDict = {}     
        
        # Local stop single number count
        self. stopOrderCount = 0
        # stopOrderID = STOPORDERPREFIX + str(stopOrderCount)
        
        # Stop the single dictionary locally
        # key is stopOrderID and value is the stopOrder object
        self. stopOrderDict = {} # The stop order is not removed from this dictionary after it is undone
        self. workingStopOrderDict = {} # Stopsheet is removed from this dictionary when it is undone
        
        # Position cache dictionary
        # key is vtSymbol, and value is the PositionBuffer object
        self. posBufferDict = {}

        # A collection of deal numbers to filter the deals that have already been received
        self. tradeSet = set()

        # The engine type is real
        self. engineType = ENGINETYPE_TRADING
        
        # Register event listening
        self. registerEvent()

        self. loadSetting()
 
    #----------------------------------------------------------------------
    def sendOrder(self, vtSymbol, orderType, price, volume, strategy):
        """Billing"""
        # self.mainEngine.tickHaltSwitch(['OKCOIN', 'ZHCOIN']) # halt receiving the tick info from OKCOIN and ZHCOIN
        # print 'aaa'
        contract = self. mainEngine. getContract(vtSymbol)
        # print 'contract %s' % contract.__dict__
        req = VtOrderReq()
        req. symbol = contract. symbol
        req. exchange = contract. exchange
        req. price = price
        req. volume = volume
        
        req. productClass = strategy. productClass
        req. currency = strategy. currency        
        
        # Delegates designed for the CTA engine are only allowed to use limit orders
        req. priceType = PRICETYPE_LIMITPRICE    
        
        # CTA delegate type mapping
        if orderType == CTAORDER_BUY:
            req. direction = DIRECTION_LONG
            req. offset = OFFSET_OPEN
            
        elif orderType == CTAORDER_SELL:
            req. direction = DIRECTION_SHORT
            
            # Only in the last period should we consider the ordinary present and the ordinary yesterday
            if contract. exchange != EXCHANGE_SHFE:
                req. offset = OFFSET_CLOSE
            else:
                # Get position cache data
                posBuffer = self. posBufferDict. get(vtSymbol, None)
                # If it fails to get the position cache, it will be closed by default
                if not posBuffer:
                    req. offset = OFFSET_CLOSE
                # Otherwise, if there is a long position, then use the flat this time
                alif posBuffer. longToday:
                    req. offset= OFFSET_CLOSETODAY
                # Other cases use flat yesterday
                else:
                    req. offset = OFFSET_CLOSE
                
        elif orderType == CTAORDER_SHORT:
            req. direction = DIRECTION_SHORT
            req. offset = OFFSET_OPEN
            
        elif orderType == CTAORDER_COVER:
            req. direction = DIRECTION_LONG
            
            # Only in the last period should we consider the ordinary present and the ordinary yesterday
            if contract. exchange != EXCHANGE_SHFE:
                req. offset = OFFSET_CLOSE
            else:
                # Get position cache data
                posBuffer = self. posBufferDict. get(vtSymbol, None)
                # If it fails to get the position cache, it will be closed by default
                if not posBuffer:
                    req. offset = OFFSET_CLOSE
                # Otherwise, if there is a short position, then use the flat today
                alif posBuffer. shortToday:
                    req. offset= OFFSET_CLOSETODAY
                # Other cases use flat yesterday
                else:
                    req. offset = OFFSET_CLOSE

        vtOrderID = self. mainEngine. sendOrder(req, contract. gatewayName) # 发单

        # print vtOrderID
        self. orderStrategyDict[vtOrderID] = strategy # Saves the mapping of vtOrderID and policy
        # self.writeCtaLog(u'策略%s发送委托，%s，%s，%s@%s' %(strategy.name, vtSymbol, req.direction, volume, price))
        # logger.info(u'策略%s发送委托，%s，%s，%s@%s' %(strategy.name, vtSymbol, req.direction, volume, price))
        
        return vtOrderID

    # ----------------------------------------------------------------------
    def findOrderId(self, targetPrice, orderType):
        """find Order ID"""
        orderIdlst = self. mainEngine. findOrderID(targetPrice, orderType)
        return orderIdlst

    # ----------------------------------------------------------------------
    def updateOrderStrategyDict(self, strategy):
        """Execute at the beginning to update last-time open(untraded) orders """
        initAllWorkingOrders = self. mainEngine. getAllWorkingOrders()
        for ord in initAllWorkingOrders:
            if not ord. vtOrderID in self. orderStrategyDict:
                self. orderStrategyDict[ord. vtOrderID] = strategy # Saves the mapping of vtOrderID and policy

    #----------------------------------------------------------------------
    def findVtSymbolWorkingOrders(self, vtSymbol):
        """get all working orders in the corresponding vtSymbol of strategy"""
        allWorkingOrders = self. mainEngine. getAllWorkingOrders()
        # print 'findVtSymbolWorkingOrders %s' % allWorkingOrders
        vtSymbolWorkingOrders = []
        for ord in allWorkingOrders:
            if ord. vtOrderID in self. orderStrategyDict:
                if ord. vtSymbol == vtSymbol:
                    vtSymbolWorkingOrders. append(ord)

        return len(vtSymbolWorkingOrders)

    #----------------------------------------------------------------------
    def findWorkingOrders(self):
        """Check how many orders are in workingOrders"""
        return len(self. mainEngine. getAllWorkingOrders())

    #----------------------------------------------------------------------
    def getAllWorkingOrders(self):
        return self. mainEngine. getAllWorkingOrders()

    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """Withdraw"""
        # self.mainEngine.tickHaltSwitch(['OKCOIN', 'ZHCOIN']) # halt receiving the tick info from OKCOIN and ZHCOIN
        # print 'cancelOrder: %s' % vtOrderID
        # Query the order object
        orderIdlst = []
        gatewayName = ''
        for id in vtOrderID:
            order = self. mainEngine. getOrder(id)
            # If the query is successful
            if order:
                # Check whether the order is still valid, and only issue a cancellation order when it is valid
                orderFinished = (order. status == STATUS_ALLTRADED or order. status == STATUS_CANCELLED)
                if not orderFinished:
                    orderIdlst. append(order. orderID)
                    gatewayName = order. gatewayName

        if orderIdlst:
            self. mainEngine. cancelOrder(orderIdlst, gatewayName)
            # sleep(120) # wait 2 minutes
            # self.mainEngine.tickHaltSwitch(['OKCOIN', 'ZHCOIN'])  # proceed receiving the tick info from OKCOIN and ZHCOIN

    # ----------------------------------------------------------------------
    def cancelAll(self, vtSymbol):
        """Cancel All orders"""
        contract = self. mainEngine. getContract(vtSymbol)
        self. mainEngine. cancelAll(contract. gatewayName)
        self. writeCtaLog(u'%s Send Cancel Delegate' %  vtSymbol)

    #----------------------------------------------------------------------
    def getContract(self, vtSymbol):
        return self. mainEngine. getContract(vtSymbol)

    #----------------------------------------------------------------------
    def sendStopOrder(self, vtSymbol, orderType, price, volume, strategy):
        """Send stop order (local implementation)"""
        self. stopOrderCount += 1
        stopOrderID = STOPORDERPREFIX + str(self. stopOrderCount)
        
        so = StopOrder()
        so. vtSymbol = vtSymbol
        so. orderType = orderType
        so. price = price
        so. volume = volume
        so. strategy = strategy
        so. stopOrderID = stopOrderID
        so. status = STOPORDER_WAITING
        
        if orderType == CTAORDER_BUY:
            so. direction = DIRECTION_LONG
            so. offset = OFFSET_OPEN
        elif orderType == CTAORDER_SELL:
            so. direction = DIRECTION_SHORT
            so. offset = OFFSET_CLOSE
        elif orderType == CTAORDER_SHORT:
            so. direction = DIRECTION_SHORT
            so. offset = OFFSET_OPEN
        elif orderType == CTAORDER_COVER:
            so. direction = DIRECTION_LONG
            so. offset = OFFSET_CLOSE           
        
        # Save the stopOrder object to the dictionary
        self. stopOrderDict[stopOrderID] = so
        self. workingStopOrderDict[stopOrderID] = so
        
        return stopOrderID
    
    #----------------------------------------------------------------------
    def cancelStopOrder(self, stopOrderID):
        """Undo stop order"""
        # Check if the stop order exists
        if stopOrderID in self. workingStopOrderDict:
            so = self. workingStopOrderDict[stopOrderID]
            so. status = STOPORDER_CANCELLED
            del self. workingStopOrderDict[stopOrderID]

    #----------------------------------------------------------------------
    def processStopOrder(self, tick):
        """Processing local stop orders after receiving quotes (check if they are to be issued immediately)"""
        vtSymbol = tick. vtSymbol
        
        # First check if there is a strategy to trade the contract
        if vtSymbol in self. tickStrategyDict:
            # Traverse the pending stop order to check if it will be triggered
            for so in self. workingStopOrderDict. values():
                if so. vtSymbol == vtSymbol:
                    longTriggered = so. direction==DIRECTION_LONG and tick. lastPrice>=so. price # The long stop order is triggered
                    shortTriggered = so. direction==DIRECTION_SHORT and tick. lastPrice<=so. Price # Short stop order is triggered
                    
                    if longTriggered or shortTriggered:
                        # Buy and sell orders are issued at the stop-and-go price respectively (simulated market order)
                        if so. direction==DIRECTION_LONG:
                            price = tick. upperLimit
                        else:
                            price = tick. lowerLimit
                        
                        so. status = STOPORDER_TRIGGERED
                        self. sendOrder(so. vtSymbol, so. orderType, price, so. volume, so. strategy)
                        del self. workingStopOrderDict[so. stopOrderID]

    #----------------------------------------------------------------------
    def processTickEvent(self, event):
        tick = event. dict_['data']
        if tick. vtSymbol in self. tickStrategyDict:
            mmTick = MMTickData()
            d = mmTick. __dict__
            for key in d. keys():
                if key != 'datetime':
                    d[key] = tick. __getattribute__(key)
            if tick. exchange in ["ZHCOIN"]:
                mmTick. datetime = datetime. strptime(' '. join([tick. date, tick. time]), '%Y%m%d %H:%M:%S')
            else:
                mmTick. datetime = datetime. strptime(' '. join([tick. date, tick. time]), '%Y%m%d %H:%M:%S.%f')


            l = self. tickStrategyDict[tick. vtSymbol]
            for strategy in l:
                if strategy. inited:
                    self. callStrategyFunc(strategy, strategy. onTick, mmTick)
    
    #----------------------------------------------------------------------
    def processOrderEvent(self, event):
        """Handling delegate push"""
        order = event. dict_['data']
        for k in self. strategyDict:
            strategy = self. strategyDict[k]
            self. callStrategyFunc(strategy, strategy. onOrder, order)
    
    #----------------------------------------------------------------------
    def processTradeEvent(self, event):
        """Process deal push"""
        trade = event. dict_['data']
        # print 'processTrade: %s' % trade.__dict__
        # if trade.vtSymbol in self.tickStrategyDict:
        # # Push to the policy instances one by one
        #     l = self.tickStrategyDict[trade.vtSymbol]
        #     for strategy in l:
        #         self.callStrategyFunc(strategy, strategy.onTick, trade)

        # Filter the returns of deals that have been received
        if trade. vtTradeID in self. tradeSet:
            return
        self. tradeSet. add(trade. vtTradeID)

        if trade. vtOrderID in self. orderStrategyDict:
            strategy = self. orderStrategyDict[trade. vtOrderID]
            sg = '.'. join([trade. symbol, trade. gatewayName])

            if sg == strategy. tarVtSymbol:
                # Calculate strategy positions
                if trade. direction == DIRECTION_LONG:
                    strategy. pos[0] += trade. volume
                else:
                    strategy. pos[0] -= trade. volume
            elif sg == strategy. refVtSymbol:
                # Calculate strategy positions
                if trade. direction == DIRECTION_LONG:
                    strategy. pos[1] += trade. volume
                else:
                    strategy. pos[1] -= trade. volume

            self. callStrategyFunc(strategy, strategy. onTrade, trade)

        # Update position cache data
        if trade. vtSymbol in self. tickStrategyDict:
            posBuffer = self. posBufferDict. get(trade. vtSymbol, None)
            if not posBuffer:
                posBuffer = PositionBuffer()
                posBuffer. vtSymbol = trade. vtSymbol
                self. posBufferDict[trade. vtSymbol] = posBuffer
            posBuffer. updateTradeData(trade)
            
    #----------------------------------------------------------------------
    def processPositionEvent(self, event):
        """Process position push"""
        pos = event. dict_['data']
        
        # Update position cache data
        if pos. vtSymbol in self. tickStrategyDict:
            posBuffer = self. posBufferDict. get(pos. vtSymbol, None)
            if not posBuffer:
                posBuffer = PositionBuffer()
                posBuffer. vtSymbol = pos. vtSymbol
                self. posBufferDict[pos. vtSymbol] = posBuffer
            posBuffer. updatePositionData(pos)
    
    #----------------------------------------------------------------------
    def registerEvent(self):
        """Register Event Listening"""
        self. eventEngine. register(EVENT_TICK, self. processTickEvent)
        self. eventEngine. register(EVENT_ORDER, self. processOrderEvent)
        # self.eventEngine.register(EVENT_TRADE, self.processTradeEvent)
        # self.eventEngine.register(EVENT_POSITION, self.processPositionEvent)

    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """Fast issue CTA module log events"""
        log = VtLogData()
        log. logContent = content
        event = Event(type_=EVENT_CTA_LOG)
        event. dict_['data'] = log
        self. eventEngine. put(event)   
    
    #----------------------------------------------------------------------
    def __loadStrategy(self, setting):
        """Onboarding Policy"""
        try:
            name = setting['name']
            className = setting['className']
        except Exception as e:
            self. writeCtaLog(u'Loading policy error: %s' %e)
            return
        
        # Get the policy class
        strategyClass = STRATEGY_CLASS. get(className, None)
        if not strategyClass:
            self. writeCtaLog(u' Policy class not found: %s' %className)
            return
        
        # Prevent policy rename
        if name in self. strategyDict:
            self. writeCtaLog(u' policy instance duplicate: %s' %name)
        else:
            # Create a policy instance
            strategy = strategyClass(self, setting)  
            self. strategyDict[name] = strategy
            # Save the Tick mapping relationship
            # It is possible to have 1 vtSymbol to multiple strategies
            # Plus, it is also possible to have multiple vtSymbols to 1 strategy
            for symbol in strategy. vtSymbol:
                if symbol in self. tickStrategyDict:
                    l = self. tickStrategyDict[symbol]
                else:
                    l = []
                    self. tickStrategyDict[symbol] = l
                l. append(strategy)

            # Subscribe to the contract
            # contract = self.mainEngine.getContract(strategy.vtSymbol)
            # if contract:
            #     req = VtSubscribeReq()
            #     req.symbol = contract.symbol
            #     req.exchange = contract.exchange
            #
            # # For the currency and product type required by the IB interface to subscribe to quotes, get it from the policy properties
            #     req.currency = strategy.currency
            #     req.productClass = strategy.productClass
            #
            #     self.mainEngine.subscribe(req, contract.gatewayName)
            # else:
            # self.writeCtaLog(u'%s trading contract%s cannot be found'%(name, strategy.vtSymbol))

    #----------------------------------------------------------------------
    def initStrategy(self, name):
        """Initialization policy"""
        if name in self. strategyDict:
            strategy = self. strategyDict[name]
            
            if not strategy. inited:
                strategy. inited = True
                self. callStrategyFunc(strategy, strategy. onInit)
            else:
                self. writeCtaLog(u'Do not repeat the initialization policy instance: %s' %name)
        else:
            self. writeCtaLog(u' policy instance does not exist: %s' %name)        

    #---------------------------------------------------------------------
    def startStrategy(self, name):
        """Startup Policy"""
        if name in self. strategyDict:
            strategy = self. strategyDict[name]
            
            if strategy. inited and not strategy. trading:
                strategy. trading = True
                self. callStrategyFunc(strategy, strategy. onStart)
        else:
            self. writeCtaLog(u' policy instance does not exist: %s' %name)
    
    #----------------------------------------------------------------------
    def stopStrategy(self, name):
        """Stop the ruse"""
        if name in self. strategyDict:
            strategy = self. strategyDict[name]
            
            if strategy. trading:
                strategy. trading = False
                self. callStrategyFunc(strategy, strategy. onStop)
                
                # Cancel all limit orders issued by the strategy
                for vtOrderID, s in self. orderStrategyDict. items():
                    if s is strategy:
                        self. cancelOrder(vtOrderID)
                
                # Cancel all local stop orders issued for this policy
                for stopOrderID, so in self. workingStopOrderDict. items():
                    if so. strategy is strategy:
                        self. cancelStopOrder(stopOrderID)   
        else:
            self. writeCtaLog(u' policy instance does not exist: %s' %name)        
    
    #----------------------------------------------------------------------
    def saveSetting(self):
        """Save Policy Configuration"""
        with open(self. settingFileName, 'w') as f:
            l = []
            
            for strategy in self. strategyDict. values():
                setting = {}
                for param in strategy. paramList:
                    setting[param] = strategy. __getattribute__(param)
                l. append(setting)
            
            jsonL = json. dumps(l, indent=4)
            f. write(jsonL)
    
    #----------------------------------------------------------------------
    def loadSetting(self):
        """Read Policy Configuration"""
        with open(self. settingFileName) as f:
            l = json. load(f)
            
            for setting in l:
                self. __loadStrategy(setting)
    
    #----------------------------------------------------------------------
    def getStrategyVar(self, name):
        """Get the current variable dictionary of the policy"""
        if name in self. strategyDict:
            strategy = self. strategyDict[name]
            varDict = OrderedDict()
            
            for key in strategy. varList:
                varDict[key] = strategy. __getattribute__(key)
            
            return varDict
        else:
            self. writeCtaLog(u' policy instance does not exist: ' + name)    
            return None
    
    #----------------------------------------------------------------------
    def getStrategyParam(self, name):
        """Get parameter dictionary for policy"""
        if name in self. strategyDict:
            strategy = self. strategyDict[name]
            paramDict = OrderedDict()
            
            for key in strategy. paramList: 
                paramDict[key] = strategy. __getattribute__(key)
            
            return paramDict
        else:
            self. writeCtaLog(u' policy instance does not exist: ' + name)    
            return None   
        
    #----------------------------------------------------------------------
    def putStrategyEvent(self, name):
        """Trigger policy state change events (typically used to notify GUI updates)"""
        event = Event(EVENT_CTA_STRATEGY+name)
        self. eventEngine. put(event)
        
    #----------------------------------------------------------------------
    def callStrategyFunc(self, strategy, func, params=None):
        """A function that calls the policy to catch an exception if it triggers"""
        try:
            if params:
                func(params)
            else:
                func()
        except Exception:
            # Stop the policy, modify the status to Uninitialized
            strategy. trading = False
            strategy. inited = False
            
            # Issue logs
            print traceback. format_exc()
            content = '\n'. join([u'Policy%sTriggered Exception Stopped'%strategy.' name,
                                traceback. format_exc()])
            self. writeCtaLog(content)


########################################################################
class PositionBuffer(object):
    """Position cache information (locally maintained position data)"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self. vtSymbol = EMPTY_STRING
        
        # Bulls
        self. longPosition = EMPTY_INT
        self. longToday = EMPTY_INT
        self. longYd = EMPTY_INT
        
        # Bears
        self. shortPosition = EMPTY_INT
        self. shortToday = EMPTY_INT
        self. shortYd = EMPTY_INT
        
    #----------------------------------------------------------------------
    def updatePositionData(self, pos):
        """Update position data"""
        if pos. direction == DIRECTION_LONG:
            self. longPosition = pos. position
            self. longYd = pos. ydPosition
            self. longToday = self. longPosition - self. longYd
        else:
            self. shortPosition = pos. position
            self. shortYd = pos. ydPosition
            self. shortToday = self. shortPosition - self. shortYd
    
    #----------------------------------------------------------------------
    def updateTradeData(self, trade):
        """Update deal data"""
        if trade. direction == DIRECTION_LONG:
            # Multi-party position, corresponding to the increase of the long position and this position
            if trade. offset == OFFSET_OPEN:
                self. longPosition += trade. volume
                self. longToday += trade. volume
            # Multi-side flat today, corresponding to the short position and this position decreased
            elif trade. offset == OFFSET_CLOSETODAY:
                self. shortPosition -= trade. volume
                self. shortToday -= trade. volume
            # Multi-sided flat yesterday, corresponding to the short position and yesterday's position decreased
            else:
                self. shortPosition -= trade. volume
                self. shortYd -= trade. volume
        else:
            # Bears are the same as bulls
            if trade. offset == OFFSET_OPEN:
                self. shortPosition += trade. volume
                self. shortToday += trade. volume
            elif trade. offset == OFFSET_CLOSETODAY:
                self. longPosition -= trade. volume
                self. longToday -= trade. volume
            else:
                self. longPosition -= trade. volume
                self. longYd -= trade. volume
        
        
    
    
