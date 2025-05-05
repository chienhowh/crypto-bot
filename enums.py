from enum import Enum

class EntryType(Enum):
    BUY = 'buy'
    SELL = 'sell'
    CLOSE_LONG = 'close_long'
    CLOSE_SHORT = 'close_short'
    REVERSE_TO_LONG = 'reverse_to_long'
    REVERSE_TO_SHORT = 'reverse_to_short'
    STOPLOSS = 'stoploss'
    TAKEPROFIT = 'takeprofit'
    TRAILING_STOP = 'trailing_stop'
    LONG = 'long'
    SHORT = 'short'
    HOLD = 'hold'