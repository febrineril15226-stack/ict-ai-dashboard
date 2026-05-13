import streamlit as st
import google.generativeai as genai
from PIL import Image
import yfinance as yf

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="ICT Master Audit AI",
    page_icon="⚖️",
    layout="wide"
)

# 2. Setup API Key Gemini
# API Key Anda: AIzaSyAXHdTyql-rk4VnBAyFGlXjOCgZHPs8lk8
genai.configure(api_key="AIzaSyAXHdTyql-rk4VnBAyFGlXjOCgZHPs8lk8")

st.title("⚖️ ICT Master Trader Audit AI")
st.markdown("---")

# --- SIDEBAR: MONITORING HARGA LIVE ---
with st.sidebar:
    st.header("📊 Forex Live Rates")
    forex_pairs = {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "AUD/USD": "AUDUSD=X",
        "USD/JPY": "JPY=X",
        "GOLD (XAUUSD)": "GC=F"
    }
    selected_label = st.selectbox("Pilih Pair", list(forex_pairs.keys()))
    symbol = forex_pairs[selected_label]
    
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            st.metric(label=f"Harga {selected_label}", value=f"{price:.5f}")
    except:
        st.write("Memuat harga...")
    
    st.markdown("---")
    st.caption("Model: Gemini 1.5 Flash Pro v2")

# --- MAIN: UPLOAD MULTI-TIMEFRAME ---
st.subheader("📸 Audit Struktur Market (Daily, H1, M5)")
st.info("Unggah 3 screenshot chart Anda untuk mendapatkan audit ketat dari AI.")

uploaded_files = st.file_uploader(
    "Upload 3 Gambar (Urutan: Daily, H1, M5)", 
    type=['png', 'jpg', 'jpeg'], 
    accept_multiple_files=True
)

if uploaded_files:
    cols = st.columns(len(uploaded_files))
    for i, file in enumerate(uploaded_files):
        img = Image.open(file)
        cols[i].image(img, caption=f"Timeframe {i+1}", use_container_width=True)

    if st.button("🚀 Jalankan Audit Master ICT"):
        if len(uploaded_files) < 1:
            st.warning("Mohon unggah setidaknya satu gambar chart.")
        else:
            with st.spinner("Sedang melakukan audit ketat pada likuiditas dan struktur..."):
                try:
                    # Menggunakan model paling stabil dan cerdas untuk visi
                    model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
                    
                    images_to_analyze = [Image.open(f) for f in uploaded_files]
                    
                    # PROMPT SUPER PRO YANG ANDA MINTA
                    prompt = """
                    Anda adalah seorang Master Trader ICT dengan pengalaman 20 tahun. 
                    Tugas Anda adalah melakukan audit ketat pada 3 gambar chart ini (Daily, H1, M5).

                    Gunakan Protokol Analisa berikut:
                    1. ANALISA LIKUIDITAS: Cari di mana Buy-Side Liquidity (BSL) dan Sell-Side Liquidity (SSL) berada. Apakah sudah di-sweep?
                    2. STRUKTUR MARKET: Identifikasi Break of Structure (BOS) dan Market Structure Shift (MSS) secara presisi.
                    3. POINT OF INTEREST (POI): Cari Fair Value Gap (FVG) yang belum terisi (imbalance) atau Order Block (OB) yang valid.
                    4. DISPLACEMENT: Pastikan ada pergerakan harga yang kuat (displacement) setelah MSS sebelum menentukan entry.

                    Berikan jawaban dengan format:
                    - TREN UTAMA (BIAS):
                    - KONFIRMASI STRUKTUR:
                    - AREA ENTRY (Sangat Detail):
                    - ESTIMASI SL & TP (RR minimal 1:2):
                    - TINGKAT KEPERCAYAAN (1-100%):
                    
                    Berikan narasi dalam Bahasa Indonesia yang tegas, profesional, dan objektif.
                    """
                    
                    response = model.generate_content([prompt] + images_to_analyze)
                    st.success("Audit Selesai!")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Terjadi kesalahan teknis: {e}")
                    st.info("Coba segarkan halaman atau cek koneksi internet Anda.")

# Footer
st.divider()
st.caption("Peringatan: Trading melibatkan risiko tinggi. Gunakan AI hanya sebagai alat bantu konfirmasi analisa Anda.")
