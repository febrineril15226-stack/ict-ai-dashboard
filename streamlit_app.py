import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Konfigurasi API - Jalur REST lebih stabil untuk Streamlit Cloud
genai.configure(api_key="AIzaSyAXHdTyql-rk4VnBAyFGlXjOCgZHPs8lk8", transport='rest')

st.set_page_config(page_title="ICT Institutional Audit Pro", layout="wide", page_icon="⚖️")

st.title("⚖️ ICT Institutional Audit Pro")
st.caption("Khusus Pair Forex (Major/Minor) - Analisa Algoritma Interbank")
st.markdown("---")

# 2. Upload Gambar Multi-Timeframe
st.subheader("📸 Multi-Timeframe Analysis (HTF to LTF)")
uploaded_files = st.file_uploader("Unggah Chart (Urutan: Daily -> H1 -> M5/M1)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    cols = st.columns(len(uploaded_files))
    for i, file in enumerate(uploaded_files):
        cols[i].image(Image.open(file), use_container_width=True, caption=f"TF Level {i+1}")

    if st.button("🚀 Jalankan Analisa Institusional"):
        if len(uploaded_files) < 1:
            st.warning("Mohon unggah setidaknya satu chart.")
        else:
            with st.spinner("Membaca jejak Big Boys (Smart Money)..."):
                try:
                    # Menggunakan model Pro-002 untuk penalaran visual terbaik
                    model = genai.GenerativeModel(model_name='models/gemini-1.5-pro')
                    
                    imgs = [Image.open(f) for f in uploaded_files]
                    
                    # PROMPT ICT TINGKAT LANJUT
                    prompt = """
                    Anda adalah Senior Technical Analyst di Hedge Fund yang ahli dalam ICT (Inner Circle Trader).
                    Analisa chart pair forex ini dengan sangat detail.

                    TUGAS ANALISA:
                    1. BIAS & HTF CONTEXT: Tentukan Draw on Liquidity (DOL) pada Timeframe Daily/H4. Apakah harga mengejar BSL atau SSL?
                    2. MARKET STRUCTURE: Identifikasi Market Structure Shift (MSS) yang disertai DISPLACEMENT kuat.
                    3. LIKUIDITAS: Cari tanda-tanda Inducement, SMT Divergence (jika ada), dan Liquidity Sweep sebelum entry.
                    4. ENTRY POINT: Cari area Optimal Trade Entry (OTE) atau Fair Value Gap (FVG) yang berhimpitan dengan Order Block/Breaker Block.
                    5. POWER OF 3 (AMD): Apakah Anda melihat pola Accumulation, Manipulation, dan Distribution?

                    FORMAT OUTPUT:
                    ---
                    ### 🏛️ INSTITUTIONAL BIAS
                    * **Arah Utama:** [Bullish/Bearish]
                    * **Target Harga (DOL):** [Sebutkan level harga jika terlihat]
                    
                    ### 🔍 STRUKTUR & LIKUIDITAS
                    * **Audit Struktur:** [Misal: MSS terkonfirmasi dengan candle besar]
                    * **Liquidity Taken:** [Misal: Previous Daily High diambil]

                    ### 🎯 TRADE EXECUTION PLAN
                    * **Entry Zone:** [Detail area FVG/OB]
                    * **Stop Loss:** [Letakkan di area aman sesuai rule ICT]
                    * **Take Profit:** [Level likuiditas terdekat]
                    * **Risk/Reward:** [Minimal 1:2]

                    ### ⚠️ CATATAN VALIDASI
                    * Sebutkan jika ada ancaman berita High Impact atau ketidakpastian struktur.
                    ---
                    Gunakan Bahasa Indonesia yang teknis dan tajam.
                    """
                    
                    response = model.generate_content([prompt] + imgs)
                    st.success("Audit Institusional Selesai!")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Koneksi API Terganggu: {e}")
                    st.info("Saran: Jika error 404 muncul, silakan tekan REBOOT di dashboard Streamlit.")

# 3. Footer Manajemen Risiko
st.divider()
st.info("Pesan Master: 'Trade what you see, not what you think.' Selalu gunakan manajemen lot yang tepat pada pair forex.")
