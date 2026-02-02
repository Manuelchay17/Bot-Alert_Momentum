import ccxt
import pandas as pd
import requests
import time

# ===== KONFIGURASI =====
TOKEN = "7590175438:AAFqBJHECghMybwf-Cgr_vMBGzSbNsbDAVM"
CHAT_ID = "1387658073"

exchange = ccxt.bingx()
timeframe = "5m"
limit_coins = 50

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try: requests.post(url, data=payload)
    except: pass

def get_top_symbols():
    try:
        tickers = exchange.fetch_tickers()
        df = pd.DataFrame.from_dict(tickers, orient='index')
        df = df[df['symbol'].str.contains('/USDT')]
        return df.sort_values(by='quoteVolume', ascending=False).head(limit_coins)['symbol'].tolist()
    except: return []

def check_box_sideways(symbol):
    try:
        # Ambil 20 candle terakhir (sekitar 1.5 jam di TF 5m)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=20)
        df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
        
        # Cari harga tertinggi dan terendah dalam "Kotak" tersebut
        highest_price = df['high'].max()
        lowest_price = df['low'].min()
        
        # Hitung jarak kotak dalam persen
        # Rumus: ((Highest - Lowest) / Lowest) * 100
        box_range = ((highest_price - lowest_price) / lowest_price) * 100
        
        # KRITERIA: Jika dalam 20 candle harganya cuma muter-muter di bawah 0.5%
        # Ini berarti koin benar-benar terjebak di area kotak seperti gambarmu.
        if box_range < 0.5:
            tv_symbol = symbol.replace('/', '')
            msg = (
                f"📦 *BOX SIDEWAYS DETECTED*\n\n"
                f"Asset: `{symbol}`\n"
                f"Box Range: `{box_range:.2f}%` 🤏\n"
                f"Timeframe: `M5` (20 Candles)\n\n"
                f"📍 *Status:* Harga terjebak di area sempit. Cocok untuk strategi nunggu Breakout Kotak!"
                f"\n\n📊 [Buka TradingView](https://www.tradingview.com/chart/?symbol=BINGX:{tv_symbol})"
            )
            send_telegram(msg)
            return True
    except: pass
    return False

if __name__ == "__main__":
    print("Mencari koin yang terjebak di area Box...")
    symbols = get_top_symbols()
    for s in symbols:
        check_box_sideways(s)
        time.sleep(0.3)
    print("Scan Selesai.")
