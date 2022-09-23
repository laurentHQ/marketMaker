# encoding: UTF-8

'''
This file is for the definition of event type constants only.
Since there is no real concept of constants in python, it is chosen to use all capitalized variable names instead of constants.
The naming convention designed here begins with a EVENT_ prefix.
The contents of a constant typically choose a string that represents the true meaning (easy to understand).
It is recommended that you place all constant definitions in this file to check for duplication.
'''

# System dependent
EVENT_TIMER = 'eTimer' # timer event, sent every 1 second
EVENT_LOG = 'eLog' # log event, global common

# Gateway related
EVENT_TICK = 'eTick.' # TICK market event, followed by specific vtSymbol
EVENT_CANDLE = 'eCandle'

EVENT_TRADE = 'eTrade.' # Deal Return Event
EVENT_ORDER = 'eOrder.' # Reporting Event
EVENT_POSITION = 'ePosition.' # Position Return Event
EVENT_ACCOUNT = 'eAccount.' # Account Returns Event
EVENT_CONTRACT = 'eContract.' # Contract Base Information Reward Event
EVENT_ERROR = 'eError.' # Error Reward Event

# CTA module related
EVENT_CTA_LOG = 'eCtaLog' # CTA-related log event
EVENT_CTA_STRATEGY = 'eCtaStrategy.' # CTA Policy State Change Event

# HF module related
EVENT_HF_LOG = 'eHfLog' # HF-related log event
EVENT_HF_STRATEGY = 'eHfStrategy.' # HF Policy State Change Event

# Quotes record module related
EVENT_DATARECORDER_LOG = 'eDataRecorderLog' # Market Logging Update Event

# Wind interface related
EVENT_WIND_CONNECTREQ = 'eWindConnectReq' # Wind interface request connection event


#----------------------------------------------------------------------
def test():
    """Check for the presence of duplicate content constant definitions"""
    check_dict = {}
    
    global_dict = globals()    
    
    for key, value in global_dict. items():
        if '__' not in key: # does not check python built-in objects 
            if value in check_dict:
                check_dict[value]. append(key)
            else:
                check_dict[value] = [key]
            
    for key, value in check_dict. items():
        if len(value)>1:
            print (u' has a duplicate constant definition: ' + str(key) )
            for name in value:
                print (name)
            print ('')
        
    print (u'Test Complete')
    

# Run the script directly to test
if __name__ == '__main__':
    test()
