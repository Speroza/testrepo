import requests
import pandas as pd
from ta.trend import EMAIndicator, SMAIndicator, MACD
from ta.momentum import RSIIndicator
from datetime import datetime
import os

# --- Configuration ---
TWELVE_DATA_API_KEY = "99d51c6ee5d74cfa9b9da21bb1cfa546"
TELEGRAM_TOKEN = "7898366669:AAEaveJ7bhw8T3DEiY_ascVPExvYfnqcAJw"
TELEGRAM_CHAT_ID = "6748459560"
SIGNAL_FILE = "last_signal.txt"  # to remember last signal across runs

# --- Telegram Alert Function ---
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, data=payload)
        return res.status_code == 200
    except Exception as e:
        print("Telegram error:", e)
        return False

# --- Fetch Gold Data from Twelve Data ---
def fetch_gold_data():
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": "XAU/USD",
        "interval": "1h",
        "outputsize": 500,
        "apikey": TWELVE_DATA_API_KEY
    }
    res = requests.get(url, params=params)
    data = res.json()

    if 'values' not in data:
        print("Error from Twelve Data:", data.get('message'))
        return pd.DataFrame()

    df = pd.DataFrame(data['values'])
    df = df.rename(columns={"datetime": "Date", "open": "Open", "high": "High",
                            "low": "Low", "close": "Close", "volume": "Volume"})
    df = df.astype({"Open": float, "High": float, "Low": float, "Close": float})
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values("Date").set_index("Date")

    # Add indicators
    df['EMA20'] = EMAIndicator(close=df['Close'], window=20).ema_indicator()
    df['SMA50'] = SMAIndicator(close=df['Close'], window=50).sma_indicator()
    df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
    df['MACD'] = MACD(close=df['Close']).macd_diff()

    # Trading signal logic
    def get_signal(row):
        if row['RSI'] < 30 and row['Close'] > row['EMA20']:
            return 'Buy'
        elif row['RSI'] > 70 and row['Close'] < row['EMA20']:
            return 'Sell'
        return 'Hold'

    df['Signal'] = df.apply(get_signal, axis=1)
    return df

# --- Load last signal ---
def load_last_signal():
    if os.path.exists(SIGNAL_FILE):
        with open(SIGNAL_FILE, 'r') as file:
            return file.read().strip()
    return None

# --- Save current signal ---
def save_current_signal(signal):
    with open(SIGNAL_FILE, 'w') as file:
        file.write(signal)

# --- Main Execution ---
def main():
    df = fetch_gold_data()
    if df.empty:
        return

    latest = df.iloc[-1]
    signal = latest['Signal']
    last_signal = load_last_signal()

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Current signal: {signal}, Last: {last_signal}")

    if signal != last_signal and signal in ['Buy', 'Sell']:
        msg = (
            f"🟡 *Gold Trading Alert*\n\n"
            f"*Signal*: {signal}\n"
            f"*Price*: ${latest['Close']:.2f}\n"
            f"*Time*: {latest.name.strftime('%Y-%m-%d %H:%M')}"
        )
        sent = send_telegram_alert(msg)
        if sent:
            print("✅ Alert sent to Telegram.")
        else:
            print("❌ Failed to send alert.")
        save_current_signal(signal)
    else:
        print("No alert — signal unchanged or Hold.")

if __name__ == "__main__":
    main()
