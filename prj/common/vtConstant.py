# encoding: UTF-8

# Default null value
EMPTY_STRING = ''
EMPTY_UNICODE = u''
EMPTY_INT = 0
EMPTY_FLOAT = 0.0

# Direction constant
DIRECTION_NONE = u 'no direction'
DIRECTION_LONG = u'buy'
DIRECTION_SHORT = u'sell'
DIRECTION_UNKNOWN = u 'Unknown'
DIRECTION_NET = u'square'
DIRECTION_SELL = u'sell' # IB interface

# Open the usual amount
OFFSET_NONE = u'No opening'
OFFSET_OPEN = u 'Open Position'
OFFSET_CLOSE = u'Close Position'
OFFSET_CLOSETODAY = u'flat today'
OFFSET_CLOSEYESTERDAY = u'flat yesterday'
OFFSET_UNKNOWN = u 'unknown'

# Status constant
STATUS_NOTTRADED = u 'unfilled'
STATUS_PARTTRADED = u'partial deal'
STATUS_ALLTRADED = u 'All Deal'
STATUS_CANCELLED = u 'Undone'
STATUS_PENDING = u 'In Queue'
STATUS_UNKNOWN = u 'unknown'
STATUS_NOSENT = u'sentFail'
STATUS_PRESUBMITTED = u'pre_submitted'
STATUS_PRECANCELLED = u'pre_cancelled'

# Contract type constant
PRODUCT_EQUITY = u 'stock'
PRODUCT_FUTURES = u'futures'
PRODUCT_OPTION = u'option'
PRODUCT_INDEX = u 'exponent'
PRODUCT_COMBINATION = u 'combined'
PRODUCT_FOREX = u'Forex'
PRODUCT_UNKNOWN = u 'unknown'
PRODUCT_SPOT = u 'Spot'
PRODUCT_DEFER = u 'deferred'
PRODUCT_NONE = ''

# Price type constant
PRICETYPE_LIMITPRICE = u 'limit'
PRICETYPE_MARKETPRICE = u'mark'
PRICETYPE_FAK = u'FAK'
PRICETYPE_FOK = u'FOK'

# Option type
OPTION_CALL = u'Call Options'
OPTION_PUT = u 'Put Option'

# Exchange type
EXCHANGE_SSE = 'SSE' # SSE
EXCHANGE_SZSE = 'SZSE' # SZSE
EXCHANGE_CFFEX = 'CFFEX' # CICC
EXCHANGE_SHFE = 'SHFE' # previous period
EXCHANGE_CZCE = 'CZCE' # Zheng Shang Suo
EXCHANGE_DCE = 'DCE' # Daishon
EXCHANGE_SGE = 'SGE' # Shangjinsuo
EXCHANGE_UNKNOWN = 'UNKNOWN'# unknown exchange
EXCHANGE_NONE = '' # short exchange
EXCHANGE_HKEX = 'HKEX' # HKEx

EXCHANGE_SMART = 'SMART' # IB Smart Routing (Stocks, Options).
EXCHANGE_NYMEX = 'NYMEX' # IB Futures
EXCHANGE_GLOBEX = 'GLOBEX' # CME electronic trading platform
EXCHANGE_IDEALPRO = 'IDEALPRO' # IB Forex ECN

EXCHANGE_CME = 'CME' # CME Exchange
EXCHANGE_ICE = 'ICE' # ICE exchange

EXCHANGE_OANDA = 'OANDA' # OANDA Forex Market Maker
EXCHANGE_OKCOIN = 'OKCOIN' # OKCOIN Bitcoin Exchange
EXCHANGE_HUOBI = 'HUOBI' # HUOBI Bitcoin Exchange
EXCHANGE_HUOBIETH = 'HUOBIETH' # HUOBI Bitcoin Exchange
EXCHANGE_BTCC = 'BTCC' # BTCC Bitcoin Exchange
EXCHANGE_ZHCOIN = 'ZHCOIN'#'TOKENBANK'

# Currency type
CURRENCY_USD = 'USD' # USD
CURRENCY_CNY = 'CNY' # RMB
CURRENCY_UNKNOWN = 'UNKNOWN' # unknown currency
CURRENCY_NONE = '' # Empty currency

# Currency symbol
SYMBOL_BTC_CNY = 'BTC_CNY'
SYMBOL_ETH_CNY = 'ETH_CNY'
SYMBOL_LTC_CNY = 'LTC_CNY'
