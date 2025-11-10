import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.data_fetcher import get_stock_data
from streamlit_autorefresh import st_autorefresh

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Manas", layout="wide")

st.title("📊 Manas - Where the market mind reveals itself.")

# --- Stock Options ---
stocks = {
    "TCS": "TCS.NS",
    "WIPRO": "WIPRO.NS",
    "INFY": "INFY.NS",
    "RELIANCE": "RELIANCE.NS",
    "JSWSTEEL": "JSWSTEEL.NS",
    "ATGL": "ATGL.NS"
}

selected = st.selectbox("Choose a stock", list(stocks.keys()))

# --- Fetch Data ---
with st.spinner("Fetching latest data..."):
    df = get_stock_data(stocks[selected], period="6mo", interval="1d")
    st.write(df.head())  # 👈 Debug preview for structure

# --- Clean Data ---
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0].lower() for col in df.columns]
else:
    df.columns = df.columns.str.lower()

df = df.dropna(subset=['close']).reset_index(drop=True)

# --- Display Latest Info ---
try:
    latest_price = float(df['close'].tail(1).values[0])
    st.metric(label=f"Latest {selected} Price (₹)", value=f"{latest_price:,.2f}")
except Exception as e:
    st.error(f"Error getting latest price: {e}")
    st.stop()

# --- Auto-refresh every 60 seconds ---
st_autorefresh(interval=60 * 1000, key="data_refresh")

# --- Calculate Primitive VIX ---
df['returns'] = df['close'].pct_change()
df['primitive_vix'] = df['returns'].rolling(window=14).std() * np.sqrt(252) * 100  # %

# --- Identify Zones ---
HIGH_VOL = 30  # Fear zone = Buy opportunity
BLUE_LOW, BLUE_HIGH = 12, 15  # Calm zone = Short-sell zone

df['buy_signal'] = df['primitive_vix'] > HIGH_VOL
df['short_signal'] = df['primitive_vix'].between(BLUE_LOW, BLUE_HIGH)

buy_points = df[df['buy_signal'] & df['close'].notna()]
short_points = df[df['short_signal'] & df['close'].notna()]

# --- Price Chart with Buy + Short Signals ---
fig_price = px.line(df, x='date', y='close', title=f"{selected} – Last 6 Months")
fig_price.update_traces(line_color='#00CC96')

# Add Buy Markers (Red ▲)
fig_price.add_scatter(
    x=buy_points['date'],
    y=buy_points['close'],
    mode='markers',
    marker=dict(size=10, color='red', symbol='triangle-up'),
    name='Buy Signal (VIX > 30)'
)

# Add Short Markers (Blue ▼)
fig_price.add_scatter(
    x=short_points['date'],
    y=short_points['close'],
    mode='markers',
    marker=dict(size=10, color='blue', symbol='triangle-down'),
    name='Short Signal (12 ≤ VIX ≤ 15)'
)

fig_price.update_layout(
    xaxis_title="Date",
    yaxis_title="Close Price (₹)",
    template="plotly_dark",
    title_x=0.5,
    font=dict(size=14)
)

st.plotly_chart(fig_price, use_container_width=True)

# --- Plot Primitive VIX ---
st.subheader(f"📈 Primitive Volatility Index (VIX-style) – {selected}")

fig_vix = px.line(
    df, x='date', y='primitive_vix',
    title=f"{selected} – 14-day Rolling Volatility (Primitive VIX)",
    labels={'primitive_vix': 'Volatility (%)', 'date': 'Date'}
)
fig_vix.update_traces(line_color='#FFA500')
fig_vix.update_layout(template="plotly_dark", title_x=0.5)

# Highlight High Volatility Zone (Red)
fig_vix.add_hrect(
    y0=HIGH_VOL, y1=df['primitive_vix'].max(),
    fillcolor="red", opacity=0.1, line_width=0,
    annotation_text="High Volatility Zone (Buy)",
    annotation_position="top left"
)

# Highlight Calm Zone (Blue)
fig_vix.add_hrect(
    y0=BLUE_LOW, y1=BLUE_HIGH,
    fillcolor="blue", opacity=0.1, line_width=0,
    annotation_text="Calm Zone (Short)",
    annotation_position="bottom left"
)

st.plotly_chart(fig_vix, use_container_width=True)

# --- Show Latest VIX Value ---
latest_vix = float(df['primitive_vix'].tail(1).values[0])
st.metric(label=f"Latest {selected} Volatility (%)", value=f"{latest_vix:,.2f}")
