from PIL import Image
import sys
import os
import hashlib

# --- UTILITY FUNCTIONS ---

def text_to_bits(text):
    """Mengubah string teks menjadi string bit."""
    bits = [bin(ord(c))[2:].zfill(8) for c in text]
    return "".join(bits)

def bits_to_text(bits):
    """Mengubah string bit menjadi string teks."""
    if len(bits) % 8 != 0:
        bits = bits[:-(len(bits) % 8)]
    
    text = ""
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        text += chr(int(byte, 2))
    return text

def get_max_capacity(input_img_path):
    """
    Menghitung jumlah maksimum karakter (byte) yang dapat disisipkan.
    """
    try:
        img = Image.open(input_img_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        width, height = img.size
        total_available_bits = width * height * 3
        max_capacity_chars = total_available_bits // 8
        effective_capacity = max_capacity_chars - 1
        
        return max(0, effective_capacity)
        
    except FileNotFoundError:
        print(f"Error: File tidak ditemukan di path: {input_img_path}")
        return 0
    except Exception as e:
        print(f"Error saat menghitung kapasitas: {e}")
        return 0

def generate_watermark_hash(text, max_bits):
    """
    Generate SHA512 hash from text and repeat it to fill max_bits.
    Returns bit string of the repeated hash.
    """
    # Generate SHA512 hash from input text
    sha512_hash = hashlib.sha512(text.encode()).hexdigest()
    print(f"SHA512 Hash (hex): {sha512_hash}")
    
    # Convert hex hash to binary string
    hash_bits = bin(int(sha512_hash, 16))[2:].zfill(512)  # SHA512 produces 512 bits
    
    # Repeat the hash to fill the required bits
    repeated_hash = ""
    while len(repeated_hash) < max_bits:
        repeated_hash += hash_bits
    
    # Trim to exact required length
    return repeated_hash[:max_bits]

def embed_watermark(input_img_path, output_img_path, watermark_text):
    """
    Embed a digital watermark by repeating SHA512 hash throughout the image.
    """
    try:
        print("Membaca gambar sumber...")
        img = Image.open(input_img_path).convert("RGB")
        width, height = img.size
        
        # Calculate maximum capacity in bits
        max_capacity_bits = width * height * 3
        
        print(f"Generating watermark from: '{watermark_text}'")
        print(f"Kapasitas Maksimal Bit: {max_capacity_bits} bit")
        
        # Generate repeated hash bits
        watermark_bits = generate_watermark_hash(watermark_text, max_capacity_bits)
        
        # Get pixel data
        pixel_data = list(img.getdata())
        bit_index = 0
        new_pixel_data = []
        
        print("Menyisipkan watermark...")
        
        # Loop through each pixel
        for r, g, b in pixel_data:
            if bit_index < len(watermark_bits):
                # Modify LSB of Red component
                msg_bit = int(watermark_bits[bit_index])
                r = (r & 0xFE) | msg_bit
                bit_index += 1
            
            if bit_index < len(watermark_bits):
                # Modify LSB of Green component
                msg_bit = int(watermark_bits[bit_index])
                g = (g & 0xFE) | msg_bit
                bit_index += 1

            if bit_index < len(watermark_bits):
                # Modify LSB of Blue component
                msg_bit = int(watermark_bits[bit_index])
                b = (b & 0xFE) | msg_bit
                bit_index += 1
            
            new_pixel_data.append((r, g, b))
            
            if bit_index >= len(watermark_bits):
                break
        
        # Add remaining unmodified pixels
        new_pixel_data.extend(pixel_data[len(new_pixel_data):])
        
        # Create new image with embedded watermark
        watermarked_img = Image.new(img.mode, img.size)
        watermarked_img.putdata(new_pixel_data)
        
        print(f"Menulis ke {output_img_path}...")
        watermarked_img.save(output_img_path)
        print("Sukses! Watermark tersimpan.")
        
        # Return the original hash for verification purposes
        original_hash = hashlib.sha512(watermark_text.encode()).hexdigest()
        return original_hash
        
    except Exception as e:
        print(f"Error pada embedding watermark: {e}")
        return None

def extract_watermark_hash(input_img_path):
    """
    Extract the repeated hash bits from the watermarked image.
    Returns the extracted bits as a string.
    """
    try:
        print("Membaca gambar dengan watermark...")
        img = Image.open(input_img_path).convert("RGB")
        width, height = img.size
        
        # Calculate maximum capacity in bits
        max_capacity_bits = width * height * 3
        
        # Get pixel data
        pixel_data = list(img.getdata())
        
        extracted_bits = ""
        bit_index = 0
        
        print("Mengekstrak watermark hash...")
        
        # Loop through each pixel
        for r, g, b in pixel_data:
            if bit_index >= max_capacity_bits:
                break
                
            # Extract LSB from Red component
            extracted_bits += str(r & 1)
            bit_index += 1
            
            if bit_index >= max_capacity_bits:
                break
                
            # Extract LSB from Green component
            extracted_bits += str(g & 1)
            bit_index += 1
            
            if bit_index >= max_capacity_bits:
                break
                
            # Extract LSB from Blue component
            extracted_bits += str(b & 1)
            bit_index += 1
        
        # Since we fill the entire image, we get all bits
        print(f"Berhasil mengekstrak {len(extracted_bits)} bit")
        
        # The first 512 bits should be the hash (repeated)
        if len(extracted_bits) >= 512:
            first_hash_bits = extracted_bits[:512]
            # Convert bits to hex for display
            hash_hex = hex(int(first_hash_bits, 2))[2:].zfill(128)
            return extracted_bits, hash_hex
        else:
            return extracted_bits, None
            
    except Exception as e:
        print(f"Error pada ekstraksi watermark: {e}")
        return None, None

def verify_watermark_comprehensive(input_img_path, watermark_text):
    """
    Verify if the watermark in the image matches the given text.
    Check ALL repeated hash instances throughout the image.
    """
    try:
        print(f"Memverifikasi watermark dengan teks: '{watermark_text}'")
        
        # Generate expected hash from the provided text
        expected_hash = hashlib.sha512(watermark_text.encode()).hexdigest()
        expected_bits = bin(int(expected_hash, 16))[2:].zfill(512)
        
        print(f"Hash yang diharapkan (hex): {expected_hash}")
        print(f"Hash yang diharapkan (panjang bit): {len(expected_bits)} bit")
        
        # Extract all bits from image
        extracted_bits, extracted_hex = extract_watermark_hash(input_img_path)
        
        if not extracted_bits:
            print("Gagal mengekstrak watermark dari gambar.")
            return False
        
        total_bits = len(extracted_bits)
        print(f"Total bit yang diekstrak: {total_bits}")
        
        # Calculate how many complete hash blocks we have
        num_blocks = total_bits // 512
        print(f"Jumlah blok hash 512-bit yang dapat diperiksa: {num_blocks}")
        
        if num_blocks == 0:
            print("ERROR: Gambar tidak mengandung cukup data untuk satu hash lengkap!")
            return False
        
        # Analyze each hash block
        mismatched_blocks = 0
        corruption_report = []
        
        for block_num in range(num_blocks):
            start_idx = block_num * 512
            end_idx = start_idx + 512
            block_bits = extracted_bits[start_idx:end_idx]
            
            # Compare this block with expected hash
            if block_bits == expected_bits:
                # Perfect match
                pass
            else:
                mismatched_blocks += 1
                
                # Calculate bit error rate for this block
                errors = sum(1 for i in range(512) if block_bits[i] != expected_bits[i])
                error_percentage = (errors / 512) * 100
                
                # Store corruption info
                corruption_info = {
                    'block': block_num,
                    'errors': errors,
                    'error_percentage': error_percentage,
                    'position': f"Bit {start_idx}-{end_idx-1}"
                }
                corruption_report.append(corruption_info)
                
                if block_num == 0:
                    print(f"  Blok #{block_num}: {errors} bit berbeda ({error_percentage:.2f}%)")
        
        # Calculate overall statistics
        total_possible_matches = num_blocks
        matched_blocks = num_blocks - mismatched_blocks
        match_percentage = (matched_blocks / num_blocks) * 100
        
        print(f"\n=== HASIL VERIFIKASI KOMPREHENSIF ===")
        print(f"Total blok hash: {num_blocks}")
        print(f"Blok yang cocok: {matched_blocks}")
        print(f"Blok yang tidak cocok: {mismatched_blocks}")
        print(f"Persentase kecocokan: {match_percentage:.2f}%")
        
        if mismatched_blocks == 0:
            print("\n=== VERIFIKASI BERHASIL 100% ===")
            print("SEMUA instance hash cocok dengan watermark yang diberikan.")
            print("Gambar tidak terdeteksi mengalami modifikasi.")
            print("===================================\n")
            return True
        elif match_percentage > 80:  # Threshold for partial match
            print(f"\n=== VERIFIKASI SEBAGIAN ({match_percentage:.2f}%) ===")
            print(f"Watermark terdeteksi tetapi gambar mungkin telah dimodifikasi.")
            print(f"{mismatched_blocks} dari {num_blocks} blok hash rusak.")
            print("========================================\n")
            
            # Show details of corruption if there are few blocks
            if mismatched_blocks <= 10:
                print("Detail blok yang rusak:")
                for corrupt in corruption_report[:10]:  # Show first 10
                    print(f"  Blok #{corrupt['block']}: {corrupt['errors']} bit error ({corrupt['error_percentage']:.2f}%) pada {corrupt['position']}")
                if mismatched_blocks > 10:
                    print(f"  ... dan {mismatched_blocks - 10} blok lainnya")
            return "partial"
        else:
            print(f"\n=== VERIFIKASI GAGAL ===")
            print(f"Hanya {match_percentage:.2f}% watermark yang cocok.")
            print("Gambar mungkin bukan gambar asli atau telah sangat dimodifikasi.")
            print("==========================\n")
            
            # Show corruption details for debugging
            if corruption_report:
                print("Contoh blok yang rusak (maks 5):")
                for corrupt in corruption_report[:5]:
                    print(f"  Blok #{corrupt['block']}: {corrupt['errors']} bit error ({corrupt['error_percentage']:.2f}%)")
            return False
            
    except Exception as e:
        print(f"Error pada verifikasi watermark: {e}")
        return False

def analyze_watermark_integrity(input_img_path):
    """
    Analyze the watermark integrity without knowing the expected text.
    Check for consistency of repeated patterns.
    """
    try:
        print("Menganalisis integritas watermark...")
        
        # Extract all bits from image
        extracted_bits, extracted_hex = extract_watermark_hash(input_img_path)
        
        if not extracted_bits:
            print("Gagal mengekstrak watermark dari gambar.")
            return
        
        total_bits = len(extracted_bits)
        num_blocks = total_bits // 512
        
        if num_blocks < 2:
            print("Tidak cukup data untuk analisis konsistensi (minimal 2 blok hash diperlukan).")
            return
        
        print(f"Menganalisis {num_blocks} blok hash 512-bit...")
        
        # Compare each block with the first block
        first_block = extracted_bits[:512]
        inconsistencies = []
        
        for block_num in range(1, num_blocks):
            start_idx = block_num * 512
            end_idx = start_idx + 512
            block_bits = extracted_bits[start_idx:end_idx]
            
            if block_bits != first_block:
                errors = sum(1 for i in range(512) if block_bits[i] != first_block[i])
                error_percentage = (errors / 512) * 100
                inconsistencies.append({
                    'block': block_num,
                    'errors': errors,
                    'error_percentage': error_percentage
                })
        
        print(f"\n=== ANALISIS INTEGRITAS WATERMARK ===")
        print(f"Total blok hash: {num_blocks}")
        print(f"Blok yang konsisten dengan blok pertama: {num_blocks - len(inconsistencies)}")
        print(f"Blok yang tidak konsisten: {len(inconsistencies)}")
        
        if len(inconsistencies) == 0:
            print("✓ SEMUA blok hash identik. Watermark konsisten di seluruh gambar.")
            print("  Hash pertama (hex):", hex(int(first_block, 2))[2:].zfill(128)[:32] + "...")
        else:
            print("✗ Ditemukan inkonsistensi dalam watermark!")
            print(f"  {len(inconsistencies)} blok berbeda dari blok pertama.")
            
            # Show summary of inconsistencies
            max_errors = max(incons['errors'] for incons in inconsistencies)
            avg_errors = sum(incons['errors'] for incons in inconsistencies) / len(inconsistencies)
            print(f"  Rata-rata error per blok: {avg_errors:.1f} bit")
            print(f"  Error maksimum: {max_errors} bit")
            
            # Suggest possible issues
            if max_errors > 400:
                print("\n  KEMUNGKINAN: Gambar mungkin tidak memiliki watermark yang valid")
            elif max_errors > 100:
                print("\n  KEMUNGKINAN: Bagian gambar mungkin telah dimodifikasi secara signifikan")
            else:
                print("\n  KEMUNGKINAN: Noise atau kompresi mungkin mempengaruhi watermark")
        
        print("======================================\n")
        
    except Exception as e:
        print(f"Error pada analisis integritas: {e}")

# --- MAIN EXECUTION ---

def print_usage(prog_name):
    print("Penggunaan:")
    print(f"  python {prog_name} capacity <input.png/bmp>")
    print(f"  python {prog_name} watermark <input.png/bmp> <output.png/bmp> \"Watermark Text\"")
    print(f"  python {prog_name} verify <watermarked.png/bmp> \"Watermark Text\"")
    print(f"  python {prog_name} analyze <watermarked.png/bmp>")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage(sys.argv[0])
        sys.exit(1)

    mode = sys.argv[1].lower()
    
    if mode == "capacity": 
        if len(sys.argv) != 3:
            print("Error: Argumen capacity kurang.")
            print_usage(sys.argv[0])
            sys.exit(1)
            
        input_file = sys.argv[2]
        max_chars = get_max_capacity(input_file)
        
        print("\n=== Analisis Kapasitas Steganografi ===")
        print(f"File Sumber: {input_file}")
        print(f"Kapasitas Maksimal (Karakter): {max_chars} karakter")
        print(f"Kapasitas Maksimal (Bit): {max_chars * 8} bit")
        print("======================================\n")
    
    elif mode == "watermark":
        if len(sys.argv) != 5:
            print("Error: Argumen watermark kurang.")
            print_usage(sys.argv[0])
            sys.exit(1)
            
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        watermark_text = sys.argv[4]
        
        original_hash = embed_watermark(input_file, output_file, watermark_text)
        if original_hash:
            print(f"\n=== Watermark Berhasil Ditambahkan ===")
            print(f"Hash asli (simpan untuk verifikasi): {original_hash}")
            print("=======================================\n")
    
    elif mode == "verify":
        if len(sys.argv) != 4:
            print("Error: Argumen verify kurang.")
            print_usage(sys.argv[0])
            sys.exit(1)
            
        input_file = sys.argv[2]
        watermark_text = sys.argv[3]
        
        verify_watermark_comprehensive(input_file, watermark_text)
    
    elif mode == "analyze":
        if len(sys.argv) != 3:
            print("Error: Argumen analyze kurang.")
            print_usage(sys.argv[0])
            sys.exit(1)
            
        input_file = sys.argv[2]
        analyze_watermark_integrity(input_file)

    else:
        print_usage(sys.argv[0])
        sys.exit(1)
