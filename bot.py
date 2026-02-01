import ccxt
import pandas as pd
import requests
import time

# ===== KONFIGURASI =====
TOKEN = "7590175438:AAFqBJHECghMybwf-Cgr_vMBGzSbNsbDAVM"
CHAT_ID = "1387658073"

# Setting Market
exchange = ccxt.bingx() 
timeframe = "15m"
multiplier = 2.0  
limit_coins = 100  # Sekarang mengecek 100 koin volume tertinggi

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True # Biar chat tidak penuh dengan preview link
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

def get_top_symbols():
    """Mengambil 100 koin dengan Volume (USDT) tertinggi."""
    try:
        tickers = exchange.fetch_tickers()
        df_tickers = pd.DataFrame.from_dict(tickers, orient='index')
        
        # Filter hanya pair USDT
        df_tickers = df_tickers[df_tickers['symbol'].str.contains('/USDT')]
        
        # URUTKAN BERDASARKAN VOLUME (quoteVolume)
        # Koin dengan volume besar lebih valid untuk analisa momentum
        top_df = df_tickers.sort_values(by='quoteVolume', ascending=False).head(limit_coins)
        return top_df['symbol'].tolist()
    except Exception as e:
        print(f"Error ambil daftar koin: {e}")
        return []

def check_momentum(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=30)
        df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
        
        # Hitung ukuran body candle
        df['body'] = abs(df['close'] - df['open'])
        
        # Rata-rata body 29 candle sebelumnya
        avg_body = df['body'][:-1].mean()
        last_body = df['body'].iloc[-1]
        
        power = last_body / avg_body

        if last_body >= avg_body * multiplier:
            is_bull = df['close'].iloc[-1] > df['open'].iloc[-1]
            icon = "🟢 BULLISH" if is_bull else "🔴 BEARISH"
            price = df['close'].iloc[-1]
            
            # Format TradingView
            tv_symbol = symbol.replace('/', '')
            
            msg = (
                f"🚨 *MOMENTUM ALERT*\n\n"
                f"Asset: `{symbol}`\n"
                f"Signal: {icon}\n"
                f"Price: `{price}`\n"
                f"Power: *{power:.1f}x*\n\n"
                f"📊 [Buka TradingView](https://www.tradingview.com/chart/?symbol=BINGX:{tv_symbol})"
            )
            return {"power": power, "message": msg}
    except:
        pass
    return None

if __name__ == "__main__":
    print(f"Memulai scanning {limit_coins} koin Volume Tertinggi...")
    symbols = get_top_symbols()
    
    found_signals = []

    for s in symbols:
        result = check_momentum(s)
        if result:
            found_signals.append(result)
            print(f"Match: {s} ({result['power']:.1f}x)")
        
        # Jeda tipis agar API tidak timeout
        time.sleep(0.3)
    
    # SORTING: Power TERBESAR muncul di paling bawah (pesan terbaru)
    found_signals.sort(key=lambda x: x['power'])

    for signal in found_signals:
        send_telegram(signal['message'])
        time.sleep(1) 
    
    print(f"Selesai. {len(found_signals)} sinyal terdeteksi.")
