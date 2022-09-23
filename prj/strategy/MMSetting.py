
# encoding: UTF-8

'''
Introduce all the policy classes that you want to use in your system in this file
This dictionary holds the name of the policy to be run and the mapping relationship of the policy class.
After the user's policy class is written, it is first introduced in the file, and the name is set, and then
Write the class and contract settings for each policy object in CTA_setting.json.
'''

from MMstrategy_v5 import MarketBalance
STRATEGY_CLASS = {}
STRATEGY_CLASS['MarketBalance'] = MarketBalance
