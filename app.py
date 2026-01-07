import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
from datetime import datetime
import re

# Setup
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
st.set_page_config(
    page_title="BESTINDO - Auto OCR",
    page_icon="⚡",
    layout="centered"
)

# Header
st.title("⚡ BESTINDO - Upload Langsung Proses")
st.markdown("**Upload → Auto OCR → Edit Admin → Print**")

# Inisialisasi session state
if 'auto_process' not in st.session_state:
    st.session_state.auto_process = False

# Fungsi proses OCR
def process_ocr(image):
    """Proses OCR pada gambar"""
    try:
        # Convert ke grayscale
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        
        # Enhance contrast untuk hasil lebih baik
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # OCR dengan bahasa Indonesia
        text = pytesseract.image_to_string(enhanced, lang='ind')
        
        return text
    except Exception as e:
        return f"Error: {str(e)}"

# Fungsi filter items
def filter_items(ocr_text):
    """Filter hanya items belanja"""
    lines = ocr_text.strip().split('\n')
    filtered = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip jika mengandung keyword yang tidak diinginkan
        exclude_keywords = ['TANGGAL', 'NPWP', 'JUMLAH', 'TOTAL', 'BAYAR', 'KEMBALI', 'PPN']
        if any(keyword in line.upper() for keyword in exclude_keywords):
            continue
        
        # Skip jika format tanggal
        if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line):
            continue
        
        # Skip jika hanya waktu
        if re.match(r'\d{1,2}[:]\d{2}([:]\d{2})?', line):
            continue
        
        # Ambil jika mengandung angka (kemungkinan item)
        if any(char.isdigit() for char in line):
            # Potong jika terlalu panjang
            if len(line) > 40:
                line = line[:40]
            filtered.append(line)
    
    return '\n'.join(filtered[:8])  # Maks 8 items

# Fungsi buat struk
def create_struk(items_text, admin_fee="2500"):
    """Buat struk BESTINDO"""
    
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Hitung total
    try:
        admin = int(admin_fee) if admin_fee.isdigit() else 2500
    except:
        admin = 2500
    
    subtotal = 25000
    total = subtotal + admin
    change = 30000 - total
    
    # Format struk
    struk = f"""          BESTINDO
      Jl. Raya Contoh No. 123
        Telp: (021) 555-1234
================================
Tanggal: {current_time}
Kasir   : ADMIN
================================
"""
    
    # Tambahkan items
    if items_text:
        for line in items_text.split('\n'):
            if line.strip():
                struk += f"{line.strip()}\n"
    else:
        struk += "ITEM CONTOH       1   10.000\n"
        struk += "ITEM LAIN         2   15.000\n"
    
    struk += f"""================================
Subtotal     : Rp {subtotal:,}
Biaya Admin  : Rp {admin:,}
--------------------------------
TOTAL        : Rp {total:,}
================================
Pembayaran   : TUNAI
Tunai        : Rp 30.000
Kembali      : Rp {change:,}
================================
Terima kasih telah berbelanja
================================
"""
    
    return struk

# ========== UPLOAD & AUTO PROCESS ==========
st.header("1. Upload Struk (Auto Proses)")

uploaded = st.file_uploader(
    "Pilih gambar struk - akan diproses otomatis",
    type=['jpg', 'png', 'jpeg'],
    key="file_uploader"
)

# Auto proses ketika file diupload
if uploaded and not st.session_state.auto_process:
    with st.spinner("🔄 Memproses OCR otomatis..."):
        # Tampilkan gambar
        st.image(uploaded, use_container_width=True)
        
        # Proses OCR
        image = Image.open(uploaded)
        ocr_result = process_ocr(image)
        
        # Filter items
        items_text = filter_items(ocr_result)
        
        # Simpan ke session
        st.session_state.uploaded_file = uploaded
        st.session_state.ocr_result = ocr_result
        st.session_state.items_text = items_text
        st.session_state.auto_process = True
    
    st.success("✅ OCR selesai secara otomatis!")
    
    # Tampilkan hasil OCR singkat
    with st.expander("📄 Lihat hasil OCR"):
        st.text_area("OCR Result:", ocr_result, height=150)

# ========== EDIT BIAYA ADMIN ==========
if st.session_state.auto_process:
    st.header("2. Edit Biaya Admin")
    
    # Input biaya admin
    admin_fee = st.text_input(
        "💰 Biaya Admin (Rp):",
        "2500",
        key="admin_fee_input",
        help="Edit biaya admin sesuai kebutuhan"
    )
    
    # Tampilkan items yang ditemukan
    st.subheader("Items Terdeteksi")
    items_display = st.text_area(
        "Items dari struk:",
        st.session_state.items_text,
        height=150,
        key="items_display"
    )
    
    # ========== STRUK FINAL ==========
    st.header("3. Struk Siap Print")
    
    # Buat struk
    struk_text = create_struk(items_display, admin_fee)
    
    # Tampilkan struk
    st.text_area("Struk BESTINDO:", struk_text, height=300)
    
    # ========== PRINT OPTIONS ==========
    st.header("4. 🖨️ Print")
    
    # Tombol Print HTML
    if st.button("🖨️ PRINT SEKARANG", type="primary", use_container_width=True):
        # HTML sederhana untuk print
        html = f'''<!DOCTYPE html>
        <html>
        <head>
            <title>Print Struk BESTINDO</title>
            <style>
                @media print {{
                    body {{ 
                        font-family: "Courier New", monospace;
                        font-size: 12px;
                        margin: 0;
                        padding: 10px;
                    }}
                }}
                pre {{
                    font-family: "Courier New", monospace;
                    font-size: 12px;
                    white-space: pre-line;
                }}
            </style>
        </head>
        <body>
        <pre>{struk_text}</pre>
        <script>
            window.onload = function() {{
                setTimeout(function() {{
                    window.print();
                }}, 500);
            }};
        </script>
        </body>
        </html>'''
        
        # Tampilkan untuk print
        st.components.v1.html(html, height=400)
        st.success("✅ Print dialog akan muncul...")
    
    # Tombol Copy
    st.markdown(f"""
    <div id="copyText" style="display: none;">{struk_text}</div>
    <button onclick="copyToClipboard()" style="
        width: 100%;
        padding: 15px;
        background: #4CAF50;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        cursor: pointer;
        margin: 10px 0;
    ">
        📋 COPY TEKS UNTUK PRINT MANUAL
    </button>
    
    <script>
    function copyToClipboard() {{
        var text = document.getElementById("copyText").textContent;
        navigator.clipboard.writeText(text).then(function() {{
            alert("Struk berhasil disalin ke clipboard!");
        }});
    }}
    </script>
    """, unsafe_allow_html=True)
    
    # Tombol Reset
    if st.button("🔄 UPLOAD STRUK BARU", type="secondary", use_container_width=True):
        for key in ['uploaded_file', 'ocr_result', 'items_text', 'auto_process']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Jika belum upload
if not st.session_state.auto_process:
    st.info("""
    **⚡ Fitur Auto Process:**
    1. **Upload** gambar struk
    2. **Otomatis proses OCR** (tidak perlu klik tombol)
    3. **Edit biaya admin** sesuai kebutuhan
    4. **Print** langsung
    
    **Items akan otomatis difilter:**
    ✅ Diambil: Items belanja dengan harga
    ❌ Dihapus: Tanggal, NPWP, Total, PPN
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <strong>BESTINDO - Auto OCR Processing</strong><br>
    Upload langsung proses, tanpa klik tombol
</div>
""", unsafe_allow_html=True)
