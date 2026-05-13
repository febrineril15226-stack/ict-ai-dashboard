import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import yfinance as yf

# 1. Konfigurasi Halaman & Tema
st.set_page_config(
    page_title="ICT Forex Smart Money AI",
    page_icon="🎯",
    layout="wide"
)

# 2. Setup API Key Gemini (Sudah digabungkan)
# API Key yang Anda berikan: AIzaSyAXHdTyql-rk4VnBAyFGlXjOCgZHPs8lk8
genai.configure(api_key="AIzaSyAXHdTyql-rk4VnBAyFGlXjOCgZHPs8lk8")

# Judul Utama
st.title("🎯 ICT Forex Smart Money AI")
st.markdown("---")

# --- SIDEBAR: MONITORING HARGA LIVE ---
with st.sidebar:
    st.header("📊 Forex Live Rates")
    st.write("Pantau harga real-time sebelum analisa.")
    
    # Daftar Pair Forex Major
    forex_pairs = {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "AUD/USD": "AUDUSD=X",
        "USD/JPY": "JPY=X",
        "USD/CAD": "CAD=X",
        "USD/CHF": "CHF=X",
        "NZD/USD": "NZDUSD=X",
        "GOLD (XAUUSD)": "GC=F"
    }
    
    selected_label = st.selectbox("Pilih Pair", list(forex_pairs.keys()))
    symbol = forex_pairs[selected_label]
    
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            st.metric(label=f"Harga {selected_label}", value=f"{price:.5f}")
        else:
            st.write("Data harga tidak tersedia saat ini.")
    except:
        st.write("Koneksi harga terganggu.")
    
    st.markdown("---")
    st.caption("Terminal Analisa Struktur Market v2.0")

# --- MAIN DASHBOARD: UPLOAD MULTI-TIMEFRAME ---
st.subheader("📸 Analisa Top-Down (Multi-Timeframe)")
st.info("Pilih 3 gambar sekaligus: 1. Daily (Bias), 2. H1 (Structure), 3. M5 (Entry)")

# Fitur upload banyak gambar
uploaded_files = st.file_uploader(
    "Upload screenshots chart Anda", 
    type=['png', 'jpg', 'jpeg'], 
    accept_multiple_files=True
)

# Tampilan Preview Gambar
if uploaded_files:
    st.write(f"✅ {len(uploaded_files)} Gambar terdeteksi.")
    cols = st.columns(len(uploaded_files))
    for i, file in enumerate(uploaded_files):
        img = Image.open(file)
        cols[i].image(img, caption=f"Timeframe {i+1}", use_container_width=True)

    st.markdown("---")
    
    # Tombol Eksekusi AI
    if st.button("🚀 Jalankan Analisa ICT Pro"):
        with st.spinner("AI sedang memproses struktur market dan likuiditas..."):
            try:
                # Menggunakan model flash yang stabil dan cepat
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Menyiapkan file gambar untuk AI
                images_to_analyze = [Image.open(f) for f in uploaded_files]
                
                prompt = """
                Anda adalah seorang Master Trader ICT (Inner Circle Trader).
                Tugas Anda adalah melakukan analisa teknikal profesional berdasarkan gambar chart yang diberikan.
                
                Instruksi Khusus:
                1. Lihat gambar pertama sebagai Timeframe Daily: Tentukan arah Bias Utama.
                2. Lihat gambar kedua sebagai Timeframe H1: Cari Market Structure Shift (MSS) atau Fair Value Gap (FVG).
                3. Lihat gambar ketiga sebagai Timeframe M5/M1: Tentukan titik Precision Entry.
                
                Berikan Output dalam format berikut:
                ## 📈 HASIL ANALISA ICT
                - **DAILY BIAS**: (Jelaskan Bullish/Bearish & Alasannya)
                - **KEY LEVELS**: (Sebutkan FVG, Order Block, atau Liquidity yang terdeteksi)
                - **STRATEGI**: (BUY / SELL / WAIT)
                
                ## 🎯 RENCANA EKSEKUSI
                - **ENTRY**: (Harga spesifik)
                - **STOP LOSS**: (Harga spesifik)
                - **TAKE PROFIT**: (Harga spesifik)
                
                Berikan narasi yang tegas dan profesional dalam Bahasa Indonesia.
                """
                
                # Proses pengiriman ke Gemini AI
                response = model.generate_content([prompt] + images_to_analyze)
                
                st.success("Analisa Berhasil!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Terjadi kesalahan teknis: {e}")
                st.info("Pastikan Anda sudah mengunggah gambar dan koneksi internet stabil.")
else:
    st.warning("Silakan upload screenshot chart Anda untuk memulai analisa.")

# Footer
st.markdown("---")
st.caption("Disclaimer: Analisa AI hanyalah referensi. Risiko trading sepenuhnya di tangan pengguna.")
