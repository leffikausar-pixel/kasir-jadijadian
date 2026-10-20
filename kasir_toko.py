import io
import pandas as pd
import requests
import streamlit as st
from datetime import datetime

# Mengatur tampilan halaman web agar lebih luas dan modern
st.set_page_config(page_title="Kasir Toko Berkah", layout="wide")
st.title("🏪 Kasir Toko Berkah")

# --- INISIALISASI SESSION STATE ---
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []
if "riwayat_lokal" not in st.session_state:
    st.session_state.riwayat_lokal = []

# 🔗 KODE IDENTITAS GOOGLE FORMS ASLI ANDA (SUDAH DIKOREKSI)
FORM_ID = "1FAIpQLSdFefIUsHXofGALOOD3ZWDmf44Jvra1UU_U-3YQIPpmX2X2oQ"
ENTRY_METODE = "entry.431569343"
ENTRY_TOTAL = "entry.892601940"

# 🔗 LINK WEBHOOK DISCORD ANDA
URL_WEBHOOK = "https://discordapp.com"


# --- FUNGSI PROSES DAN PENGIRIMAN DATA ---

def kirim_ke_sheets(metode_bayar, total_harga):
    url = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"
    data_payload = {
        ENTRY_METODE: str(metode_bayar),
        ENTRY_TOTAL: str(total_harga)
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(url, data=data_payload, headers=headers)
        return response.status_code == 200
    except:
        return False

def kirim_ke_database(metode_bayar, total_harga):
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

# Fungsi simulasi generate QRIS Dinamis berdasarkan nominal belanja
def generate_qris_dinamis(nominal):
    # Ini adalah simulasi tampilan teks/gambar QRIS
    st.image(f"https://qrserver.com_{nominal}", 
             caption=f"Scan QRIS - Total Tagihan: Rp {nominal:,}")


# --- MENU DAN INPUT UTAMA KASIR ---

# Daftar Barang (Menu Toko)
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


# --- PROSES PEMBAYARAN (JIKA ADA BARANG) ---
if total_akhir > 0:
    st.markdown("---")
    st.header("💳 Metode Pembayaran")
    
    tab1, tab2 = st.tabs(["💵 Pembayaran Tunai", "📱 Pembayaran QRIS"])
    
    with tab1:
        nominal_bayar = st.number_input("Jumlah Uang Tunai Diterima (Rp)", min_value=int(total_akhir), step=5000)
        kembalian = nominal_bayar - total_akhir
        st.success(f"### 💵 Kembalian: Rp {kembalian:,}")
        
        if st.button("💾 Konfirmasi Transaksi Lunas", key="btn_tunai"):
            kirim_ke_sheets("Tunai", total_akhir)
            kirim_ke_database("Tunai", total_akhir)
            
            st.session_state.riwayat_lokal.append({"Metode": "Tunai", "Total Belanja": total_akhir})
            st.toast("🚀 Sukses! Transaksi lunas otomatis masuk Google Sheets & Discord!")
            
            st.session_state.keranjang = []
            st.rerun()
            
       with tab2:
        st.info("Silakan scan kode QRIS dinamis di bawah ini:")
        
        # 📱 KODE QRIS TOKO BELANJA VALL (SUDAH DI-SET DINAMIS)
        generate_qris_dinamis(
            part1="00020101021226570011ID.DANA.WWW011893600915387331088002098733108800303UMI51440014ID.CO.QRIS.WWW0215ID10253904693320303UMI52045499530336054", 
            part2="5802ID5917Toko Belanja Vall6015Kota Jakarta Ti6105134106304", 
            nominal=total_akhir
        )
        
        if st.button("✅ Konfirmasi Pembayaran QRIS Sukses", key="btn_qris"):
            st.balloons()
            kirim_ke_sheets("QRIS", total_akhir)
            kirim_ke_database("QRIS", total_akhir)
            
            st.session_state.riwayat_lokal.append({"Metode": "QRIS", "Total Belanja": total_akhir})
            st.success("🚀 Pembayaran QRIS sukses & tercatat di database!")
            
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
