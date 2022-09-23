# encoding: UTF-8
import logging
import the
from vtFunction import *


class vnLog(object):
	def __init__(self, name):
		# Create a logger
		self. logger = logging. getLogger(name)
		self. logger. setLevel(logging. DEBUG)
		# Create a handler to write to the log file
		path = getRootPath()
		path = os. path. join(path, 'log', name)
		fh = logging. FileHandler(path)
		fh. setLevel(logging. DEBUG)
		# Create another handler for output to the console
		ch = logging. StreamHandler()
		ch. setLevel(logging. DEBUG)
		# Define the output format of the handler
		formatter = logging. Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		fh. setFormatter(formatter)
		ch. setFormatter(formatter)
		# Add a handler to the logger
		self. logger. addHandler(fh)
		self. logger. addHandler(ch)

	def write(self, log):
		self. logger. info(log)
		

if __name__ == '__main__':
	print (getRootPath())
	vnlog = vnLog('test_log.txt')
	vnlog. write('hi wu')
