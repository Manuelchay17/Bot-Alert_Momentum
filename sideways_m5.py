import ccxt
import pandas as pd
import requests
import time

# ===== KONFIGURASI =====
TOKEN = "7590175438:AAFqBJHECghMybwf-Cgr_vMBGzSbNsbDAVM"
CHAT_ID = "1387658073"

exchange = ccxt.bingx()
timeframe = "5m" # Timeframe 5 Menit
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
        # Mengambil koin volume tertinggi agar tidak terjebak di koin mati (illiquid)
        return df.sort_values(by='quoteVolume', ascending=False).head(limit_coins)['symbol'].tolist()
    except: return []

def check_sideways_m5(symbol):
    try:
        # Mengambil 50 candle terakhir untuk akurasi rata-rata
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=50)
        df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
        
        # Indikator Bollinger Bands
        df['ma'] = df['close'].rolling(window=20).mean()
        df['std'] = df['close'].rolling(window=20).std()
        df['upper'] = df['ma'] + (2 * df['std'])
        df['lower'] = df['ma'] - (2 * df['std'])
        
        # Lebar pergerakan (Bandwidth) dalam persen
        df['bandwidth'] = ((df['upper'] - df['lower']) / df['ma']) * 100
        
        current_bw = df['bandwidth'].iloc[-1]
        
        # KRITERIA SIDEWAYS M5: 
        # Bandwidth di bawah 0.8% (Sangat sempit untuk skala 5 menit)
        if current_bw < 0.8:
            tv_symbol = symbol.replace('/', '')
            
            msg = (
                f"🔲 *M5 SIDEWAYS DETECTED*\n\n"
                f"Asset: `{symbol}`\n"
                f"Range: `{current_bw:.2f}%` (Squeeze)\n"
                f"Timeframe: `5 Minutes`\n\n"
                f"💡 *Analisa:* Harga sedang terjebak di range sempit. Siap-siap pasang jaring jika terjadi breakout!"
                f"\n\n📊 [TradingView](https://www.tradingview.com/chart/?symbol=BINGX:{tv_symbol})"
            )
            send_telegram(msg)
            return True
    except: pass
    return False

if __name__ == "__main__":
    print(f"Scanning Sideways di TF {timeframe}...")
    symbols = get_top_symbols()
    found = 0
    for s in symbols:
        if check_sideways_m5(s):
            found += 1
            print(f"Sideways: {s}")
        time.sleep(0.3)
    print(f"Selesai. Ditemukan {found} koin.")
