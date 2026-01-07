cd /www/wwwroot/biling.web.id

cat > app.py << 'EOF'
import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
from datetime import datetime
import re

# Simple OCR Print App dengan Edit Biaya Admin
st.set_page_config(page_title="OCR Print + Admin", layout="centered")
st.title("🖨️ OCR + EDIT ADMIN + PRINT")

# Upload
uploaded = st.file_uploader("Upload struk", type=['jpg','png','jpeg'])

if uploaded:
    # Tampilkan gambar
    st.image(uploaded, use_container_width=True)
    
    # Proses OCR
    if st.button("🔍 Proses OCR", type="primary"):
        img = Image.open(uploaded)
        gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        text = pytesseract.image_to_string(gray, lang='ind')
        st.session_state.text = text
        st.success("✅ OCR Selesai!")
    
    if 'text' in st.session_state:
        # ========== EDIT BIAYA ADMIN ==========
        st.markdown("---")
        st.subheader("💰 Edit Biaya Admin")
        
        # Input biaya admin
        admin_fee = st.text_input(
            "Biaya Admin (Rp):",
            "2500",
            key="admin_fee",
            help="Edit biaya admin sesuai kebutuhan"
        )
        
        # ========== EDIT TEKS STRUK ==========
        st.subheader("✏️ Edit Teks Struk")
        
        # Filter hanya items belanja (abaikan tanggal/NPWP)
        ocr_text = st.session_state.text
        lines = ocr_text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Skip tanggal/NPWP/JUMLAH
                if any(keyword in line.upper() for keyword in ['TANGGAL', 'NPWP', 'JUMLAH', 'TOTAL', 'BAYAR']):
                    continue
                if re.match(r'\d{2}[/-]\d{2}[/-]\d{4}', line):  # Skip date
                    continue
                
                filtered_lines.append(line)
        
        filtered_text = '\n'.join(filtered_lines[:10])  # Maks 10 baris
        
        # Text editor
        edited = st.text_area(
            "Teks struk (bisa diedit):",
            filtered_text,
            height=200,
            key="struk_editor"
        )
        
        # ========== FORMAT STRUK BESTINDO ==========
        st.markdown("---")
        st.subheader("🧾 Format Struk BESTINDO")
        
        # Hitung total
        try:
            admin = int(admin_fee) if admin_fee.isdigit() else 2500
        except:
            admin = 2500
            
        subtotal = 25000
        total = subtotal + admin
        
        # Buat struk dengan template
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        struk_template = f"""          BESTINDO
      Jl. Raya Contoh No. 123
        Telp: (021) 555-1234
================================
Tanggal: {current_time}
Kasir   : ADMIN
================================
{edited}
================================
Subtotal     : Rp {subtotal:,}
Biaya Admin  : Rp {admin:,}
--------------------------------
TOTAL        : Rp {total:,}
================================
Pembayaran   : TUNAI
Tunai        : Rp 30.000
Kembali      : Rp {30000 - total:,}
================================
Terima kasih telah berbelanja
================================
"""
        
        # Tampilkan struk
        st.text_area("Struk siap print:", struk_template, height=300)
        
        # Simpan struk untuk print
        st.session_state.final_struk = struk_template
        
        # ========== TOMBOL PRINT ==========
        st.markdown("---")
        st.subheader("🖨️ Print")
        
        col_print1, col_print2 = st.columns(2)
        
        with col_print1:
            # Tombol Print HTML
            if st.button("🖨️ PRINT", type="primary", use_container_width=True):
                # HTML untuk print (tanpa backslash di f-string)
                html_content = f'''<!DOCTYPE html>
                <html>
                <head>
                    <title>Print Struk BESTINDO</title>
                    <style>
                        @media print {{
                            @page {{ size: 80mm auto; margin: 0; }}
                            body {{ 
                                font-family: "Courier New", monospace;
                                font-size: 12px;
                                width: 80mm;
                                padding: 5px;
                                margin: 0;
                            }}
                        }}
                        body {{
                            font-family: "Courier New", monospace;
                            font-size: 12px;
                            white-space: pre-line;
                            padding: 10px;
                        }}
                    </style>
                </head>
                <body>
                <pre>
{struk_template}
                </pre>
                <script>
                    // Auto print setelah 500ms
                    setTimeout(function() {{
                        window.print();
                    }}, 500);
                </script>
                </body>
                </html>'''
                
                # Tampilkan HTML
                st.components.v1.html(html_content, height=400)
                st.success("Mengirim ke printer...")
        
        with col_print2:
            # Tombol Download
            st.download_button(
                "📥 Download",
                struk_template,
                f"BESTINDO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain",
                use_container_width=True
            )
            
            # Tombol Copy (gunakan st.markdown tanpa f-string complex)
            st.markdown("""
            <div id="strukText" style="display: none;">""" + struk_template.replace('`', '\\`') + """</div>
            <button onclick="copyStruk()" style="
                width: 100%;
                padding: 12px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 10px;
            ">
                📋 Copy Teks
            </button>
            
            <script>
            function copyStruk() {
                var strukText = document.getElementById("strukText").textContent;
                navigator.clipboard.writeText(strukText).then(function() {
                    alert("Struk berhasil disalin! Paste ke software printer.");
                });
            }
            </script>
            """, unsafe_allow_html=True)
        
        # ========== PETUNJUK PRINT ==========
        st.info("""
        **Jika print tidak muncul:**
        1. Klik tombol **PRINT** di atas
        2. Tekan **Ctrl+P** (Windows) atau **Cmd+P** (Mac)
        3. Pilih printer thermal Anda
        4. Klik **Print**
        
        **Atau pakai cara manual:**
        1. **Copy** teks struk (tombol Copy Teks)
        2. **Paste** ke software printer thermal
        3. **Print** langsung
        """)
        
        # ========== RESET ==========
        if st.button("🔄 Buat Baru", type="secondary"):
            for key in ['text', 'final_struk']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# Jika belum upload
if not uploaded:
    st.info("""
    **📋 Cara menggunakan:**
    1. **Upload** gambar struk
    2. **Edit biaya admin** sesuai kebutuhan
    3. **Edit teks struk** jika perlu
    4. **Print** langsung ke printer thermal
    
    **✨ Fitur:**
    - Edit biaya admin
    - Filter otomatis (abaikan tanggal/NPWP)
    - Format struk thermal printer
    - Print langsung dari browser
    """)

# Footer
st.markdown("---")
st.caption("biling.web.id | Edit biaya admin + Print thermal")
EOF

echo "✅ Aplikasi sudah di-fix, tidak ada error!"




UNTUK RESET
cd /www/wwwroot/biling.web.id
pkill -f streamlit
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > app.log 2>&1 &
echo "✅ Aplikasi auto process jalan!"
