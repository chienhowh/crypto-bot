def strategy(df):
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()

    df['prev_ma5'] = df['ma5'].shift(1)
    df['prev_ma20'] = df['ma20'].shift(1)

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