# 初版
# def strategy(df):
#     df['ma7'] = df['close'].rolling(7).mean()
#     df['ma25'] = df['close'].rolling(25).mean()
#     df['prev_ma7'] = df['ma7'].shift(1)
#     df['prev_ma25'] = df['ma25'].shift(1)

#     df['signal'] = 'hold'
#     df['entry_type'] = None
#     df['stop_price'] = None

#     position = None  # None, 'long', 'short'
#     entry_candle = None  # row ref for stop-loss
#     buffer_pct = 0.003  # 0.3% 停損 buffer
#     for i in range(26, len(df) - 1):  # 從第26根開始（因為 MA25）
#         prev = df.iloc[i - 1]
#         curr = df.iloc[i]
#         next_open = df.iloc[i + 1]['open']

#         # 平倉邏輯
#         if position == 'long':
#             stop = entry_candle['low'] * (1 - buffer_pct)
#             # stop = entry_candle['low']
#             if curr['close'] < stop:
#                 df.at[i + 1, 'signal'] = 'sell'
#                 df.at[i + 1, 'entry_type'] = 'stoploss'
#                 df.at[i + 1, 'stop_price'] = stop
#                 position = None
#                 entry_candle = None
#                 continue
#             elif prev['ma7'] > prev['ma25'] and curr['ma7'] < curr['ma25']:
#                 df.at[i + 1, 'signal'] = 'sell'
#                 df.at[i + 1, 'entry_type'] = 'reverse_to_short'
#                 df.at[i + 1, 'stop_price'] = curr['high']
#                 position = 'short'
#                 entry_candle = curr
#                 continue

#         elif position == 'short':
#             stop = entry_candle['high'] * (1 + buffer_pct)
#             # stop = entry_candle['high']
#             if curr['close'] > stop:
#                 df.at[i + 1, 'signal'] = 'buy'
#                 df.at[i + 1, 'entry_type'] = 'stoploss'
#                 df.at[i + 1, 'stop_price'] = stop
#                 position = None
#                 entry_candle = None
#                 continue
#             elif prev['ma7'] < prev['ma25'] and curr['ma7'] > curr['ma25']:
#                 df.at[i + 1, 'signal'] = 'buy'
#                 df.at[i + 1, 'entry_type'] = 'reverse_to_long'
#                 df.at[i + 1, 'stop_price'] = curr['low']
#                 position = 'long'
#                 entry_candle = curr
#                 continue

#         # 開倉邏輯
#         if position is None:
#             if prev['ma7'] < prev['ma25'] and curr['ma7'] > curr['ma25']:
#                 df.at[i + 1, 'signal'] = 'buy'
#                 df.at[i + 1, 'entry_type'] = 'long'
#                 df.at[i + 1, 'stop_price'] = curr['low']
#                 position = 'long'
#                 entry_candle = curr

#             elif prev['ma7'] > prev['ma25'] and curr['ma7'] < curr['ma25']:
#                 df.at[i + 1, 'signal'] = 'sell'
#                 df.at[i + 1, 'entry_type'] = 'short'
#                 df.at[i + 1, 'stop_price'] = curr['high']
#                 position = 'short'
#                 entry_candle = curr

#     return df

# 固定停利
# def strategy(df):
#     df['ma7'] = df['close'].rolling(7).mean()
#     df['ma25'] = df['close'].rolling(25).mean()
#     df['prev_ma7'] = df['ma7'].shift(1)
#     df['prev_ma25'] = df['ma25'].shift(1)

#     df['signal'] = 'hold'
#     df['entry_type'] = None
#     df['stop_price'] = None
#     df['entry_price'] = None
#     df['entry_time'] = None
#     df['exit_price'] = None
#     df['exit_time'] = None

#     position = None
#     entry_candle = None
#     entry_price = None
#     entry_time = None

#     buffer_pct = 0.003
#     take_profit_pct = 0.03

#     for i in range(26, len(df) - 1):
#         prev = df.iloc[i - 1]
#         curr = df.iloc[i]
#         next_open = df.iloc[i + 1]['open']
#         next_time = df.iloc[i + 1]['timestamp']

#         # 平倉邏輯
#         if position == 'long':
#             stop = entry_candle['low'] * (1 - buffer_pct)
#             tp = entry_price * (1 + take_profit_pct)

#             if curr['close'] < stop:
#                 df.at[i + 1, 'signal'] = 'sell'
#                 df.at[i + 1, 'entry_type'] = 'stoploss'
#                 df.at[i + 1, 'stop_price'] = stop
#                 df.at[i + 1, 'entry_price'] = entry_price
#                 df.at[i + 1, 'entry_time'] = entry_time
#                 df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
#                 df.at[i + 1, 'exit_time'] = next_time
#                 position = None
#                 entry_candle = None
#                 entry_price = None
#                 entry_time = None
#                 continue
#             elif curr['close'] > tp:
#                 df.at[i + 1, 'signal'] = 'sell'
#                 df.at[i + 1, 'entry_type'] = 'takeprofit'
#                 df.at[i + 1, 'stop_price'] = tp
#                 df.at[i + 1, 'entry_price'] = entry_price
#                 df.at[i + 1, 'entry_time'] = entry_time
#                 df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
#                 df.at[i + 1, 'exit_time'] = next_time
#                 position = None
#                 entry_candle = None
#                 entry_price = None
#                 entry_time = None
#                 continue
#             elif prev['ma7'] > prev['ma25'] and curr['ma7'] < curr['ma25']:
#                 df.at[i + 1, 'signal'] = 'sell'
#                 df.at[i + 1, 'entry_type'] = 'reverse_to_short'
#                 df.at[i + 1, 'stop_price'] = curr['high']
#                 df.at[i + 1, 'entry_price'] = entry_price
#                 df.at[i + 1, 'entry_time'] = entry_time
#                 df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
#                 df.at[i + 1, 'exit_time'] = next_time
#                 position = 'short'
#                 entry_candle = curr
#                 entry_price = df.iloc[i + 1]['open']
#                 entry_time = next_time
#                 continue

#         elif position == 'short':
#             stop = entry_candle['high'] * (1 + buffer_pct)
#             tp = entry_price * (1 - take_profit_pct)

#             if curr['close'] > stop:
#                 df.at[i + 1, 'signal'] = 'buy'
#                 df.at[i + 1, 'entry_type'] = 'stoploss'
#                 df.at[i + 1, 'stop_price'] = stop
#                 df.at[i + 1, 'entry_price'] = entry_price
#                 df.at[i + 1, 'entry_time'] = entry_time
#                 df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
#                 df.at[i + 1, 'exit_time'] = next_time
#                 position = None
#                 entry_candle = None
#                 entry_price = None
#                 entry_time = None
#                 continue
#             elif curr['close'] < tp:
#                 df.at[i + 1, 'signal'] = 'buy'
#                 df.at[i + 1, 'entry_type'] = 'takeprofit'
#                 df.at[i + 1, 'stop_price'] = tp
#                 df.at[i + 1, 'entry_price'] = entry_price
#                 df.at[i + 1, 'entry_time'] = entry_time
#                 df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
#                 df.at[i + 1, 'exit_time'] = next_time
#                 position = None
#                 entry_candle = None
#                 entry_price = None
#                 entry_time = None
#                 continue
#             elif prev['ma7'] < prev['ma25'] and curr['ma7'] > curr['ma25']:
#                 df.at[i + 1, 'signal'] = 'buy'
#                 df.at[i + 1, 'entry_type'] = 'reverse_to_long'
#                 df.at[i + 1, 'stop_price'] = curr['low']
#                 df.at[i + 1, 'entry_price'] = entry_price
#                 df.at[i + 1, 'entry_time'] = entry_time
#                 df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
#                 df.at[i + 1, 'exit_time'] = next_time
#                 position = 'long'
#                 entry_candle = curr
#                 entry_price = df.iloc[i + 1]['open']
#                 entry_time = next_time
#                 continue

#         # 開倉
#         if position is None:
#             if prev['ma7'] < prev['ma25'] and curr['ma7'] > curr['ma25']:
#                 df.at[i + 1, 'signal'] = 'buy'
#                 df.at[i + 1, 'entry_type'] = 'long'
#                 df.at[i + 1, 'stop_price'] = curr['low']
#                 position = 'long'
#                 entry_candle = curr
#                 entry_price = df.iloc[i + 1]['open']
#                 entry_time = next_time

#             elif prev['ma7'] > prev['ma25'] and curr['ma7'] < curr['ma25']:
#                 df.at[i + 1, 'signal'] = 'sell'
#                 df.at[i + 1, 'entry_type'] = 'short'
#                 df.at[i + 1, 'stop_price'] = curr['high']
#                 position = 'short'
#                 entry_candle = curr
#                 entry_price = df.iloc[i + 1]['open']
#                 entry_time = next_time

#     return df

# 移動停利
def strategy(df):
    df['ma7'] = df['close'].rolling(7).mean()
    df['ma25'] = df['close'].rolling(25).mean()
    df['prev_ma7'] = df['ma7'].shift(1)
    df['prev_ma25'] = df['ma25'].shift(1)

    df['signal'] = 'hold'
    df['entry_type'] = None
    df['stop_price'] = None
    df['entry_price'] = None
    df['entry_time'] = None
    df['exit_price'] = None
    df['exit_time'] = None

    position = None
    entry_candle = None
    entry_price = None
    entry_time = None

    buffer_pct = 0.003
    highest_close = None  # for long
    lowest_close = None   # for short
    trailing_stop_pct = 0.015  # 1.5%

    for i in range(26, len(df) - 1):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        next_open = df.iloc[i + 1]['open']
        next_time = df.iloc[i + 1]['timestamp']

        # 平倉邏輯
        if position == 'long':
            stop = entry_candle['low'] * (1 - buffer_pct)
            if highest_close is None:
                highest_close = curr['close']
            else:
                highest_close = max(highest_close, curr['close'])

            if curr['close'] < stop:
                df.at[i + 1, 'signal'] = 'sell'
                df.at[i + 1, 'entry_type'] = 'stoploss'
                df.at[i + 1, 'stop_price'] = stop
                df.at[i + 1, 'entry_price'] = entry_price
                df.at[i + 1, 'entry_time'] = entry_time
                df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
                df.at[i + 1, 'exit_time'] = next_time
                position = None
                entry_candle = None
                entry_price = None
                entry_time = None
                continue
            elif curr['close'] < highest_close * (1 - trailing_stop_pct):
                    df.at[i + 1, 'signal'] = 'sell'
                    df.at[i + 1, 'entry_type'] = 'trailing_stop'
                    df.at[i + 1, 'stop_price'] = highest_close * (1 - trailing_stop_pct)
                    df.at[i + 1, 'entry_price'] = entry_price
                    df.at[i + 1, 'entry_time'] = entry_time
                    df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
                    df.at[i + 1, 'exit_time'] = next_time
                    position = None
                    entry_candle = None
                    entry_price = None
                    entry_time = None
                    highest_close = None
                    continue
            elif prev['ma7'] > prev['ma25'] and curr['ma7'] < curr['ma25']:
                df.at[i + 1, 'signal'] = 'sell'
                df.at[i + 1, 'entry_type'] = 'reverse_to_short'
                df.at[i + 1, 'stop_price'] = curr['high']
                df.at[i + 1, 'entry_price'] = entry_price
                df.at[i + 1, 'entry_time'] = entry_time
                df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
                df.at[i + 1, 'exit_time'] = next_time
                position = 'short'
                entry_candle = curr
                entry_price = df.iloc[i + 1]['open']
                entry_time = next_time
                continue

        elif position == 'short':
            stop = entry_candle['high'] * (1 + buffer_pct)
            if lowest_close is None:
                lowest_close = curr['close']
            else:
                lowest_close = min(lowest_close, curr['close'])

            if curr['close'] > stop:
                df.at[i + 1, 'signal'] = 'buy'
                df.at[i + 1, 'entry_type'] = 'stoploss'
                df.at[i + 1, 'stop_price'] = stop
                df.at[i + 1, 'entry_price'] = entry_price
                df.at[i + 1, 'entry_time'] = entry_time
                df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
                df.at[i + 1, 'exit_time'] = next_time
                position = None
                entry_candle = None
                entry_price = None
                entry_time = None
                continue
            elif curr['close'] > lowest_close * (1 + trailing_stop_pct):
                df.at[i + 1, 'signal'] = 'buy'
                df.at[i + 1, 'entry_type'] = 'trailing_stop'
                df.at[i + 1, 'stop_price'] = lowest_close * (1 + trailing_stop_pct)
                df.at[i + 1, 'entry_price'] = entry_price
                df.at[i + 1, 'entry_time'] = entry_time
                df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
                df.at[i + 1, 'exit_time'] = next_time
                position = None
                entry_candle = None
                entry_price = None
                entry_time = None
                lowest_close = None
                continue
            elif prev['ma7'] < prev['ma25'] and curr['ma7'] > curr['ma25']:
                df.at[i + 1, 'signal'] = 'buy'
                df.at[i + 1, 'entry_type'] = 'reverse_to_long'
                df.at[i + 1, 'stop_price'] = curr['low']
                df.at[i + 1, 'entry_price'] = entry_price
                df.at[i + 1, 'entry_time'] = entry_time
                df.at[i + 1, 'exit_price'] = df.iloc[i + 1]['open']
                df.at[i + 1, 'exit_time'] = next_time
                position = 'long'
                entry_candle = curr
                entry_price = df.iloc[i + 1]['open']
                entry_time = next_time
                continue

        # 開倉
        if position is None:
            if prev['ma7'] < prev['ma25'] and curr['ma7'] > curr['ma25']:
                df.at[i + 1, 'signal'] = 'buy'
                df.at[i + 1, 'entry_type'] = 'long'
                df.at[i + 1, 'stop_price'] = curr['low']
                position = 'long'
                entry_price = df.iloc[i + 1]['open']
                entry_time = next_time
                highest_close = curr['close']
                entry_candle = curr

            elif prev['ma7'] > prev['ma25'] and curr['ma7'] < curr['ma25']:
                df.at[i + 1, 'signal'] = 'sell'
                df.at[i + 1, 'entry_type'] = 'short'
                df.at[i + 1, 'stop_price'] = curr['high']
                position = 'short'
                entry_price = df.iloc[i + 1]['open']
                entry_time = next_time
                lowest_close = curr['close']
                entry_candle = curr

    return df