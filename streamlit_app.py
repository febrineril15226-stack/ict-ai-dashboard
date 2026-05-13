import streamlit as st
import google.generativeai as genai
from PIL import Image
import yfinance as yf

# 1. Konfigurasi Halaman - Menegaskan Level Pro
st.set_page_config(
    page_title="ICT Elite Audit Pro AI",
    page_icon="⚖️",
    layout="wide"
)

# 2. Setup API Key Gemini
# API Key Anda: AIzaSyAXHdTyql-rk4VnBAyFGlXjOCgZHPs8lk8
genai.configure(api_key="AIzaSyAXHdTyql-rk4VnBAyFGlXjOCgZHPs8lk8")

st.title("⚖️ ICT Elite Audit Pro AI")
st.caption("Powered by Google Gemini 1.5 Pro - Analisa Level Institusional")
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
    st.info("Catatan: Data Live memiliki delay ±15 menit.")

# --- MAIN: UPLOAD MULTI-TIMEFRAME ---
st.subheader("📸 Audit Struktur Market (Daily, H1, M5)")
st.info("PENTING: Unggah 3 screenshot dengan urutan: 1. Daily (Trend), 2. H1 (Struktur), 3. M5 (Entry)")

uploaded_files = st.file_uploader(
    "Upload 3 Gambar Chart Anda", 
    type=['png', 'jpg', 'jpeg'], 
    accept_multiple_files=True
)

if uploaded_files:
    # Membatasi input agar AI tidak bingung
    if len(uploaded_files) > 3:
        st.warning("Mohon unggah hanya 3 gambar untuk Top-Down Analysis yang akurat. Gambar tambahan akan diabaikan.")
        files_to_process = uploaded_files[:3]
    else:
        files_to_process = uploaded_files

    # Preview Gambar
    cols = st.columns(len(files_to_process))
    for i, file in enumerate(files_to_process):
        img = Image.open(file)
        cols[i].image(img, caption=f"Timeframe {i+1} (Order: D, H1, M5)", use_container_width=True)

    if st.button("🚀 Jalankan Audit Elite ICT Pro"):
        if len(files_to_process) < 3:
            st.error("Gagal Audit: Anda harus mengunggah tepat 3 gambar untuk analisa top-down yang valid.")
        else:
            with st.spinner("Mengakses model Gemini 1.5 Pro... Menghitung likuiditas dan audit struktur mendalam..."):
                try:
                    # BERALIH KE MODEL PRO YANG JAUH LEBIH CERDAS DAN STABIL
                    # Ini akan menyelesaikan error 404
                    model = genai.GenerativeModel(model_name='gemini-1.5-pro')
                    
                    images_to_analyze = [Image.open(f) for f in files_to_process]
                    
                    # PROMPT SUPER ELITE - DITINGKATKAN UNTUK MODEL PRO
                    prompt = """
                    Anda adalah seorang Master Trader ICT paling senior, setara dengan Michael J. Huddleston, dengan keahlian institusional.
                    Lakukan AUDIT KETAT DAN MENDALAM pada 3 chart ini secara berurutan: Daily (untuk Bias Besar), H1 (untuk Struktur Menengah), dan M5 (untuk Konfirmasi Entry).

                    Gunakan Protokol Analisa Elite berikut:
                    1.  **DRAW ON LIQUIDITY (Daily)**: Tentukan tujuan utama harga berdasarkan timeframe Daily. Cari level Buy-Side Liquidity (BSL) atau Sell-Side Liquidity (SSL) utama yang akan dituju.
                    2.  **AUDIT LIKUIDITAS & MSS (H1/M5)**: Verifikasi apakah sudah terjadi *valid Liquidity Sweep* sebelum adanya *Market Structure Shift (MSS)*. Jika MSS terjadi tanpa displacement, abaikan setup tersebut.
                    3.  **VALIDASI POI (M5)**: Cari *Fair Value Gap (FVG)*, *Order Block (OB)*, atau *Breaker Block* di timeframe kecil (M5) yang berkonfluensi dengan POI timeframe besar.
                    4.  **TANDA PERINGATAN (Red Flags)**: Berikan peringatan jika ada tanda-tanda 'inducement' (pancingan) di M5 sebelum zona entry.

                    Berikan jawaban dengan format:
                    -   **NARASI PASAR (BIAS HARIAN & DRAW ON LIQUIDITY):**
                    -   **AUDIT STRUKTUR (VALIDASI MSS & DISPLACEMENT):**
                    -   **ZONA ENTRY ELITE (AREA HARGA DETAIL):**
                    -   **RISK/REWARD & VALIDASI RR (Rasio minimal 1:2.5):**
                    -   **TINGKAT KEPERCAYAAN INSTITUSIONAL (1-100%):**

                    Gunakan Bahasa Indonesia yang profesional, tegas, dan tajam. Analisa Anda harus mengutamakan keselamatan modal.
                    """
                    
                    response = model.generate_content([prompt] + images_to_analyze)
                    st.success("Audit Selesai!")
                    st.markdown(response.text)
                    
                except Exception as e:
                    # Penanganan Error yang Lebih Detail
                    st.error(f"Terjadi kesalahan teknis: {e}")
                    if "429" in str(e):
                        st.info("Pesan: Terlalu banyak permintaan API. Mohon tunggu beberapa menit lalu coba lagi.")
                    elif "404" in str(e):
                        st.info("Pesan: Masalah API berkelanjutan. Coba buat API Key baru atau hubungi administrator.")
                    else:
                        st.info("Coba segarkan halaman atau cek koneksi internet Anda.")

# Footer
st.divider()
st.caption("Terminal Analisa Level Pro v3.0 | Risiko trading sepenuhnya di tangan pengguna.")
