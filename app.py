import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
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
        background: linear-gradient(135deg, #7c3aed, #2962FF);
        color: white; border: none; border-radius: 10px;
        padding: 12px; font-weight: bold; font-size: 1rem;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }
    .result-box {
        background: #131722; border-left: 4px solid #7c3aed;
        border-radius: 8px; padding: 20px;
        margin-top: 12px; line-height: 1.8; color: #e2e8f0;
    }
    .signal-buy {
        background: #0d2b1a; border-left: 4px solid #4ade80;
        border-radius: 8px; padding: 16px; margin: 8px 0;
        font-size: 1.2rem; font-weight: bold; color: #4ade80; text-align: center;
    }
    .signal-sell {
        background: #2b0d0d; border-left: 4px solid #f87171;
        border-radius: 8px; padding: 16px; margin: 8px 0;
        font-size: 1.2rem; font-weight: bold; color: #f87171; text-align: center;
    }
    .signal-wait {
        background: #1a1a0d; border-left: 4px solid #facc15;
        border-radius: 8px; padding: 16px; margin: 8px 0;
        font-size: 1.2rem; font-weight: bold; color: #facc15; text-align: center;
    }
    .badge-groq {
        background: #1a0d2b; border: 1px solid #7c3aed;
        border-radius: 20px; padding: 4px 14px; color: #a78bfa;
        font-weight: bold; font-size: 0.85rem; display: inline-block;
    }
    .badge-deepseek {
        background: #0d1a2b; border: 1px solid #60a5fa;
        border-radius: 20px; padding: 4px 14px; color: #60a5fa;
        font-weight: bold; font-size: 0.85rem; display: inline-block;
    }
    h1, h2, h3 { color: #e2e8f0; }
    .stTabs [data-baseweb="tab"] {
        background: #131722; color: #a0aec0;
        font-weight: 600; padding: 10px 20px; border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background: #1e1535 !important; color: #a78bfa !important;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════
st.title("🏛️ ICT AI Trading Platform")
st.caption("Real-Time Market + ICT + Smart Money Concept — Groq AI (Gratis) + DeepSeek")
st.markdown("---")

# ══════════════════════════════════════════
# AI ENGINE INFO
# ══════════════════════════════════════════
st.markdown("""
<div style="background:#131722;border:1px solid #2A2E39;border-radius:12px;padding:16px;margin-bottom:16px;">
<b>🤖 AI Engine yang tersedia:</b><br><br>
🟣 <b>Groq AI</b> — <span style="color:#4ade80">GRATIS sepenuhnya</span>, sangat cepat, support baca gambar chart (Vision) ✅<br>
🔵 <b>DeepSeek V3</b> — Analisa teks sangat mendalam, butuh saldo kecil (~$2)<br><br>
<span style="color:#a0aec0;font-size:0.85rem;">
Daftar Groq gratis: <b>console.groq.com</b> | 
Daftar DeepSeek: <b>platform.deepseek.com</b>
</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# API KEYS
# ══════════════════════════════════════════
col1, col2 = st.columns(2)
with col1:
    groq_api = st.text_input(
        "🟣 Groq API Key — GRATIS (Wajib)",
        type="password", placeholder="gsk_..."
    )
    st.caption("📌 Daftar gratis di console.groq.com → API Keys → Create")

with col2:
    deepseek_api = st.text_input(
        "🔵 DeepSeek API Key (Opsional)",
        type="password", placeholder="sk-... (opsional)"
    )
    st.caption("📌 platform.deepseek.com — Butuh saldo, analisa lebih mendalam")

# ══════════════════════════════════════════
# AI ENGINE SELECTOR
# ══════════════════════════════════════════
ai_engine = st.radio(
    "Pilih AI Engine untuk Analisa:",
    ["🟣 Groq AI (Gratis)", "🔵 DeepSeek V3"],
    horizontal=True
)
use_deepseek = "DeepSeek" in ai_engine

# Init clients
groq_client = OpenAI(
    api_key=groq_api or "placeholder",
    base_url="https://api.groq.com/openai/v1"
) if groq_api else None

ds_client = OpenAI(
    api_key=deepseek_api,
    base_url="https://api.deepseek.com"
) if deepseek_api else None

# ══════════════════════════════════════════
# TRADING SETTINGS
# ══════════════════════════════════════════
st.markdown("---")
c1, c2, c3 = st.columns(3)
with c1:
    pair = st.selectbox("💱 Forex Pair", [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
        "USDCAD", "USDCHF", "NZDUSD", "EURJPY",
        "GBPJPY", "EURGBP", "GBPAUD", "EURCAD",
        "XAUUSD (Gold)", "US100 (NQ)",
    ])
with c2:
    interval = st.selectbox("⏱️ Timeframe", [
        "5min", "15min", "30min", "1hour", "4hour", "daily"
    ])
with c3:
    ai_mode = st.selectbox("🎯 Strategy", [
        "ICT Sniper", "Smart Money Concept",
        "Institutional Analysis", "Scalping Setup"
    ])

# ══════════════════════════════════════════
# YFINANCE DATA (No API key needed!)
# ══════════════════════════════════════════
TICKER_MAP = {
    "EURUSD": "EURUSD=X",   "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",      "AUDUSD": "AUDUSD=X",
    "USDCAD": "CAD=X",      "USDCHF": "CHF=X",
    "NZDUSD": "NZDUSD=X",   "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",   "EURGBP": "EURGBP=X",
    "GBPAUD": "GBPAUD=X",   "EURCAD": "EURCAD=X",
    "XAUUSD (Gold)": "GC=F","US100 (NQ)": "NQ=F",
}
INTERVAL_MAP = {
    "5min":"5m","15min":"15m","30min":"30m",
    "1hour":"60m","4hour":"1h","daily":"1d"
}
PERIOD_MAP = {
    "5min":"1d","15min":"2d","30min":"5d",
    "1hour":"5d","4hour":"30d","daily":"60d"
}

@st.cache_data(ttl=120)
def get_data(pair, interval):
    ticker  = TICKER_MAP.get(pair, "EURUSD=X")
    yf_int  = INTERVAL_MAP.get(interval, "15m")
    yf_per  = PERIOD_MAP.get(interval, "5d")
    try:
        df = yf.Ticker(ticker).history(period=yf_per, interval=yf_int)
        if df.empty:
            return None, "Data kosong dari yFinance"
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        tcol = "datetime" if "datetime" in df.columns else "date"
        df = df.rename(columns={tcol: "time"})
        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
        df = df[["time","open","high","low","close"]].dropna()
        df = df.tail(150).reset_index(drop=True)
        return df, None
    except Exception as e:
        return None, str(e)

# ══════════════════════════════════════════
# ICT INDICATORS
# ══════════════════════════════════════════
def safe_ema(s, w):
    if len(s) < w:
        return pd.Series([np.nan]*len(s), index=s.index)
    return ta.trend.ema_indicator(s, window=w)

def calc_indicators(df):
    trend_str = "Sideways"
    e50  = safe_ema(df["close"], 50)
    e200 = safe_ema(df["close"], 200)
    if not np.isnan(e200.iloc[-1]):
        trend_str = "Bullish" if e50.iloc[-1] > e200.iloc[-1] else "Bearish"
    elif not np.isnan(e50.iloc[-1]):
        trend_str = "Bullish" if df["close"].iloc[-1] > e50.iloc[-1] else "Bearish"

    n   = min(12, len(df)-1)
    bos = "No BOS"
    if n >= 3:
        if df["close"].iloc[-1] > df["high"].iloc[-n-1:-1].max(): bos = "Bullish BOS ✅"
        elif df["close"].iloc[-1] < df["low"].iloc[-n-1:-1].min(): bos = "Bearish BOS ✅"

    choch = "No CHoCH"
    if len(df) >= 15:
        if (df["low"].iloc[-8:-1].min() > df["low"].iloc[-15:-8].min() and
            df["high"].iloc[-8:-1].max() < df["high"].iloc[-15:-8].max()):
            choch = "CHoCH Detected ⚠️"

    rsi_val = np.nan
    if len(df) >= 15:
        rsi_val = round(ta.momentum.RSIIndicator(df["close"],14).rsi().iloc[-1], 2)

    fvg_str = "No FVG"
    for i in range(len(df)-1, 1, -1):
        if df["low"].iloc[i] > df["high"].iloc[i-2]:
            fvg_str = f"Bullish FVG: {round(df['high'].iloc[i-2],5)}–{round(df['low'].iloc[i],5)}"
            break
        elif df["high"].iloc[i] < df["low"].iloc[i-2]:
            fvg_str = f"Bearish FVG: {round(df['high'].iloc[i],5)}–{round(df['low'].iloc[i-2],5)}"
            break

    n2   = min(20, len(df))
    ssl  = round(df["low"].tail(n2).min(), 5)
    bsl  = round(df["high"].tail(n2).max(), 5)

    ob_l, ob_h = "N/A", "N/A"
    if len(df) >= 5:
        t   = df.tail(10)
        idx = abs(t["close"]-t["open"]).idxmax()
        ob_l = round(df.loc[idx,"low"],5)
        ob_h = round(df.loc[idx,"high"],5)

    price = round(df["close"].iloc[-1], 5)
    return {
        "trend": trend_str, "bos": bos, "choch": choch,
        "rsi": rsi_val, "fvg": fvg_str,
        "ssl": ssl, "bsl": bsl, "ob_l": ob_l, "ob_h": ob_h,
        "price": price, "e50": e50, "e200": e200,
        "rsi_series": ta.momentum.RSIIndicator(df["close"],14).rsi()
            if len(df)>=15 else pd.Series([np.nan]*len(df))
    }

# ══════════════════════════════════════════
# CHART
# ══════════════════════════════════════════
def build_chart(df, ind, pair, interval):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75,0.25], vertical_spacing=0.03)

    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name=pair,
        increasing_line_color="#4ade80", decreasing_line_color="#f87171",
    ), row=1, col=1)

    e20 = safe_ema(df["close"], 20)
    for ema, name, color, w in [
        (e20,"EMA20","#facc15",1.2),
        (ind["e50"],"EMA50","#60a5fa",1.5),
        (ind["e200"],"EMA200","#f97316",2.0)
    ]:
        if not ema.isna().all():
            fig.add_trace(go.Scatter(x=df["time"],y=ema,name=name,
                                      line=dict(color=color,width=w)), row=1, col=1)

    fig.add_trace(go.Scatter(x=df["time"],y=ind["rsi_series"],name="RSI",
                              line=dict(color="#a78bfa",width=1.5)), row=2, col=1)
    for y,c in [(70,"#f87171"),(50,"#4a5568"),(30,"#4ade80")]:
        fig.add_hline(y=y, line_dash="dash", line_color=c, row=2, col=1)

    fig.update_layout(
        title=dict(text=f"📊 {pair} — {interval}  |  Data: yFinance (Real-time)",
                   font=dict(color="#e2e8f0", size=14)),
        template="plotly_dark", paper_bgcolor="#0B0F19", plot_bgcolor="#131722",
        xaxis_rangeslider_visible=False, height=580,
        legend=dict(bgcolor="#131722"), margin=dict(l=10,r=10,t=45,b=10),
    )
    fig.update_xaxes(gridcolor="#1e2a45")
    fig.update_yaxes(gridcolor="#1e2a45")
    return fig

# ══════════════════════════════════════════
# PROMPTS
# ══════════════════════════════════════════
def text_prompt(pair, interval, ai_mode, ind):
    rsi = ind["rsi"]
    rsi_note = "Overbought⚠️" if (not np.isnan(rsi) and rsi>70) else \
               "Oversold⚠️"  if (not np.isnan(rsi) and rsi<30) else "Neutral"
    rsi_str = f"{rsi} ({rsi_note})" if not np.isnan(rsi) else "N/A"
    return f"""
Kamu adalah analis profesional ICT (Inner Circle Trader) dan Smart Money Concept.
Analisa dalam Bahasa Indonesia — tajam, profesional, actionable.

== MARKET DATA ==
Pair: {pair} | Timeframe: {interval} | Strategy: {ai_mode}
Harga: {ind['price']} | Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC

== ICT INDICATORS ==
Trend: {ind['trend']} | BOS: {ind['bos']} | CHoCH: {ind['choch']}
RSI: {rsi_str} | FVG: {ind['fvg']}
Order Block: {ind['ob_l']}–{ind['ob_h']}
SSL (Sell-Side Liq): {ind['ssl']} | BSL (Buy-Side Liq): {ind['bsl']}

== FORMAT OUTPUT ==

## 🎯 SINYAL
**Arah:** BUY / SELL / WAIT
**Keyakinan:** X%

## 📋 TRADE PLAN
| Parameter | Level |
|-----------|-------|
| Entry Zone | |
| Stop Loss | |
| Take Profit 1 | |
| Take Profit 2 | |
| R:R Ratio | |

## 💧 ANALISA LIKUIDITAS
- Draw on Liquidity target
- Institutional Bias
- Level sweep penting

## 🧱 ORDER BLOCK & FVG
- Level OB kunci
- Probabilitas fill FVG

## ⚠️ INVALIDASI
- Kondisi yang batalkan setup
"""

def vision_prompt(ai_mode):
    return f"""
Kamu adalah analis ICT dan Smart Money Concept profesional.
Strategy: {ai_mode}
Analisa chart forex ini dalam Bahasa Indonesia yang profesional dan actionable.

## 🔎 IDENTIFIKASI
- Pair dan timeframe yang terlihat
- Kondisi market saat ini

## 📈 MARKET STRUCTURE
- BOS (Break of Structure) terbaru
- CHoCH (Change of Character) jika ada
- Pola HH/HL atau LH/LL

## 💧 LIKUIDITAS
- Buy-Side Liquidity (BSL)
- Sell-Side Liquidity (SSL)
- Draw on Liquidity (DOL) target

## 🧱 ORDER BLOCK & FVG
- Level Order Block kunci
- Fair Value Gap yang belum terisi

## 🎯 TRADE PLAN
| Parameter | Level |
|-----------|-------|
| Sinyal | BUY / SELL / WAIT |
| Entry | |
| Stop Loss | |
| TP 1 | |
| TP 2 | |
| R:R | |
| Keyakinan | % |

## ⚠️ INVALIDASI
- Kondisi yang membatalkan setup ini
"""

# ══════════════════════════════════════════
# AI CALLS
# ══════════════════════════════════════════
GROQ_TEXT_MODEL   = "llama-3.3-70b-versatile"
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
DEEPSEEK_MODEL    = "deepseek-chat"

def call_groq_text(prompt, client):
    r = client.chat.completions.create(
        model=GROQ_TEXT_MODEL,
        messages=[{"role":"user","content":prompt}],
        max_tokens=2000, temperature=0.7,
    )
    return r.choices[0].message.content

def call_groq_vision(pil_img, prompt, client):
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    r = client.chat.completions.create(
        model=GROQ_VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type":"image_url",
                 "image_url":{"url":f"data:image/jpeg;base64,{b64}"}},
                {"type":"text","text":prompt}
            ]
        }],
        max_tokens=2000,
    )
    return r.choices[0].message.content

def call_deepseek_text(prompt, client):
    r = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role":"user","content":prompt}],
        max_tokens=2000, temperature=0.7,
    )
    return r.choices[0].message.content

def show_signal(result):
    r = result.upper()
    if "BUY" in r and "SELL" not in r[:80]:
        st.markdown('<div class="signal-buy">🟢 SINYAL: BUY</div>',
                    unsafe_allow_html=True)
    elif "SELL" in r:
        st.markdown('<div class="signal-sell">🔴 SINYAL: SELL</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="signal-wait">🟡 SINYAL: WAIT</div>',
                    unsafe_allow_html=True)

def show_badge(engine):
    if "Groq" in engine:
        st.markdown('<span class="badge-groq">🟣 Powered by Groq AI (Free)</span>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-deepseek">🔵 Powered by DeepSeek V3</span>',
                    unsafe_allow_html=True)

def handle_error(e):
    err = str(e)
    if "401" in err or "auth" in err.lower():
        st.error("❌ API Key tidak valid. Cek kembali key kamu.")
    elif "429" in err or "quota" in err.lower() or "rate" in err.lower():
        st.error("❌ Rate limit. Tunggu beberapa detik lalu coba lagi.")
    elif "402" in err or "balance" in err.lower() or "insufficient" in err.lower():
        st.error("❌ Saldo DeepSeek habis. Top up di platform.deepseek.com")
    elif "model" in err.lower():
        st.error(f"❌ Model error: {err}")
    else:
        st.error(f"❌ Error: {err}")

# ══════════════════════════════════════════
# TABS
# ══════════════════════════════════════════
tab1, tab2 = st.tabs(["📡  Realtime Analysis", "📸  Screenshot Analysis"])

# ──────────────────────────────────────────
# TAB 1 — REALTIME
# ──────────────────────────────────────────
with tab1:
    if st.button("🚀 Analyze Realtime Market", key="btn_rt"):
        # Validasi
        if use_deepseek and not deepseek_api:
            st.error("❌ Masukkan DeepSeek API Key, atau pilih Groq AI.")
            st.stop()
        if not use_deepseek and not groq_api:
            st.error("❌ Masukkan Groq API Key. Daftar gratis di console.groq.com")
            st.stop()

        with st.spinner("📡 Mengambil data real-time..."):
            df, err = get_data(pair, interval)

        if df is None:
            st.error(f"❌ {err}")
            st.stop()

        ind = calc_indicators(df)
        st.caption(f"✅ **{len(df)} candle** — {pair} {interval} — yFinance")
        st.plotly_chart(build_chart(df, ind, pair, interval),
                        use_container_width=True)

        # Metrics
        rsi_disp = ind["rsi"] if not np.isnan(ind["rsi"]) else "N/A"
        m1,m2,m3,m4,m5,m6 = st.columns(6)
        m1.metric("💰 Price",   ind["price"])
        m2.metric("📊 Trend",   ind["trend"])
        m3.metric("💥 BOS",     ind["bos"])
        m4.metric("🔄 CHoCH",   ind["choch"])
        m5.metric("📈 RSI",     rsi_disp)
        m6.metric("💧 BSL/SSL", f"{ind['bsl']}/{ind['ssl']}")
        st.info(f"**FVG:** {ind['fvg']}  |  **OB:** {ind['ob_l']}–{ind['ob_h']}")

        engine = "DeepSeek V3" if use_deepseek else "Groq AI"
        with st.spinner(f"🤖 {engine} menganalisa market..."):
            try:
                prompt = text_prompt(pair, interval, ai_mode, ind)
                if use_deepseek:
                    result = call_deepseek_text(prompt, ds_client)
                else:
                    result = call_groq_text(prompt, groq_client)

                show_badge(engine)
                show_signal(result)
                st.markdown(f"## 🤖 {engine} ICT Analysis")
                st.markdown(f'<div class="result-box">{result}</div>',
                            unsafe_allow_html=True)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                st.download_button("⬇️ Download Analisa",
                    result.encode(), f"ICT_{pair}_{ts}.txt", "text/plain")
            except Exception as e:
                handle_error(e)

# ──────────────────────────────────────────
# TAB 2 — SCREENSHOT
# ──────────────────────────────────────────
with tab2:
    st.subheader("📸 Screenshot Chart Analysis")

    if not groq_api:
        st.warning("⚠️ Masukkan **Groq API Key** untuk analisa screenshot. Daftar gratis di console.groq.com")
    else:
        st.markdown("""
        <div style="background:#1a0d2b;border:1px solid #7c3aed;border-radius:8px;
                    padding:12px;color:#a78bfa;margin-bottom:12px;">
        🟣 Screenshot dianalisa oleh <b>Groq AI Vision (Llama 4 Scout)</b> — Gratis & Akurat ✅
        </div>""", unsafe_allow_html=True)

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
                st.image(img, use_column_width=True,
                         caption=f"Chart {i+1}: {f.name}")

        if st.button("🧠 Analisa Semua Chart dengan Groq Vision", key="btn_ss"):
            if not groq_api:
                st.error("❌ Masukkan Groq API Key. Daftar gratis di console.groq.com")
                st.stop()

            for fname, img in imgs:
                st.markdown(f"### 📊 {fname}")
                with st.spinner(f"🟣 Groq Vision membaca {fname}..."):
                    try:
                        prompt = vision_prompt(ai_mode)
                        result = call_groq_vision(img, prompt, groq_client)
                        show_badge("Groq")
                        show_signal(result)
                        st.markdown(f'<div class="result-box">{result}</div>',
                                    unsafe_allow_html=True)
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        st.download_button(
                            f"⬇️ Download {fname}", result.encode(),
                            f"ICT_Vision_{fname}_{ts}.txt", "text/plain",
                            key=f"dl_{fname}_{ts}"
                        )
                    except Exception as e:
                        handle_error(e)
                st.markdown("---")
    else:
        st.markdown("""
        <div style="text-align:center;padding:50px;border:2px dashed #2A2E39;
                    border-radius:12px;color:#4a5568;">
            <h3>📸 Upload chart dari TradingView</h3>
            <p>Groq Vision (Llama 4) akan analisa chart secara visual<br>
            menggunakan ICT & Smart Money Concept — <b>100% Gratis</b></p>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════
st.markdown("---")
engine_info = "DeepSeek V3" if use_deepseek else "Groq AI (Free)"
st.caption(
    f"📈 ICT AI Platform  •  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    f"  •  Data: yFinance  •  AI: {engine_info}"
)
