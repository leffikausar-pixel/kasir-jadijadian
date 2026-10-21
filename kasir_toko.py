import io
import pandas as pd
import requests
import streamlit as st
import qrcode
from datetime import datetime, timedelta  # Menambahkan timedelta untuk kalkulasi manual jika diperlukan

# Mengatur tampilan halaman web agar lebih luas dan modern
st.set_page_config(page_title="Kasir Toko Berkah", layout="wide")
st.title("🏪 Kasir Toko Berkah")

# --- INISIALISASI SESSION STATE ---
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []
if "riwayat_lokal" not in st.session_state:
    st.session_state.riwayat_lokal = []

# 🔗 LINK WEBHOOK DISCORD ANDA
URL_WEBHOOK = "https://discordapp.com"


# --- FUNGSI AUXILIARY & PENGIRIMAN DATA ---

def crc16_checksum(data: str) -> str:
    """Menghitung kode pengaman CRC16 standar perbankan untuk QRIS Dinamis"""
    crc = 0xFFFF
    for byte in data.encode('ascii'):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def kirim_ke_database(metode_bayar, total_harga):
    """Mengirim baris teks bersih dengan Waktu Indonesia Barat (WIB) yang dikunci total"""
    # Trik Paksa: Ambil jam server saat ini
    waktu_server = datetime.now()
    
    # Deteksi apakah jam server tertinggal 7 jam (ciri khas server Streamlit luar negeri)
    # Kita paksa tambahkan 7 jam secara manual agar menjadi Waktu Indonesia Barat (WIB) yang absolut
    waktu_wib = (waktu_server + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Format baris teks CSV: Waktu,Metode,Total
    payload = {
        "content": f"{waktu_wib},{metode_bayar},{total_harga}"
    }
    try:
        response = requests.post(URL_WEBHOOK, json=payload, timeout=10)
        return response.status_code == 204
    except:
        return False

def generate_qris_dinamis(part1, part2, nominal):
    """Menyusun teks QRIS Dinamis dan membuat gambar Barcode secara mandiri via library lokal"""
    string_nominal = f"{len(str(nominal)):02d}{nominal}"
    qris_setengah_jadi = f"{part1}{string_nominal}{part2}"
    checksum_baru = crc16_checksum(qris_setengah_jadi)
    qris_final = f"{qris_setengah_jadi}{checksum_baru}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qris_final)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    
    st.image(byte_im, caption=f"Scan QRIS Toko Belanja Vall - Total: Rp {nominal:,}", width=300)


# --- MENU DAN INPUT UTAMA KASIR ---

MENU_BARANG = {
    "Beras 1kg": 15000,
    "Minyak Goreng 1L": 18000,
    "Gula Pasir 1kg": 16000,
    "Telur 1kg": 28000,
    "Mie Instan": 35000
}

col_menu, col_keranjang = st.columns(2)

with col_menu:
    st.header("🛍️ Menu Barang")
    for nama_barang, harga in MENU_BARANG.items():
        if st.button(f"➕ {nama_barang} - Rp {harga:,}", key=f"menu_{nama_barang}"):
            st.session_state.keranjang.append({"Barang": nama_barang, "Harga": harga})
            st.toast(f"{nama_barang} dimasukkan ke keranjang!")

with col_keranjang:
    st.header("🛒 Keranjang Belanja")
    if not st.session_state.keranjang:
        st.info("Keranjang masih kosong.")
        total_akhir = 0
    else:
        df_keranjang = pd.DataFrame(st.session_state.keranjang)
        st.dataframe(df_keranjang, use_container_width=True)
        
        total_akhir = df_keranjang["Harga"].sum()
        st.metric(label="Total yang Harus Dibayar", value=f"Rp {total_akhir:,}")
        
        if st.button("🗑️ Kosongkan Keranjang"):
            st.session_state.keranjang = []
            st.rerun()


# --- PROSES PEMBAYARAN KASIR ---
if total_akhir > 0:
    st.markdown("---")
    st.header("💳 Metode Pembayaran")
    
    tab1, tab2 = st.tabs(["💵 Pembayaran Tunai", "📱 Pembayaran QRIS"])
    
    with tab1:
        nominal_bayar = st.number_input("Jumlah Uang Tunai Diterima (Rp)", min_value=int(total_akhir), step=5000)
        kembalian = nominal_bayar - total_akhir
        st.success(f"### 💵 Kembalian: Rp {kembalian:,}")
        
        if st.button("💾 Konfirmasi Transaksi Lunas", key="btn_tunai"):
            sukses = kirim_ke_database("Tunai", total_akhir)
            st.session_state.riwayat_lokal.append({"Metode": "Tunai", "Total Belanja": total_akhir})
            
            if sukses:
                st.toast("🚀 Transaksi Sukses! Data dikirim ke Zapier.")
            else:
                st.error("Gagal mengirim data ke Discord!")
                
            st.session_state.keranjang = []
            st.rerun()
            
    with tab2:
        st.info("Silakan scan kode QRIS dinamis di bawah ini:")
        generate_qris_dinamis(
            part1="00020101021226570011ID.DANA.WWW011893600915387331088002098733108800303UMI51440014ID.CO.QRIS.WWW0215ID10253904693320303UMI52045499530336054", 
            part2="5802ID5917Toko Belanja Vall6015Kota Jakarta Ti6105134106304", 
            nominal=total_akhir
        )
        
        if st.button("✅ Konfirmasi Pembayaran QRIS Sukses", key="btn_qris"):
            st.balloons()
            sukses = kirim_ke_database("QRIS", total_akhir)
            st.session_state.riwayat_lokal.append({"Metode": "QRIS", "Total Belanja": total_akhir})
            
            if sukses:
                st.success("🚀 Pembayaran QRIS Sukses! Data diproses ke Zapier.")
            else:
                st.error("Gagal mengirim data QRIS ke Discord!")
                
            st.session_state.keranjang = []
            st.rerun()


# --- BAGIAN PALING BAWAH: TABEL RINGKASAN SESI ---
st.markdown("---")
st.header("📊 Ringkasan Penjualan Sesi Ini")

if not st.session_state.riwayat_lokal:
    st.info("Belum ada transaksi pada sesi ini.")
else:
    df_riwayat = pd.DataFrame(st.session_state.riwayat_lokal)
    st.dataframe(df_riwayat, use_container_width=True)
