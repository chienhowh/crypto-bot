# --- import ---
import importlib.util
import ccxt
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os
import pandas as pd

# --- 動態載入策略 ---
def load_strategy(strategy_name):
    strategy_path = f"strategies/{strategy_name}.py"
    if not os.path.exists(strategy_path):
        raise FileNotFoundError(f"策略檔案不存在：{strategy_path}")

    spec = importlib.util.spec_from_file_location("strategy", strategy_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.strategy


def analyze_backtest_dual(df, symbol='BTC/USDT', initial_balance=1000, desc ='test'):
    balance = initial_balance
    position = None  # 'long' or 'short'
    entry_price = 0
    entry_value = 0
    portfolio_values = []
    trades = []

    for i, row in df.iterrows():
        signal = row['signal']
        price = row['close']
        entry_type = row.get('entry_type', 'hold')

        # 平倉
        if signal == 'buy' and position == 'short':
            pnl_pct = (entry_price - price) / entry_price
            pnl = entry_value * pnl_pct
            balance += pnl
            trades.append({
                'side': 'short',
                'entry': entry_price,
                'exit': price,
                'pnl': pnl,
                'pnl_pct': pnl_pct * 100,
                'entry_value': entry_value,
                'win': pnl > 0
            })
            position = None

        elif signal == 'sell' and position == 'long':
            pnl_pct = (price - entry_price) / entry_price
            pnl = entry_value * pnl_pct
            balance += pnl
            trades.append({
                'side': 'long',
                'entry': entry_price,
                'exit': price,
                'pnl': pnl,
                'pnl_pct': pnl_pct * 100,
                'entry_value': entry_value,
                'win': pnl > 0
            })
            position = None

        # 開倉
        if entry_type in ['long', 'reverse_to_long'] and signal == 'buy':
            position = 'long'
            entry_price = price
            entry_value = balance

        elif entry_type in ['short', 'reverse_to_short'] and signal == 'sell':
            position = 'short'
            entry_price = price
            entry_value = balance

        # 紀錄當前資產變化（不管持倉或現金）
        portfolio_values.append(balance)

    final_value = balance
    total_return = (final_value - initial_balance) / initial_balance * 100
    max_drawdown = max([
        max(portfolio_values[:i+1]) - v
        for i, v in enumerate(portfolio_values)
    ]) if portfolio_values else 0
    win_rate = sum([1 for t in trades if t['win']]) / len(trades) * 100 if trades else 0

    # 平均獲利 / 虧損 / R:R
    profits = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in trades if t['pnl'] < 0]
    avg_profit = sum(profits) / len(profits) if profits else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    rr_ratio = avg_profit / avg_loss if avg_loss != 0 else float('inf')
    avg_trade_return = sum(t['pnl'] for t in trades) / len(trades) if trades else 0

    print("\n📊 雙向回測報告（真實資金）")
    print(f"初始資金：${initial_balance:.2f}")
    print(f"最終資產：${final_value:.2f}")
    print(f"總報酬率：{total_return:.2f}%")
    print(f"總交易次數：{len(trades)}")
    print(f"勝率：{win_rate:.2f}%")
    print(f"最大回撤：約 ${max_drawdown:.2f}")
    print(f"平均獲利：${avg_profit:.2f}")
    print(f"平均虧損：${avg_loss:.2f}")
    print(f"盈虧比（R:R）：{rr_ratio:.2f}")
    print(f"平均每筆報酬：${avg_trade_return:.2f}")
    if desc:
        save_summary_row(
            desc=desc,
            symbol=symbol,
            initial_balance=initial_balance,
            final_value=final_value,
            total_return=total_return,
            trades=trades,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            rr_ratio=rr_ratio,
            avg_trade_return=avg_trade_return
        )

def plot_signals(df, strategy_name):
    plt.figure(figsize=(12, 6))
    plt.plot(df['timestamp'], df['close'], label='Close')

    # 畫 MA 線（如果存在）
    if 'ma5' in df.columns:
        plt.plot(df['timestamp'], df['ma5'], '--', label='MA5')
    if 'ma20' in df.columns:
        plt.plot(df['timestamp'], df['ma20'], '--', label='MA20')

    # 畫買進訊號
    plt.scatter(
        df[df['signal'] == 'buy']['timestamp'],
        df[df['signal'] == 'buy']['close'],
        label='Buy', marker='^', color='g'
    )
    # 畫賣出訊號
    plt.scatter(
        df[df['signal'] == 'sell']['timestamp'],
        df[df['signal'] == 'sell']['close'],
        label='Sell', marker='v', color='r'
    )

    plt.title(f"{strategy_name} Strategy Signals")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def save_summary_row(desc, symbol, initial_balance, final_value, total_return, trades, win_rate, max_drawdown, avg_profit, avg_loss, rr_ratio, avg_trade_return):
    symbol_name = symbol.replace('/', '')
    file_path = f'results/{symbol_name}.csv'
    os.makedirs('results', exist_ok=True)

    new_row = pd.DataFrame([{
        'strategy': desc,
        'initial_balance': initial_balance,
        'final_balance': final_value,
        'total_return_pct': round(total_return, 2),
        'total_trades': len(trades),
        'win_rate_pct': round(win_rate, 2),
        'max_drawdown': round(max_drawdown, 2),
        'avg_profit': round(avg_profit, 2),
        'avg_loss': round(avg_loss, 2),
        'rr_ratio': round(rr_ratio, 2),
        'avg_trade_return': round(avg_trade_return, 2)
    }])

    if os.path.exists(file_path):
        existing = pd.read_csv(file_path)
        updated = pd.concat([existing, new_row], ignore_index=True)
        updated.to_csv(file_path, index=False)
    else:
        new_row.to_csv(file_path, index=False)

# --- 主程式 ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--strategy', type=str, required=True)
    parser.add_argument('--symbol', type=str, default='BTC/USDT')
    parser.add_argument('--timeframe', type=str, default='1h')
    parser.add_argument('--limit', type=int, default=500)
    parser.add_argument('--desc', type=str, default='test')
    parser.add_argument('--backtest', action='store_true', help='啟用回測模式')
    args = parser.parse_args()

    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(args.symbol, timeframe=args.timeframe, limit=args.limit)
    print("🚀 ~ ohlcv:", ohlcv)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    strategy_fn = load_strategy(args.strategy)
    df = strategy_fn(df)

    if args.backtest:
        analyze_backtest_dual(df, symbol=args.symbol, desc=args.desc)
    else:
        plot_signals(df, args.strategy)
# script
# python strategy_framework.py --strategy cross_ma --limit 200 --backtest
# python strategy_framework.py --strategy ma7_ma25 --symbol BTC/USDT --timeframe 1h --backtest
