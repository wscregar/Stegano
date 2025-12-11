from PIL import Image
import hashlib
import os


# Fungsi untuk mendapatkan kapasitas maksimum penyimpanan watermark dalam gambar
def get_max_capacity(input_img_path):
    try:
        img = Image.open(input_img_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        width, height = img.size
        # Kapasitas dalam karakter (byte)
        return (width * height * 3) // 8
    except Exception as e:
        print(f"Error capacity: {e}")
        return 0

# Fungsi untuk menghasilkan hash watermark yang diulang sesuai kapasitas gambar
def generate_watermark_hash(text, max_bits):
    # Membuat hash SHA512
    sha512_hash = hashlib.sha512(text.encode()).hexdigest()
    # Mengubah ke biner
    hash_bits = bin(int(sha512_hash, 16))[2:].zfill(512)
    
    # Mengulang hash sampai memenuhi kapasitas gambar
    repeated_hash = ""
    while len(repeated_hash) < max_bits:
        repeated_hash += hash_bits
    return repeated_hash[:max_bits]

# Fungsi untuk menyisipkan watermark ke dalam gambar
def embed_watermark(input_img_path, output_img_path, watermark_text):
    try:
        img = Image.open(input_img_path).convert("RGB")
        width, height = img.size
        max_capacity_bits = width * height * 3
        
        watermark_bits = generate_watermark_hash(watermark_text, max_capacity_bits)
        pixel_data = list(img.getdata())
        
        new_pixel_data = []
        bit_index = 0
        
        # Proses penyisipan LSB
        for r, g, b in pixel_data:
            if bit_index < len(watermark_bits):
                r = (r & 0xFE) | int(watermark_bits[bit_index])
                bit_index += 1
            if bit_index < len(watermark_bits):
                g = (g & 0xFE) | int(watermark_bits[bit_index])
                bit_index += 1
            if bit_index < len(watermark_bits):
                b = (b & 0xFE) | int(watermark_bits[bit_index])
                bit_index += 1
            new_pixel_data.append((r, g, b))
            
        watermarked_img = Image.new(img.mode, img.size)
        watermarked_img.putdata(new_pixel_data)
        watermarked_img.save(output_img_path)
        
        # Return hash asli untuk verifikasi
        return hashlib.sha512(watermark_text.encode()).hexdigest()
    except Exception as e:
        print(f"Error embedding: {e}")
        return None

# Fungsi untuk mengambil watermark dari gambar
def extract_watermark_hash(input_img_path):
    try:
        img = Image.open(input_img_path).convert("RGB")
        pixel_data = list(img.getdata())
        extracted_bits = ""
        
        # Ambil semua bit LSB
        for r, g, b in pixel_data:
            extracted_bits += str(r & 1)
            extracted_bits += str(g & 1)
            extracted_bits += str(b & 1)
            
        return extracted_bits
    except Exception as e:
        return None

# Fungsi untuk memverifikasi watermark
def verify_watermark_comprehensive(input_img_path, watermark_text):
    try:
        print(f"Memverifikasi watermark: '{watermark_text}'...")
        expected_hash = hashlib.sha512(watermark_text.encode()).hexdigest()
        expected_bits = bin(int(expected_hash, 16))[2:].zfill(512)
        
        extracted_bits = extract_watermark_hash(input_img_path)
        if not extracted_bits: return False
        
        # Hitung berapa blok hash yang ada
        num_blocks = len(extracted_bits) // 512
        if num_blocks == 0: return False

        mismatched_blocks = 0
        
        for i in range(num_blocks):
            block = extracted_bits[i*512 : (i+1)*512]
            if block != expected_bits:
                mismatched_blocks += 1
        
        match_percentage = ((num_blocks - mismatched_blocks) / num_blocks) * 100
        print(f"Kecocokan: {match_percentage:.2f}% ({num_blocks - mismatched_blocks}/{num_blocks} blok)")
        
        if mismatched_blocks == 0: return True
        elif match_percentage > 80: return "partial"
        else: return False
    except Exception as e:
        print(f"Error verify: {e}")
        return False

# Fungsi untuk menganalisis integritas watermark
def analyze_watermark_integrity(input_img_path):
    try:
        print("Menganalisis integritas...")
        extracted_bits = extract_watermark_hash(input_img_path)
        if not extracted_bits: return
        
        first_block = extracted_bits[:512]
        num_blocks = len(extracted_bits) // 512
        inconsistencies = 0
        
        for i in range(1, num_blocks):
            block = extracted_bits[i*512 : (i+1)*512]
            if block != first_block:
                inconsistencies += 1
                
        if inconsistencies == 0:
            print("✓ SEMUA blok hash identik. Integritas terjaga.")
        else:
            print(f"✗ Ditemukan {inconsistencies} blok yang tidak konsisten.")
            
    except Exception as e:
        print(f"Error analyze: {e}")
