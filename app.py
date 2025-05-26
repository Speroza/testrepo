import yfinance as yf
import pandas as pd
import ta
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Gold Trading Dashboard", layout="wide")
st.title("📈 Gold Price Dashboard (CFD: XAUUSD)")

# Load data
@st.cache_data(ttl=3600)
def load_data():
    df = yf.download('GC=F', interval='1h', period='60d')
    df.dropna(inplace=True)
    df['EMA20'] = ta.trend.ema_indicator(df['Close'], window=20)
    df['SMA50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    df['MACD'] = ta.trend.macd_diff(df['Close'])

    def generate_signal(row):
        if row['RSI'] < 30 and row['Close'] > row['EMA20']:
            return 'Buy'
        elif row['RSI'] > 70 and row['Close'] < row['EMA20']:
            return 'Sell'
        else:
            return 'Hold'

    df['Signal'] = df.apply(generate_signal, axis=1)
    return df

df = load_data()
latest = df.iloc[-1]

# Signal Summary
st.metric("Latest Signal", latest['Signal'])
st.metric("Close Price", f"${latest['Close']:.2f}")
st.metric("RSI", f"{latest['RSI']:.2f}")
st.metric("MACD", f"{latest['MACD']:.2f}")

# Chart
st.subheader("Gold Price Chart with EMA/SMA")
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['Close'], label='Close', color='black')
ax.plot(df['EMA20'], label='EMA 20', linestyle='--')
ax.plot(df['SMA50'], label='SMA 50', linestyle=':')
ax.set_title("Gold CFD (XAU/USD) - 1H Chart")
ax.legend()
st.pyplot(fig)

# Show raw data
if st.checkbox("Show Raw Data"):
    st.dataframe(df.tail(50))
