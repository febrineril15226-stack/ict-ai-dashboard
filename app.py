import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import google.generativeai as genai
from openai import OpenAI
import io, base64, ta
from datetime import datetime
import numpy as np
import yfinance as yf

# ══════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════
st.set_page_config(
    page_title="ICT AI Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0B0F19; color: white; }
    .block-container { padding-top: 1rem; }
    div[data-testid="metric-container"] {
        background: #131722; border: 1px solid #2A2E39;
        border-radius: 12px; padding: 12px;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #2962FF, #0097A7);
        color: white; border: none; border-radius: 10px;
        padding: 12px; font-weight: bold; font-size: 1rem;
    }
    .stButton > button:hover { opacity: 0.85; }
    .result-box {
        background: #131722; border-left: 4px solid #2962FF;
        border-radius: 8px; padding: 20px;
        margin-top: 12px; line-height: 1.8; color: #e2e8f0;
    }
    .signal-buy {
        background: #0d2b1a; border-left: 4px solid #4ade80;
        border-radius: 8px; padding: 14px; margin: 8px 0;
        font-size: 1.1rem; font-weight: bold; color: #4ade80; text-align: center;
    }
    .signal-sell {
        background: #2b0d0d; border-left: 4px solid #f87171;
        border-radius: 8px; padding: 14px; margin: 8px 0;
        font-size: 1.1rem; font-weight: bold; color: #f87171; text-align: center;
    }
    .signal-wait {
        background: #1a1a0d; border-left: 4px solid #facc15;
        border-radius: 8px; padding: 14px; margin: 8px 0;
        font-size: 1.1rem; font-weight: bold; color: #facc15; text-align: center;
    }
    .info-green {
        background: #0d2b1a; border: 1px solid #4ade80;
        border-radius: 8px; padding: 12px; color: #4ade80;
        margin: 6px 0; font-size: 0.9rem;
    }
    .info-blue {
        background: #0d1a2b; border: 1px solid #60a5fa;
        border-radius: 8px; padding: 12px; color: #60a5fa;
        margin: 6px 0; font-size: 0.9rem;
    }
    h1, h2, h3 { color: #e2e8f0; }
    .stTabs [data-baseweb="tab"] {
        background: #131722; color: #a0aec0;
        font-weight: 600; padding: 10px 20px; border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background: #1e2a45 !important; color: #2962FF !important;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════
st.title("🏛️ ICT AI Trading Platform")
st.caption("Real-Time Market + ICT + Smart Money Concept — Multi AI Engine")
st.markdown("---")

# ══════════════════════════════════════════
# AI ENGINE SELECTOR
# ══════════════════════════════════════════
st.markdown("### 🤖 Pilih AI Engine")
ai_engine = st.radio(
    "AI", ["🟢 Gemini AI — Gratis (Google)", "🔵 DeepSeek V3 — Pintar & Murah"],
    horizontal=True, label_visibility="collapsed"
)
use_deepseek = "DeepSeek" in ai_engine

# Info box per engine
if use_deepseek:
    st.markdown("""
    <div class="info-blue">
    🔵 <b>DeepSeek V3</b> — Analisa teks sangat mendalam. 
    Untuk screenshot, otomatis pakai Gemini Vision.<br>
    ⚠️ Butuh saldo di <a href="https://platform.deepseek.com" style="color:#60a5fa">platform.deepseek.com</a> 
    (top up min $2, sangat murah)
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="info-green">
    🟢 <b>Gemini 1.5 Flash</b> — Gratis, support vision (baca gambar chart). 
    Kuota: ~1500 req/hari. Jika habis, ganti ke DeepSeek atau buat API key baru.
    </div>""", unsafe_allow_html=True)

st.markdown("")

# ══════════════════════════════════════════
# API KEYS
# ══════════════════════════════════════════
col1, col2 = st.columns(2)
with col1:
    if use_deepseek:
        deepseek_api = st.text_input("🔵 DeepSeek API Key", type="password",
                                      placeholder="sk-...")
        st.caption("📌 platform.deepseek.com/api_keys")
        gemini_api = ""
    else:
        gemini_api = st.text_input("🟢 Gemini API Key", type="password",
                                    placeholder="Paste Gemini key...")
        st.caption("📌 Gratis: aistudio.google.com/app/apikey")
        deepseek_api = ""

with col2:
    alpha_api = st.text_input("📊 Alpha Vantage API Key (opsional)", type="password",
                               placeholder="Opsional — bisa kosong")
    st.caption("📌 Gratis: alphavantage.co  |  Jika kosong, pakai yFinance otomatis")

# Gemini selalu dibutuhkan untuk vision
gemini_for_vision = gemini_api if gemini_api else ""
if use_deepseek and not gemini_api:
    gemini_for_vision = st.text_input(
        "🟢 Gemini API Key (untuk Screenshot Analysis)",
        type="password",
        placeholder="Diperlukan untuk analisa screenshot...",
        key="gemini_vision_key"
    )
    st.caption("Screenshot selalu pakai Gemini Vision karena DeepSeek tidak support gambar")

# Configure clients
if gemini_api:
    genai.configure(api_key=gemini_api, transport='rest')
elif gemini_for_vision:
    genai.configure(api_key=gemini_for_vision, transport='rest')

ds_client = None
if deepseek_api:
    ds_client = OpenAI(api_key=deepseek_api, base_url="https://api.deepseek.com")

# ══════════════════════════════════════════
# TRADING SETTINGS
# ══════════════════════════════════════════
st.markdown("---")
c1, c2, c3 = st.columns(3)
with c1:
    pair = st.selectbox("💱 Pair", [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
        "USDCAD", "USDCHF", "NZDUSD", "EURJPY",
        "GBPJPY", "EURGBP", "GBPAUD", "EURCAD",
    ])
with c2:
    interval = st.selectbox("⏱️ Timeframe", [
        "5min", "15min", "30min", "60min", "daily"
    ])
with c3:
    ai_mode = st.selectbox("🎯 Strategy", [
        "ICT Sniper", "Smart Money Concept",
        "Institutional Analysis", "Scalping Setup"
    ])

# ══════════════════════════════════════════
# DATA SOURCES
# ══════════════════════════════════════════
# Alpha Vantage → yFinance fallback
YFINANCE_MAP = {
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X", "USDCAD": "CAD=X",   "USDCHF": "CHF=X",
    "NZDUSD": "NZDUSD=X", "EURJPY": "EURJPY=X", "GBPJPY": "GBPJPY=X",
    "EURGBP": "EURGBP=X", "GBPAUD": "GBPAUD=X", "EURCAD": "EURCAD=X",
}
YF_INTERVAL_MAP = {
    "5min": "5m", "15min": "15m", "30min": "30m",
    "60min": "60m", "daily": "1d"
}
YF_PERIOD_MAP = {
    "5min": "1d", "15min": "2d", "30min": "5d",
    "60min": "5d", "daily": "60d"
}

@st.cache_data(ttl=180)
def fetch_yfinance(pair, interval):
    """Fetch dari yFinance — selalu tersedia, tidak butuh API key."""
    ticker   = YFINANCE_MAP.get(pair, pair + "=X")
    yf_int   = YF_INTERVAL_MAP.get(interval, "15m")
    yf_per   = YF_PERIOD_MAP.get(interval, "5d")
    try:
        df = yf.Ticker(ticker).history(period=yf_per, interval=yf_int)
        if df.empty:
            return None, "yFinance: data kosong"
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        time_col = "datetime" if "datetime" in df.columns else "date"
        df = df.rename(columns={time_col: "time"})
        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
        df = df[["time","open","high","low","close","volume"]].dropna()
        return df, None
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=180)
def fetch_alphavantage(pair, interval, api_key):
    """Fetch dari Alpha Vantage."""
    from_sym = pair[:3]
    to_sym   = pair[3:]
    if interval == "daily":
        url = (f"https://www.alphavantage.co/query?function=FX_DAILY"
               f"&from_symbol={from_sym}&to_symbol={to_sym}"
               f"&outputsize=compact&apikey={api_key}")
        key = "Time Series FX (Daily)"
    else:
        url = (f"https://www.alphavantage.co/query?function=FX_INTRADAY"
               f"&from_symbol={from_sym}&to_symbol={to_sym}"
               f"&interval={interval}&outputsize=compact&apikey={api_key}")
        key = f"Time Series FX ({interval})"
    try:
        r    = requests.get(url, timeout=15)
        data = r.json()
        if "Note" in data or "Information" in data:
            return None, "Rate limit / kuota Alpha Vantage habis"
        if key not in data:
            return None, f"Key tidak ditemukan: {list(data.keys())}"
        rows = []
        for t, v in data[key].items():
            rows.append({
                "time":   pd.to_datetime(t),
                "open":   float(v["1. open"]),
                "high":   float(v["2. high"]),
                "low":    float(v["3. low"]),
                "close":  float(v["4. close"]),
                "volume": 0,
            })
        df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)
        return df, None
    except Exception as e:
        return None, str(e)

def get_data(pair, interval, alpha_api):
    """Coba Alpha Vantage dulu, fallback ke yFinance."""
    source = "yFinance"
    if alpha_api:
        df, err = fetch_alphavantage(pair, interval, alpha_api)
        if df is not None and not df.empty:
            source = "Alpha Vantage"
            return df, None, source
    # Fallback yFinance
    df, err = fetch_yfinance(pair, interval)
    if df is not None and not df.empty:
        return df, None, source
    return None, err or "Gagal ambil data", source

# ══════════════════════════════════════════
# ICT INDICATORS
# ══════════════════════════════════════════
def safe_ema(s, w):
    if len(s) < w:
        return pd.Series([np.nan]*len(s), index=s.index)
    return ta.trend.ema_indicator(s, window=w)

def get_trend(df):
    e50  = safe_ema(df["close"], 50)
    e200 = safe_ema(df["close"], 200)
    last = df["close"].iloc[-1]
    if not np.isnan(e200.iloc[-1]):
        return "📈 Bullish" if e50.iloc[-1] > e200.iloc[-1] else "📉 Bearish"
    if not np.isnan(e50.iloc[-1]):
        return "📈 Bullish" if last > e50.iloc[-1] else "📉 Bearish"
    return "➡️ Sideways"

def get_bos(df):
    n = min(12, len(df)-1)
    if n < 3: return "N/A"
    h = df["high"].iloc[-n-1:-1].max()
    l = df["low"].iloc[-n-1:-1].min()
    c = df["close"].iloc[-1]
    if c > h: return "✅ Bullish BOS"
    if c < l: return "✅ Bearish BOS"
    return "❌ No BOS"

def get_choch(df):
    if len(df) < 15: return "N/A"
    ph = df["high"].iloc[-15:-8].max()
    pl = df["low"].iloc[-15:-8].min()
    rh = df["high"].iloc[-8:-1].max()
    rl = df["low"].iloc[-8:-1].min()
    return "⚠️ CHoCH Detected" if (rl > pl and rh < ph) else "❌ No CHoCH"

def get_rsi(df):
    if len(df) < 15: return np.nan
    return round(ta.momentum.RSIIndicator(df["close"], 14).rsi().iloc[-1], 2)

def get_fvg(df):
    fvgs = []
    for i in range(2, len(df)):
        ph = df["high"].iloc[i-2]; cl = df["low"].iloc[i]
        pl = df["low"].iloc[i-2];  ch = df["high"].iloc[i]
        if cl > ph: fvgs.append(f"🟢 Bullish FVG: {round(ph,5)}–{round(cl,5)}")
        elif ch < pl: fvgs.append(f"🔴 Bearish FVG: {round(ch,5)}–{round(pl,5)}")
    return fvgs[-1] if fvgs else "Tidak ada FVG"

def get_liquidity(df):
    n = min(20, len(df))
    return round(df["low"].tail(n).min(), 5), round(df["high"].tail(n).max(), 5)

def get_ob(df):
    if len(df) < 5: return "N/A", "N/A"
    t   = df.tail(10)
    idx = abs(t["close"]-t["open"]).idxmax()
    return round(df.loc[idx,"low"],5), round(df.loc[idx,"high"],5)

# ══════════════════════════════════════════
# CHART
# ══════════════════════════════════════════
def build_chart(df, pair, interval, source):
    e20  = safe_ema(df["close"], 20)
    e50  = safe_ema(df["close"], 50)
    e200 = safe_ema(df["close"], 200)
    rsi_s = ta.momentum.RSIIndicator(df["close"],14).rsi() \
            if len(df)>=15 else pd.Series([np.nan]*len(df))

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75,0.25], vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name=pair,
        increasing_line_color="#4ade80", decreasing_line_color="#f87171",
    ), row=1, col=1)

    for ema, name, color, w in [
        (e20,"EMA 20","#facc15",1.2),(e50,"EMA 50","#60a5fa",1.5),(e200,"EMA 200","#f97316",2.0)
    ]:
        if not ema.isna().all():
            fig.add_trace(go.Scatter(x=df["time"],y=ema,name=name,
                                      line=dict(color=color,width=w)), row=1, col=1)

    fig.add_trace(go.Scatter(x=df["time"],y=rsi_s,name="RSI",
                              line=dict(color="#a78bfa",width=1.5)), row=2, col=1)
    for y, c in [(70,"#f87171"),(50,"#4a5568"),(30,"#4ade80")]:
        fig.add_hline(y=y, line_dash="dash", line_color=c, row=2, col=1)

    fig.update_layout(
        title=dict(text=f"📊 {pair} — {interval}  |  Source: {source}",
                   font=dict(color="#e2e8f0", size=14)),
        template="plotly_dark", paper_bgcolor="#0B0F19", plot_bgcolor="#131722",
        xaxis_rangeslider_visible=False, height=600,
        legend=dict(bgcolor="#131722"), margin=dict(l=10,r=10,t=45,b=10),
    )
    fig.update_xaxes(gridcolor="#1e2a45")
    fig.update_yaxes(gridcolor="#1e2a45")
    return fig

# ══════════════════════════════════════════
# PROMPT
# ══════════════════════════════════════════
def build_prompt(pair, interval, ai_mode, trend, bos, choch,
                  rsi, fvg, ob_l, ob_h, ssl, bsl, price):
    rsi_note = "Overbought⚠️" if rsi>70 else "Oversold⚠️" if rsi<30 else "Neutral"
    return f"""
Kamu adalah analis profesional ICT (Inner Circle Trader) dan Smart Money Concept.
Berikan analisa dalam Bahasa Indonesia yang tajam dan actionable.

== MARKET DATA ==
Pair: {pair} | Timeframe: {interval} | Strategy: {ai_mode}
Harga: {price} | Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC

== ICT INDICATORS ==
Trend: {trend} | BOS: {bos} | CHoCH: {choch}
RSI: {rsi} ({rsi_note}) | FVG: {fvg}
Order Block: {ob_l}–{ob_h} | SSL: {ssl} | BSL: {bsl}

== WAJIB OUTPUT ==

## 🎯 SINYAL
**Arah:** BUY / SELL / WAIT | **Keyakinan:** X%

## 📋 TRADE PLAN
| Parameter | Level |
|-----------|-------|
| Entry Zone | |
| Stop Loss | |
| TP 1 | |
| TP 2 | |
| R:R Ratio | |

## 💧 LIKUIDITAS
Draw on Liquidity target | Institutional Bias | Sweep levels

## 🧱 OB & FVG
Level kunci | Probabilitas fill

## ⚠️ INVALIDASI
Kondisi yang batalkan setup
"""

def build_vision_prompt(ai_mode):
    return f"""
Kamu adalah analis ICT dan Smart Money Concept profesional.
Strategy: {ai_mode}
Analisa chart forex ini dalam Bahasa Indonesia.

## 🔎 IDENTIFIKASI — Pair, timeframe, kondisi
## 📈 MARKET STRUCTURE — BOS, CHoCH, HH/HL
## 💧 LIKUIDITAS — BSL, SSL, DOL
## 🧱 OB & FVG — Level kunci
## 🎯 TRADE PLAN
| Sinyal | BUY/SELL/WAIT |
| Entry | |
| SL | |
| TP1 | |
| TP2 | |
| R:R | |
| Keyakinan | % |
## ⚠️ INVALIDASI
"""

# ══════════════════════════════════════════
# AI CALLS
# ══════════════════════════════════════════
def call_gemini_text(prompt, api_key):
    genai.configure(api_key=api_key, transport='rest')
    model = genai.GenerativeModel('gemini-1.5-flash')  # ✅ Model yang benar
    return model.generate_content(prompt).text

def call_gemini_vision(pil_img, prompt, api_key):
    genai.configure(api_key=api_key, transport='rest')
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=85)
    model = genai.GenerativeModel('gemini-1.5-flash')  # ✅ Model yang benar
    return model.generate_content([
        prompt,
        {"mime_type": "image/jpeg", "data": buf.getvalue()}
    ]).text

def call_deepseek_text(prompt, client):
    r = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"user","content":prompt}],
        max_tokens=2000, temperature=0.7,
    )
    return r.choices[0].message.content

def show_signal(result):
    r = result.upper()
    if "BUY" in r and "SELL" not in r[:80]:
        st.markdown('<div class="signal-buy">🟢 SINYAL: BUY</div>', unsafe_allow_html=True)
    elif "SELL" in r:
        st.markdown('<div class="signal-sell">🔴 SINYAL: SELL</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="signal-wait">🟡 SINYAL: WAIT</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════
# TABS
# ══════════════════════════════════════════
tab1, tab2 = st.tabs(["📡  Realtime Analysis", "📸  Screenshot Analysis"])

# ──────────────────────────────────────────
# TAB 1 — REALTIME
# ──────────────────────────────────────────
with tab1:
    if st.button("🚀 Analyze Realtime Forex Market", key="btn_rt"):
        # Validasi key AI
        if use_deepseek and not deepseek_api:
            st.error("❌ Masukkan DeepSeek API Key.")
            st.stop()
        if not use_deepseek and not gemini_api:
            st.error("❌ Masukkan Gemini API Key.")
            st.stop()

        # Fetch data
        with st.spinner("📡 Mengambil data forex..."):
            df, err, source = get_data(pair, interval, alpha_api)

        if df is None:
            st.error(f"❌ Gagal ambil data: {err}")
            st.stop()

        st.caption(f"✅ Data dari: **{source}** — {len(df)} candle")
        st.plotly_chart(build_chart(df, pair, interval, source),
                        use_container_width=True)

        # Indicators
        trend = get_trend(df)
        bos   = get_bos(df)
        choch = get_choch(df)
        rsi   = get_rsi(df)
        fvg   = get_fvg(df)
        ssl, bsl = get_liquidity(df)
        ob_l, ob_h = get_ob(df)
        price  = round(df["close"].iloc[-1], 5)
        rsi_v  = rsi if not np.isnan(rsi) else "N/A"

        m1,m2,m3,m4,m5,m6 = st.columns(6)
        m1.metric("💰 Price",   price)
        m2.metric("📊 Trend",   trend)
        m3.metric("💥 BOS",     bos)
        m4.metric("🔄 CHoCH",   choch)
        m5.metric("📈 RSI",     rsi_v)
        m6.metric("💧 SSL/BSL", f"{ssl}/{bsl}")
        st.info(f"**FVG:** {fvg}  |  **OB:** {ob_l}–{ob_h}")

        # AI Analysis
        engine = "DeepSeek V3" if use_deepseek else "Gemini 1.5 Flash"
        with st.spinner(f"🤖 {engine} menganalisa..."):
            try:
                prompt = build_prompt(pair, interval, ai_mode, trend,
                                       bos, choch, rsi_v, fvg,
                                       ob_l, ob_h, ssl, bsl, price)
                if use_deepseek:
                    result = call_deepseek_text(prompt, ds_client)
                else:
                    result = call_gemini_text(prompt, gemini_api)

                show_signal(result)
                st.markdown(f"## 🤖 {engine} ICT Analysis")
                st.markdown(f'<div class="result-box">{result}</div>',
                            unsafe_allow_html=True)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                st.download_button("⬇️ Download", result.encode(),
                    f"ICT_{pair}_{ts}.txt", "text/plain")

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower():
                    st.error("❌ Kuota Gemini habis hari ini!")
                    st.warning("💡 Solusi: Ganti ke **DeepSeek AI** di atas, atau buat API key Gemini baru di aistudio.google.com/app/apikey")
                elif "402" in err_str or "Insufficient" in err_str:
                    st.error("❌ Saldo DeepSeek habis!")
                    st.warning("💡 Top up di platform.deepseek.com/billing  (min $2, sangat murah)")
                else:
                    st.error(f"❌ Error: {err_str}")

# ──────────────────────────────────────────
# TAB 2 — SCREENSHOT
# ──────────────────────────────────────────
with tab2:
    st.subheader("📸 Upload Chart Screenshot")

    # Screenshot SELALU pakai Gemini Vision
    vision_key = gemini_api or gemini_for_vision
    if not vision_key:
        st.warning("⚠️ Screenshot analysis membutuhkan **Gemini API Key** (gratis). Masukkan di atas.")
    else:
        st.markdown('<div class="info-green">🟢 Screenshot analysis menggunakan <b>Gemini 1.5 Flash Vision</b> (gratis)</div>',
                    unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload chart", type=["png","jpg","jpeg"],
        accept_multiple_files=True, label_visibility="collapsed",
    )

    if uploaded:
        imgs = []
        cols = st.columns(min(len(uploaded), 3))
        for i, f in enumerate(uploaded):
            img = Image.open(f).convert("RGB")
            imgs.append((f.name, img))
            with cols[i % 3]:
                st.image(img, use_column_width=True, caption=f"Chart {i+1}: {f.name}")

        st.markdown("")
        if st.button("🧠 Analisa Semua Chart", key="btn_ss"):
            if not vision_key:
                st.error("❌ Masukkan Gemini API Key untuk analisa screenshot.")
                st.stop()

            for fname, img in imgs:
                st.markdown(f"### 📊 {fname}")
                with st.spinner(f"Gemini Vision membaca {fname}..."):
                    try:
                        prompt = build_vision_prompt(ai_mode)
                        result = call_gemini_vision(img, prompt, vision_key)
                        show_signal(result)
                        st.markdown(f'<div class="result-box">{result}</div>',
                                    unsafe_allow_html=True)
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        st.download_button(
                            f"⬇️ Download {fname}", result.encode(),
                            f"ICT_{fname}_{ts}.txt", "text/plain",
                            key=f"dl_{fname}_{ts}"
                        )
                    except Exception as e:
                        err_str = str(e)
                        if "429" in err_str or "quota" in err_str.lower():
                            st.error("❌ Kuota Gemini habis!")
                            st.warning("💡 Buat API key Gemini baru di aistudio.google.com/app/apikey (gratis)")
                        else:
                            st.error(f"❌ {fname}: {err_str}")
                st.markdown("---")
    else:
        st.markdown("""
        <div style="text-align:center;padding:50px;border:2px dashed #2A2E39;
                    border-radius:12px;color:#4a5568;">
            <h3>📸 Upload chart dari TradingView</h3>
            <p>Gemini Vision akan analisa secara visual menggunakan ICT methodology</p>
        </div>""", unsafe_allow_html=True)

st.markdown("---")
engine_info = "DeepSeek V3" if use_deepseek else "Gemini 1.5 Flash"
st.caption(f"📈 ICT AI Platform  •  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  •  {engine_info}")
