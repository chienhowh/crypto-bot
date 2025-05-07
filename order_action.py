import time
from utils import log
from enums import EntryType

def get_balance(exchange):
    balance = exchange.fetch_balance()
    return balance['USDT']['free'] if 'USDT' in balance else 0

def get_position_info(exchange, symbol):
 
    try:
        positions = exchange.fetch_positions([symbol])
        for pos in positions:
            if pos['info']['symbol'] == symbol.replace('/', ''):
                size = float(pos['contracts'])     # 倉位大小（張數）
                side = pos['side'].lower()         # 'long' / 'short' / 'none'
                return size, side
     
    except Exception as e:
        print(f"Position check error: {e}", "ERROR")
    return 0, None

# new_size: 開倉 offset_size: 平倉
def execute_trade(exchange, symbol, entry_type: EntryType, new_size=None):
    try:
        if entry_type == EntryType.REVERSE_TO_SHORT:
            auto_close(exchange, symbol)
            if new_size:
                order = safe_order(exchange, symbol, 'sell', new_size)
                entry_price = float(order['average'])  # 平均成交價格
                create_protective_orders(exchange, symbol, EntryType.SHORT, entry_price)

        elif entry_type == EntryType.REVERSE_TO_LONG:
            auto_close(exchange, symbol)
            if new_size:
                order = safe_order(exchange, symbol, 'buy', new_size)
                entry_price = float(order['average'])  # 平均成交價格
                create_protective_orders(exchange, symbol, EntryType.LONG, entry_price)

        elif entry_type == EntryType.BUY:
            if new_size:
                order = safe_order(exchange, symbol, 'buy', new_size)
                entry_price = float(order['average'])  # 平均成交價格
                create_protective_orders(exchange, symbol, EntryType.LONG, entry_price)
            else:
                log(f"{symbol} ❗ 缺少 new_size 參數 (買單)", "ERROR")

        elif entry_type == EntryType.SELL:
            if new_size:
                order = safe_order(exchange, symbol, 'sell', new_size)
                entry_price = float(order['average'])  # 平均成交價格
                create_protective_orders(exchange, symbol, EntryType.SHORT, entry_price)
            else:
                log(f"{symbol} ❗ 缺少 new_size 參數 (賣單)", "ERROR")

        elif entry_type == EntryType.CLOSE_LONG or entry_type == EntryType.CLOSE_SHORT:
            auto_close(exchange, symbol)

        else:
            log(f"{symbol} ⚠️ 未知的 entry_type: {entry_type}", "ERROR")

    except Exception as e:
        log(f"{symbol} ❌ execute_trade 發生錯誤：{e}", "ERROR")
        
def create_protective_orders(exchange, symbol, side, entry_price, stop_loss_pct=0.003, trailing_stop_pct=0.02):
    params = {}
    size, _ = get_position_info(exchange, symbol)  # ⬅️ 加上這一行
    if size < 0.001:
        log(f"{symbol} ❌ 倉位過小（{size}），無法掛保護單", "ERROR")
        return
    
    stop_price = None
    callback_rate = trailing_stop_pct * 100  # %，Binance 要用百分比

    if side == EntryType.LONG:
        # 停損低於入場價
        stop_price = entry_price * (1 - stop_loss_pct)
        side_str = 'sell'
    elif side == EntryType.SHORT:
        # 停損高於入場價
        stop_price = entry_price * (1 + stop_loss_pct)
        side_str = 'buy'
    else:
        log(f"{symbol} ❌ 無效方向：{side}", "ERROR")
        return

    try:
        # 掛止損單
        exchange.create_order(
            symbol=symbol,
            type='STOP_MARKET',
            side=side_str,
            amount=0,  # 讓 ccxt 幫你自動處理（或填倉位大小）
            params={
                'stopPrice': round(stop_price, 2),
                'closePosition': True
            }
        )
        log(f"{symbol} 📌 已掛 STOP_MARKET（{side_str} @ {stop_price:.2f}）", "PROTECT")

        # 掛移動停利單
        exchange.create_order(
            symbol=symbol,
            type='TRAILING_STOP_MARKET',
            side=side_str,
            amount=size,
            params={
                'callbackRate': round(callback_rate, 1),
                'activationPrice': round(entry_price, 2),
                'reduceOnly': True
            }
        )
        log(f"{symbol} 📈 已掛 TRAILING_STOP_MARKET（callback: {callback_rate:.1f}%）", "PROTECT")

    except Exception as e:
        log(f"{symbol} ❌ 掛保護單失敗：{e}", "ERROR")


def safe_order(exchange, symbol, side, amount, reduce_only=False, max_retry=1, delay_sec=3):
    """
    安全下單（含 reduceOnly），自動處理 timeout 重送
    side: 'buy' 或 'sell'
    reduce_only: True 時為平倉單
    """
    params = {'reduceOnly': True} if reduce_only else {}

    for attempt in range(max_retry + 1):
        try:
            log(f"📤 嘗試下單 {symbol} {side.upper()} {amount:.4f} reduceOnly={reduce_only}", "TRADE")

            if side == 'buy':
                order = exchange.create_market_buy_order(symbol, amount, params)
            elif side == 'sell':
                order = exchange.create_market_sell_order(symbol, amount, params)
            else:
                log(f"{symbol} ❗ 不支援的 side: {side}", "ERROR")
                return None

            log(f"✅ 下單成功：{symbol} {side.upper()} {amount:.4f} reduceOnly={reduce_only}", "TRADE")
            return order

        except Exception as e:
            error_msg = str(e)
            if "Timeout" in error_msg or "Send status unknown" in error_msg:
                log(f"{symbol} ⚠️ 下單超時，準備重試 ({attempt + 1}/{max_retry})...", "WARN")
                time.sleep(delay_sec)

                # 嘗試查倉位，看是否其實已成交
                size, current_side = get_position_info(exchange, symbol)
                if reduce_only and size == 0:
                    log(f"{symbol} ✅ 查詢顯示已平倉成功，略過重送", "TRADE")
                    return None
                elif not reduce_only and size > 0:
                    log(f"{symbol} ✅ 查詢顯示已開倉成功，略過重送", "TRADE")
                    return None
                # 否則重送下一輪
            else:
                log(f"{symbol} ❌ 下單失敗：{e}", "ERROR")
                return None

    log(f"{symbol} ❌ 最多重試 {max_retry + 1} 次仍失敗", "ERROR")
    return None


def auto_close(exchange, symbol):
    size, side = get_position_info(exchange, symbol)
    
     # 取消所有掛單
    exchange.cancel_all_orders(symbol)
    log(f"{symbol} 🔁 已清除所有未成交訂單", "ORDER")


    if size == 0 or side is None:
        log(f"{symbol} 沒有倉位可平", "INFO")
        return

    try:
        if side == 'long':
            safe_order(exchange, symbol, 'sell', size, reduce_only=True)
        elif side == 'short':
            safe_order(exchange, symbol, 'buy', size, reduce_only=True)
        else:
            log(f"{symbol} ⚠️ 倉位方向未知: {side}", "ERROR")
    except Exception as e:
        log(f"{symbol} ❌ 平倉失敗：{e}", "ERROR")  
        
def get_current_price(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        log(f"{symbol} ❌ 無法獲取價格: {e}", "ERROR")
        return None

def calculate_order_size(exchange, symbol, leverage=20, ratio=0.4):
    usdt_balance = get_balance(exchange)
    price = get_current_price(exchange, symbol)
    if price:
        usd_to_use = usdt_balance * ratio
        size = usd_to_use * leverage / price
        return round(size, 3)  # 四捨五入避免小數過多
    return 0
        
# 检查现有仓位
# size, side = get_position_info('ETH/USDT')
# print('size', size)
# print('side', side)

# execute_trade('ETH/USDT', EntryType.BUY, new_size=0.03)
# execute_trade('ETH/USDT', EntryType.CLOSE_LONG, offset_size=0.1)
# execute_trade('ETH/USDT', EntryType.CLOSE_LONG, offset_size=0.03)
# execute_trade('ETH/USDT', EntryType.REVERSE_TO_SHORT, new_size=0.05, offset_size=0.05)
# execute_trade('ETH/USDT', EntryType.REVERSE_TO_LONG, new_size=0.05, offset_size=0.05)

# 建倉: limit, sell
# order = exchange.create_order(symbol='ETH/USDT', type='market', side='buy', amount=0.05)
# print('order', order)
# sys.exit()

