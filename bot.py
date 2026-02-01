import ccxt
import pandas as pd
import requests
import time

# ===== KONFIGURASI =====
# Ganti dengan Token Bot baru dari BotFather (karena yang lama sudah tidak aman)
TOKEN = "7590175438:AAFqBJHECghMybwf-Cgr_vMBGzSbNsbDAVM" 
# Ganti dengan Chat ID kamu (dapatkan dari @userinfobot di Telegram)
CHAT_ID = "1387658073" 

# Setting Market
exchange = ccxt.bingx() 
timeframe = "15m"
multiplier = 2.0  # Minimal 2x lipat rata-rata body
limit_coins = 50   # Scan 50 koin volume tertinggi

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
    """Mengambil daftar koin dengan volume tertinggi di BingX."""
    try:
        tickers = exchange.fetch_tickers()
        df_tickers = pd.DataFrame.from_dict(tickers, orient='index')
        
        # Filter hanya pair USDT
        df_tickers = df_tickers[df_tickers['symbol'].str.contains('/USDT')]
        
        # Urutkan berdasarkan volume (quoteVolume)
        top_df = df_tickers.sort_values(by='quoteVolume', ascending=False).head(limit_coins)
        return top_df['symbol'].tolist()
    except Exception as e:
        print(f"Error ambil daftar koin: {e}")
        return []

def check_momentum(symbol):
    """Mengecek momentum pada satu koin."""
    try:
        # Ambil data candle
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=30)
        df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
        
        # Hitung ukuran body candle terakhir
        df['body'] = abs(df['close'] - df['open'])
        
        # Hitung rata-rata body 29 candle sebelumnya
        avg_body = df['body'][:-1].mean()
        last_body = df['body'].iloc[-1]
        
        # Hitung kekuatan momentum (Power)
        power = last_body / avg_body

        # Jika memenuhi syarat multiplier
        if last_body >= avg_body * multiplier:
            is_bull = df['close'].iloc[-1] > df['open'].iloc[-1]
            icon = "🟢 BULLISH" if is_bull else "🔴 BEARISH"
            price = df['close'].iloc[-1]
            
            msg = (
                f"🚨 *MOMENTUM ALERT*\n\n"
                f"Asset: `{symbol}`\n"
                f"Signal: {icon}\n"
                f"Price: `{price}`\n"
                f"Power: *{power:.1f}x* lipat rata-rata\n\n"
                f"🔗 [Buka Chart BingX](https://bingx.com/en-us/spot/{symbol.replace('/', '')}/)"
            )
            return {"power": power, "message": msg}
    except:
        pass
    return None

if __name__ == "__main__":
    print(f"Memulai scanning {limit_coins} koin di BingX...")
    symbols = get_top_symbols()
    
    found_signals = []

    for s in symbols:
        result = check_momentum(s)
        if result:
            found_signals.append(result)
            print(f"Match ditemukan: {s} (Power: {result['power']:.1f}x)")
    
    # SORTING: Urutkan dari Power terkecil ke terbesar
    # Supaya di Telegram, pesan dengan Power TERBESAR berada di paling bawah (paling baru)
    found_signals.sort(key=lambda x: x['power'])

    # Kirim semua sinyal yang ditemukan
    for signal in found_signals:
        send_telegram(signal['message'])
        time.sleep(1) # Jeda 1 detik agar tidak dianggap spam oleh Telegram
    
    print(f"Scan selesai. Berhasil mengirim {len(found_signals)} notifikasi.")
