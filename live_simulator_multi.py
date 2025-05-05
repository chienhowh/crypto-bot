
import ccxt
import pandas as pd
import time
from datetime import datetime
from strategies import ma7_ma25
from dotenv import load_dotenv
import os
import requests
import sys

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TEST_KEY = os.getenv("TEST_KEY")
TEST_SECRET = os.getenv("TEST_SECRET")

# symbols = ['BTC/USDT', 'ETH/USDT']
symbols = ['ETH/USDT']
initial_balance = 3000
timeframe = '1h'
fetch_limit = 100
interval = 60  # seconds

exchange_id = 'binance'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': TEST_KEY,
    'secret': TEST_SECRET,
    'options':{'defaultType':'future'}
})

exchange.set_sandbox_mode(True)

balance = exchange.fetch_balance()
usdt_balance = balance['USDT']['free'] if 'USDT' in balance else 0
print(usdt_balance)
# sys.exit()

state = {}

for symbol in symbols:
    state[symbol] = {
        'balance': initial_balance,
        'coins': 0,
        'position': None,
        'entry_price': None,
        'entry_time': None,
        'last_signal_time': None,
        'trades': []
    }

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full = f"[{level}] {timestamp} | {message}"
    print(full)
    if BOT_TOKEN and CHAT_ID:
        try:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
            data = {'chat_id': CHAT_ID, 'text': full}
            requests.post(url, data=data)
        except Exception as e:
            print(f"Telegram Error: {e}")

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

def get_account_balance():
    try:
        balance = exchange.fetch_balance()
        usdt_balance = balance['USDT']['free'] if 'USDT' in balance else 0
        log(f"Current USDT Balance: {usdt_balance}", "BALANCE")
        return usdt_balance
    except Exception as e:
        log(f"Error fetching balance: {e}", "ERROR")
        return 0


def execute_trade(symbol, action, amount=None):
    try:
        symbol_formatted = symbol  # 可能需要根据交易所要求调整格式
        # TODO: future格式好像是BTCUSDT
        
        # 检查现有仓位
        positions = exchange.fetch_positions([symbol_formatted])
        current_position = None
        for pos in positions:
            if pos['symbol'] == symbol_formatted:
                current_position = pos
                break
        
        current_size = float(current_position['contracts']) if current_position else 0
        side = current_position['side'] if current_position else None
        
        if action == 'buy':
            # 如果已经有空头仓位，先平仓
            if side == 'short' and current_size > 0:
                exchange.create_market_buy_order(symbol_formatted, current_size, {'reduceOnly': True})
                log(f"{symbol} ❌ Close SHORT position of {current_size}", "TRADE")
            
            # 开多头仓位
            if amount:
                order = exchange.create_market_buy_order(symbol_formatted, amount)
                log(f"{symbol} ✅ LONG ENTRY with {amount} @ market price", "TRADE")
                return order
                
        elif action == 'sell':
            # 如果已经有多头仓位，先平仓
            if side == 'long' and current_size > 0:
                exchange.create_market_sell_order(symbol_formatted, current_size, {'reduceOnly': True})
                log(f"{symbol} ❌ Close LONG position of {current_size}", "TRADE")
            
            # 开空头仓位
            if amount:
                order = exchange.create_market_sell_order(symbol_formatted, amount)
                log(f"{symbol} ✅ SHORT ENTRY with {amount} @ market price", "TRADE")
                return order
        
        return None
    except Exception as e:
        log(f"Trading Error: {e}", "ERROR")
        return None

def simulate_trade(symbol, df):
    global state
    df = ma7_ma25.strategy(df)
    last = df.iloc[-1]
    
    signal = last['signal']
    now_time = last['timestamp']
    s = state[symbol]
    curr_price = last['close']

    # === 自動偵測出場邏輯 ===
    stoploss_pct = 0.003
    trailing_stop_pct = 0.015
    
    if s['position'] == 'long':
        s['highest_close'] = max(s.get('highest_close', curr_price), curr_price)
        trail_stop = s['highest_close'] * (1 - trailing_stop_pct)
        stop_loss = s['entry_price'] * (1 - stoploss_pct)

        if curr_price < trail_stop or curr_price < stop_loss:
            log(f"🛑 {symbol} LONG 出場 | 現價: {curr_price:.2f}, 停利線: {trail_stop:.2f}, 停損線: {stop_loss:.2f}", "TRADE")
            execute_trade(symbol, 'sell')
            s['position'] = None
            s['entry_price'] = None
            s['highest_close'] = None

    elif s['position'] == 'short':
        s['lowest_close'] = min(s.get('lowest_close', curr_price), curr_price)
        trail_stop = s['lowest_close'] * (1 + trailing_stop_pct)
        stop_loss = s['entry_price'] * (1 + stoploss_pct)

        if curr_price > trail_stop or curr_price > stop_loss:
            log(f"🛑 {symbol} SHORT 出場 | 現價: {curr_price:.2f}, 停利線: {trail_stop:.2f}, 停損線: {stop_loss:.2f}", "TRADE")
            execute_trade(symbol, 'buy')
            s['position'] = None
            s['entry_price'] = None
            s['lowest_close'] = None
    
    # === 建倉處理 ===
    if signal in ['buy', 'sell'] and s.get('last_signal_time') != now_time:
        usdt_balance = get_account_balance()
        trade_amount = usdt_balance * 0.95 / last['open']

        execute_trade(symbol, signal, trade_amount)
        s['last_signal_time'] = now_time
        s['entry_price'] = last['open']
        s['position'] = 'long' if signal == 'buy' else 'short'
        if signal == 'buy':
            s['highest_close'] = last['close']
        else:
            s['lowest_close'] = last['close']

    # === 倉位狀態回報 ===
    try:
        positions = exchange.fetch_positions([symbol])
        position_size = 0
        position_side = "none"
        for pos in positions:
            if pos['symbol'] == symbol.replace('/', ''):
                position_size = float(pos['contracts'])
                position_side = pos['side']
                break
        log(f"{symbol} 💼 Position: {position_side} {position_size} | Time: {now_time}", "STATUS")
    except Exception as e:
        log(f"Position check error: {e}", "ERROR")

def save_trades():
    all_trades = []
    for symbol in state:
        all_trades.extend(state[symbol]['trades'])
    if all_trades:
        df = pd.DataFrame(all_trades)
        df.to_csv('sim_trades.csv', index=False)

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
    save_trades()
except Exception as e:
    log(f"Unexpected error: {e}", "ERROR")
    save_trades()