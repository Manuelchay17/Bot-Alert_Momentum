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
multiplier = 2.0  # Minimal 2x lipat rata-rata body candle
limit_coins = 50   # Scan 50 koin dengan kenaikan (ROI) tertinggi

def send_telegram(message):
    """Mengirim pesan ke Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

def get_top_symbols():
    """Mengambil 50 koin dengan ROI (persentase kenaikan) tertinggi."""
    try:
        tickers = exchange.fetch_tickers()
        df_tickers = pd.DataFrame.from_dict(tickers, orient='index')
        
        # Filter hanya pair USDT
        df_tickers = df_tickers[df_tickers['symbol'].str.contains('/USDT')]
        
        # SORTING BERDASARKAN ROI (Percentage)
        # Mengambil koin yang sedang 'terbang' atau volatil
        top_df = df_tickers.sort_values(by='percentage', ascending=False).head(limit_coins)
        return top_df['symbol'].tolist()
    except Exception as e:
        print(f"Error ambil daftar koin: {e}")
        return []

def check_momentum(symbol):
    """Mengecek momentum candle pada satu koin."""
    try:
        # Ambil data candle
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=30)
        df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
        
        # Hitung ukuran body candle (Open - Close)
        df['body'] = abs(df['close'] - df['open'])
        
        # Hitung rata-rata body 29 candle sebelumnya
        avg_body = df['body'][:-1].mean()
        last_body = df['body'].iloc[-1]
        
        # Hitung kekuatan momentum (Power)
        power = last_body / avg_body

        # Jika body candle terakhir >= 2x rata-rata
        if last_body >= avg_body * multiplier:
            is_bull = df['close'].iloc[-1] > df['open'].iloc[-1]
            icon = "🟢 BULLISH" if is_bull else "🔴 BEARISH"
            price = df['close'].iloc[-1]
            
            # Link khusus TradingView (Format BINGX:SYMBOL)
            tv_symbol = symbol.replace('/', '')
            
            msg = (
                f"🚨 *MOMENTUM ALERT*\n\n"
                f"Asset: `{symbol}`\n"
                f"Signal: {icon}\n"
                f"Price: `{price}`\n"
                f"Power: *{power:.1f}x*\n\n"
                f"📊 [Buka di TradingView](https://www.tradingview.com/chart/?symbol=BINGX:{tv_symbol})"
            )
            return {"power": power, "message": msg}
    except:
        pass
    return None

if __name__ == "__main__":
    print(f"Memulai scanning {limit_coins} koin Top ROI di BingX...")
    symbols = get_top_symbols()
    
    found_signals = []

    for s in symbols:
        result = check_momentum(s)
        if result:
            found_signals.append(result)
            print(f"Match: {s} ({result['power']:.1f}x)")
        
        # Jeda 0.5 detik agar tidak kena blokir API BingX
        time.sleep(0.5)
    
    # URUTKAN: Power terkecil ke terbesar
    # Supaya Power TERBESAR (paling meledak) berada di chat paling bawah
    found_signals.sort(key=lambda x: x['power'])

    # Kirim ke Telegram
    for signal in found_signals:
        send_telegram(signal['message'])
        time.sleep(1) # Jeda antar pesan Telegram
    
    print(f"Selesai. {len(found_signals)} sinyal terdeteksi.")
