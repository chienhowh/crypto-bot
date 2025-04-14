import ccxt
import pandas as pd
import ta
import matplotlib.pyplot as plt

pd.set_option('display.max_rows', 200)

# 抓取 Binance 上 BTC/USDT 的歷史 K 線
exchange = ccxt.binance()

def fetch_ohlcv(symbol='BTC/USDT', timeframe='15m', limit=1000):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    print("\n📊 後 5 筆資料：")
    print(df.tail())
    return df

# 策略：RSI < 30 且價格高於 SMA → 買進
#      RSI > 70 或跌破 SMA → 賣出

def cross_strategy(df):
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['prev_ma5'] = df['ma5'].shift(1)
    df['prev_ma20'] = df['ma20'].shift(1)
    # 只保留 RSI 和 SMA 都不是 NaN 的資料
    df = df.dropna(subset=['prev_ma5', 'prev_ma20']).reset_index(drop=True)

    signals = []

    for i in range(len(df)):
        if df['prev_ma5'].iloc[i] < df['prev_ma20'].iloc[i] and df['ma5'].iloc[i] > df['ma20'].iloc[i]:
            signals.append('buy')
        elif df['prev_ma5'].iloc[i] > df['prev_ma20'].iloc[i] and df['ma5'].iloc[i] < df['ma20'].iloc[i]:
            signals.append('sell')
        else:
            signals.append('hold')

    df['signal'] = signals
    return df

# 回測邏輯

def backtest(df, initial_balance=1000):
    balance = initial_balance
    coins = 0
    entry_price = 0
    balances = []
    actions = []
    action = 'hold'

    for i, row in df.iterrows():
        price = row['close']

        # 建倉：黃金交叉時進場
        if balance > 0 and row['signal'] == 'buy':
            coins = balance / price
            entry_price = price
            balance = 0
            action = 'buy'

        # 出場條件：停損 or 死亡交叉 or 跌破MA5
        elif action == 'buy':
            if price < entry_price * 0.9:
                balance = coins * price
                coins = 0
                entry_price = 0
                action = 'hold'
            elif row['signal'] == 'sell':
                balance = coins * price
                coins = 0
                entry_price = 0
                action = 'hold'
            elif price < row['ma5']:
                balance = coins * price
                coins = 0
                entry_price = 0
                action = 'hold'

        portfolio_value = balance + coins * price
        balances.append(portfolio_value)
        actions.append(action)

    df['portfolio_value'] = balances
    df['action'] = actions
    # df.to_csv('backtest_result.csv', index=False)
    final_value = balances[-1]
    return final_value

# 畫出資產變化曲線圖

def plot_portfolio(df):
    plt.figure(figsize=(12, 6))
    plt.plot(df['timestamp'], df['portfolio_value'], label='Portfolio Value')
    plt.xlabel('Time')
    plt.ylabel('Value (USD)')
    plt.title('Backtest Portfolio Value Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('portfolio_curve.png')
    plt.show()

# 執行整體流程
df = fetch_ohlcv()
df = cross_strategy(df)
final_balance = backtest(df)
print(f"📈 回測結束，模擬最終資產：${final_balance:.2f}")
print("📁 所有回測數據已輸出至 backtest_result.csv")

plot_portfolio(df)