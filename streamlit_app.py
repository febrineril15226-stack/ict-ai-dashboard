import streamlit as st
import google.generativeai as genai
from PIL import Image
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import io
import requests
import json
import threading
import time
import os
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ─────────────────────────────────────────────
# 1. PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ICT Institutional Audit Pro",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 2. CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    [data-testid="stMetric"] {
        background: #1c2333; border: 1px solid #2d3748;
        border-radius: 10px; padding: 10px 14px; margin-bottom: 8px;
    }
    [data-testid="stMetricValue"] { font-size: 0.95rem !important; font-weight: 700; }
    .result-box {
        background: #1c2333; border-left: 4px solid #4ade80;
        border-radius: 8px; padding: 20px; margin-top: 16px; line-height: 1.8;
    }
    .info-box {
        background: #1a2744; border-left: 4px solid #60a5fa;
        border-radius: 8px; padding: 16px; margin: 10px 0;
    }
    .success-box {
        background: #0d2b1a; border-left: 4px solid #4ade80;
        border-radius: 8px; padding: 16px; margin: 10px 0;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #4ade80, #22d3ee);
        color: #0e1117; font-weight: 700; font-size: 1rem;
        border: none; border-radius: 10px; padding: 14px;
        margin-top: 8px; transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }
    .stTabs [data-baseweb="tab"] {
        background: #1c2333; border-radius: 8px 8px 0 0;
        color: #a0aec0; font-weight: 600; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background: #2d3748 !important; color: #4ade80 !important; }
    [data-testid="stFileUploader"] { border: 2px dashed #4a5568; border-radius: 12px; padding: 12px; }
    h1, h2, h3 { color: #e2e8f0; }
    p, li { color: #a0aec0; }
    code { background: #1c2333; color: #4ade80; padding: 2px 6px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. KONSTANTA
# ─────────────────────────────────────────────
OANDA_INSTRUMENTS = {
    "EUR/USD": "EUR_USD", "GBP/USD": "GBP_USD", "AUD/USD": "AUD_USD",
    "USD/JPY": "USD_JPY", "USD/CAD": "USD_CAD", "NZD/USD": "NZD_USD",
    "USD/CHF": "USD_CHF", "GBP/JPY": "GBP_JPY", "EUR/JPY": "EUR_JPY",
    "XAU/USD (Gold)": "XAU_USD", "XAG/USD (Silver)": "XAG_USD",
    "NAS100": "NAS100_USD", "US30 (DJIA)": "US30_USD", "SPX500": "SPX500_USD",
    "BTC/USD": "BTC_USD", "ETH/USD": "ETH_USD",
}

OANDA_GRANULARITIES = {
    "Monthly (MN)": "M", "Weekly (W1)": "W",
    "Daily (D1)": "D", "4 Hour (H4)": "H4",
    "1 Hour (H1)": "H1", "30 Min (M30)": "M30",
    "15 Min (M15)": "M15", "5 Min (M5)": "M5",
}

WEBHOOK_FILE = os.path.join(tempfile.gettempdir(), "ict_tv_webhook.json")
_webhook_started = False

# ─────────────────────────────────────────────
# 4. OANDA FUNCTIONS
# ─────────────────────────────────────────────
def fetch_oanda_candles(instrument, granularity, count, api_key, is_demo=True):
    base = "https://api-fxpractice.oanda.com" if is_demo else "https://api-fxtrade.oanda.com"
    url  = f"{base}/v3/instruments/{instrument}/candles"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    params  = {"granularity": granularity, "count": count, "price": "M"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError:
        return {"error": f"HTTP {r.status_code}: {r.text}"}
    except Exception as e:
        return {"error": str(e)}

def candles_to_df(data):
    if "error" in data or "candles" not in data:
        return None
    candles = [c for c in data["candles"] if c.get("complete", True)]
    if not candles:
        return None
    rows = []
    for c in candles:
        m = c["mid"]
        rows.append({
            "Date":   pd.to_datetime(c["time"]).tz_localize(None),
            "Open":   float(m["o"]), "High":  float(m["h"]),
            "Low":    float(m["l"]), "Close": float(m["c"]),
            "Volume": int(c.get("volume", 0)),
        })
    return pd.DataFrame(rows).set_index("Date")

def generate_chart_image(df, title):
    """Candlestick chart — tries mplfinance first, falls back to matplotlib."""
    if df is None or df.empty:
        return None
    try:
        import mplfinance as mpf
        buf = io.BytesIO()
        mc = mpf.make_marketcolors(
            up='#4ade80', down='#f87171', edge='inherit',
            wick={'up': '#4ade80', 'down': '#f87171'},
            volume={'up': '#4ade80', 'down': '#f87171'},
        )
        s = mpf.make_mpf_style(
            marketcolors=mc, facecolor='#0e1117', edgecolor='#2d3748',
            figcolor='#0e1117', gridcolor='#1c2333', gridstyle='--',
            y_on_right=True,
            rc={'font.size': 8, 'text.color': '#a0aec0', 'axes.labelcolor': '#a0aec0'},
        )
        fig, _ = mpf.plot(df, type='candle', style=s, title=f"\n{title}",
                          volume=True, returnfig=True, figsize=(12, 6), tight_layout=True)
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                    facecolor='#0e1117', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf).copy()
    except ImportError:
        return _chart_fallback(df, title)

def _chart_fallback(df, title):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7),
                                    gridspec_kw={'height_ratios': [3, 1]})
    fig.patch.set_facecolor('#0e1117')
    for ax in [ax1, ax2]:
        ax.set_facecolor('#1c2333')
        ax.tick_params(colors='#a0aec0')
        for spine in ax.spines.values():
            spine.set_color('#2d3748')

    for i, (_, row) in enumerate(df.iterrows()):
        color = '#4ade80' if row['Close'] >= row['Open'] else '#f87171'
        ax1.plot([i, i], [row['Low'], row['High']], color=color, lw=1)
        rect = mpatches.Rectangle(
            (i - 0.3, min(row['Open'], row['Close'])),
            0.6, abs(row['Close'] - row['Open']),
            color=color, zorder=3
        )
        ax1.add_patch(rect)

    ax1.set_title(title, color='#e2e8f0', fontsize=12, pad=10)
    ax1.set_ylabel('Price', color='#a0aec0')
    ax1.set_xlim(-1, len(df))
    ax1.grid(True, color='#2d3748', lw=0.5, alpha=0.5)
    ax1.set_xticks([])

    x = np.arange(len(df))
    bar_colors = ['#4ade80' if df['Close'].iloc[i] >= df['Open'].iloc[i]
                  else '#f87171' for i in range(len(df))]
    ax2.bar(x, df['Volume'], color=bar_colors, width=0.7, alpha=0.8)
    ax2.set_ylabel('Volume', color='#a0aec0')
    ax2.set_xlim(-1, len(df))
    ax2.grid(True, color='#2d3748', lw=0.5, alpha=0.5)

    step = max(1, len(df) // 8)
    ticks = list(range(0, len(df), step))
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([df.index[i].strftime('%m/%d %H:%M') for i in ticks],
                         rotation=30, ha='right', color='#a0aec0', fontsize=7)
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                facecolor='#0e1117', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).copy()

# ─────────────────────────────────────────────
# 5. WEBHOOK HELPERS
# ─────────────────────────────────────────────
def save_webhook(data):
    alerts = load_webhooks()
    alerts.insert(0, {"timestamp": datetime.now().isoformat(), "data": data})
    with open(WEBHOOK_FILE, 'w') as f:
        json.dump(alerts[:20], f, indent=2)

def load_webhooks():
    if not os.path.exists(WEBHOOK_FILE):
        return []
    try:
        with open(WEBHOOK_FILE) as f:
            return json.load(f)
    except:
        return []

def clear_webhooks():
    if os.path.exists(WEBHOOK_FILE):
        os.remove(WEBHOOK_FILE)

def start_webhook_server(port=5001):
    global _webhook_started
    if _webhook_started:
        return True, port
    try:
        from flask import Flask, request as freq, jsonify
        app_wh = Flask("tv_webhook")

        @app_wh.route('/webhook', methods=['POST'])
        def receive():
            raw = freq.get_data(as_text=True)
            try:
                data = json.loads(raw)
            except:
                data = {"raw": raw}
            save_webhook(data)
            return jsonify({"status": "received"}), 200

        @app_wh.route('/ping', methods=['GET'])
        def ping():
            return jsonify({"status": "ok", "alerts": len(load_webhooks())}), 200

        t = threading.Thread(
            target=lambda: app_wh.run(host='0.0.0.0', port=port, debug=False, use_reloader=False),
            daemon=True
        )
        t.start()
        time.sleep(1.5)
        _webhook_started = True
        return True, port
    except Exception as e:
        return False, str(e)

# ─────────────────────────────────────────────
# 6. GEMINI ANALYSIS
# ─────────────────────────────────────────────
def run_gemini_analysis(images, depth, session, lang, api_key):
    genai.configure(api_key=api_key, transport='rest')
    depth_map = {
        "Standard":   "Berikan analisa komprehensif dengan semua komponen utama ICT.",
        "Deep Dive":  "Analisa sangat mendalam, sertakan konteks historical dan multi-konfirmasi.",
        "Quick Scan": "Ringkas dan to-the-point. Fokus pada setup terbaik saja.",
    }
    s_str = "" if session == "Auto Detect" else f"Fokus pada konteks {session}."
    l_str = "Tulis seluruh analisa dalam Bahasa Indonesia profesional." \
            if lang == "Indonesia" else "Write the full analysis in professional English."

    prompt = f"""
Kamu adalah analis institusional ICT (Inner Circle Trader) & Smart Money Concept.
{depth_map[depth]} {s_str} {l_str}

Analisa chart dengan struktur:

## 🔎 1. IDENTIFIKASI ASET & TIMEFRAME
Pair | Timeframe | Kondisi (trending/ranging/akumulasi/distribusi)

## 📈 2. MARKET STRUCTURE
HH/HL (Bullish) atau LH/LL (Bearish) | BOS terbaru | CHoCH | Liquidity sweep

## 💧 3. LIQUIDITY MAPPING
Buy-Side Liquidity (BSL) | Sell-Side Liquidity (SSL) | Draw on Liquidity (DOL)

## 🧱 4. ORDER BLOCKS
Bullish OB & Bearish OB dengan level | Mitigation Block

## ⚡ 5. FVG & IMBALANCE
FVG belum terisi | CE level | Single Candle Imbalance

## 🎯 6. TRADE PLAN
| Parameter | Detail |
|-----------|--------|
| Bias | Bullish/Bearish/Netral |
| DOL Target | Level likuiditas tujuan |
| Entry Zone | Range entry (OB/FVG) |
| Stop Loss | Level SL |
| TP 1 | Internal liquidity |
| TP 2 | External liquidity/DOL |
| R:R Ratio | Estimasi |
| Invalidasi | Kondisi pembatal |

## ⚠️ 7. RISIKO & KONFIRMASI
Konfirmasi sebelum entry | Faktor risiko | Skor keyakinan: ⭐ (1–5)

Gunakan bahasa tajam, profesional, dan actionable.
"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model.generate_content([prompt] + images).text

# ─────────────────────────────────────────────
# 7. API KEY SETUP
# ─────────────────────────────────────────────
API_KEY = ""
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except:
    pass

if not API_KEY:
    with st.sidebar:
        st.warning("⚠️ API Key belum diset di `secrets.toml`")
        API_KEY = st.text_input("Gemini API Key:", type="password", key="gem_key")

# ─────────────────────────────────────────────
# 8. SIDEBAR — LIVE RATES
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Live Market Rates")
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    PAIRS = {
        "EUR/USD 🇪🇺": ("EURUSD=X", 5), "GBP/USD 🇬🇧": ("GBPUSD=X", 5),
        "AUD/USD 🇦🇺": ("AUDUSD=X", 5), "USD/JPY 🇯🇵": ("JPY=X",    3),
        "USD/CAD 🇨🇦": ("CAD=X",    5), "Gold XAU ✨":  ("GC=F",     2),
        "US100 NQ 📈":  ("NQ=F",     1),
    }
    for name, (ticker, dec) in PAIRS.items():
        try:
            h = yf.Ticker(ticker).history(period="2d", interval="1d")
            if len(h) >= 2:
                cur, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                chg = cur - prev
                st.metric(name, f"{cur:.{dec}f}", f"{chg:+.{dec}f} ({chg/prev*100:+.2f}%)")
            else:
                st.metric(name, "N/A", "—")
        except:
            st.metric(name, "—", "Gagal")
    st.markdown("---")
    st.info("💡 D1 bias → H4 konfirmasi → M15 entry")
    st.caption("🏛️ ICT Institutional Audit Pro v3.0")

# ─────────────────────────────────────────────
# 9. MAIN HEADER
# ─────────────────────────────────────────────
st.title("🏛️ ICT Institutional Audit Pro")
st.markdown("**Smart Money Concept & ICT Methodology — Powered by Gemini AI**")
st.markdown("---")

# Opsi global
c1, c2, c3 = st.columns(3)
with c1:
    analysis_depth = st.selectbox("🔍 Kedalaman", ["Standard", "Deep Dive", "Quick Scan"])
with c2:
    session_focus = st.selectbox("⏰ Sesi", ["Auto Detect", "London Session", "New York Session", "Asian Session"])
with c3:
    output_lang = st.selectbox("🌐 Bahasa", ["Indonesia", "English"])

st.markdown("")

# ─────────────────────────────────────────────
# 10. TIGA TAB UTAMA
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📁  Manual Upload",
    "🔴  OANDA Auto-Fetch",
    "📡  TradingView Webhook",
])

# ══════════════════════════════════════════════
# TAB 1 — MANUAL UPLOAD
# ══════════════════════════════════════════════
with tab1:
    st.subheader("📸 Upload Chart Multi-Timeframe")
    st.caption("Disarankan: D1 + H4 + M15. Format: PNG/JPG.")

    uploaded_files = st.file_uploader(
        "Upload chart", type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True, label_visibility="collapsed",
    )

    if uploaded_files:
        cols = st.columns(min(len(uploaded_files), 3))
        images = []
        for i, f in enumerate(uploaded_files):
            img = Image.open(f)
            images.append(img)
            with cols[i % 3]:
                st.image(img, use_container_width=True, caption=f"Chart {i+1}: {f.name}")

        if st.button("🚀 Jalankan Analisa ICT", key="btn_manual"):
            if not API_KEY:
                st.error("❌ Masukkan Gemini API Key di sidebar.")
            else:
                with st.spinner("🧠 AI membedah pasar..."):
                    try:
                        result = run_gemini_analysis(
                            images, analysis_depth, session_focus, output_lang, API_KEY)
                        st.success("✅ Analisa Selesai!")
                        st.markdown(f'<div class="result-box">{result}</div>',
                                    unsafe_allow_html=True)
                        st.download_button(
                            "⬇️ Download (.txt)", result.encode(),
                            f"ICT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "text/plain")
                    except Exception as e:
                        st.error(f"❌ {e}")
    else:
        st.markdown("""
        <div style="text-align:center;padding:50px 20px;border:2px dashed #2d3748;
                    border-radius:12px;color:#718096;">
            <h3>📊 Upload chart untuk memulai</h3>
            <p>Upload 1–3 chart dari timeframe berbeda untuk hasil terbaik.</p>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 2 — OANDA AUTO-FETCH
# ══════════════════════════════════════════════
with tab2:
    st.subheader("🔴 OANDA Auto-Fetch Real-Time Candles")

    with st.expander("📖 Panduan Daftar Akun OANDA (Gratis, Klik untuk buka)"):
        st.markdown("""
<div class="info-box">

### 🪜 Cara Daftar & Dapatkan API Token OANDA

**Langkah 1 — Buka halaman registrasi**
👉 https://www.oanda.com/register/#/sign-up/demo

**Langkah 2 — Isi formulir**
- Nama, email, password
- Pilih **Demo Account** (gratis, tidak butuh deposit)
- Klik **Create Demo Account**

**Langkah 3 — Dapatkan API Token**
- Login → klik nama profil kanan atas
- Pilih **My Services** → **Manage API Access**
- Klik **Generate** → copy token yang muncul

**Langkah 4 — Paste token di kolom bawah ini** ✅

> ⚠️ Demo Account 100% gratis. Tidak perlu kartu kredit.

</div>
        """, unsafe_allow_html=True)

    st.markdown("")
    col_a, col_b = st.columns(2)
    with col_a:
        oanda_token = st.text_input("🔑 OANDA API Token", type="password",
                                     placeholder="Paste token OANDA di sini...")
    with col_b:
        is_demo = st.radio("Tipe Akun", ["Demo", "Live"], horizontal=True) == "Demo"

    col_c, col_d = st.columns(2)
    with col_c:
        selected_pair = st.selectbox("💱 Pair", list(OANDA_INSTRUMENTS.keys()))
    with col_d:
        selected_tfs = st.multiselect(
            "📊 Timeframe (1–3)", list(OANDA_GRANULARITIES.keys()),
            default=["Daily (D1)", "4 Hour (H4)", "1 Hour (H1)"],
        )

    candle_count = st.slider("🕯️ Jumlah Candle", 50, 300, 150, 25)

    if st.button("📥 Ambil Data & Analisa Otomatis", key="btn_oanda"):
        if not oanda_token:
            st.error("❌ Masukkan OANDA API Token.")
        elif not API_KEY:
            st.error("❌ Masukkan Gemini API Key di sidebar.")
        elif not selected_tfs:
            st.error("❌ Pilih minimal 1 timeframe.")
        else:
            instrument = OANDA_INSTRUMENTS[selected_pair]
            chart_images, chart_labels = [], []
            prog = st.progress(0, "Mengambil data candles...")

            for i, tf_label in enumerate(selected_tfs[:3]):
                gran = OANDA_GRANULARITIES[tf_label]
                prog.progress((i + 0.3) / len(selected_tfs),
                              f"Fetching {selected_pair} {tf_label}...")

                raw = fetch_oanda_candles(instrument, gran, candle_count,
                                          oanda_token, is_demo)
                if "error" in raw:
                    st.error(f"❌ {tf_label}: {raw['error']}")
                    break

                df = candles_to_df(raw)
                if df is None:
                    st.warning(f"⚠️ Data {tf_label} kosong.")
                    continue

                prog.progress((i + 0.7) / len(selected_tfs), f"Generating chart {tf_label}...")
                img = generate_chart_image(df, f"{selected_pair} — {tf_label}")
                if img:
                    chart_images.append(img)
                    chart_labels.append(tf_label)
                prog.progress((i + 1) / len(selected_tfs), f"✅ {tf_label}")

            prog.empty()

            if chart_images:
                st.success(f"✅ {len(chart_images)} chart berhasil dibuat!")
                cols = st.columns(len(chart_images))
                for i, img in enumerate(chart_images):
                    cols[i].image(img, use_container_width=True,
                                  caption=f"{selected_pair} — {chart_labels[i]}")

                with st.spinner("🧠 Menganalisa chart..."):
                    try:
                        result = run_gemini_analysis(
                            chart_images, analysis_depth, session_focus, output_lang, API_KEY)
                        st.success("✅ Analisa Selesai!")
                        st.markdown(f'<div class="result-box">{result}</div>',
                                    unsafe_allow_html=True)
                        fname = f"ICT_OANDA_{selected_pair.replace('/','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        st.download_button("⬇️ Download Hasil Analisa", result.encode(), fname, "text/plain")
                    except Exception as e:
                        st.error(f"❌ Gemini error: {e}")

# ══════════════════════════════════════════════
# TAB 3 — TRADINGVIEW WEBHOOK
# ══════════════════════════════════════════════
with tab3:
    st.subheader("📡 TradingView Webhook Receiver")

    with st.expander("📖 Cara Setup Alert Webhook di TradingView (Klik untuk buka)"):
        st.markdown("""
<div class="info-box">

### 🪜 Langkah Setup TradingView → Webhook

**1. Start server di bawah ini terlebih dahulu**

**2. Expose ke internet dengan ngrok (gratis)**
```
# Download: https://ngrok.com/download
ngrok http 5001
```
Copy URL hasil ngrok, contoh: `https://abc123.ngrok-free.app`

**3. Buka TradingView → Chart → klik ikon Alert (🔔)**
- Klik **Create Alert**
- Set kondisi sesuai strategi ICT kamu

**4. Di bagian "Alert Actions":**
- Centang **Webhook URL**
- Isi: `https://abc123.ngrok-free.app/webhook`

**5. Isi kolom Message dengan JSON:**
```json
{
  "pair": "{{ticker}}",
  "timeframe": "{{interval}}",
  "price": {{close}},
  "action": "BUY",
  "message": "ICT Bullish OB Detected"
}
```

**6. Klik Save** → Alert aktif! Data masuk otomatis ke sini 🚀

</div>
        """, unsafe_allow_html=True)

    st.markdown("")
    col_w1, col_w2, col_w3 = st.columns([2, 1, 1])
    with col_w1:
        wh_port = st.number_input("Port", value=5001, min_value=1024, max_value=65535)
    with col_w2:
        if st.button("▶️ Start Server", key="start_wh"):
            ok, info = start_webhook_server(int(wh_port))
            if ok:
                st.markdown(f"""
<div class="success-box">
✅ <b>Server berjalan di port {wh_port}</b><br>
🌐 Local: <code>http://localhost:{wh_port}/webhook</code><br>
🔗 Untuk TradingView jalankan: <code>ngrok http {wh_port}</code>
</div>""", unsafe_allow_html=True)
            else:
                st.error(f"❌ Gagal: {info} — Install flask dulu: pip install flask")
    with col_w3:
        if st.button("🗑️ Clear Alerts", key="clear_wh"):
            clear_webhooks()
            st.success("✅ Alert dihapus.")

    # Test manual
    st.markdown("#### 🧪 Test Alert Manual")
    test_json = st.text_area("JSON Payload:", value=json.dumps({
        "pair": "EURUSD", "timeframe": "H1",
        "price": 1.1234, "action": "BUY",
        "message": "ICT Bullish OB Detected"
    }, indent=2), height=110)

    if st.button("📨 Kirim Test Alert", key="test_wh"):
        try:
            save_webhook(json.loads(test_json))
            st.success("✅ Alert test berhasil!")
        except json.JSONDecodeError:
            st.error("❌ JSON tidak valid.")

    st.markdown("---")

    # List alerts
    alerts = load_webhooks()
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"#### 📥 Alert Masuk ({len(alerts)})")
    with col_h2:
        if st.button("🔄 Refresh", key="ref_wh"):
            st.rerun()

    if not alerts:
        st.markdown("""
        <div style="text-align:center;padding:30px;border:2px dashed #2d3748;
                    border-radius:12px;color:#718096;">
            <p>📭 Belum ada alert. Start server & kirim dari TradingView.</p>
        </div>""", unsafe_allow_html=True)
    else:
        for idx, alert in enumerate(alerts):
            ts   = alert.get("timestamp", "—")
            data = alert.get("data", {})
            pair = data.get("pair", data.get("ticker", "Unknown"))
            act  = str(data.get("action", "ALERT")).upper()
            price= data.get("price", "")
            icon = "🟢" if "BUY" in act else "🔴" if "SELL" in act else "🔵"

            with st.expander(
                f"{icon} [{ts[11:19]}]  {pair}  —  {act}  {'@ '+str(price) if price else ''}",
                expanded=(idx == 0)
            ):
                col_j1, col_j2 = st.columns(2)
                with col_j1:
                    st.json(data)
                with col_j2:
                    msg = data.get("message","")
                    if msg:
                        st.markdown(f"**📝 Message:** {msg}")
                    st.markdown(f"**🕐 Waktu:** `{ts}`")

                    oanda_key_wh = st.text_input(
                        "OANDA Token (untuk auto-chart)",
                        type="password", key=f"wt_{idx}"
                    )
                    tf_wh = st.selectbox("Timeframe analisa", list(OANDA_GRANULARITIES.keys()),
                                          index=4, key=f"wtf_{idx}")
                    acc_wh = st.radio("Akun", ["Demo", "Live"], horizontal=True, key=f"wacc_{idx}") == "Demo"

                if st.button(f"📊 Analisa Alert Ini", key=f"wa_{idx}"):
                    if not API_KEY:
                        st.error("❌ Gemini API Key belum diisi.")
                    elif oanda_key_wh:
                        raw_pair = str(pair).upper().replace("/","_").replace("-","_")
                        if "_" not in raw_pair and len(raw_pair) == 6:
                            raw_pair = raw_pair[:3] + "_" + raw_pair[3:]
                        gran = OANDA_GRANULARITIES[tf_wh]
                        with st.spinner(f"Fetching {raw_pair} {tf_wh}..."):
                            raw = fetch_oanda_candles(raw_pair, gran, 150, oanda_key_wh, acc_wh)
                            df  = candles_to_df(raw)
                            if df is not None:
                                img = generate_chart_image(df, f"{pair} — {tf_wh}")
                                if img:
                                    st.image(img, use_container_width=True)
                                    with st.spinner("Menganalisa..."):
                                        try:
                                            result = run_gemini_analysis(
                                                [img], analysis_depth, session_focus, output_lang, API_KEY)
                                            st.markdown(
                                                f'<div class="result-box">{result}</div>',
                                                unsafe_allow_html=True)
                                        except Exception as e:
                                            st.error(f"❌ {e}")
                            else:
                                st.error(f"❌ Fetch gagal: {raw.get('error','')}")
                    else:
                        st.info("ℹ️ Isi OANDA Token untuk auto-chart, atau gunakan Tab 1 untuk upload manual.")
