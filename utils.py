from datetime import datetime
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{level}] {timestamp} | {message}"
    print(full_message)

    if BOT_TOKEN and CHAT_ID:
        try:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
            data = {'chat_id': CHAT_ID, 'text': full_message}
            requests.post(url, data=data)
        except Exception as e:
            print(f"⚠️ 發送 Telegram 失敗: {e}")