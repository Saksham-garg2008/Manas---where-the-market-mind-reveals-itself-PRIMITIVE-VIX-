import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.data_fetcher import get_stock_data
from streamlit_autorefresh import st_autorefresh

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Manas", layout="wide")

st.title("📊 Manas - Where the market mind reveals itself.")

# =====================================================
#              STOCK LIST (Categorized)
# =====================================================

large_cap = {
    "RELIANCE": "RELIANCE.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HINDUNILVR": "HINDUNILVR.NS"
}

mid_cap = {
    "TATAPOWER": "TATAPOWER.NS",
    "JSWSTEEL": "JSWSTEEL.NS",
    "ADANIGREEN": "ADANIGREEN.NS",
    "LTTS": "LTTS.NS",
    "VOLTAS": "VOLTAS.NS",
    "CUMMINSIND": "CUMMINSIND.NS"
}

small_cap = {
    "TANLA": "TANLA.NS",
    "CDSL": "CDSL.NS",
    "BSE": "BSE.NS",
    "DEEPAKNTR": "DEEPAKNTR.NS",
    "MAZDOCK": "MAZDOCK.NS",
    "KRBL": "KRBL.NS"
}

# Merged dictionary
stocks = {**large_cap, **mid_cap, **small_cap}

# =====================================================
#                 UI DROPDOWN (Organized)
# =====================================================

category = st.selectbox(
    "Select Category",
    ["Large Cap", "Mid Cap", "Small Cap"]
)

if category == "Large Cap":
    selected = st.selectbox("Choose a stock", list(large_cap.keys()))
elif category == "Mid Cap":
    selected = st.selectbox("Choose a stock", list(mid_cap.keys()))
else:
    selected = st.selectbox("Choose a stock", list(small_cap.keys()))

symbol = stocks[selected]

# =====================================================
#                   FETCH DATA
# =====================================================

with st.spinner("Fetching latest data..."):
    df = get_stock_data(symbol, period="6mo", interval="1d")
    st.write(df.head())  # Debug preview

# Clean data
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0].lower() for col in df.columns]
else:
    df.columns = df.columns.str.lower()

df = df.dropna(subset=['close']).reset_index(drop=True)

# =====================================================
#                 SHOW LATEST PRICE
# =====================================================

try:
    latest_price = float(df['close'].tail(1).values[0])
    st.metric(label=f"Latest {selected} Price (₹)", value=f"{latest_price:,.2f}")
except Exception as e:
    st.error(f"Error getting latest price: {e}")
    st.stop()

# Auto-refresh
st_autorefresh(interval=60 * 1000, key="data_refresh")

# =====================================================
#               PRIMITIVE VIX CALCULATION
# =====================================================

df['returns'] = df['close'].pct_change()
df['primitive_vix'] = df['returns'].rolling(window=14).std() * np.sqrt(252) * 100

# BUY SIGNAL
HIGH_VOL = 30
df['buy_signal'] = df['primitive_vix'] > HIGH_VOL
buy_points = df[df['buy_signal'] & df['close'].notna()]

# =====================================================
#                   PRICE CHART
# =====================================================

fig_price = px.line(df, x='date', y='close', title=f"{selected} – Last 6 Months")
fig_price.update_traces(line_color='#00CC96')

# Buy markers
fig_price.add_scatter(
    x=buy_points['date'],
    y=buy_points['close'],
    mode='markers',
    marker=dict(size=10, color='red', symbol='triangle-up'),
    name='Buy Signal (VIX > 30)'
)

fig_price.update_layout(
    xaxis_title="Date",
    yaxis_title="Close Price (₹)",
    template="plotly_dark",
    title_x=0.5
)

st.plotly_chart(fig_price, use_container_width=True)

# =====================================================
#                   VIX GRAPH
# =====================================================

st.subheader(f"📈 Primitive Volatility Index (VIX-style) – {selected}")

fig_vix = px.line(
    df, x='date', y='primitive_vix',
    title=f"{selected} – 14-day Rolling Volatility (Primitive VIX)",
)

fig_vix.update_traces(line_color='#FFA500')
fig_vix.update_layout(template="plotly_dark", title_x=0.5)

# Red zone
fig_vix.add_hrect(
    y0=HIGH_VOL,
    y1=df['primitive_vix'].max(),
    fillcolor="red", opacity=0.1, line_width=0,
    annotation_text="High Volatility Zone (Buy)",
    annotation_position="top left"
)

st.plotly_chart(fig_vix, use_container_width=True)

# Latest VIX
latest_vix = float(df['primitive_vix'].tail(1).values[0])
st.metric(label=f"Latest {selected} Volatility (%)", value=f"{latest_vix:,.2f}")