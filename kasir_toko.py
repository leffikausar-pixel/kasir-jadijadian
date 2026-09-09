import streamlit as st
import qrcode
import io
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Mengatur tampilan halaman web agar lebih luas dan modern
st.set_page_config(page_title="Kasir Toko Berkah", layout="wide")
st.title("🏪 Kasir Toko Berkah")

# Inisialisasi Koneksi Aman Google Sheets menggunakan berkas Secrets Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. DAFTAR BARANG DAN HARGA
menu_barang = {
    1: {"nama": "Beras 5kg", "harga": 65000, "foto": "https://unsplash.com"},
    2: {"nama": "Minyak Goreng 1L", "harga": 19000, "foto": "https://unsplash.com"},
    3: {"nama": "Gula Pasir 1kg", "harga": 16000, "foto": "https://unsplash.com"},
    4: {"nama": "Telur 1kg", "harga": 26000, "foto": "https://unsplash.com"},
    5: {"nama": "Mie Instan", "harga": 3000, "foto": "https://unsplash.com"}
}

# 2. INISIALISASI VARIABEL KERANJANG
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

# Membagi halaman web menjadi 2 kolom utama
kolom_kiri, kolom_kanan = st.columns(2)

# --- KOLOM SEBELAH KIRI: MENU & INPUT BARANG ---
with kolom_kiri:
    st.subheader("🛒 Pilih & Masukkan Barang")
    
    pilihan_opsi = {f"{info['nama']} - Rp {info['harga']:,}": kode for kode, info in menu_barang.items()}
    pilihan_user = st.selectbox("Silakan pilih barang:", list(pilihan_opsi.keys()))
    kode_terpilih = pilihan_opsi[pilihan_user]
    
    if "foto" in menu_barang[kode_terpilih]:
        st.image(menu_barang[kode_terpilih]["foto"], width=180)
    
    jumlah = st.number_input(f"Masukkan jumlah beli untuk {menu_barang[kode_terpilih]['nama']}:", min_value=1, step=1, value=1)
    
    if st.button("➕ Tambah ke Keranjang", type="primary"):
        st.session_state.keranjang.append({
            "nama": menu_barang[kode_terpilih]["nama"],
            "harga": menu_barang[kode_terpilih]["harga"],
            "jumlah": jumlah,
            "subtotal": menu_barang[kode_terpilih]["harga"] * jumlah
        })
        st.success(f"Berhasil menambahkan {jumlah} {menu_barang[kode_terpilih]['nama']} ke keranjang.")
    
    st.markdown("---")
    st.subheader("🎟️ Voucher & Diskon")
    kode_voucher = st.text_input("Masukkan Kode Voucher (Opsional):", placeholder="Contoh: DISKON10")
    
    diskon_persen = 0
    if kode_voucher.upper() == "DISKON10":
        diskon_persen = 10
        st.success("🎉 Potongan 10% Aktif!")
    elif kode_voucher.upper() == "HEMAT5":
        diskon_persen = 5
        st.success("🎉 Potongan 5% Aktif!")

    if st.button("🗑️ Kosongkan Keranjang", type="secondary"):
        st.session_state.keranjang = []
        st.rerun()

# --- KOLOM SEBELAH KANAN: STRUK BELANJA & PEMBAYARAN ---
with kolom_kanan:
    st.subheader("🧾 Struk Belanja & Pembayaran")
    
    if not st.session_state.keranjang:
        st.info("Belum ada transaksi. Keranjang belanja kosong.")
    else:
        total_belanja = 0
        teks_struk = "========== STRUK BELANJA ==========\n"
        for i, item in enumerate(st.session_state.keranjang):
            st.write(f"{i+1}. **{item['nama']}** (x{item['jumlah']}) = Rp {item['subtotal']:,}")
            teks_struk += f"{item['nama']} x{item['jumlah']} = Rp {item['subtotal']:,}\n"
            total_belanja += item["subtotal"]
            
        potongan = int(total_belanja * (diskon_persen / 100))
        total_akhir = total_belanja - potongan
        
        st.markdown("---")
        st.write(f"Subtotal Belanja: Rp {total_belanja:,}")
        st.write(f"Potongan Diskon: Rp {potongan:,}")
        st.markdown(f"## **Total Harus Dibayar: Rp {total_akhir:,}**")
        
        st.markdown("---")
        st.subheader("💳 Metode Pembayaran")
        metode = st.radio("Pilih Metode:", ["Tunai (Cash)", "QRIS / E-Wallet"])
        
        if metode == "Tunai (Cash)":
            uang_bayar = st.number_input("Masukkan uang pembayaran (Rp):", min_value=0, step=1000, value=0)
            if uang_bayar > 0:
                if uang_bayar < total_akhir:
                    st.error(f"Uang kurang Rp {total_akhir - uang_bayar:,}.")
                else:
                    kembalian = uang_bayar - total_akhir
                    st.balloons()
                    st.success(f"### 💵 Kembalian: Rp {kembalian:,}")
                    
                    if st.button("💾 Konfirmasi Transaksi Lunas"):
                        # Membaca data yang sudah ada di cloud sheet
                        try:
                            df_lama = conn.read(ttl="0d") # Memaksa membaca data paling update
                        except:
                            df_lama = pd.DataFrame(columns=["Metode", "Total Belanja", "Status"])
                        
                        # Gabungkan baris data baru
                        data_baru = pd.DataFrame([{"Metode": "Tunai", "Total Belanja": int(total_akhir), "Status": "Lunas"}])
                        df_update = pd.concat([df_lama, data_baru], ignore_index=True)
                        
                        # Mengirim data update ke Google Sheets secara aman
                        conn.update(data=df_update)
                        st.toast("🛒 Transaksi tunai lunas otomatis masuk ke Google Sheets!")
                        st.session_state.keranjang = []
                        st.rerun()
        
        elif metode == "QRIS / E-Wallet":
            st.info("Silakan scan kode QRIS di bawah ini untuk melakukan pembayaran:")
            qris_part1 = "00020101021126570011ID.DANA.WWW011893600915387331088002098733108800303UMI51440014ID.CO.QRIS.WWW0215ID10253904693320303UMI520454995303360"
            qris_part2 = "5802ID5917Toko Belanja Vall6015Kota Jakarta Ti610513410" 
            
            def generate_qris_dinamis(part1, part2, nominal):
                sub_nominal = f"54{len(str(nominal)):02d}{nominal}"
                qris_tanpa_crc = part1 + sub_nominal + part2 + "6304"
                crc = 0xFFFF
                for char in qris_tanpa_crc:
                    crc ^= ord(char) << 8
                    for _ in range(8):
                        if crc & 0x8000: crc = (crc << 1) ^ 0x1021
                        else: crc <<= 1
                        crc &= 0xFFFF
                return qris_tanpa_crc + format(crc, '04X')

            qris_final = generate_qris_dinamis(qris_part1, qris_part2, total_akhir)
            img = qrcode.make(qris_final)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            
            st.image(buf.getvalue(), caption=f"QRIS Otomatis: Rp {total_akhir:,}", width=250)
            
            if st.button("✅ Konfirmasi Pembayaran QRIS Sukses"):
                st.balloons()
                
                try:
                    df_lama = conn.read(ttl="0d")
                except:
                    df_lama = pd.DataFrame(columns=["Metode", "Total Belanja", "Status"])
                
                data_baru = pd.DataFrame([{"Metode": "QRIS", "Total Belanja": int(total_akhir), "Status": "Lunas"}])
                df_update = pd.concat([df_lama, data_baru], ignore_index=True)
                
                conn.update(data=df_update)
                st.success("🚀 Pembayaran QRIS sukses & otomatis tersimpan ke Google Sheets!")
                st.session_state.keranjang = []
                st.rerun()

# --- BAGIAN PALING BAWAH: DATA REAL-TIME DARI GOOGLE SHEETS ---
st.markdown("---")
st.header("📊 Daftar Transaksi Terkunci di Google Sheets")

try:
    df_db = conn.read(ttl="0d") # Membaca data real-time langsung dari Google Sheets
    if df_db.empty:
        st.info("Belum ada transaksi tersimpan di Google Sheets.")
    else:
        df_db.index = df_db.index + 1
        df_db.index.name = "No. Antrean"
        st.dataframe(df_db, use_container_width=True)
        
        total_omset = df_db["Total Belanja"].astype(int).sum()
        st.metric(label="💰 Total Pendapatan Toko di Google Sheets", value=f"Rp {total_omset:,}")
except:
    st.warning("Hubungan ke Google Sheets sedang memproses. Pastikan link di menu Secrets Streamlit Cloud sudah disimpan.")
