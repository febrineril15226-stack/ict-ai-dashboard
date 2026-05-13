import streamlit as st
import google.generativeai as genai
from PIL import Image
import yfinance as yf

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Institutional ICT Audit", page_icon="🏛️", layout="wide")

# 2. Setup API Key (Versi Terbaru)
genai.configure(api_key="AIzaSyAXHdTyql-rk4VnBAyFGlXjOCgZHPs8lk8")

st.title("🏛️ Institutional ICT Audit AI")
st.caption("Menggunakan Engine High-Reasoning untuk Akurasi Pro")
st.markdown("---")

# --- SIDEBAR: HARGA REAL-TIME ---
with st.sidebar:
    st.header("📊 Market Monitor")
    pair = st.selectbox("Pilih Pair", ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "JPY=X", "GC=F"])
    try:
        data = yf.Ticker(pair).history(period="1d")
        if not data.empty:
            st.metric(label=pair.replace("=X",""), value=f"{data['Close'].iloc[-1]:.5f}")
    except: st.write("Loading...")

# --- MAIN: UPLOAD ---
st.subheader("📸 Multi-Timeframe Analysis")
uploaded_files = st.file_uploader("Upload D1, H1, dan M5", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    cols = st.columns(len(uploaded_files))
    for i, file in enumerate(uploaded_files):
        cols[i].image(Image.open(file), use_container_width=True)

    if st.button("🚀 Jalankan Analisa Institusional"):
        with st.spinner("AI sedang menghitung algoritma bank..."):
            try:
                # MENGGUNAKAN VERSI MODEL TERKUAT & TERBARU (Mencegah 404)
                model = genai.GenerativeModel('gemini-1.5-pro-002')
                
                imgs = [Image.open(f) for f in uploaded_files]
                
                prompt = """
                Anda adalah Senior Analyst di Hedge Fund yang menggunakan strategi ICT/SMC.
                Analisa 3 gambar ini dengan tingkat ketelitian 100%.

                Tugas:
                1. Identifikasi 'Higher Timeframe Draw on Liquidity'.
                2. Cari 'Sisi Likuiditas' yang sudah diambil (External Range Liquidity).
                3. Validasi MSS (Market Structure Shift) dengan Displacement kuat.
                4. Tentukan area 'Fair Value Gap' atau 'Order Block' untuk Entry.

                Output wajib:
                - BIAS NARATIVE: (Bullish/Bearish & Alasannya)
                - POI (Point of Interest): (Area harga spesifik)
                - TRADE PLAN: (Entry, SL, TP dengan RR minimal 1:3)
                - PROBABILITAS: (0-100%)
                """
                
                response = model.generate_content([prompt] + imgs)
                st.success("Analisa Selesai")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Koneksi API Gagal: {e}")
                st.info("Saran: Jika error 404 menetap, server Streamlit Anda sedang memblokir request. Silakan 'Reboot' aplikasi di dashboard Streamlit Cloud.")
