from realtime_strategies import ma7_ma25
from config import create_exchange, symbols, leverage
import os
print("main:", list(os.environ.keys()))
if __name__ == "__main__":
    exchange = create_exchange()

    # 設定槓桿在主程式階段
    try:
        for symbol in symbols:
            exchange.set_leverage(leverage=leverage, symbol=symbol)
    except Exception as e:
        print(f"設定槓桿失敗：{e}")
        
    ma7_ma25.run(exchange)  # 你要把 ma7_ma25 裡的主程式包成 run()
