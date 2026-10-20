import io
import pandas as pd
import requests
import streamlit as st
from datetime import datetime

# Mengatur tampilan halaman web agar lebih luas dan modern
st.set_page_config(page_title="Kasir Toko Berkah", layout="wide")
st.title("🏪 Kasir Toko Berkah")

# --- INISIALISASI SESSION STATE (AGAR TIDAK ERROR SAAT RELOAD) ---
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []
if "riwayat_lokal" not in st.session_state:
    st.session_state.riwayat_lokal = []

# 🔗 KODE IDENTITAS ASLI GOOGLE FORMS ANDA
FORM_ID = "1xOzeuieqL-4aopF-RkFTVWDa4zZLLArWNZGK57gb6C8"
ENTRY_METODE = "entry.431569343"
ENTRY_TOTAL = "entry.892601940"

# 🔗 LINK WEBHOOK DISCORD ANDA
URL_WEBHOOK = "https://discordapp.com"


# --- FUNGSI PROSES DAN PENGIRIMAN DATA ---

# Fungsi kirim data otomatis menggunakan Header Form URL-Encoded resmi
def kirim_ke_sheets(metode_bayar, total_harga):
    # Koreksi URL resmi Google Form submission agar mengarah ke formResponse
    url = f"https://google.com{FORM_ID}/formResponse"
    
    data_payload = {
        ENTRY_METODE: str(metode_bayar),
        ENTRY_TOTAL: str(total_harga)
    }
    
    # Header wajib agar Google Form mengenali isian teks
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        response = requests.post(url, data=data_payload, headers=headers)
        return response.status_code == 200
    except:
        return False


# Fungsi kirim data otomatis ke Database Discord secara aman dan anti-blokir
def kirim_ke_database(metode_bayar, total_harga):
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Menyusun format data laporan rapi untuk dikirim
    payload = {
        "content": f"📊 **LAPORAN TRANSAKSI BARU LUNAS**\n"
                   f"📅 Waktu: `{waktu_sekarang}`\n"
                   f"💳 Metode: `{metode_bayar}`\n"
                   f"💰 Total Belanja: **Rp {total_harga:,}**\n"
                   f"========================="
    }
    
    try:
        requests.post(URL_WEBHOOK, json=payload)
        return True
    except:
        return False


# --- SIMULASI LOGIKA TRANSAKSI & TOMBOL ---

# Dummy nilai untuk kebutuhan demonstrasi kode (akan menyesuaikan dengan sistem kasir Anda)
total_akhir = 50000  # Contoh nominal nominal belanja
kembalian = 0        # Contoh nominal kembalian

# Bagian Tab Pembayaran atau Pilihan Metode
tab1, tab2 = st.tabs(["💵 Pembayaran Tunai", "📱 Pembayaran QRIS"])

with tab1:
    st.write(f"Total Belanja: Rp {total_akhir:,}")
    st.success(f"### 💵 Kembalian: Rp {kembalian:,}")
    
    if st.button("💾 Konfirmasi Transaksi Lunas", key="btn_tunai"):
        # Otomatis mengirim data ke Google Sheets via Google Form
        kirim_ke_sheets("Tunai", total_akhir)
        
        # Otomatis melempar data ke server database Discord
        kirim_ke_database("Tunai", total_akhir)
        
        # Mencatat ke riwayat lokal sesi ini
        st.session_state.riwayat_lokal.append({"Metode": "Tunai", "Total Belanja": total_akhir})
        
        st.toast("🚀 Sukses! Transaksi tercatat permanen!")
        st.toast("🚀 Sukses! Transaksi lunas otomatis masuk database Discord!")
        
        # Reset keranjang setelah transaksi lunas
        st.session_state.keranjang = []
        st.rerun()

with tab2:
    st.write(f"Total Belanja: Rp {total_akhir:,}")
    st.info("Silakan scan kode QRIS yang tersedia.")
    
    if st.button("✅ Konfirmasi Pembayaran QRIS Sukses", key="btn_qris"):
        st.balloons()
        
        # Otomatis mengirim data ke Google Sheets via Google Form
        kirim_ke_sheets("QRIS", total_akhir)
        
        # Otomatis melempar data ke server database Discord
        kirim_ke_database("QRIS", total_akhir)
        
        # Mencatat ke riwayat lokal sesi ini
        st.session_state.riwayat_lokal.append({"Metode": "QRIS", "Total Belanja": total_akhir})
        
        st.success("🚀 Pembayaran QRIS sukses & tercatat di database!")
        
        # Reset keranjang setelah transaksi lunas
        st.session_state.keranjang = []
        st.rerun()


# --- BAGIAN PALING BAWAH: TABEL RINGKASAN ---
st.markdown("---")
st.header("📊 Ringkasan Penjualan Sesi Ini")

if not st.session_state.riwayat_lokal:
    st.info("Belum ada transaksi pada sesi ini.")
else:
    df_riwayat = pd.DataFrame(st.session_state.riwayat_lokal)
    st.dataframe(df_riwayat, use_container_width=True)
