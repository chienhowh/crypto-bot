import ccxt
import pandas as pd
import ta
import time
import argparse
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
exchange = ccxt.binance()
pd.set_option('display.max_rows', 100)
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{level}] {timestamp} | {message}"
    print(full_message)
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = {'chat_id': CHAT_ID, 'text': full_message}
        requests.post(url, data=data)
    except Exception as e:
        print(f"⚠️ 發送 Telegram 失敗: {e}")


def fetch_latest_ohlcv(symbol='BTC/USDT', timeframe='5m', limit=50):
    ohlcv = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    print("🚀 ~ ohlcv:", ohlcv)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def strategy(df):
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['prev_ma5'] = df['ma5'].shift(1)
    df['prev_ma20'] = df['ma20'].shift(1)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if prev['ma5'] < prev['ma20'] and last['ma5'] > last['ma20']:
        return 'buy'
    elif prev['ma5'] > prev['ma20'] and last['ma5'] < last['ma20']:
        return 'sell'
    else:
        return 'hold'

def live_simulate(symbol='BTC/USDT', timeframe='5m', interval=300, initial_balance=1000):
    balance = initial_balance
    coins = 0
    entry_price = 0
    action = 'hold'

    log(f"🚀 開始模擬交易 | 交易對: {symbol} | 週期: {timeframe} | 每 {interval}s 更新一次")
    log(f"初始資金：${balance}")


    while True:
        df = fetch_latest_ohlcv(symbol=symbol, timeframe=timeframe, limit=50)
        signal = strategy(df)
        price = df['close'].iloc[-1]
        timestamp = df['timestamp'].iloc[-1]

        log(f"⏱️ {timestamp} | 現價: {price:.2f} | 訊號: {signal} | 倉位: {action}")

        if balance > 0 and signal == 'buy':
            coins = balance / price
            entry_price = price
            balance = 0
            action = 'buy'
            log(f"✅ 建倉：多單 @ {entry_price:.2f}")

        elif action == 'buy':
            if price < entry_price * 0.9:
                balance = coins * price
                log(f"❌ 停損出場 @ {price:.2f} | 損益: {balance - initial_balance:.2f}")
                coins = 0
                action = 'hold'
            elif signal == 'sell' or price < df['ma5'].iloc[-1]:
                balance = coins * price
                log(f"💰 出場 @ {price:.2f} | 損益: {balance - initial_balance:.2f}")
                coins = 0
                action = 'hold'

        portfolio = balance + coins * price
        log(f"💼 總資產: ${portfolio:.2f}")

        time.sleep(interval)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, default='BTC/USDT')
    parser.add_argument('--timeframe', type=str, default='5m')
    parser.add_argument('--interval', type=int, default=300, help='輪詢秒數')
    parser.add_argument('--initial_balance', type=float, default=1000)
    args = parser.parse_args()

    live_simulate(
        symbol=args.symbol,
        timeframe=args.timeframe,
        interval=args.interval,
        initial_balance=args.initial_balance
    )
