# encoding: UTF-8

# System modules
from queue import Queue, Empty
from threading import Thread, Condition
from time import sleep
from collections import defaultdict

# Third-party modules
from PyQt5. QtCore import QTimer

# Self-developed modules
from eventType import *


########################################################################
class EventEngine(object):
    """
 Event-driven engine
 All variables in the event-driven engine are set to private, which is to prevent carelessness
 The value or state of these variables was modified from the outside, causing a bug.
    
 The variable description
 __queue: Private variables, event queues
 __active: private variables, event engine switches
 __thread: Private variables, event processing threads
 __timer: private variables, timers
 __handlers: Private variables, dictionary of event handlers
    
    
 Method description
 __run: A private method that runs continuously with an event-handling thread
 __process: A private method that processes events, calls a listening function registered in the engine
 __onTimer: A private method that stores timer events into the event queue after a fixed event interval is triggered
 start: Public method to start the engine
 stop: Public method, stops the engine
 register: A public method that registers a listening function with the engine
 unregister: A public method that unregisters the listening function from the engine
 put: A public method that stores a new event to the event queue
    
 The event listening function must be defined as an input parameter that is only an event object, i.e.:
    
 function
    def func(event)
        ...
    
 Object methods
    def method(self, event)
        ...
        
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """Initialize Event Engine"""
        # Event queue
        self. __queue = Queue()
        
        # Event engine switch
        self. __active = False
        
        # Event processing thread
        self. __thread = Thread(target = self. __run)
        
        # Timer, which triggers a timer event
        self. __timer = QTimer()
        self. __timer. timeout. connect(self. __onTimer)
        
        # The __handlers here is a dictionary that holds the corresponding event call relationships
        # The value corresponding to each key is a list of functions that hold the function of listening for the event
        self. __handlers = defaultdict(list)
        
    #----------------------------------------------------------------------
    def __run(self):
        """Engine Run" """
        while self. __active == True:
            try:
                event = self. __queue. get(block  = True, timeout = 1) # The blocking time for the get event is set to 1 second
                self. __process(event)
            except Empty:
                pass
            
    #----------------------------------------------------------------------
    def __process(self, event):
        """Handling Events"""
        # Check if there is a handler that listens for the event
        if event. type_ in self. __handlers:
            # If present, events are passed sequentially to handler execution
            [handler(event) for handler in self. __handlers[event. type_]]
            
            # The above statement is written in Python list parsing, and the corresponding general loop writing method is:
            #for handler in self.__handlers[event.type_]:
                #handler(event)    
               
    #----------------------------------------------------------------------
    def __onTimer(self):
        """Storing timer events into the event queue """
        # Create a timer event
        event = Event(type_=EVENT_TIMER)
        
        # Stores timer events to the queue
        self. put(event)    

    #----------------------------------------------------------------------
    def start(self):
        """Engine start" """
        # Set the engine to start
        self. __active = True
        
        # Start the event processing thread
        self. __thread. start()
        
        # Start the timer, the timer event interval is set to 1 second by default
        self. __timer. start(1000)
    
    #----------------------------------------------------------------------
    def stop(self):
        "Stop Engine"""
        # Set the engine to stop
        self. __active = False
        
        # Stop the timer
        self. __timer. stop()
        
        # Wait for the event-processing thread to exit
        self. __thread. join()
            
    #----------------------------------------------------------------------
    def register(self, type_, handler):
        """Register Event Handler Listening" """
        # Try to get the list of handlers corresponding to the event type, and if there is no defaultDict, a new list will be created automatically
        handlerList = self. __handlers[type_]
        
        # To register a processor that is not in the list of handlers for the event, register the event
        if handler not in handlerList:
            handlerList. append(handler)
            
    #----------------------------------------------------------------------
    def unregister(self, type_, handler):
        """Logout event handler listening"""
        # Try to get a list of handlers for that event type, and ignore the logout request if not 
        handlerList = self. __handlers[type_]
            
        # If the function exists in the list, remove it
        if handler in handlerList:
            handlerList. remove(handler)

        # If the list of functions is empty, the event type is removed from the engine
        if not handlerList:
            del self. __handlers[type_]
            
    #----------------------------------------------------------------------
    def put(self, event):
        """Deposit event into the event queue """
        self. __queue. put(event)


########################################################################
class EventEngine2(object):
    """
 Timers use the event-driven engine of the python thread 
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """Initialize Event Engine"""
        # Event queue
        self. __queue = Queue()
        
        # Event engine switch
        self. __active = False
        
        # Event processing thread
        self. __thread = Thread(target = self. __run)
        
        # Timer, which triggers a timer event
        self. __timer = Thread(target = self. __runTimer)
        self. __timerActive = False # Timer operating status
        self. __timerSleep = 1# Timer trigger interval (default 1 second).
        
        # The __handlers here is a dictionary that holds the corresponding event call relationships
        # The value corresponding to each key is a list of functions that hold the function of listening for the event
        self. __handlers = defaultdict(list)

        self. __eventCondition = Condition()
        self. conditionHalt = 0

    #----------------------------------------------------------------------
    def __run(self):
        """Engine Run" """
        while self. __active == True:
            try:
                event = self. __queue. get(block  = True, timeout = 1) # The blocking time for the get event is set to 1 second
                self. __process(event)
                # if self.conditionHalt:
                #     self.__eventHalt()
            except Empty:
                pass
            
    #----------------------------------------------------------------------
    def __process(self, event):
        """Handling Events"""
        # Check if there is a handler that listens for the event
        if event. type_ in self. __handlers:
            # If present, events are passed sequentially to handler execution
            [handler(event) for handler in self. __handlers[event. type_]]
            
            # The above statement is written in Python list parsing, and the corresponding general loop writing method is:
            #for handler in self.__handlers[event.type_]:
                #handler(event)    
               
    #----------------------------------------------------------------------
    def __runTimer(self):
        """Looping function running in a timer thread" """
        while self. __timerActive:
            # Create a timer event
            event = Event(type_=EVENT_TIMER)
        
            # Stores timer events to the queue
            self. put(event)
            # Wait
            sleep(self. __timerSleep)

    #----------------------------------------------------------------------
    def start(self):
        """Engine start" """
        # Set the engine to start
        self. __active = True
        
        # Start the event processing thread
        self. __thread. start()
        
        # Start the timer, the timer event interval is set to 1 second by default
        self. __timerActive = True
        self. __timer. start()
    
    #----------------------------------------------------------------------
    def stop(self):
        "Stop Engine"""
        # Set the engine to stop
        self. __active = False
        
        # Stop the timer
        self. __timerActive = False
        self. __timer. join()
        
        # Wait for the event-processing thread to exit
        self. __thread. join()
            
    #----------------------------------------------------------------------
    def register(self, type_, handler):
        """Register Event Handler Listening" """
        # Try to get the list of handlers corresponding to the event type, and if there is no defaultDict, a new list will be created automatically
        handlerList = self. __handlers[type_]
        
        # To register a processor that is not in the list of handlers for the event, register the event
        if handler not in handlerList:
            handlerList. append(handler)
            
    #----------------------------------------------------------------------
    def unregister(self, type_, handler):
        """Logout event handler listening"""
        # Try to get a list of handlers for that event type, and ignore the logout request if not 
        handlerList = self. __handlers[type_]
            
        # If the function exists in the list, remove it
        if handler in handlerList:
            handlerList. remove(handler)

        # If the list of functions is empty, the event type is removed from the engine
        if not handlerList:
            del self. __handlers[type_]  
        
    #----------------------------------------------------------------------
    def put(self, event):
        """Deposit event into the event queue """
        self. __queue. put(event)

    #----------------------------------------------------------------------
    def timerHalt(self):
        self. __timerActive = False

    #----------------------------------------------------------------------
    def timerProceed(self):
        self. __timerActive = True

    #----------------------------------------------------------------------
    def __eventHalt(self):
        # Wait for the single callback to push the delegate number information
        self. __eventCondition. acquire()
        self. __eventCondition. wait()
        self. __eventCondition. release()

    #----------------------------------------------------------------------
    def eventProceed(self):
        # When the delegate number is received, the thread that sent the delegate is notified that the delegate number is returned
        self. __eventCondition. acquire()
        self. __eventCondition. notify()
        self. __eventCondition. release()

        self. conditionHalt = 0

########################################################################
class Event:
    """Event Object"""

    #----------------------------------------------------------------------
    def __init__(self, type_=None):
        """Constructor"""
        self. type_ = type_# Event type
        self. dict_={}# dictionary is used to hold specific event data


#----------------------------------------------------------------------
def test():
    """Test function"""
    import sys
    from datetime import datetime
    from PyQt5. QtCore import QCoreApplication
    
    def simpletest(event):
        print(u' handles timer events triggered per second: %s' %  str(datetime. now()))
    
    app = QCoreApplication(sys. argv)
    
    ee = EventEngine2()
    ee. register(EVENT_TIMER, simpletest)
    ee. start()
    
    app. exec_()
    
    
# Run the script directly to test
if __name__ == '__main__':
    test()
