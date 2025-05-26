import pandas as pd
import streamlit as st
import requests
import matplotlib.pyplot as plt

from ta.trend import EMAIndicator, SMAIndicator, MACD
from ta.momentum import RSIIndicator

# 🔧 Streamlit settings
st.set_page_config(page_title="Gold Trading Dashboard", layout="wide")
st.title("📈 Gold Price Dashboard (XAU/USD + Telegram Alerts)")

# 🛡 API keys
TWELVE_DATA_API_KEY = "99d51c6ee5d74cfa9b9da21bb1cfa546"
TELEGRAM_TOKEN = "7898366669:AAEaveJ7bhw8T3DEiY_ascVPExvYfnqcAJw"
TELEGRAM_CHAT_ID = "6748459560"

# 📤 Telegram sender
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        res = requests.post(url, data=payload)
        return res.status_code == 200
    except Exception as e:
        st.error(f"Telegram error: {e}")
        return False

# 📊 Load gold price data
@st.cache_data(ttl=3600)
def load_data():
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": "XAU/USD",
        "interval": "1h",
        "outputsize": 500,
        "apikey": TWELVE_DATA_API_KEY
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()

        if 'values' not in data:
            st.error(f"API error: {data.get('message', 'No data returned')}")
            return pd.DataFrame()

        df = pd.DataFrame(data['values'])
        df = df.rename(columns={"datetime": "Date", "open": "Open", "high": "High",
                                "low": "Low", "close": "Close", "volume": "Volume"})
        df = df.astype({
            "Open": float, "High": float, "Low": float, "Close": float
        })
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values("Date")
        df.set_index("Date", inplace=True)

        # Indicators
        df['EMA20'] = EMAIndicator(close=df['Close'], window=20).ema_indicator()
        df['SMA50'] = SMAIndicator(close=df['Close'], window=50).sma_indicator()
        df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
        df['MACD'] = MACD(close=df['Close']).macd_diff()

        # Signal logic
        def generate_signal(row):
            if row['RSI'] < 30 and row['Close'] > row['EMA20']:
                return 'Buy'
            elif row['RSI'] > 70 and row['Close'] < row['EMA20']:
                return 'Sell'
            else:
                return 'Hold'

        df['Signal'] = df.apply(generate_signal, axis=1)
        return df

    except Exception as e:
        st.error(f"Failed to fetch/process data: {e}")
        return pd.DataFrame()

# Load data
df = load_data()
if df.empty:
    st.stop()

# Get latest and previous row
latest = df.iloc[-1]
previous = df.iloc[-2]

# 🔔 Send Telegram Alert on signal change
if latest['Signal'] != previous['Signal'] and latest['Signal'] in ['Buy', 'Sell']:
    msg = (
        f"🟡 *Gold Trading Signal*\n\n"
        f"*Signal*: {latest['Signal']}\n"
        f"*Price*: ${latest['Close']:.2f}\n"
        f"*Time*: {latest.name.strftime('%Y-%m-%d %H:%M')}"
    )
    send_telegram_alert(msg)

# Display metrics
st.metric("Latest Signal", latest['Signal'])
st.metric("Close Price", f"${latest['Close']:.2f}")
st.metric("RSI", f"{latest['RSI']:.2f}")
st.metric("MACD", f"{latest['MACD']:.2f}")

# 📈 Plot chart
st.subheader("Gold Price Chart (1H) with EMA/SMA")
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['Close'], label='Close', color='black')
ax.plot(df['EMA20'], label='EMA 20', linestyle='--')
ax.plot(df['SMA50'], label='SMA 50', linestyle=':')
ax.set_title("XAU/USD - 1 Hour")
ax.legend()
st.pyplot(fig)

# Raw data
if st.checkbox("Show Raw Data"):
    st.dataframe(df.tail(50))
