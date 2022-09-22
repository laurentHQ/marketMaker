# encoding: UTF-8

'''
The risk control engine is implemented in this document to provide a series of commonly used risk control functions:
1. Delegate flow control (maximum number of orders allowed to be issued per unit time)
2. Total Deal Limit (Daily Total Deal Limit)
3. Control the number of orders in a single order
'''

import json
import the
import platform

from eventEngine import *
from vtConstant import *
from vtGateway import VtLogData
from vtFunction import *

########################################################################
class RmEngine(object):
    """Risk Control Engine"""
    settingFileName = 'RM_setting.json'
    settingFileName = os. path. join(ROOT_PATH, 'cfg', settingFileName)
    
    name = u'Risk Control Module'

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self. mainEngine = mainEngine
        self. eventEngine = eventEngine
        
        # Whether to start risk control
        self. active = False
        
        # Flow control related
        self. orderFlowCount = EMPTY_INT# Delegate count per unit of time
        self. orderFlowLimit = EMPTY_INT# delegate limit
        self. orderFlowClear = EMPTY_INT # Count Clearance Time (seconds).
        self. orderFlowTimer = EMPTY_INT # Count Clearance Time Timing
    
        # Single delegate related
        self. orderSizeLimit = EMPTY_INT # Maximum limit for a single delegate
    
        # Deal statistics related
        self. tradeCount = EMPTY_INT # Statistics on the number of contracts traded on the day
        self. tradeLimit = EMPTY_INT # Limit on the number of contracts traded on the day
        
        # Event contract related
        self. workingOrderLimit = EMPTY_INT # Maximum limit for active contracts

        # Position Control
        self. currentPos = EMPTY_INT
        self. currentPosLimit = EMPTY_INT
        
        self. loadSetting()
        self. registerEvent()
        
    #----------------------------------------------------------------------
    def loadSetting(self):
        """Read Configuration"""
        with open(self. settingFileName) as f:
            d = json. load(f)
            
            # Set risk control parameters
            self. active = d['active']
            
            self. orderFlowLimit = d['orderFlowLimit']
            self. orderFlowClear = d['orderFlowClear']
            
            self. orderSizeLimit = d['orderSizeLimit']
            
            self. tradeLimit = d['tradeLimit']
            
            self. workingOrderLimit = d['workingOrderLimit']

            self. currentPosLimit = d['currentPosLimit']
        
    #----------------------------------------------------------------------
    def saveSetting(self):
        """Save risk parameters"""
        with open(self. settingFileName, 'w') as f:
            # Save risk control parameters
            d = {}

            d['active'] = self. active
            
            d['orderFlowLimit'] = self. orderFlowLimit
            d['orderFlowClear'] = self. orderFlowClear
            
            d['orderSizeLimit'] = self. orderSizeLimit
            
            d['tradeLimit'] = self. tradeLimit
            
            d['workingOrderLimit'] = self. workingOrderLimit

            d['CurrentPosLimit'] = self. currentPosLimit
            
            # Write json
            jsonD = json. dumps(d, indent=4)
            f. write(jsonD)
        
    #----------------------------------------------------------------------
    def registerEvent(self):
        """Register Event Listening"""
        self. eventEngine. register(EVENT_TRADE, self. updateTrade)
        self. eventEngine. register(EVENT_TIMER, self. updateTimer)
        self. eventEngine. register(EVENT_POSITION, self. updatePosition)

    #----------------------------------------------------------------------
    def updateTrade(self, event):
        """Update deal data"""
        trade = event. dict_['data']
        self. tradeCount += trade. volume

    #----------------------------------------------------------------------
    def updatePosition(self, event):
        """Update deal data"""
        pos = event. dict_['data']
        self. currentPos = pos. position
        # print 'currentPos: %s' % self.currentPos
    
    #----------------------------------------------------------------------
    def updateTimer(self, event):
        """Update Timer"""
        self. orderFlowTimer += 1
        
        # If the timing exceeds the time interval for flow control emptying, the clearing is performed
        if self. orderFlowTimer >= self. orderFlowClear:
            self. orderFlowCount = 0
            self. orderFlowTimer = 0
        
    #----------------------------------------------------------------------
    def writeRiskLog(self, content):
        """Fast Log Event"""
        # Beep tone

        if platform. uname() == 'Windows':
            import winsound
            winsound. PlaySound("SystemHand", winsound. SND_ASYNC) 
        
        # Log events are emitted
        log = VtLogData()
        log. logContent = content
        log. gatewayName = self. name
        event = Event(type_=EVENT_LOG)
        event. dict_['data'] = log
        self. eventEngine. put(event)

    #----------------------------------------------------------------------
    def checkRisk(self, orderReq):
        """Check Risk"""
        # If the risk control check is not started, it will return to success directly
        if not self. active:
            return True

        if orderReq. offset in [OFFSET_CLOSE, OFFSET_CLOSETODAY, OFFSET_CLOSEYESTERDAY]:
            volume = -orderReq. volume
        else:
            volume = orderReq. volume
        # Check the current all position
        if (self. currentPos + volume) >= self. currentPosLimit:
            self. writeRiskLog(u'Total Position %s above limit %s'
                              % (self. currentPos, self. currentPosLimit))
            return False

        # Check the number of delegates
        if orderReq. volume > self. orderSizeLimit:
            self. writeRiskLog(u' number of orders per delegate %s, exceeding limit %s' 
                              %(orderReq. volume, self. orderSizeLimit))
            return False
        
        # Check the contract volume
        if self. tradeCount >= self. tradeLimit:
            self. writeRiskLog(u'Total number of contracts traded today%s, exceeding limit %s' 
                              %(self. tradeCount, self. tradeLimit))
            return False
        
        # Check the flow control
        if self. orderFlowCount >= self. orderFlowLimit:
            self. writeRiskLog(u'number of delegate streams %s, exceeding the limit %s per %s seconds' 
                              %(self. orderFlowCount, self. orderFlowClear, self. orderFlowLimit))
            return False
        
        # Check the total active contract
        workingOrderCount = len(self. mainEngine. getAllWorkingOrders())
        if workingOrderCount >= self. workingOrderLimit:
            self. writeRiskLog(u'Current active order number %s, exceeding limit %s'
                              %(workingOrderCount, self. workingOrderLimit))
            return False
        
        # For delegates through risk control, increase the flow control count
        self. orderFlowCount += 1
        
        return True    
    
    #----------------------------------------------------------------------
    def clearOrderFlowCount(self):
        """Empty Flow Count"""
        self. orderFlowCount = 0
        self. writeRiskLog(u'Clear Flow Count')
        
    #----------------------------------------------------------------------
    def clearTradeCount(self):
        """Empty Deal Quantity Count"""
        self. tradeCount = 0
        self. writeRiskLog(u'Empty total deal count')
        
    #----------------------------------------------------------------------
    def setOrderFlowLimit(self, n):
        """Set Flow Control Limits"""
        self. orderFlowLimit = n
        
    #----------------------------------------------------------------------
    def setOrderFlowClear(self, n):
        """Set Flow Control Clearance Time"""
        self. orderFlowClear = n
        
    #----------------------------------------------------------------------
    def setOrderSizeLimit(self, n):
        """Set delegate maximum limit"""
        self. orderSizeLimit = n
        
    #----------------------------------------------------------------------
    def setTradeLimit(self, n):
        """Set deal limits"""
        self. tradeLimit = n
        
    #----------------------------------------------------------------------
    def setWorkingOrderLimit(self, n):
        """Set Activity Contract Limits"""
        self. workingOrderLimit = n

    #----------------------------------------------------------------------
    def setCurrentPosLimit(self, n):
        """Set Activity Contract Limits"""
        self. currentPosLimit = n
        
    #----------------------------------------------------------------------
    def switchEngineStatus(self):
        """Switch risk engine"""
        self. active = not self. active
        
        if self. active:
            self. writeRiskLog (u'Risk Management Function Launched')
        else:
            self. writeRiskLog (u'Risk management function stopped')
