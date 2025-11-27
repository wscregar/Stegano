# Steganography - Simple BMP Steganography (LSB Method)

Project ini adalah implementasi sederhana dari teknik Steganografi Gambar menggunakan metode Least Significant Bit (LSB) dengan bahasa pemrograman C++. Alat ini memungkinkan Anda menyembunyikan pesan teks rahasia ke dalam file gambar berformat .bmp (Bitmap) tanpa mengubah tampilan visual gambar tersebut secara kasat mata.

## Konsep LSB (Least Significant Bit)

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

## Cara Menjalankan

1. Kompilasi Kode

Buka terminal di folder project dan jalankan perintah berikut untuk mengkompilasi kode:

    g++ -o stego Image-LSB.cpp

2. Menyembunyikan Pesan (Encode)

Gunakan mode encode untuk menyisipkan pesan.
Format:
`./stego encode <input.bmp> <output.bmp> "Pesan Rahasia"`

Contoh:

    ./stego encode image.bmp result.bmp "This is Secret"

3. Membaca Pesan (Decode)

Gunakan mode decode untuk mengekstrak pesan dari gambar yang sudah disisipi.
Format:
`./stego decode <gambar_rahasia.bmp>`

Contoh:

    ./stego decode result.bmp
