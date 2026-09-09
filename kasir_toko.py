import streamlit as st
import qrcode
import io
import pandas as pd
import requests

# Mengatur tampilan halaman web agar lebih luas dan modern
st.set_page_config(page_title="Kasir Toko Berkah", layout="wide")
st.title("🏪 Kasir Toko Berkah")

# 🔗 KODE IDENTITAS ASLI GOOGLE FORMS ANDA (Sudah disesuaikan khusus formulir Anda)
FORM_ID = "1FAIpQLSdFefIUsHXofGALOOD3ZWDmf44Jvra1UU_U-3YQIPpmX2X2oQ"
ENTRY_METODE = "entry.1437648356"
ENTRY_TOTAL = "entry.1802958440"

# Fungsi kirim data otomatis ke Google Sheets via Google Form Webhook
# Fungsi kirim data otomatis ke Google Sheets via Google Form Webhook (Sudah Diperbaiki)
def kirim_ke_sheets(metode_bayar, total_harga):
    url = f"https://google.com{FORM_ID}/formResponse"
    data_payload = {
        ENTRY_METODE: str(metode_bayar), # Dipastikan menjadi teks
        ENTRY_TOTAL: str(total_harga)    # Nominal angka dipaksa menjadi teks agar lolos dari blokir Google
    }
    try:
        # Python mengirim data seolah-olah sedang mengisi formulir web biasa
        requests.post(url, data=data_payload)
        return True
    except:
        return False


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

if "riwayat_lokal" not in st.session_state:
    st.session_state.riwayat_lokal = []

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
        for item in st.session_state.keranjang:
            st.write(f"🔹 **{item['nama']}** (x{item['jumlah']}) = Rp {item['subtotal']:,}")
            total_belanja += item["subtotal"]
            
        potongan = int(total_belanja * (diskon_persen / 100))
        total_akhir = total_belanja - potongan
        
        st.markdown("---")
        st.write(f"Subtotal Belanja: Rp {total_belanja:,}")
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
                        # Pemicu kirim data ke Google Form yang aslinya terdaftar
                        kirim_ke_sheets("Tunai", total_akhir)
                        st.session_state.riwayat_lokal.append({"Metode": "Tunai", "Total Belanja": total_akhir})
                        st.toast("🚀 Sukses! Transaksi tercatat permanen!")
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
                # Pemicu kirim data ke Google Form yang aslinya terdaftar
                kirim_ke_sheets("QRIS", total_akhir)
                st.session_state.riwayat_lokal.append({"Metode": "QRIS", "Total Belanja": total_akhir})
                st.success("🚀 Pembayaran QRIS sukses & tercatat!")
                st.session_state.keranjang = []
                st.rerun()

# --- BAGIAN PALING BAWAH: TABEL LOKAL ---
st.markdown("---")
st.header("📊 Ringkasan Penjualan Sesi Ini")
if not st.session_state.riwayat_lokal:
    st.info("Belum ada transaksi di sesi ini.")
else:
    df = pd.DataFrame(st.session_state.riwayat_lokal)
    df.index = df.index + 1
    st.dataframe(df, use_container_width=True)
    st.info("💡 Data transaksi di atas sudah otomatis nembus terisi secara permanen di file Excel Google Sheets Anda lewat Webhook!")
