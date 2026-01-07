import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
from datetime import datetime
import re

# ================= KONFIGURASI TESSERACT =================
# Pastikan path ini sesuai dengan instalasi di server/hosting Anda
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

st.set_page_config(
    page_title="BESTINDO PRINT - Auto OCR",
    page_icon="⚡",
    layout="centered"
)

# ================= SIDEBAR SETTINGS (MENU SETTING) =================
st.sidebar.header("⚙️ PENGATURAN STRUK")
nama_toko = st.sidebar.text_input("Nama Toko", "BESTINDO")
alamat_toko = st.sidebar.text_area("Alamat", "Jl. Raya Contoh No. 123")
telp_toko = st.sidebar.text_input("Nomor Telepon", "(021) 555-1234")

st.sidebar.markdown("---")
st.sidebar.info("""
**💡 Tips Ukuran Printer:**
Format ini dioptimalkan untuk kertas **58mm**. 
Jika teks terpotong setelah font diperbesar, silakan kurangi jumlah karakter per baris di menu setting.
""")

# ================= FUNGSI PROSES =================

def process_ocr(image):
    try:
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        text = pytesseract.image_to_string(enhanced, lang='ind')
        return text
    except Exception as e:
        return f"Error: {str(e)}"

def filter_items(ocr_text):
    lines = ocr_text.strip().split('\n')
    filtered = []
    exclude_keywords = ['TANGGAL', 'NPWP', 'JUMLAH', 'TOTAL', 'BAYAR', 'KEMBALI', 'PPN', 'STRUK', 'KASIR']
    
    for line in lines:
        if not line: continue
        if any(keyword in line.upper() for keyword in exclude_keywords): continue
        if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line): continue
        if re.match(r'\d{1,2}[:]\d{2}([:]\d{2})?', line): continue
        if any(char.isdigit() for char in line):
            if len(line) > 40: line = line[:40]
            filtered.append(line)
    return '\n'.join(filtered[:8])

def create_struk(items_text, admin_fee, toko, alamat, telp):
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    try:
        admin = int(re.sub(r'\D', '', admin_fee)) if admin_fee else 2500
    except:
        admin = 2500
    
    subtotal = 25000 
    total = subtotal + admin
    change = 30000 - total
    
    # Header dinamis rata tengah (center)
    struk = f"""{toko.center(30)}
{alamat.center(30)}
{"Telp: " + telp.center(24)}
==============================
Tanggal: {current_time}
Kasir   : ADMIN
==============================
"""
    if items_text:
        struk += items_text + "\n"
    else:
        struk += "ITEM CONTOH       1    10.000\nITEM LAIN         2    15.000\n"
        
    struk += f"""==============================
Subtotal     : Rp {subtotal:,}
Biaya Admin  : Rp {admin:,}
------------------------------
TOTAL        : Rp {total:,}
==============================
Pembayaran   : TUNAI
Tunai        : Rp 30.000
Kembali      : Rp {change:,}
==============================
Terima kasih telah berbelanja
==============================
"""
    return struk

# ================= TAMPILAN DASHBOARD =================

st.title(f"⚡ {nama_toko} PRINT")
st.markdown("**Upload → Auto OCR → Preview → Print (Teks Besar)**")

if 'auto_process' not in st.session_state:
    st.session_state.auto_process = False

# 1. UPLOAD SECTION
if not st.session_state.auto_process:
    uploaded = st.file_uploader("Upload Foto Struk", type=['jpg', 'png', 'jpeg'], key="file_uploader")
    if uploaded:
        with st.spinner("🔄 Memproses OCR otomatis..."):
            image = Image.open(uploaded)
            ocr_result = process_ocr(image)
            st.session_state.items_text = filter_items(ocr_result)
            st.session_state.auto_process = True
            st.rerun()

# 2. EDIT & ACTION SECTION
if st.session_state.auto_process:
    col1, col2 = st.columns(2)
    with col1:
        admin_fee = st.text_input("💰 Biaya Admin (Rp):", "2500")
        items_display = st.text_area("Items Terdeteksi:", st.session_state.items_text, height=150)
    
    with col2:
        struk_final = create_struk(items_display, admin_fee, nama_toko, alamat_toko, telp_toko)
        st.text_area("Preview Struk:", struk_final, height=250)

    st.markdown("---")
    
    # TOMBOL AKSI
    c1, c2 = st.columns(2)
    
    with c1:
        # Tombol Print dengan Teks Besar (16px & Bold)
        if st.button("🖨️ PRINT SEKARANG", type="primary", use_container_width=True):
            safe_struk = struk_final.replace("`", "\\`").replace("\n", "\\n")
            js_print = f"""
            <iframe id="print_frame" style="display:none;"></iframe>
            <script>
                const frame = document.getElementById('print_frame');
                const content = `<pre style="font-family:monospace; font-size:16px; font-weight:bold; line-height:1.2;">{safe_struk}</pre>`;
                const doc = frame.contentWindow.document;
                doc.open();
                doc.write('<html><head><style>@media print {{ body {{ margin: 0; }} }}</style></head><body>');
                doc.write(content);
                doc.write('</body></html>');
                doc.close();
                
                setTimeout(() => {{
                    frame.contentWindow.focus();
                    frame.contentWindow.print();
                }}, 250);
            </script>
            """
            st.components.v1.html(js_print, height=0)

    with c2:
        # Tombol Copy (Script tersembunyi)
        copy_html = f"""
        <div id="copyData" style="display: none;">{struk_final}</div>
        <button onclick="copyToClipboard()" style="width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer;">📋 COPY TEKS</button>
        <script>
        function copyToClipboard() {{
            const text = document.getElementById("copyData").innerText;
            navigator.clipboard.writeText(text).then(() => alert("✅ Struk disalin ke clipboard!"));
        }}
        </script>
        """
        st.markdown(copy_html, unsafe_allow_html=True)

    if st.button("🔄 UPLOAD STRUK LAIN", use_container_width=True):
        st.session_state.auto_process = False
        st.rerun()

# Footer
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: #666;'>{nama_toko} - Auto OCR Processing</div>", unsafe_allow_html=True)
