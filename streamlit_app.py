import streamlit as st
import google.generativeai as genai
import requests
from PIL import Image

# Setup Tampilan Website
st.set_page_config(page_title="ICT AI Trading Terminal", layout="wide")

# API Keys (Otomatis terhubung)
GEMINI_KEY = "AIzaSyDub-Lo3VFCFw90TF6M5wjtlFNKPT8uvs4"
POLYGON_KEY = "S9RS3papq8YVKMcxCauQSUZH_erlOmVn"

st.title("🎯 ICT Smart Money AI Dashboard")
st.write("Analisa Market Structure & Liquidity Otomatis")
st.markdown("---")

# Sidebar: Monitoring Harga Live
st.sidebar.header("📈 Market Live")
pair = st.sidebar.selectbox("Pilih Asset", ["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"])

def get_price(ticker):
    url = f"https://api.polygon.io/v2/last/nbbo/C:{ticker}?apiKey={POLYGON_KEY}"
    try:
        res = requests.get(url).json()
        return res['results']['p']
    except: return "N/A"

st.sidebar.metric(label=f"Harga Sekarang ({pair})", value=f"${get_price(pair)}")

# Tampilan Utama
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 Upload Foto Chart")
    st.info("Kirim screenshot chart Anda untuk dianalisa AI.")
    uploaded_file = st.file_uploader("Pilih gambar...", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Chart terdeteksi", use_container_width=True)

with col2:
    st.subheader("🤖 Analisa Profesional AI")
    if uploaded_file:
        if st.button("🚀 Jalankan Analisa ICT"):
            with st.spinner("AI sedang membaca struktur market..."):
                try:
                    genai.configure(api_key=GEMINI_KEY)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    prompt = "Berperanlah sebagai master trader ICT. Analisa gambar ini. Cari MSS/BOS, FVG, dan Liquidity. Berikan instruksi BUY/SELL yang tegas dengan target SL dan TP."
                    response = model.generate_content([prompt, img])
                    st.success("Analisa Selesai!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.write("Silakan upload foto chart untuk memulai.")
