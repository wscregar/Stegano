import streamlit as st
import os
from PIL import Image
import watermark_tools as wt
import tempfile
import sys
from io import StringIO
from contextlib import redirect_stdout

# --- KONFIGURASI HALAMAN (WAJIB PALING ATAS) ---
st.set_page_config(
    page_title="Invisible Copyright Guard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #5D5D6E; color: #ffffff; }
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, li, span, label,
    [data-testid="stMarkdownContainer"] * {
        color: #ffffff !important;
    }


    .stTextInput input, .stTextArea textarea {
        color: #000000 !important;
        background-color: #f0f2f6 !important;
    }

    /* Tombol: gunakan selector stabil + paksa warna */
    .stButton>button, button[kind="primary"], button[kind="secondary"] {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background: #4CAF50 !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: none !important;
    }
    .stButton>button:hover, button[kind="primary"]:hover, button[kind="secondary"]:hover {
        background: #45a049 !important;
    }
    
    /* Style untuk area log/code */
    code {
        color: #d63384 !important;
        background-color: #f0f0f0 !important;
    }
    
    /* Peringatan error/sukses */
    .stAlert { color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI BANTUAN ---
def save_uploaded_file(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("Digital Guardian")
    st.markdown("---")
    menu = st.radio(
        "Pilih Operasi:",
        ("🛡️ Proteksi (Watermark)", "🔍 Verifikasi", "📊 Analisis Integritas")
    )
    st.markdown("---")
    st.info("Versi Kompatibel (Streamlit 1.29.0)")

# --- HALAMAN: PROTEKSI ---
if menu == "🛡️ Proteksi (Watermark)":
    st.title("🛡️ Proteksi Hak Cipta Gambar")
    st.markdown("Sisipkan tanda tangan digital tak terlihat ke dalam karya Anda.")

    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader("Upload Gambar Asli", type=['png', 'bmp', 'jpg', 'jpeg'])
        
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        with col1:
            st.image(image, caption="Gambar Asli", use_container_width=True)
            
        temp_input_path = save_uploaded_file(uploaded_file)
        
        try:
            capacity = wt.get_max_capacity(temp_input_path)
            st.success(f"✅ Kapasitas gambar: {capacity} karakter")
        except AttributeError:
            st.error("ERROR: File watermark_tools.py belum tersimpan atau cache error.")

        with col2:
            st.subheader("Konfigurasi Watermark")
            watermark_text = st.text_input("Masukkan Teks Hak Cipta", placeholder="Copyright 2025 by Creator")
            
            if st.button("Proses Watermark"):
                if not watermark_text:
                    st.warning("Mohon isi teks watermark terlebih dahulu.")
                else:
                    with st.spinner('Sedang memproses...'):
                        output_path = temp_input_path.replace(".png", "_protected.png")
                        
                        try:
                            original_hash = wt.embed_watermark(temp_input_path, output_path, watermark_text)
                            
                            if original_hash:
                                st.success("Watermark berhasil disisipkan!")
                                st.code(f"SHA-512 Hash: {original_hash}", language="text")
                                
                                protected_image = Image.open(output_path)
                                st.image(protected_image, caption="Gambar Terproteksi", use_container_width=True)
                                
                                with open(output_path, "rb") as file:
                                    st.download_button(
                                        label="💾 Download Gambar Terproteksi",
                                        data=file,
                                        file_name="protected_image.png",
                                        mime="image/png"
                                    )
                            else:
                                st.error("Gagal menyisipkan watermark.")
                        except AttributeError:
                             st.error("Fungsi 'embed_watermark' tidak ditemukan di watermark_tools.py")

# --- HALAMAN: VERIFIKASI ---
elif menu == "🔍 Verifikasi":
    st.title("🔍 Verifikasi Kepemilikan")
    
    uploaded_file = st.file_uploader("Upload Gambar untuk Diverifikasi", type=['png', 'bmp'])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Gambar yang diupload", width=400)
        temp_path = save_uploaded_file(uploaded_file)
        
        check_text = st.text_input("Masukkan Teks untuk Dicocokkan")
        
        if st.button("Verifikasi Watermark"):
            if not check_text:
                st.warning("Masukkan teks untuk verifikasi.")
            else:
                with st.spinner('Menganalisis...'):
                    try:
                        f = StringIO()
                        with redirect_stdout(f):
                            result = wt.verify_watermark_comprehensive(temp_path, check_text)
                        
                        output_log = f.getvalue()
                        
                        if result == True:
                            st.balloons()
                            st.success("✅ VERIFIKASI SUKSES 100%!")
                        elif result == "partial":
                            st.warning("⚠️ VERIFIKASI SEBAGIAN.")
                        else:
                            st.error("❌ VERIFIKASI GAGAL.")
                        
                        st.text_area("Detail Log Verifikasi:", output_log, height=200)
                        
                    except AttributeError:
                        st.error("Fungsi 'verify_watermark_comprehensive' tidak ditemukan. Pastikan Anda sudah menyimpan file watermark_tools.py")

# --- HALAMAN: ANALISIS ---
elif menu == "📊 Analisis Integritas":
    st.title("📊 Analisis Forensik Gambar")
    
    uploaded_file = st.file_uploader("Upload Gambar", type=['png', 'bmp'])
    
    if uploaded_file is not None:
        temp_path = save_uploaded_file(uploaded_file)
        
        if st.button("Jalankan Analisis Forensik"):
            with st.spinner('Memindai konsistensi pola hash...'):
                try:
                    f = StringIO()
                    with redirect_stdout(f):
                        wt.analyze_watermark_integrity(temp_path)
                    
                    output = f.getvalue()
                    
                    if "✓ SEMUA blok hash identik" in output:
                        st.success("Integritas Sempurna")
                    elif "✗ Ditemukan inkonsistensi" in output:
                        st.error("Modifikasi Terdeteksi / Data Rusak")
                    
                    st.text_area("Log Analisis Detail", output, height=300)
                except AttributeError:
                    st.error("Fungsi 'analyze_watermark_integrity' tidak ditemukan.")
