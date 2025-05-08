from enums import EntryType
import pandas as pd
import time
from utils import log
from order_action import execute_trade, calculate_order_size
from config import symbols, timeframe, fetch_limit, interval



state = {symbol: {'position': None} for symbol in symbols}

def run(exchange):
    def fetch_ohlcv(symbol):
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=fetch_limit)
            if not ohlcv:
                log(f"❌ {symbol} OHLCV 資料為空", "ERROR")
                return None
            
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
        
        if df is None or df.empty:
            log(f"❌ OHLCV 資料為 None 或空值，跳過 {symbol} 的交易模擬", "ERROR")
            return
        
        df = strategy(df)
        last = df.iloc[-1]
        
        signal = last['signal']
        s = state[symbol]
        print('monitor', symbol, signal)
        order_size = calculate_order_size(exchange ,symbol)
        
        if s['position'] is None:
            if(signal == EntryType.BUY):
                execute_trade(exchange, symbol, EntryType.BUY, order_size)
                s['position'] = EntryType.LONG
            elif(signal == EntryType.SELL):
                execute_trade(exchange, symbol, EntryType.SELL, order_size)
                s['position'] = EntryType.SHORT

        elif s['position'] == EntryType.LONG and signal == EntryType.SELL:
            execute_trade(exchange, symbol, EntryType.REVERSE_TO_SHORT, order_size)
            s['position'] = EntryType.SHORT
        
        elif s['position'] == EntryType.SHORT and signal == EntryType.BUY:
            execute_trade(exchange, symbol, EntryType.REVERSE_TO_LONG, order_size)
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

# log('testing')
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
