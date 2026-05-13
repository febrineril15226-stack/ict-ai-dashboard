import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Setup Konfigurasi Halaman
st.set_page_config(page_title="ICT Master Audit - Gemini Pro", layout="wide", page_icon="⚖️")

# 2. Setup API Key (Google AI Studio)
# Pastikan API Key ini benar
genai.configure(api_key="AIzaSyAXHdTyql-rk4VnBAyFGlXjOCgZHPs8lk8")

st.title("⚖️ ICT Master Audit - Gemini Pro")
st.markdown("---")

# 3. Upload Gambar Multi-Timeframe
st.subheader("📸 Analisa Struktur Market (D1, H1, M5)")
uploaded_files = st.file_uploader("Unggah Chart Anda (Disarankan urutan D1, H1, M5)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    # Tampilkan preview gambar yang diunggah
    cols = st.columns(len(uploaded_files))
    for i, file in enumerate(uploaded_files):
        cols[i].image(Image.open(file), use_container_width=True, caption=f"Timeframe {i+1}")

    if st.button("🚀 Jalankan Analisa Pro"):
        if len(uploaded_files) < 1:
            st.error("Silakan unggah minimal satu gambar chart.")
        else:
            with st.spinner("Gemini Pro sedang membedah struktur market dan likuiditas..."):
                try:
                    # Menggunakan model Pro untuk akurasi logika tertinggi
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    
                    # Konversi file ke format gambar
                    imgs = [Image.open(f) for f in uploaded_files]
                    
                    # PROMPT PROFESIONAL: Fokus pada Konsep ICT
                    prompt = """
                    Anda adalah Master Trader ICT Senior dengan pengalaman 20 tahun. 
                    Analisa gambar-gambar chart ini secara mendalam dengan protokol berikut:

                    1. DRAW ON LIQUIDITY: Tentukan target besar harga berdasarkan candle di TF tinggi.
                    2. LIQUIDITY SWEEP: Identifikasi apakah ada pengambilan Buy-Side atau Sell-Side Liquidity.
                    3. MARKET STRUCTURE: Cari valid Market Structure Shift (MSS) atau Break of Structure (BOS).
                    4. ENTRY ZONE: Tentukan area Fair Value Gap (FVG) atau Order Block (OB) yang belum dimitigasi.
                    5. DISPLACEMENT: Pastikan ada dorongan harga yang kuat setelah MSS.

                    Berikan jawaban dengan format:
                    - **NARASI PASAR (BIAS):**
                    - **ANALISA STRUKTUR & LIKUIDITAS:**
                    - **REKOMENDASI TRADE (Entry, SL, TP):**
                    - **TINGKAT KEPERCAYAAN (%):**

                    Gunakan Bahasa Indonesia yang tegas, profesional, dan objektif.
                    """
                    
                    response = model.generate_content([prompt] + imgs)
                    
                    st.success("Analisa Selesai!")
                    st.markdown("### 📊 Hasil Audit Master ICT")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Terjadi Kesalahan: {e}")
                    st.info("Tips: Jika muncul error 404, silakan lakukan REBOOT aplikasi di dashboard Streamlit Cloud Anda.")

# Footer
st.divider()
st.caption("Peringatan: Trading melibatkan risiko tinggi. Analisa AI hanya sebagai alat bantu konfirmasi.")
