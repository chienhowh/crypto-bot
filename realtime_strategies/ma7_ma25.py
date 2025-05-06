from enums import EntryType
import ccxt
import pandas as pd
import time
from utils import log
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
import sys
from order_action import execute_trade, calculate_order_size
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TEST_KEY = os.getenv("TEST_KEY")
TEST_SECRET = os.getenv("TEST_SECRET")

# symbols = ['BTC/USDT', 'ETH/USDT']
symbols = ['BTC/USDT']
initial_balance = 3000
timeframe = '1h'
fetch_limit = 50
interval = 60  # seconds

exchange_id = 'binance'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': TEST_KEY,
    'secret': TEST_SECRET,
    'options':{'defaultType':'future'}
})

exchange.set_sandbox_mode(True)
exchange.set_leverage(leverage=20, symbol='BTC/USDT')
balance = exchange.fetch_balance()
usdt_balance = balance['USDT']['free'] if 'USDT' in balance else 0
print(usdt_balance)

state = {}
# symbols = ['BTC/USDT', 'ETH/USDT']
symbols = ['BTC/USDT']

for symbol in symbols:
    state[symbol] = {
        'position': None,
    }

def fetch_ohlcv(symbol):
    try:
        # 由于测试网可能数据有限，尝试从真实网络获取历史数据
        real_exchange = ccxt.binance()
        ohlcv = real_exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=fetch_limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        log(f"Error fetching OHLCV: {e}", "ERROR")
        return None
    
# With enum ma7, ma25 移動停利
# 自動停損停利，只要找出交叉就好
def strategy(df):
    df['ma7'] = df['close'].rolling(7).mean()
    df['ma25'] = df['close'].rolling(25).mean()
    df['signal'] = None
    df = df.iloc[:-1].copy()  # 去掉尚未封閉的最後一根 candle
    
    for i in range(26, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
       
        if prev['ma7'] < prev['ma25'] and curr['ma7'] > curr['ma25']:
            df.at[i, 'signal'] = EntryType.BUY

        elif prev['ma7'] > prev['ma25'] and curr['ma7'] < curr['ma25']:
            df.at[i, 'signal'] = EntryType.SELL

    return df
    
def simulate_trade(symbol, df):
    global state
    df = strategy(df)
    last = df.iloc[-1]
    
    signal = last['signal']
    s = state[symbol]
    order_size = calculate_order_size(symbol)
    
    if s['position'] is None:
        if(signal == EntryType.BUY):
            execute_trade(symbol, EntryType.BUY, order_size)
            s['position'] = EntryType.LONG
        elif(signal == EntryType.SELL):
            execute_trade(symbol, EntryType.SELL, order_size)
            s['position'] = EntryType.SHORT

    elif s['position'] == EntryType.LONG and signal == EntryType.SELL:
        execute_trade(symbol, EntryType.REVERSE_TO_SHORT, order_size)
        s['position'] = EntryType.SHORT
    
    elif s['position'] == EntryType.SHORT and signal == EntryType.BUY:
        execute_trade(symbol, EntryType.REVERSE_TO_LONG, order_size)
        s['position'] = EntryType.LONG
    
try:
    log("🚀 Multi-symbol 币安测试网交易开始...")
    # 检查连接
    markets = exchange.load_markets()
    log(f"Successfully connected to Binance Testnet. Available markets: {len(markets)}", "INFO")
    
    while True:
        for symbol in symbols:
            df = fetch_ohlcv(symbol)
            simulate_trade(symbol, df)
        # save_trades()
        time.sleep(interval)

except KeyboardInterrupt:
    log("🛑 停止交易，保存交易记录...")
except Exception as e:
    log(f"Unexpected error: {e}", "ERROR")


# df = fetch_ohlcv('BTC/USDT')
# test = strategy(df)
# print(test)
# if test['signal'] == EntryType.BUY:
#     print('strong buy!!')
# balance = get_balance()
# print('balance', balance)
# print('price', price)
# print('size',calculate_order_size('BTC/USDT',balance))
# size, side = get_position_info('BTC/USDT')
# print('size', size)
# print('side', side)

# print(state)
# s = state['BTC/USDT']
# s['position'] = EntryType.SHORT
# if s['position'] == EntryType.SHORT:
#     print('1111')
# print(state)
