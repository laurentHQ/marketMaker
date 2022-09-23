# encoding: UTF-8

from __future__ import print_function
from __future__ import print_function
import json
import shelve
from collections import OrderedDict

from pymongo import MongoClient
from pymongo. errors import ConnectionFailure

import sys
sys. path. append('.')
sys. path. append('..')
from common. vtFunction import *
from eventEngine import *
from vtGateway import *


from MMEngine import MMEngine
from rmEngine import RmEngine

########################################################################
class MainEngine(object):
    """Main Engine"""

    # ----------------------------------------------------------------------
    def __init__(self):

        def print_log_err(event):
            class_data = event. dict_['data']. __dict__
            print(str(event. type_) + ": ")
            print(json. dumps(class_data, ensure_ascii=False))

        # Create an event engine
        self. eventEngine = EventEngine2()
        self. eventEngine. register(EVENT_LOG, print_log_err)
        self. eventEngine. register(EVENT_CTA_LOG, print_log_err)
        self. eventEngine. register(EVENT_ERROR, print_log_err)
        self. eventEngine. start()

        # Create a data engine
        self. dataEngine = DataEngine(self. eventEngine)

        # MongoDB database related
        self. dbClient = None # MongoDB client object

        # Call the initialization functions one by one
        self. initGateway()

        # Extension modules
        self. mmEngine = MMEngine(self, self. eventEngine)

        self. rmEngine = RmEngine(self, self. eventEngine)
        self. rmEngine. switchEngineStatus()

    # ----------------------------------------------------------------------
    def initGateway(self):
        """Initialize Interface Object"""
        # The dictionary used to hold the interface object
        self. gatewayDict = OrderedDict()

        try:
            from gateway. okcoinGateway import OkcoinGateway
            self. _addGateway(OkcoinGateway, EXCHANGE_OKCOIN, True)
        except Exception as e:
            print (str(e))

        try:
            from gateway. zhcoinGateway import ZhcoinGateway
            self. _addGateway(ZhcoinGateway, EXCHANGE_ZHCOIN, True)
        except Exception as e:
            print (str(e))
        # try:
        #     from bithumbGateway.bithumbGateway import BithumbGateway
        #     self._addGateway(BithumbGateway, 'BITHUMB')
        #     self.gatewayDict['BITHUMB'].setQryEnabled(True)
        # except Exception, e:
        #     print e
        #
        # try:
        #     from coinoneGateway.coinoneGateway import CoinoneGateway
        #     self._addGateway(CoinoneGateway, 'COINONE')
        #     self.gatewayDict['COINONE'].setQryEnabled(True)
        # except Exception, e:
        #     print e

        # try:
        #     from btccGateway.btccGateway import BtccGateway
        #     self._addGateway(BtccGateway, 'BTCC')
        #     self.gatewayDict['BTCC'].setQryEnabled(True)
        # except Exception as e:
        #     print e

        

    # param: gateway gateway type ; gatewayName interface name
    def _addGateway(self, gateway, gatewayName, needQry):
        self. gatewayDict[gatewayName] = gateway(self. eventEngine, gatewayName)
        self. gatewayDict[gatewayName]. setQryEnabled(needQry)

    # ----------------------------------------------------------------------
    def connect(self, gatewayName, params=None):
        """Connect to a specific name of the interface"""
        if gatewayName in self. gatewayDict:
            gateway = self. gatewayDict[gatewayName]
            gateway. connect()
        else:
            self. writeLog(u' interface does not exist: %s' %  gatewayName)

    def start(self):
        self. mmEngine. initStrategy('Market Balance') # to run the on.init function and set inited = True
        self. mmEngine. startStrategy('Market Balance') # to set trading=True, in order to start trading

    # ----------------------------------------------------------------------
    def subscribe(self, subscribeReq, gatewayName):
        """Subscribe to quotes for a particular interface"""
        if gatewayName in self. gatewayDict:
            gateway = self. gatewayDict[gatewayName]
            gateway. subscribe(subscribeReq)
        else:
            self. writeLog(u' interface does not exist: %s' %  gatewayName)

    # ----------------------------------------------------------------------
    def tickHaltSwitch(self, gatewayName):
        for gate in gatewayName:
            if gate in self. gatewayDict:
                gateway = self. gatewayDict[gate]
                gateway. api. tickHaltSwitch()
            else:
                self. writeLog(u' interface does not exist: %s' %  gate)

    # ----------------------------------------------------------------------
    def sendOrder(self, orderReq, gatewayName):
        """Billing a specific interface"""
        # If the risk control check fails, no order will be issued
        if not self. rmEngine. checkRisk(orderReq):
            return ''

        if gatewayName in self. gatewayDict:
            # print gatewayName
            gateway = self. gatewayDict[gatewayName]
            vtOrderID2 = gateway. sendOrder(orderReq)
            # print 'vtOrderID2 %s' % vtOrderID2
            return vtOrderID2
        else:
            self. writeLog(u' interface does not exist: %s' %  gatewayName)

    # ----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderLst, gatewayName):
        """Cancel order for specific interface"""
        if gatewayName in self. gatewayDict:
            gateway = self. gatewayDict[gatewayName]
            gateway. cancelOrder(cancelOrderLst)
        else:
            self. writeLog(u' interface does not exist: %s' %  gatewayName)

    # ----------------------------------------------------------------------
    def cancelAll(self, gatewayName):
        """One-click revocation of all delegates for a particular interface"""
        l = self. getAllWorkingOrders()
        for order in l:
            req = VtCancelOrderReq()
            req. symbol = order. symbol
            req. exchange = order. exchange
            req. frontID = order. frontID
            req. sessionID = order. sessionID
            req. orderID = order. orderID
            if order. gatewayName == gatewayName: # cancel the orders in the corresponding gateway
                self. cancelOrder(req, order. gatewayName)

    # ----------------------------------------------------------------------
    def qryAccont(self, gatewayName):
        """Query accounts for a specific interface"""
        if gatewayName in self. gatewayDict:
            gateway = self. gatewayDict[gatewayName]
            gateway. qryAccount()
        else:
            self. writeLog(u' interface does not exist: %s' %  gatewayName)

    # ----------------------------------------------------------------------
    def qryPosition(self, gatewayName):
        """Query positions for a particular interface"""
        if gatewayName in self. gatewayDict:
            gateway = self. gatewayDict[gatewayName]
            gateway. qryPosition()
        else:
            self. writeLog(u' interface does not exist: %s' %  gatewayName)

    # ----------------------------------------------------------------------
    def exit(self):
        """Call before exiting the program to ensure a normal exit"""
        # Safely shut down all interfaces
        for gateway in self. gatewayDict. values():
            gateway. close()

        # Stop the event engine
        self. eventEngine. stop()


        # Save the contract data in the data engine to the hard disk
        self. dataEngine. saveContracts()

    # ----------------------------------------------------------------------
    def writeLog(self, content):
        """Fast Log Event"""
        log = VtLogData()
        log. logContent = content
        event = Event(type_=EVENT_LOG)
        event. dict_['data'] = log
        self. eventEngine. put(event)

    # ----------------------------------------------------------------------
    def getContract(self, vtSymbol):
        """Query Contract"""
        return self. dataEngine. getContract(vtSymbol)

    # ----------------------------------------------------------------------
    def getAllContracts(self):
        """Query all contracts (return list)"""
        return self. dataEngine. getAllContracts()

    # ----------------------------------------------------------------------
    def getOrder(self, vtOrderID):
        """Query Delegation"""
        return self. dataEngine. getOrder(vtOrderID)

    # ----------------------------------------------------------------------
    def findOrderID(self, targetPrice, orderType):
        """find Order ID"""
        return self. dataEngine. findOrderID(targetPrice, orderType)

    # ----------------------------------------------------------------------
    def getAllWorkingOrders(self):
        """Query all active delegates (returned list)"""
        return self. dataEngine. getAllWorkingOrders()


########################################################################
# Manage contracts, orders, positions and other data
class DataEngine(object):
    """Data Engine"""
    contractFileName = 'ContractData.vt'

    # ----------------------------------------------------------------------
    def __init__(self, eventEngine):
        """Constructor"""
        self. eventEngine = eventEngine

        # A dictionary to save the contract details
        self. contractDict = {}

        # A dictionary that holds delegate data
        self. orderDict = {}

        # Dictionary to save activity delegation data (i.e. revoked)
        self. workingOrderDict = {}

        # Read the contract data saved on the hard disk
        self. loadContracts()

        # Register event listening
        self. registerEvent()

        self. posDict = {}

    # ----------------------------------------------------------------------
    def updatePosition(self, event):
        pos = event. dict_['data']

        print (pos. __dict__)

    # ----------------------------------------------------------------------
    def updateContract(self, event):
        """Update contract data"""
        contract = event. dict_['data']
        self. contractDict[contract. vtSymbol] = contract
        self. contractDict[contract. symbol] = contract # Using a regular code (excluding exchanges) may result in duplication

    # ----------------------------------------------------------------------
    def getContract(self, vtSymbol):
        """Query contract object"""
        try:
            return self. contractDict[vtSymbol]
        except KeyError:
            return None

    # ----------------------------------------------------------------------
    def getAllContracts(self):
        """Query all contract objects (return list)"""
        return self. contractDict. values()

    # ----------------------------------------------------------------------
    def saveContracts(self):
        """Save all contract objects to the hard disk"""
        pass
        # f = shelve.open(self.contractFileName)
        # f['data'] = self.contractDict
        # f.close()

    # ----------------------------------------------------------------------
    def loadContracts(self):
        """Read contract object from hard disk"""
        pass
        # f = shelve.open(self.contractFileName)
        # if 'data' in f:
        #     d = f['data']
        #     for key, value in d.items():
        #         self.contractDict[key] = value
        # f.close()

    # ----------------------------------------------------------------------
    def updateOrder(self, event):
        order = event. dict_['data']
        self. orderDict[order. vtOrderID] = order

        if order. status in [STATUS_PARTTRADED, STATUS_PENDING]:
            if not self. workingOrderDict. has_key(order. vtOrderID):
                self. workingOrderDict[order. vtOrderID] = order
        else:
            if order. vtOrderID in self. workingOrderDict:
                del self. workingOrderDict[order. vtOrderID]

    # ----------------------------------------------------------------------
    def getOrder(self, vtOrderID):
        """Query Delegation"""
        try:
            return self. orderDict[vtOrderID]
        except KeyError:
            return None

    # ----------------------------------------------------------------------
    def findOrderID(self, targetPrice, orderType):
        """Query Delegation"""
        try:
            lst = []
            for i in self. orderDict:
                if orderType == DIRECTION_LONG:
                    if self. orderDict[i]. __getattribute__('direction') == DIRECTION_LONG:
                        if self. orderDict[i]. __getattribute__('price') >= targetPrice:
                            lst. append(i)
                elif orderType == DIRECTION_SHORT:
                    if self. orderDict[i]. __getattribute__('direction') == DIRECTION_SHORT:
                        if self. orderDict[i]. __getattribute__('price') <= targetPrice:
                            lst. append(i)
            return lst
        except KeyError:
            return None

    # ----------------------------------------------------------------------
    def getAllWorkingOrders(self):
        """Query all active delegates (return list)"""
        return self. workingOrderDict. values()
        # return self.workingOrderDict.keys()

    # ----------------------------------------------------------------------
    def registerEvent(self):
        """Register Event Listening"""
        self. eventEngine. register(EVENT_CONTRACT, self. updateContract)
        self. eventEngine. register(EVENT_ORDER, self. updateOrder)
        # self.eventEngine.register(EVENT_POSITION, self.updatePosition)

if __name__ == '__main__':
    """Test"""
    # from PyQt4 import QtCore
    import sys

    # app = QtCore.QCoreApplication(sys.argv)

    me = MainEngine()

    subscribeReq = VtSubscribeReq()
    subscribeReq. symbol = SYMBOL_BTC_CNY

    me. subscribe(subscribeReq, EXCHANGE_OKCOIN)
    me. connect(EXCHANGE_OKCOIN)
    me. subscribe(subscribeReq, EXCHANGE_ZHCOIN)
    me. connect(EXCHANGE_ZHCOIN)

    me. start()

    while True:
        sleep(100)
    # sys.exit(app.exec_())
