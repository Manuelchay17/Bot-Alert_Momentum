import ccxt
import pandas as pd
import requests
import time

# ===== KONFIGURASI =====
TOKEN = "7590175438:AAFqBJHECghMybwf-Cgr_vMBGzSbNsbDAVM"
CHAT_ID = "1387658073"

exchange = ccxt.bingx() 
# GANTI KE 5 MENIT
timeframe = "5m" 
multiplier = 2.0  
# KHUSUS BTC
symbol = "BTC/USDT" 

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=payload)
    except:
        pass

def check_btc_momentum():
    try:
        # Ambil data candle BTC
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=50)
        df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
        
        # Hitung body candle
        df['body'] = abs(df['close'] - df['open'])
        
        # Rata-rata body 49 candle sebelumnya
        avg_body = df['body'][:-1].mean()
        last_body = df['body'].iloc[-1]
        
        power = last_body / avg_body

        if last_body >= avg_body * multiplier:
            is_bull = df['close'].iloc[-1] > df['open'].iloc[-1]
            icon = "🚀 BTC PUMP" if is_bull else "📉 BTC DUMP"
            price = df['close'].iloc[-1]
            
            msg = (
                f"⚠️ *BTC 5M MOMENTUM ALERT*\n\n"
                f"Signal: {icon}\n"
                f"Price: `${price}`\n"
                f"Power: *{power:.1f}x*\n"
                f"Timeframe: `5 Minutes`\n\n"
                f"📊 [TradingView](https://www.tradingview.com/chart/?symbol=BINGX:BTCUSDT)"
            )
            send_telegram(msg)
            print(f"BTC Alert Sent! Power: {power}")
        else:
            print(f"BTC Normal. Power: {power:.1f}x")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_btc_momentum()
