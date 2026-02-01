import ccxt
import pandas as pd
import requests
import os

# Ambil token dari sistem keamanan GitHub
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

exchange = ccxt.mexc()
timeframe = "15m"
multiplier = 2.0
limit_coins = 50

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def get_top_symbols():
    try:
        tickers = exchange.fetch_tickers()
        df_tickers = pd.DataFrame.from_dict(tickers, orient='index')
        df_tickers = df_tickers[df_tickers['symbol'].str.contains('/USDT')]
        top_df = df_tickers.sort_values(by='quoteVolume', ascending=False).head(limit_coins)
        return top_df['symbol'].tolist()
    except: return []

def check_momentum(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=30)
        df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
        df['body'] = abs(df['close'] - df['open'])
        avg_body = df['body'][:-1].mean()
        last_body = df['body'].iloc[-1]

        if last_body >= avg_body * multiplier:
            is_bull = df['close'].iloc[-1] > df['open'].iloc[-1]
            icon = "🟢 BULLISH" if is_bull else "🔴 BEARISH"
            msg = f"🚨 *MOMENTUM DETECTED*\n\nAsset: `{symbol}`\nSignal: {icon}\nSize: {last_body/avg_body:.1f}x\n\n[Chart](https://www.mexc.com/exchange/{symbol.replace('/', '_')})"
            send_telegram(msg)
    except: pass

if __name__ == "__main__":
    symbols = get_top_symbols()
    for s in symbols:
        check_momentum(s)