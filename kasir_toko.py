import streamlit as st
import qrcode
import io 

# Mengatur tampilan halaman web agar lebih luas dan modern
st.set_page_config(page_title="Aplikasi Kasir Pro v2", layout="wide")
st.title("🏪 Aplikasi Kasir Toko Pusaka")

# 1. DAFTAR BARANG DAN HARGA (Bawaan Kode Anda)
menu_barang = {
    1: {"nama": "Beras 5kg", "harga": 65000},
    2: {"nama": "Minyak Goreng 1L", "harga": 19000},
    3: {"nama": "Gula Pasir 1kg", "harga": 16000},
    4: {"nama": "Telur 1kg", "harga": 26000},
    5: {"nama": "Mie Instan", "harga": 3000},
}

# 2. INISIALISASI VARIABEL SESSI (Supaya data tidak hilang saat tombol diklik)
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

# Membagi halaman web menjadi 2 kolom utama
kolom_kiri, kolom_kanan = st.columns(2)

# --- KOLOM SEBELAH KIRI: MENU & INPUT BARANG ---
with kolom_kiri:
    st.subheader("🛒 Pilih & Masukkan Barang")
    
    # Dropdown Pilihan Barang
    pilihan_opsi = {f"{info['nama']} - Rp {info['harga']:,}": kode for kode, info in menu_barang.items()}
    pilihan_user = st.selectbox("Silakan pilih barang:", list(pilihan_opsi.keys()))
    
    kode_terpilih = pilihan_opsi[pilihan_user]
    
    # Input jumlah barang
    jumlah = st.number_input(f"Masukkan jumlah beli untuk {menu_barang[kode_terpilih]['nama']}:", min_value=1, step=1, value=1)
    
    # Tombol Tambah ke Keranjang
    if st.button("➕ Tambah ke Keranjang", type="primary"):
        nama_barang = menu_barang[kode_terpilih]["nama"]
        harga_satuan = menu_barang[kode_terpilih]["harga"]
        subtotal = harga_satuan * jumlah
        
        st.session_state.keranjang.append({
            "nama": nama_barang,
            "harga": harga_satuan,
            "jumlah": jumlah,
            "subtotal": subtotal
        })
        st.success(f"Berhasil menambahkan {jumlah} {nama_barang} ke keranjang.")
    
    st.markdown("---")
    st.subheader("🎟️ Voucher & Diskon")
    # Fitur Input Voucher Diskon
    kode_voucher = st.text_input("Masukkan Kode Voucher (Opsional):", placeholder="Contoh: DISKON10 atau HEMAT5")
    
    diskon_persen = 0
    if kode_voucher.upper() == "DISKON10":
        diskon_persen = 10
        st.success("🎉 Voucher DISKON10 Berhasil Digunakan! Potongan 10%")
    elif kode_voucher.upper() == "HEMAT5":
        diskon_persen = 5
        st.success("🎉 Voucher HEMAT5 Berhasil Digunakan! Potongan 5%")
    elif kode_voucher != "":
        st.error("❌ Kode voucher tidak valid.")

    # Tombol Reset Keranjang
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
        
        # Menampilkan barang di keranjang & menyusun teks untuk cetak struk
        for i, item in enumerate(st.session_state.keranjang):
            st.write(f"{i+1}. **{item['nama']}** (x{item['jumlah']}) = Rp {item['subtotal']:,}")
            teks_struk += f"{item['nama']} x{item['jumlah']} = Rp {item['subtotal']:,}\n"
            total_belanja += item["subtotal"]
            
        # Hitung potongan diskon
        potongan = int(total_belanja * (diskon_persen / 100))
        total_akhir = total_belanja - potongan
        
        teks_struk += "-----------------------------------\n"
        teks_struk += f"Subtotal: Rp {total_belanja:,}\n"
        teks_struk += f"Diskon ({diskon_persen}%): Rp {potongan:,}\n"
        teks_struk += f"TOTAL AKHIR: Rp {total_akhir:,}\n"
        teks_struk += "===================================\n"
        teks_struk += "Terima kasih telah berbelanja!"

        st.markdown("---")
        st.write(f"Subtotal Belanja: Rp {total_belanja:,}")
        st.write(f"Potongan Diskon: Rp {potongan:,}")
        st.markdown(f"## **Total Harus Dibayar: Rp {total_akhir:,}**")
        
        st.markdown("---")
        st.subheader("💳 Metode Pembayaran")
        # Fitur Pilihan Metode Pembayaran
        metode = st.radio("Pilih Metode:", ["Tunai (Cash)", "QRIS / E-Wallet"])
        
        if metode == "Tunai (Cash)":
            uang_bayar = st.number_input("Masukkan uang pembayaran (Rp):", min_value=0, step=1000, value=0)
            if uang_bayar > 0:
                if uang_bayar < total_akhir:
                    st.error(f"Uang kurang Rp {total_akhir - uang_bayar:,}. Silakan tambah pembayaran.")
                else:
                    kembalian = uang_bayar - total_akhir
                    st.balloons()
                    st.success(f"### 💵 Kembalian: Rp {kembalian:,}")
                    
                    # Fitur Cetak Struk (Unduh Berkas TXT)
                    st.download_button(
                        label="📥 Cetak / Unduh Struk (TXT)",
                        data=teks_struk,
                        file_name="struk_belanja.txt",
                        mime="text/plain"
                    )
        
        elif metode == "QRIS / E-Wallet":
            st.info("Silakan scan kode QRIS di bawah ini untuk melakukan pembayaran:")
            
            # 1. Kode QRIS Anda dipecah menjadi dua bagian tepat sebelum posisi Tag 58 (5802ID)
            qris_part1 = "00020101021126570011ID.DANA.WWW011893600915387331088002098733108800303UMI51440014ID.CO.QRIS.WWW0215ID10253904693320303UMI520454995303360"
            qris_part2 = "5802ID5917Toko Belanja Vall6015Kota Jakarta Ti610513410" 
            
            # 2. Fungsi menyisipkan nominal belanjaan di tengah urutan tag yang benar
            def generate_qris_dinamis(part1, part2, nominal):
                # Tag 54 disusun berdasarkan panjang karakter nilai rupiahnya
                sub_nominal = f"54{len(str(nominal)):02d}{nominal}"
                
                # Menggabungkan bagian awal + tag nominal + bagian akhir + pemicu checksum '6304'
                qris_tanpa_crc = part1 + sub_nominal + part2 + "6304"
                
                # Hitung ulang kode verifikasi data (CRC16)
                crc = 0xFFFF
                for char in qris_tanpa_crc:
                    crc ^= ord(char) << 8
                    for _ in range(8):
                        if crc & 0x8000:
                            crc = (crc << 1) ^ 0x1021
                        else:
                            crc <<= 1
                        crc &= 0xFFFF
                
                hex_crc = format(crc, '04X')
                return qris_tanpa_crc + hex_crc

            # 3. Proses pembuatan string QRIS
            qris_final = generate_qris_dinamis(qris_part1, qris_part2, total_akhir)
            
            # 4. Merender data menjadi gambar QR murni
            img = qrcode.make(qris_final)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.image(byte_im, caption=f"QRIS Otomatis: Rp {total_akhir:,} (Toko Belanja Vall)", width=250)
            
            if st.button("✅ Konfirmasi Pembayaran QRIS Sukses"):
                st.balloons()
                st.success("🚀 Pembayaran QRIS berhasil dikonfirmasi!")
                
                st.download_button(
                    label="📥 Cetak / Unduh Struk (TXT)",
                    data=teks_struk,
                    file_name="struk_belanja.txt",
                    mime="text/plain"
                )




