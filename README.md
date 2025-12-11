# Steganography - Invisible Copyright Protection

Project ini adalah implementasi modern dari teknik **Steganografi Gambar** menggunakan metode *Least Significant Bit* (LSB) dikombinasikan dengan keamanan hash **SHA-512**. 

Dibangun menggunakan **Python** dan framework **Streamlit**, tools ini menyembunyikan tanda tangan digital (watermark) ke dalam file gambar tanpa mengubah tampilan visualnya secara kasat mata.

## Konsep Simple BMP Steganography (LSB Method)

Project ini menggunakan metode LSB, teknik yang paling umum dan mendasar dalam steganografi gambar. Berikut cara kerjanya:

1. Struktur Pixel

Setiap titik warna (pixel) pada gambar 24-bit terdiri dari 3 komponen warna: Merah (R), Hijau (G), dan Biru (B). Masing-masing komponen berukuran 1 Byte (8 bit), dengan nilai antara 0 hingga 255.

2. Manipulasi Bit

Dalam 1 Byte (8 bit), posisi paling kiri disebut MSB (Most Significant Bit) yang paling berpengaruh pada nilai warna, dan posisi paling kanan disebut LSB (Least Significant Bit) yang paling sedikit pengaruhnya.

Metode ini mengganti bit terakhir (LSB) dari byte gambar dengan bit pesan rahasia.

Ilustrasi:

Misalkan kita ingin menyisipkan bit pesan bernilai 1 ke dalam komponen warna merah yang bernilai 200.

Kesimpulan: 

Mata manusia tidak dapat membedakan perubahan warna dari nilai 200 menjadi 201. Perbedaan ini tidak terlihat (invisible), namun data biner di dalamnya telah berubah dan menyimpan pesan kita.

## Konsep SHA-512 Hashing

Tidak seperti steganografi biasa yang menyisipkan teks mentah, program ini mengubah teks hak cipta menjadi pola hash SHA-512 yang unik dan menyebarkannya ke seluruh permukaan gambar. Ini memastikan integritas data yang lebih tinggi.

## Cara Menjalankan

### 1. Prerequisites
Pastikan PC kita memiliki:
* **Python** (versi 3.8 atau lebih baru).
* File Program: Pastikan `app.py` dan `watermark_tools.py` berada dalam satu folder.

### 2. Instalasi Library
Buka terminal atau Command Prompt (CMD) di folder project, lalu jalankan perintah berikut:

```bash
pip install streamlit pillow
```

### 3. Menjalankan Aplikasi
```bash
python -m streamlit run app.py
```

### 4. Panduan Penggunaan

Aplikasi memiliki navigasi menu di sebelah kiri (Sidebar):

### A. Mode Proteksi (Encode)

* Pilih menu "Watermark".

* Upload gambar asli (.png/.bmp).

* Ketik pesan rahasia/copyright di kolom teks.

* Klik tombol "Proses Watermark".

* Download gambar hasil watermark.

### B. Mode Verifikasi (Decode)

* Pilih menu "Verifikasi".

* Upload gambar yang sudah diproteksi.

* Masukkan teks/password yang sama persis dengan saat proses enkripsi.

* Klik "Verifikasi Watermark" untuk membuktikan kepemilikan.

### C. Mode Analisis 

* Pilih menu "Analisis Integritas".

* Upload gambar apa saja.

* Klik "Jalankan Analisis" untuk mengecek apakah gambar tersebut konsisten atau pernah diedit (crop/manipulasi) tanpa perlu mengetahui passwordnya.
