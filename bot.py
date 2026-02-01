import ccxt
import pandas as pd
import requests

# ===== KONFIGURASI LANGSUNG =====
TOKEN = "7590175438:AAFqBJHECghMybwf-Cgr_vMBGzSbNsbDAVM" # Ganti jika sudah kamu revoke
CHAT_ID = "1387658073" # Ganti dengan ID Telegram kamu

# Ganti ke BingX
exchange = ccxt.bingx() 
timeframe = "15m"
multiplier = 2.0
limit_coins = 50

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except:
        pass

def get_top_symbols():
    try:
        # Ambil semua data harga dari BingX
        tickers = exchange.fetch_tickers()
        df_tickers = pd.DataFrame.from_dict(tickers, orient='index')
        
        # Filter hanya pair USDT
        df_tickers = df_tickers[df_tickers['symbol'].str.contains('/USDT')]
        
        # URUTKAN BERDASARKAN ROI TERTINGGI (Top Gainers)
        # 'percentage' adalah kolom untuk kenaikan dalam 24 jam
        top_df = df_tickers.sort_values(by='percentage', ascending=False).head(limit_coins)
        
        return top_df['symbol'].tolist()
    except Exception as e:
        print(f"Error ambil daftar koin: {e}")
        return []

def check_momentum(symbol):
    try:
        # Ambil data lilin (candle)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=30)
        df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
        
        # Hitung body candle (Selisih Harga Buka & Tutup)
        df['body'] = abs(df['close'] - df['open'])
        
        # Rata-rata body dari 29 candle sebelumnya
        avg_body = df['body'][:-1].mean()
        last_body = df['body'].iloc[-1]

        # Jika body candle terakhir lebih besar dari rata-rata dikali multiplier
        if last_body >= avg_body * multiplier:
            is_bull = df['close'].iloc[-1] > df['open'].iloc[-1]
            icon = "🟢 MOMENTUM NAIK (BULL)" if is_bull else "🔴 MOMENTUM TURUN (BEAR)"
            
            msg = (
                f"🚨 *BINGX MOMENTUM ALERT*\n\n"
                f"Asset: `{symbol}`\n"
                f"Sinyal: {icon}\n"
                f"Power: {last_body/avg_body:.1f}x lipat rata-rata\n\n"
                f"[Buka Chart BingX](https://bingx.com/en-us/spot/{symbol.replace('/', '')}/)"
            )
            send_telegram(msg)
            print(f"Alert terkirim untuk: {symbol}")
    except:
        pass

if __name__ == "__main__":
    print("Memulai scanning koin BingX...")
    symbols = get_top_symbols()
    if not symbols:
        print("Daftar koin kosong.")
    for s in symbols:
        check_momentum(s)
    print("Proses scan selesai.")


