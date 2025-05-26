import pandas as pd
import streamlit as st
import requests
import matplotlib.pyplot as plt

from ta.trend import EMAIndicator, SMAIndicator, MACD
from ta.momentum import RSIIndicator

# Page config
st.set_page_config(page_title="Gold Trading Dashboard", layout="wide")
st.title("📈 Gold Price Dashboard (XAU/USD via Twelve Data)")

# Your Twelve Data API key
API_KEY = "99d51c6ee5d74cfa9b9da21bb1cfa546"

# Load data from Twelve Data
@st.cache_data(ttl=3600)
def load_data():
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": "XAU/USD",
        "interval": "1h",
        "outputsize": 500,
        "apikey": API_KEY
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

        # Technical indicators
        df['EMA20'] = EMAIndicator(close=df['Close'], window=20).ema_indicator()
        df['SMA50'] = SMAIndicator(close=df['Close'], window=50).sma_indicator()
        df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
        df['MACD'] = MACD(close=df['Close']).macd_diff()

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
        st.error(f"Failed to fetch or process data: {e}")
        return pd.DataFrame()

# Load and validate
df = load_data()
if df.empty:
    st.stop()

latest = df.iloc[-1]

# Display metrics
st.metric("Latest Signal", latest['Signal'])
st.metric("Close Price", f"${latest['Close']:.2f}")
st.metric("RSI", f"{latest['RSI']:.2f}")
st.metric("MACD", f"{latest['MACD']:.2f}")

# Plot chart
st.subheader("Gold Price Chart (1H) with EMA/SMA")
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['Close'], label='Close', color='black')
ax.plot(df['EMA20'], label='EMA 20', linestyle='--')
ax.plot(df['SMA50'], label='SMA 50', linestyle=':')
ax.set_title("XAU/USD - 1 Hour Candles")
ax.legend()
st.pyplot(fig)

# Raw data
if st.checkbox("Show Raw Data"):
    st.dataframe(df.tail(50))
