import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
from openai import OpenAI
import base64
import io
import ta
from datetime import datetime
import numpy as np

# ══════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════
st.set_page_config(
    page_title="Forex Grok AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════
# CSS
# ══════════════════════════════════════════
st.markdown("""
<style>
    .stApp { background-color: #0B0F19; color: white; }
    .block-container { padding-top: 1rem; }
    div[data-testid="metric-container"] {
        background: #131722; border: 1px solid #2A2E39;
        border-radius: 14px; padding: 15px;
    }
    .stButton > button {
        width: 100%; background: linear-gradient(135deg, #2962FF, #0097A7);
        color: white; border: none; border-radius: 10px;
        padding: 12px; font-weight: bold; font-size: 1rem;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }
    .result-box {
        background: #131722; border-left: 4px solid #2962FF;
        border-radius: 8px; padding: 20px;
        margin-top: 16px; line-height: 1.8; color: #e2e8f0;
    }
    .signal-buy {
        background: #0d2b1a; border-left: 4px solid #4ade80;
        border-radius: 8px; padding: 16px; margin: 8px 0;
        font-size: 1.1rem; font-weight: bold; color: #4ade80;
    }
    .signal-sell {
        background: #2b0d0d; border-left: 4px solid #f87171;
        border-radius: 8px; padding: 16px; margin: 8px 0;
        font-size: 1.1rem; font-weight: bold; color: #f87171;
    }
    h1, h2, h3 { color: #e2e8f0; }
    .stTabs [data-baseweb="tab"] {
        background: #131722; color: #a0aec0; font-weight: 600; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background: #1e2a45 !important; color: #2962FF !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════
st.title("📈 Forex Grok AI Trading Platform")
st.caption("ICT + Smart Money Concept + Realtime Forex Analysis — Powered by Grok AI")
st.markdown("---")

# ══════════════════════════════════════════
# API KEY INPUT
# ══════════════════════════════════════════
col1, col2 = st.columns(2)
with col1:
    grok_api = st.text_input("🤖 Grok API Key (xAI)", type="password",
                              placeholder="xai-...")
    st.caption("Daftar gratis: https://console.x.ai")
with col2:
    alpha_api = st.text_input("📊 Alpha Vantage API Key", type="password",
                               placeholder="Paste API key Alpha Vantage...")
    st.caption("Daftar gratis: https://www.alphavantage.co/support/#api-key")

# ══════════════════════════════════════════
# GROK CLIENT
# ══════════════════════════════════════════
client = None
if grok_api:
    client = OpenAI(api_key=grok_api, base_url="https://api.x.ai/v1")

# ══════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════
st.markdown("---")
c1, c2, c3 = st.columns(3)
with c1:
    pair = st.selectbox("💱 Forex Pair", [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP",
        "XAUUSD"
    ])
with c2:
    interval = st.selectbox("⏱️ Timeframe", [
        "5min", "15min", "30min", "60min", "daily"
    ])
with c3:
    ai_mode = st.selectbox("🎯 AI Strategy", [
        "ICT Sniper", "Smart Money Concept",
        "Institutional Analysis", "Scalping"
    ])

# ══════════════════════════════════════════
# FETCH MARKET DATA
# ══════════════════════════════════════════
@st.cache_data(ttl=300)  # cache 5 menit
def fetch_market_data(pair, interval, api_key):
    """Ambil data candle dari Alpha Vantage."""
    from_sym = pair[:3]
    to_sym   = pair[3:] if pair != "XAUUSD" else "USD"

    if interval == "daily":
        url = (
            f"https://www.alphavantage.co/query?"
            f"function=FX_DAILY"
            f"&from_symbol={from_sym}&to_symbol={to_sym}"
            f"&outputsize=compact&apikey={api_key}"
        )
        key = "Time Series FX (Daily)"
    else:
        url = (
            f"https://www.alphavantage.co/query?"
            f"function=FX_INTRADAY"
            f"&from_symbol={from_sym}&to_symbol={to_sym}"
            f"&interval={interval}&outputsize=compact"
            f"&apikey={api_key}"
        )
        key = f"Time Series FX ({interval})"

    try:
        r    = requests.get(url, timeout=15)
        data = r.json()

        # Cek rate limit
        if "Note" in data:
            return None, "⚠️ Rate limit Alpha Vantage (max 25 req/hari). Coba 1 menit lagi."
        if "Information" in data:
            return None, "⚠️ API Key Alpha Vantage tidak valid atau kuota habis."
        if key not in data:
            return None, f"❌ Data tidak tersedia. Response: {list(data.keys())}"

        rows = []
        for time_str, v in data[key].items():
            rows.append({
                "time":   pd.to_datetime(time_str),
                "open":   float(v["1. open"]),
                "high":   float(v["2. high"]),
                "low":    float(v["3. low"]),
                "close":  float(v["4. close"]),
                "volume": 0,
            })

        df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)
        return df, None

    except requests.exceptions.Timeout:
        return None, "❌ Timeout saat mengambil data. Cek koneksi internet."
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

# ══════════════════════════════════════════
# ICT INDICATOR FUNCTIONS
# ══════════════════════════════════════════
def safe_ema(series, window):
    """EMA dengan fallback jika data kurang."""
    if len(series) < window:
        return pd.Series([np.nan] * len(series))
    return ta.trend.ema_indicator(series, window=window)

def detect_trend(df):
    ema20  = safe_ema(df["close"], 20)
    ema50  = safe_ema(df["close"], 50)
    ema200 = safe_ema(df["close"], 200)
    last   = df["close"].iloc[-1]

    if not np.isnan(ema200.iloc[-1]):
        if ema50.iloc[-1] > ema200.iloc[-1]:
            return "📈 Bullish", "#4ade80"
        return "📉 Bearish", "#f87171"
    elif not np.isnan(ema50.iloc[-1]):
        if last > ema50.iloc[-1]:
            return "📈 Bullish", "#4ade80"
        return "📉 Bearish", "#f87171"
    return "➡️ Sideways", "#facc15"

def detect_bos(df):
    if len(df) < 12:
        return "N/A"
    recent_high = df["high"].iloc[-12:-1].max()
    recent_low  = df["low"].iloc[-12:-1].min()
    current     = df["close"].iloc[-1]
    if current > recent_high:
        return "✅ Bullish BOS"
    if current < recent_low:
        return "✅ Bearish BOS"
    return "❌ No BOS"

def detect_choch(df):
    if len(df) < 15:
        return "N/A"
    prev_trend_high = df["high"].iloc[-15:-8].max()
    prev_trend_low  = df["low"].iloc[-15:-8].min()
    recent_high     = df["high"].iloc[-8:-1].max()
    recent_low      = df["low"].iloc[-8:-1].min()
    if recent_low > prev_trend_low and recent_high < prev_trend_high:
        return "⚠️ CHoCH Detected"
    return "❌ No CHoCH"

def detect_rsi(df):
    if len(df) < 15:
        return np.nan
    rsi = ta.momentum.RSIIndicator(close=df["close"], window=14).rsi()
    val = round(rsi.iloc[-1], 2)
    return val

def detect_order_block(df):
    """Deteksi Order Block sederhana."""
    if len(df) < 5:
        return "N/A", "N/A"
    # Cari candle besar sebelum pergerakan kuat
    recent = df.tail(10)
    body_sizes = abs(recent["close"] - recent["open"])
    strongest_idx = body_sizes.idxmax()
    ob = df.loc[strongest_idx]
    ob_high = round(ob["high"], 5)
    ob_low  = round(ob["low"], 5)
    return f"{ob_low}", f"{ob_high}"

def detect_fvg(df):
    """Deteksi Fair Value Gap."""
    fvgs = []
    for i in range(2, len(df)):
        prev_high = df["high"].iloc[i-2]
        curr_low  = df["low"].iloc[i]
        prev_low  = df["low"].iloc[i-2]
        curr_high = df["high"].iloc[i]
        if curr_low > prev_high:  # Bullish FVG
            fvgs.append(("Bullish", round(prev_high, 5), round(curr_low, 5)))
        elif curr_high < prev_low:  # Bearish FVG
            fvgs.append(("Bearish", round(curr_high, 5), round(prev_low, 5)))
    if fvgs:
        last = fvgs[-1]
        return f"{last[0]} FVG: {last[1]} – {last[2]}"
    return "No FVG terdeteksi"

def detect_liquidity(df):
    """Identifikasi area likuiditas."""
    if len(df) < 20:
        return "N/A", "N/A"
    bsl = round(df["high"].tail(20).max(), 5)  # Buy Side Liquidity
    ssl = round(df["low"].tail(20).min(), 5)   # Sell Side Liquidity
    return ssl, bsl

# ══════════════════════════════════════════
# CHART BUILDER
# ══════════════════════════════════════════
def build_chart(df, pair, interval):
    ema20  = safe_ema(df["close"], 20)
    ema50  = safe_ema(df["close"], 50)
    ema200 = safe_ema(df["close"], 200)
    rsi_s  = ta.momentum.RSIIndicator(close=df["close"], window=14).rsi() if len(df) >= 15 else pd.Series([np.nan]*len(df))

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name=pair,
        increasing_line_color="#4ade80",
        decreasing_line_color="#f87171",
    ), row=1, col=1)

    # EMAs
    if not ema20.isna().all():
        fig.add_trace(go.Scatter(x=df["time"], y=ema20, name="EMA 20",
                                  line=dict(color="#facc15", width=1.2)), row=1, col=1)
    if not ema50.isna().all():
        fig.add_trace(go.Scatter(x=df["time"], y=ema50, name="EMA 50",
                                  line=dict(color="#60a5fa", width=1.5)), row=1, col=1)
    if not ema200.isna().all():
        fig.add_trace(go.Scatter(x=df["time"], y=ema200, name="EMA 200",
                                  line=dict(color="#f97316", width=2)), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df["time"], y=rsi_s, name="RSI 14",
                              line=dict(color="#a78bfa", width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#f87171", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#4ade80", row=2, col=1)

    fig.update_layout(
        title=dict(text=f"📊 {pair} — {interval}", font=dict(color="#e2e8f0", size=16)),
        template="plotly_dark",
        paper_bgcolor="#0B0F19",
        plot_bgcolor="#131722",
        xaxis_rangeslider_visible=False,
        height=650,
        legend=dict(bgcolor="#131722", bordercolor="#2A2E39"),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    fig.update_xaxes(gridcolor="#1e2a45")
    fig.update_yaxes(gridcolor="#1e2a45")
    return fig

# ══════════════════════════════════════════
# IMAGE TO BASE64
# ══════════════════════════════════════════
def image_to_base64(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# ══════════════════════════════════════════
# GROK ANALYSIS FUNCTION
# ══════════════════════════════════════════
def grok_analyze_text(client, pair, interval, ai_mode, trend, bos, choch,
                       rsi, fvg, ob_low, ob_high, ssl, bsl, latest_price):
    rsi_note = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
    prompt = f"""
You are a professional ICT (Inner Circle Trader) and Smart Money Concept trader.
Analyze this forex market with precision.

== MARKET DATA ==
Pair: {pair}
Timeframe: {interval}
Strategy Mode: {ai_mode}
Current Price: {latest_price}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC

== ICT INDICATORS ==
Trend: {trend}
Break of Structure (BOS): {bos}
Change of Character (CHoCH): {choch}
RSI (14): {rsi} — {rsi_note}
Fair Value Gap: {fvg}
Order Block Range: {ob_low} – {ob_high}
Sell-Side Liquidity (SSL): {ssl}
Buy-Side Liquidity (BSL): {bsl}

== REQUIRED OUTPUT FORMAT ==

## 🎯 SIGNAL
**Direction:** BUY / SELL / WAIT
**Confidence:** X%

## 📊 TRADE PLAN
| Parameter | Level |
|-----------|-------|
| Entry Zone | |
| Stop Loss | |
| TP 1 | |
| TP 2 | |
| R:R Ratio | |

## 💧 LIQUIDITY ANALYSIS
- Draw on Liquidity target
- Institutional bias
- Sweep levels

## 🧱 ORDER BLOCK & FVG
- Key OB levels to watch
- FVG fill probability

## ⚠️ INVALIDATION
- What would cancel this setup

Use professional ICT language. Be precise and actionable.
"""
    response = client.chat.completions.create(
        model="grok-3",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
    )
    return response.choices[0].message.content

def grok_analyze_image(client, pil_img, ai_mode):
    b64 = image_to_base64(pil_img)
    prompt = f"""
You are a professional ICT (Inner Circle Trader) and Smart Money Concept analyst.
Strategy Mode: {ai_mode}

Analyze this forex chart screenshot using ICT methodology:

## 🔎 1. MARKET IDENTIFICATION
Pair, timeframe, current trend direction

## 📈 2. MARKET STRUCTURE
BOS, CHoCH, HH/HL or LH/LL pattern

## 💧 3. LIQUIDITY
BSL, SSL, Draw on Liquidity target

## 🧱 4. ORDER BLOCKS & FVG
Key OB levels, Fair Value Gaps unfilled

## 🎯 5. TRADE PLAN
| Parameter | Level |
|-----------|-------|
| Signal | BUY/SELL/WAIT |
| Entry | |
| Stop Loss | |
| TP 1 | |
| TP 2 | |
| R:R | |
| Confidence | % |

## ⚠️ 6. INVALIDATION
Conditions that cancel the setup

Be precise and actionable.
"""
    response = client.chat.completions.create(
        model="grok-2-vision-latest",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": prompt}
            ]
        }],
        max_tokens=1500,
    )
    return response.choices[0].message.content

# ══════════════════════════════════════════
# TABS
# ══════════════════════════════════════════
tab1, tab2 = st.tabs(["📡  Realtime Analysis", "📸  Chart Screenshot Analysis"])

# ══════════════════════════════════════════
# TAB 1 — REALTIME
# ══════════════════════════════════════════
with tab1:
    if st.button("🚀 Analyze Realtime Forex Market", key="btn_realtime"):
        if not grok_api:
            st.error("❌ Masukkan Grok API Key")
            st.stop()
        if not alpha_api:
            st.error("❌ Masukkan Alpha Vantage API Key")
            st.stop()

        with st.spinner("📡 Mengambil data forex real-time..."):
            df, err = fetch_market_data(pair, interval, alpha_api)

        if err:
            st.error(err)
            st.info("💡 Alpha Vantage gratis max **25 request/hari**. Daftar di https://www.alphavantage.co/support/#api-key")
            st.stop()

        if df is None or df.empty:
            st.error("❌ Data kosong.")
            st.stop()

        # Chart
        st.plotly_chart(build_chart(df, pair, interval), use_container_width=True)

        # Compute indicators
        trend_label, trend_color = detect_trend(df)
        bos    = detect_bos(df)
        choch  = detect_choch(df)
        rsi    = detect_rsi(df)
        fvg    = detect_fvg(df)
        ob_low, ob_high = detect_order_block(df)
        ssl, bsl = detect_liquidity(df)
        latest = round(df["close"].iloc[-1], 5)

        # Metrics row
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("📊 Price",   latest)
        m2.metric("🔼 Trend",   trend_label)
        m3.metric("💥 BOS",     bos)
        m4.metric("🔄 CHoCH",   choch)
        m5.metric("📈 RSI",     rsi if not np.isnan(rsi) else "N/A")
        m6.metric("💧 BSL/SSL", f"{ssl} / {bsl}")

        st.markdown("")
        st.info(f"**FVG:** {fvg}  |  **Order Block:** {ob_low} – {ob_high}")

        # Grok Analysis
        with st.spinner("🤖 Grok AI menganalisa market..."):
            try:
                result = grok_analyze_text(
                    client, pair, interval, ai_mode,
                    trend_label, bos, choch,
                    rsi if not np.isnan(rsi) else 50,
                    fvg, ob_low, ob_high, ssl, bsl, latest
                )

                # Detect signal for colored box
                if "BUY" in result.upper() and "SELL" not in result.upper()[:50]:
                    st.markdown(f'<div class="signal-buy">🟢 SIGNAL: BUY — {pair}</div>',
                                unsafe_allow_html=True)
                elif "SELL" in result.upper():
                    st.markdown(f'<div class="signal-sell">🔴 SIGNAL: SELL — {pair}</div>',
                                unsafe_allow_html=True)

                st.markdown("## 🤖 Grok AI ICT Analysis")
                st.markdown(f'<div class="result-box">{result}</div>',
                            unsafe_allow_html=True)

                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                st.download_button("⬇️ Download Hasil Analisa",
                    result.encode(), f"GrokICT_{pair}_{ts}.txt", "text/plain")

            except Exception as e:
                st.error(f"❌ Grok API error: {e}")
                st.caption("Pastikan Grok API Key valid. Daftar di https://console.x.ai")

# ══════════════════════════════════════════
# TAB 2 — SCREENSHOT ANALYSIS
# ══════════════════════════════════════════
with tab2:
    st.subheader("📸 Upload Forex Chart Screenshot")
    st.caption("Upload chart dari TradingView atau platform manapun. AI akan analisa langsung dari gambar.")

    uploaded_files = st.file_uploader(
        "Upload screenshot chart",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        # Preview semua gambar
        st.markdown(f"**{len(uploaded_files)} chart diupload:**")
        cols = st.columns(min(len(uploaded_files), 3))
        images = []
        for i, f in enumerate(uploaded_files):
            img = Image.open(f).convert("RGB")
            images.append((f.name, img))
            with cols[i % 3]:
                st.image(img, use_container_width=True, caption=f"Chart {i+1}: {f.name}")

        st.markdown("")

        if st.button("🧠 Analisa Semua Chart dengan Grok Vision", key="btn_screenshot"):
            if not grok_api:
                st.error("❌ Masukkan Grok API Key")
                st.stop()

            for fname, img in images:
                st.markdown(f"### 📊 Analisa: {fname}")
                with st.spinner(f"Grok Vision membaca {fname}..."):
                    try:
                        result = grok_analyze_image(client, img, ai_mode)

                        if "BUY" in result.upper() and "SELL" not in result.upper()[:50]:
                            st.markdown('<div class="signal-buy">🟢 SIGNAL: BUY</div>',
                                        unsafe_allow_html=True)
                        elif "SELL" in result.upper():
                            st.markdown('<div class="signal-sell">🔴 SIGNAL: SELL</div>',
                                        unsafe_allow_html=True)

                        st.markdown(f'<div class="result-box">{result}</div>',
                                    unsafe_allow_html=True)

                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        st.download_button(
                            f"⬇️ Download analisa {fname}",
                            result.encode(),
                            f"GrokVision_{fname}_{ts}.txt",
                            "text/plain",
                            key=f"dl_{fname}_{ts}"
                        )

                    except Exception as e:
                        st.error(f"❌ Error analisa {fname}: {e}")

                st.markdown("---")
    else:
        st.markdown("""
        <div style="text-align:center;padding:50px;border:2px dashed #2A2E39;
                    border-radius:12px;color:#4a5568;">
            <h3>📸 Upload chart dari TradingView</h3>
            <p>Grok Vision akan membaca dan menganalisa chart secara visual<br>
            menggunakan ICT methodology</p>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════
st.markdown("---")
st.caption(f"📈 Forex Grok AI Dashboard  •  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  •  ICT + SMC Methodology")
