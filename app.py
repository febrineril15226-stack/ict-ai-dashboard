import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from PIL import Image
from openai import OpenAI
import ta
from datetime import datetime

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="Forex Grok AI",
    page_icon="📈",
    layout="wide"
)

# ==================================================
# MODERN UI
# ==================================================
st.markdown("""
<style>

.stApp{
    background-color:#0B0F19;
    color:white;
}

.block-container{
    padding-top:1rem;
}

div[data-testid="metric-container"]{
    background:#131722;
    border:1px solid #2A2E39;
    border-radius:14px;
    padding:15px;
}

.stButton > button{
    width:100%;
    background:#2962FF;
    color:white;
    border:none;
    border-radius:10px;
    padding:12px;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# TITLE
# ==================================================
st.title("🏛️ Forex Grok AI Trading Platform")
st.caption("ICT + Smart Money Concept + Realtime Forex Market")

# ==================================================
# API KEY INPUT
# ==================================================
col1, col2 = st.columns(2)

with col1:
    grok_api = st.text_input(
        "Masukkan Grok API Key",
        type="password"
    )

with col2:
    alpha_api = st.text_input(
        "Masukkan Alpha Vantage API Key",
        type="password"
    )

# ==================================================
# GROK CLIENT
# ==================================================
client = None

if grok_api:

    client = OpenAI(
        api_key=grok_api,
        base_url="https://api.x.ai/v1"
    )

# ==================================================
# FOREX SETTINGS
# ==================================================
st.markdown("---")

c1, c2, c3 = st.columns(3)

with c1:
    pair = st.selectbox(
        "Forex Pair",
        [
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "AUDUSD",
            "USDCAD",
            "USDCHF",
            "NZDUSD",
            "EURJPY",
            "GBPJPY",
            "EURGBP"
        ]
    )

with c2:
    interval = st.selectbox(
        "Timeframe",
        [
            "1min",
            "5min",
            "15min",
            "30min",
            "60min"
        ]
    )

with c3:
    ai_mode = st.selectbox(
        "AI Strategy",
        [
            "ICT Sniper",
            "Scalping",
            "Smart Money",
            "Institutional Analysis"
        ]
    )

# ==================================================
# FETCH FOREX DATA
# ==================================================
def fetch_market_data():

    from_symbol = pair[:3]
    to_symbol = pair[3:]

    url = (
        "https://www.alphavantage.co/query?"
        "function=FX_INTRADAY"
        f"&from_symbol={from_symbol}"
        f"&to_symbol={to_symbol}"
        f"&interval={interval}"
        "&outputsize=compact"
        f"&apikey={alpha_api}"
    )

    response = requests.get(url)

    data = response.json()

    key = f"Time Series FX ({interval})"

    if key not in data:
        return None

    rows = []

    for time, values in data[key].items():

        rows.append({
            "time": time,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"])
        })

    df = pd.DataFrame(rows)

    df["time"] = pd.to_datetime(df["time"])

    df = df.sort_values("time")

    return df

# ==================================================
# ICT ANALYSIS
# ==================================================
def detect_trend(df):

    ema50 = ta.trend.ema_indicator(
        df["close"],
        window=50
    )

    ema200 = ta.trend.ema_indicator(
        df["close"],
        window=200
    )

    if ema50.iloc[-1] > ema200.iloc[-1]:
        return "Bullish"

    return "Bearish"

def detect_bos(df):

    recent_high = df["high"].rolling(10).max().iloc[-2]

    current = df["close"].iloc[-1]

    if current > recent_high:
        return "Bullish BOS"

    return "No BOS"

def detect_choch(df):

    recent_low = df["low"].rolling(10).min().iloc[-2]

    current = df["close"].iloc[-1]

    if current < recent_low:
        return "Bearish CHOCH"

    return "No CHOCH"

def detect_rsi(df):

    rsi = ta.momentum.RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    return round(rsi.iloc[-1], 2)

# ==================================================
# ANALYZE REALTIME MARKET
# ==================================================
if st.button("🚀 Analyze Realtime Forex Market"):

    if not grok_api:
        st.error("Masukkan Grok API Key")
        st.stop()

    if not alpha_api:
        st.error("Masukkan Alpha Vantage API Key")
        st.stop()

    with st.spinner("Mengambil realtime forex data..."):

        df = fetch_market_data()

    if df is None:
        st.error("Forex market data gagal diambil")
        st.stop()

    # ==================================================
    # FOREX CHART
    # ==================================================
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"]
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0B0F19",
        plot_bgcolor="#0B0F19",
        xaxis_rangeslider_visible=False,
        height=700
    )

    st.plotly_chart(fig)

    # ==================================================
    # METRICS
    # ==================================================
    trend = detect_trend(df)
    bos = detect_bos(df)
    choch = detect_choch(df)
    rsi = detect_rsi(df)

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("Trend", trend)

    with m2:
        st.metric("BOS", bos)

    with m3:
        st.metric("CHOCH", choch)

    with m4:
        st.metric("RSI", rsi)

    # ==================================================
    # AI PROMPT
    # ==================================================
    latest_price = df["close"].iloc[-1]

    prompt = f"""
    You are a professional ICT and Smart Money Concept trader.

    Analyze this realtime forex market using:

    - ICT
    - Smart Money Concept
    - Liquidity
    - BOS
    - CHOCH
    - Order Block
    - Fair Value Gap
    - Scalping
    - Sniper Entry

    Pair:
    {pair}

    Timeframe:
    {interval}

    AI Strategy:
    {ai_mode}

    Trend:
    {trend}

    BOS:
    {bos}

    CHOCH:
    {choch}

    RSI:
    {rsi}

    Current Price:
    {latest_price}

    Give:
    - BUY or SELL
    - Market Direction
    - Entry Zone
    - Stop Loss
    - Take Profit
    - Confidence %
    - Liquidity Target
    - Institutional Bias
    """

    # ==================================================
    # GROK ANALYSIS
    # ==================================================
    with st.spinner("Grok AI sedang menganalisa forex market..."):

        try:

            response = client.chat.completions.create(
                model="grok-3",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            result = response.choices[0].message.content

            st.markdown("## 🤖 Grok AI Forex Analysis")

            st.write(result)

        except Exception as e:

            st.error(e)

# ==================================================
# SCREENSHOT ANALYSIS
# ==================================================
st.markdown("---")

st.subheader("📸 Upload Forex Chart Screenshot")

uploaded = st.file_uploader(
    "Upload Screenshot",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded:

    for file in uploaded:

        image = Image.open(file)

        st.image(
            image,
            width=700
        )

        if st.button(f"🧠 Analyze {file.name}"):

            if not grok_api:
                st.error("Masukkan Grok API Key")
                st.stop()

            with st.spinner("AI sedang membaca forex chart..."):

                try:

                    prompt = f"""
                    You are a professional ICT forex trader.

                    Analyze this forex chart screenshot using:

                    - ICT
                    - Smart Money Concept
                    - Liquidity
                    - BOS
                    - CHOCH
                    - Order Block
                    - Fair Value Gap
                    - Scalping Setup
                    - Sniper Entry

                    Give:
                    - BUY or SELL
                    - Market Direction
                    - Entry Zone
                    - Stop Loss
                    - Take Profit
                    - Confidence %
                    - Institutional Bias
                    """

                    response = client.chat.completions.create(
                        model="grok-3",
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    )

                    result = response.choices[0].message.content

                    st.markdown("## 📈 AI Screenshot Forex Analysis")

                    st.write(result)

                except Exception as e:

                    st.error(e)

# ==================================================
# FOOTER
# ==================================================
st.markdown("---")

st.caption(
    f"Realtime Forex AI Dashboard • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
