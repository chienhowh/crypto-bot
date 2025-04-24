
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

symbols = ['BTC/USDT', 'ETH/USDT']
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
    account_balance = get_account_balance()
        
    # 计算交易数量（这里简化处理，实际应用中可能需要更复杂的仓位管理）
    trade_amount = account_balance * 0.1 / last['open']  # 使用10%资金

    if signal in ['buy', 'sell'] and signal != 'hold':
        if s['last_signal_time'] == now_time:
            return  # 已处理过
            
        # 获取实际账户余额
        usdt_balance = get_account_balance()
        
        # 计算交易数量（这里简化处理，实际应用中可能需要更复杂的仓位管理）
        trade_amount = usdt_balance * 0.95 / last['open']  # 使用10%资金
        
        # 执行交易
        execute_trade(symbol, signal, trade_amount)
        
        s['last_signal_time'] = now_time

    # 检查当前仓位并报告
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
        save_trades()
        time.sleep(interval)

except KeyboardInterrupt:
    log("🛑 停止交易，保存交易记录...")
    save_trades()
except Exception as e:
    log(f"Unexpected error: {e}", "ERROR")
    save_trades()