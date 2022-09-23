# encoding: UTF-8

"""
Contains some functions that are commonly used in development
"""

import the
import decimal
import json
from datetime import datetime
import sys
import os


MAX_NUMBER = 10000000000000
MAX_DECIMAL = 4

def getRootPath():
	path = ''
	for i in range(1,10):
		path = os. path. abspath(os. path. dirname('../'*i))
		path = path 
		if os. path. exists(path+'/log/') and os. path. exists(path+'/cfg/'):
			break
	return path

ROOT_PATH = getRootPath()
def appendPath(path):
	files = os. listdir(path)
	for fi in files:
		fi_d = os. path. join(path, fi)
		if os. path. isdir(fi_d):
			sys. path. append(fi_d)
			appendPath(fi_d)

appendPath(ROOT_PATH)

#----------------------------------------------------------------------
def safeUnicode(value):
    """Check the interface data for potential errors to ensure that the converted string is correct"""
    # Check is the upper limit of the floating-point number that appears when the number is close to 0
    if type(value) is int or type(value) is float:
        if value > MAX_NUMBER:
            value = 0
    
    # Check to prevent too many decimal places
    if type(value) is float:
        d = decimal. Decimal(str(value))
        if abs(d. as_tuple(). exponent) > MAX_DECIMAL:
            value = round(value, ndigits=MAX_DECIMAL)
    
    return unicode(value)

#----------------------------------------------------------------------
def loadMongoSetting():
    """Configuration of loading MongoDB database"""
    fileName = 'VT_setting.json'
    fileName = os. path. join(ROOT_PATH, 'cfg', fileName)  
    
    try:
        f = file(fileName)
        setting = json. load(f)
        host = setting['mongoHost']
        port = setting['mongoPort']
    except:
        host = 'localhost'
        port = 27017
        
    return host, port

#----------------------------------------------------------------------
def todayDate():
    """Get the date of the current native PC time"""
    return datetime. now(). replace(hour=0, minute=0, second=0, microsecond=0)    

def priceUniform(price):
    return int(round(float(price)*100))/100.0

def volumeUniform(volume):
    return int(round(float(volume) * 10000)) / 10000.0


if __name__ == '__main__':
    print (ROOT_PATH)