import streamlit as st
import google.generativeai as genai
from PIL import Image
import yfinance as yf
import pandas as pd
from datetime import datetime
import io

# ─────────────────────────────────────────────
# 1. KONFIGURASI HALAMAN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ICT Institutional Audit Pro",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 2. STYLING CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0e1117; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #1c2333;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    [data-testid="stMetricValue"] { font-size: 1rem !important; font-weight: 700; }

    /* Result box */
    .result-box {
        background: #1c2333;
        border-left: 4px solid #4ade80;
        border-radius: 8px;
        padding: 20px;
        margin-top: 16px;
        line-height: 1.7;
    }

    /* Upload area */
    [data-testid="stFileUploader"] {
        border: 2px dashed #4a5568;
        border-radius: 12px;
        padding: 12px;
    }

    /* Button */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #4ade80, #22d3ee);
        color: #0e1117;
        font-weight: 700;
        font-size: 1rem;
        border: none;
        border-radius: 10px;
        padding: 14px;
        margin-top: 10px;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }

    h1, h2, h3 { color: #e2e8f0; }
    p, li { color: #a0aec0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. SETUP API KEY (aman via st.secrets / input)
# ─────────────────────────────────────────────
API_KEY = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""

if not API_KEY:
    with st.sidebar:
        st.warning("⚠️ API Key belum diset di `secrets.toml`")
        API_KEY = st.text_input("Masukkan Gemini API Key:", type="password", key="api_key_input")

if API_KEY:
    genai.configure(api_key=API_KEY, transport='rest')

# ─────────────────────────────────────────────
# 4. SIDEBAR — LIVE FOREX RATES
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Live Market Rates")
    st.caption(f"🕐 Update: {datetime.now().strftime('%H:%M:%S')}")

    FOREX_PAIRS = {
        "EUR/USD 🇪🇺": "EURUSD=X",
        "GBP/USD 🇬🇧": "GBPUSD=X",
        "AUD/USD 🇦🇺": "AUDUSD=X",
        "USD/JPY 🇯🇵": "JPY=X",
        "USD/CAD 🇨🇦": "CAD=X",
        "Gold XAU/USD ✨": "GC=F",
        "US100 (NQ) 📈": "NQ=F",
    }

    rate_data = []
    for name, ticker in FOREX_PAIRS.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d", interval="1d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev    = hist['Close'].iloc[-2]
                change  = current - prev
                pct     = (change / prev) * 100
                decimals = 3 if "JPY" in name or "NQ" in name or "Gold" in name else 5
                st.metric(
                    label=name,
                    value=f"{current:.{decimals}f}",
                    delta=f"{change:+.{decimals}f}  ({pct:+.2f}%)"
                )
                rate_data.append({"Pair": name, "Price": round(current, decimals), "Change": round(change, decimals)})
            else:
                st.metric(label=name, value="N/A", delta="Data tidak cukup")
        except Exception:
            st.metric(label=name, value="—", delta="Gagal memuat")

    st.markdown("---")
    st.info("💡 **Tips ICT:** Gunakan D1 untuk bias, H4/H1 untuk konfirmasi, M15/M5 untuk entry presisi.")
    st.markdown("---")
    st.caption("🏛️ ICT Institutional Audit Pro v2.0")

# ─────────────────────────────────────────────
# 5. MAIN — HEADER
# ─────────────────────────────────────────────
st.title("🏛️ ICT Institutional Audit Pro")
st.markdown("**Analisa berbasis Smart Money Concept & ICT Methodology — Powered by Gemini AI**")
st.markdown("---")

# ─────────────────────────────────────────────
# 6. PILIHAN OPSI ANALISA
# ─────────────────────────────────────────────
col_opt1, col_opt2, col_opt3 = st.columns(3)

with col_opt1:
    analysis_depth = st.selectbox(
        "🔍 Kedalaman Analisa",
        ["Standard", "Deep Dive", "Quick Scan"],
        index=0,
    )

with col_opt2:
    session_focus = st.selectbox(
        "⏰ Sesi Trading",
        ["Auto Detect", "London Session", "New York Session", "Asian Session"],
        index=0,
    )

with col_opt3:
    output_lang = st.selectbox(
        "🌐 Bahasa Output",
        ["Indonesia", "English"],
        index=0,
    )

# ─────────────────────────────────────────────
# 7. UPLOAD CHART
# ─────────────────────────────────────────────
st.subheader("📸 Upload Chart Multi-Timeframe")
st.caption("Disarankan: D1 (bias) + H4 (struktur) + H1/M15 (entry). Format: PNG/JPG.")

uploaded_files = st.file_uploader(
    "Drag & drop chart di sini (bisa lebih dari 1 gambar)",
    type=['png', 'jpg', 'jpeg'],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

# ─────────────────────────────────────────────
# 8. PREVIEW CHART
# ─────────────────────────────────────────────
if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} chart diupload:**")
    cols = st.columns(min(len(uploaded_files), 3))
    images = []
    for i, file in enumerate(uploaded_files):
        img = Image.open(file)
        images.append(img)
        with cols[i % 3]:
            st.image(img, use_container_width=True, caption=f"📊 Chart {i+1}: {file.name}")

    # ─────────────────────────────────────────
    # 9. TOMBOL ANALISA
    # ─────────────────────────────────────────
    st.markdown("")
    run_btn = st.button("🚀 Jalankan Analisa Institusional ICT", use_container_width=True)

    if run_btn:
        if not API_KEY:
            st.error("❌ API Key belum dimasukkan. Silakan isi di sidebar.")
            st.stop()

        # Susun prompt berdasarkan opsi user
        depth_instruction = {
            "Standard":   "Berikan analisa komprehensif dengan semua komponen utama ICT.",
            "Deep Dive":  "Berikan analisa sangat mendalam, sertakan konteks historical dan multi-konfirmasi setiap level.",
            "Quick Scan": "Ringkas dan to-the-point. Fokus pada setup terbaik saja.",
        }[analysis_depth]

        session_instruction = "" if session_focus == "Auto Detect" else f"Fokus pada konteks {session_focus}."
        lang_instruction = "Tulis seluruh analisa dalam Bahasa Indonesia yang profesional." if output_lang == "Indonesia" else "Write the full analysis in professional English."

        prompt = f"""
Kamu adalah analis institusional berpengalaman dengan spesialisasi ICT (Inner Circle Trader) Methodology 
dan Smart Money Concept. {depth_instruction} {session_instruction} {lang_instruction}

Analisa chart yang diunggah secara menyeluruh dengan struktur berikut:

---

## 🔎 1. IDENTIFIKASI ASET & TIMEFRAME
- Identifikasi pair/aset yang terlihat di chart
- Identifikasi timeframe setiap chart
- Kondisi market saat ini (trending / ranging / akumulasi / distribusi)

## 📈 2. MARKET STRUCTURE ANALYSIS
- Higher Highs / Higher Lows (Bullish) atau Lower Highs / Lower Lows (Bearish)
- Break of Structure (BOS) terbaru
- Change of Character (CHoCH) jika ada
- Internal vs External liquidity sweep

## 💧 3. LIQUIDITY MAPPING
- Identifikasi Buy-Side Liquidity (BSL): equal highs, previous HOD/HOW
- Identifikasi Sell-Side Liquidity (SSL): equal lows, previous LOD/LOW
- Draw on Liquidity (DOL): kemana harga kemungkinan besar tertarik

## 🧱 4. ORDER BLOCKS (OB)
- Bullish OB: koordinat level & konfirmasi volume/momentum
- Bearish OB: koordinat level & konfirmasi
- Mitigation Block jika ada

## ⚡ 5. FAIR VALUE GAPS (FVG) & IMBALANCE
- Lokasi FVG yang belum terisi
- Consequent Encroachment (CE) level
- Single Candle Imbalance (SCI) jika ada

## 🎯 6. TRADE PLAN LENGKAP
| Parameter     | Detail |
|---------------|--------|
| **Bias**      | Bullish / Bearish / Netral |
| **DOL Target**| Level harga likuiditas tujuan |
| **Entry Zone**| Range harga entry (OB/FVG level) |
| **Stop Loss** | Level SL (di bawah/atas OB) |
| **TP 1**      | Target pertama (internal liquidity) |
| **TP 2**      | Target kedua (external liquidity / DOL) |
| **R:R Ratio** | Estimasi risk-to-reward |
| **Invalidasi**| Kondisi yang membatalkan setup |

## ⚠️ 7. CATATAN RISIKO & KONFIRMASI
- Konfirmasi tambahan yang diperlukan sebelum entry
- Faktor risiko utama (news, low liquidity session, dll)
- Skor keyakinan setup: ⭐⭐⭐⭐⭐ (1–5 bintang)

---
Gunakan bahasa yang tajam, profesional, dan actionable.
        """

        with st.spinner("🧠 AI sedang membedah algoritma pasar... Mohon tunggu."):
            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content([prompt] + images)

                st.success("✅ Analisa Institusional Selesai!")
                st.markdown(
                    f'<div class="result-box">{response.text}</div>',
                    unsafe_allow_html=True
                )

                # Tombol download hasil analisa
                result_bytes = response.text.encode("utf-8")
                st.download_button(
                    label="⬇️ Download Hasil Analisa (.txt)",
                    data=result_bytes,
                    file_name=f"ICT_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                )

            except genai.types.generation_types.BlockedPromptException:
                st.error("❌ Prompt diblokir oleh filter keamanan. Coba upload ulang chart yang berbeda.")
            except Exception as e:
                st.error(f"❌ Terjadi kesalahan: {str(e)}")
                st.caption("Pastikan API Key valid dan kuota Gemini API masih tersedia.")

else:
    # Placeholder saat belum ada upload
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; border: 2px dashed #2d3748; border-radius: 12px; color: #718096;">
        <h3>📊 Belum ada chart yang diupload</h3>
        <p>Upload minimal 1 chart di atas untuk memulai analisa ICT.<br>
        Untuk hasil terbaik, upload chart dari 3 timeframe berbeda (contoh: D1 + H4 + M15).</p>
    </div>
    """, unsafe_allow_html=True)
