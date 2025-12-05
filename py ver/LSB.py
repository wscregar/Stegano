from PIL import Image
import sys
import os

# --- UTILITY FUNCTIONS ---

def text_to_bits(text):
    """Mengubah string teks menjadi string bit."""
    # Mengubah setiap karakter menjadi representasi ASCII/Unicode, lalu ke biner 8 bit
    bits = [bin(ord(c))[2:].zfill(8) for c in text]
    return "".join(bits)

def bits_to_text(bits):
    """Mengubah string bit menjadi string teks."""
    # Pastikan panjang string bit adalah kelipatan 8
    if len(bits) % 8 != 0:
        bits = bits[:-(len(bits) % 8)] # Truncate jika ada sisa
    
    # Memproses setiap 8 bit untuk membentuk satu karakter
    text = ""
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        # Mengonversi biner 8-bit ke integer, lalu ke karakter
        text += chr(int(byte, 2))
    return text


def get_max_capacity(input_img_path):
    """
    Menghitung jumlah maksimum karakter (byte) yang dapat disisipkan.
    """
    try:
        img = Image.open(input_img_path)
        # pastikan gambar dalam mode RGB untuk 3 byte per pixel
        # pakai RGB agar kelihatan lebih tersembunyi 
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        width, height = img.size
        
        # total bit yang tersedia (3 komponen warna * 1 bit/komponen)
        total_available_bits = width * height * 3
        
        # kapasitas dalam karakter (8 bit per karakter)
        max_capacity_chars = total_available_bits // 8
        
        # pesan encoding harus diakhiri dengan null terminator ('\0') agar tidak menghasilkan noise
        # null terminator juga memakan 1 karakter (8 bit).
        # kapasitas efektif = kapasitas total - 1 (untuk null terminator).
        effective_capacity = max_capacity_chars - 1 
        
        return max(0, effective_capacity) # memastikan hasil tidak negatif
        
    except FileNotFoundError:
        print(f"Error: File tidak ditemukan di path: {input_img_path}")
        return 0
    except Exception as e:
        print(f"Error saat menghitung kapasitas: {e}")
        return 0

def encode_image(input_img_path, output_img_path, message):
    """
    Menyisipkan pesan ke dalam gambar menggunakan LSB.
    Bekerja dengan format lossless seperti BMP atau PNG.
    """
    try:
        print("Membaca gambar sumber...")
        img = Image.open(input_img_path).convert("RGB")
        width, height = img.size
        
        # tambahkan null terminator '\0' ke pesan
        message_with_terminator = message + '\0'
        
        # ubah pesan menjadi string bit (setiap karakter 8 bit)
        bit_message = text_to_bits(message_with_terminator)
        message_length = len(bit_message)
        
        # hitung kapasitas: 1 pixel (3 byte RGB) dapat menyimpan 3 bit.
        # per bit pesan menggunakan 1 byte 
        # Total byte pixel yang tersedia adalah (width * height * 3)
        max_capacity_bits = width * height * 3 

        # karenamenggunakan satu byte gambar untuk satu bit pesan:
        # kapasitas bit yang sebenarnya adalah total byte gambar.
        # total pixel = width * height. total byte = Total pixel * 3 (RGB).
        max_capacity_bits = width * height * 3
        
        if message_length > max_capacity_bits:
            raise ValueError(f"Pesan terlalu panjang! Kapasitas maks: {max_capacity_bits // 8} karakter.")

        print(f"Pesan: {len(message)} karakter ({message_length} bit)")
        print(f"Kapasitas Maksimal: {max_capacity_bits // 8} karakter.")
        print("Menyisipkan pesan...")

        # dapatkan data pixel dalam bentuk list
        pixel_data = list(img.getdata())
        data_index = 0
        bit_index = 0
        
        # list baru untuk menyimpan pixel yang sudah dimodifikasi
        new_pixel_data = []

        # loop melalui setiap pixel (r, g, b)
        for r, g, b in pixel_data:
            if bit_index < message_length:
                # modifikasi LSB dari komponen Merah (R)
                # ambil bit pesan (0 atau 1)
                msg_bit = int(bit_message[bit_index])
                # bersihkan LSB byte R (r & ~1 atau r & 0xFE), lalu masukkan bit pesan (r | msg_bit)
                r = (r & 0xFE) | msg_bit
                bit_index += 1
            
            if bit_index < message_length:
                # modifikasi LSB dari komponen Hijau (G)
                msg_bit = int(bit_message[bit_index])
                g = (g & 0xFE) | msg_bit
                bit_index += 1

            if bit_index < message_length:
                # modifikasi LSB dari komponen Biru (B)
                msg_bit = int(bit_message[bit_index])
                b = (b & 0xFE) | msg_bit
                bit_index += 1
            
            new_pixel_data.append((r, g, b))
            
            if bit_index >= message_length:
                break # Pesan selesai disisipkan

        # Tambahkan sisa pixel yang tidak dimodifikasi
        new_pixel_data.extend(pixel_data[len(new_pixel_data):])
        
        # Buat gambar baru dari data pixel yang telah dimodifikasi
        stego_img = Image.new(img.mode, img.size)
        stego_img.putdata(new_pixel_data)
        
        print(f"Menulis ke {output_img_path}...")
        stego_img.save(output_img_path)
        print("Sukses! Pesan tersimpan.")

    except Exception as e:
        print(f"Error pada encoding: {e}")


def decode_image(input_img_path):
    """
    Mengekstrak pesan dari gambar LSB.
    """
    try:
        print("Membaca gambar dengan pesan rahasia...")
        img = Image.open(input_img_path).convert("RGB")
        
        # Dapatkan data pixel
        pixel_data = list(img.getdata())
        
        extracted_bits = ""
        null_terminator_bits = text_to_bits('\0') # 8 bit null terminator
        
        print("Mencoba mendekode pesan...")

        # Loop melalui setiap pixel dan setiap komponen warna (R, G, B)
        for r, g, b in pixel_data:
            # Ekstraksi LSB dari R: (r & 1)
            extracted_bits += str(r & 1)
            
            # Cek apakah 8 bit (satu karakter) telah terkumpul
            if len(extracted_bits) % 8 == 0:
                last_char_bits = extracted_bits[-8:]
                if last_char_bits == null_terminator_bits:
                    # Hapus null terminator dan hentikan loop
                    extracted_text = bits_to_text(extracted_bits[:-8])
                    print("\n=== Pesan Rahasia ===")
                    print(extracted_text)
                    print("=====================\n")
                    return

            # Ekstraksi LSB dari G: (g & 1)
            extracted_bits += str(g & 1)
            if len(extracted_bits) % 8 == 0:
                last_char_bits = extracted_bits[-8:]
                if last_char_bits == null_terminator_bits:
                    extracted_text = bits_to_text(extracted_bits[:-8])
                    print("\n=== Pesan Rahasia ===")
                    print(extracted_text)
                    print("=====================\n")
                    return
            
            # Ekstraksi LSB dari B: (b & 1)
            extracted_bits += str(b & 1)
            if len(extracted_bits) % 8 == 0:
                last_char_bits = extracted_bits[-8:]
                if last_char_bits == null_terminator_bits:
                    extracted_text = bits_to_text(extracted_bits[:-8])
                    print("\n=== Pesan Rahasia ===")
                    print(extracted_text)
                    print("=====================\n")
                    return
        
        print("Pesan tidak ditemukan (Null terminator tidak tercapai).")

    except Exception as e:
        print(f"Error pada decoding: {e}")

# --- MAIN EXECUTION ---

def print_usage(prog_name):
    print("Penggunaan:")
    print(f"  python {prog_name} encode <input.png/bmp> <output.png/bmp> \"Pesan Rahasia\"")
    print(f"  python {prog_name} decode <input_with_secret.png/bmp>")
    print(f"  python {prog_name} capacity <input.png/bmp>")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage(sys.argv[0])
        sys.exit(1)

    mode = sys.argv[1].lower()
    
    
    if mode == "encode":
        if len(sys.argv) != 5:
            print("Error: Argumen encode kurang.")
            print_usage(sys.argv[0])
            sys.exit(1)
        
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        message = sys.argv[4]
        
        encode_image(input_file, output_file, message)
    
    elif mode == "decode":
        if len(sys.argv) != 3:
            print("Error: Argumen decode kurang.")
            print_usage(sys.argv[0])
            sys.exit(1)
            
        input_file = sys.argv[2]
        decode_image(input_file)

    elif mode == "capacity": 
        if len(sys.argv) != 3:
            print("Error: Argumen capacity kurang.")
            print_usage(sys.argv[0])
            sys.exit(1)
            
        input_file = sys.argv[2]
        max_chars = get_max_capacity(input_file)
        
        print("\n=== Analisis Kapasitas Steganografi ===")
        print(f"File Sumber: {input_file}")
        print(f"Kapasitas Maksimal (Karakter): {max_chars} karakter")
        print("======================================\n")

    else:
        print_usage(sys.argv[0])
        sys.exit(1)