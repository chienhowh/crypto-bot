import requests
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
resp = requests.get(url)
print(resp.json())