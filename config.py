# config.py
import os
import ccxt

from dotenv import load_dotenv
load_dotenv()

TEST_KEY = os.getenv("TEST_KEY")
TEST_SECRET = os.getenv("TEST_SECRET")

if not TEST_KEY or not TEST_SECRET:
    print("❌ 無法取得 TEST_KEY 或 TEST_SECRET，請檢查環境變數是否正確設定")

symbols = ['BTC/USDT']
leverage = 20
timeframe = '1h'
fetch_limit = 50
interval = 60  # seconds


def create_exchange():
    exchange_id = 'binance'
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
        'apiKey': TEST_KEY,
        'secret': TEST_SECRET,
        'options': {'defaultType': 'future'}
    })
    exchange.set_sandbox_mode(True)
    return exchange


