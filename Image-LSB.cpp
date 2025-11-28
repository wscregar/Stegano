#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cstdint>
#include <bitset>

// Header BMP standar biasanya 54 byte
const int BMP_HEADER_SIZE = 54;

/**
Membaca seluruh isi file ke dalam vector byte.
 */
std::vector<uint8_t> read_file(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Gagal membuka file: " + filename);
    }
    
    // Dapatkan ukuran file
    file.seekg(0, std::ios::end);
    size_t file_size = file.tellg();
    file.seekg(0, std::ios::beg);

    std::vector<uint8_t> data(file_size);
    file.read(reinterpret_cast<char*>(data.data()), file_size);
    return data;
}

/**
Menulis vector byte ke file baru.
 */
void write_file(const std::string& filename, const std::vector<uint8_t>& data) {
    std::ofstream file(filename, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Gagal membuat file output: " + filename);
    }
    file.write(reinterpret_cast<const char*>(data.data()), data.size());
}

/**
Menyisipkan pesan ke dalam data gambar BMP menggunakan teknik LSB.
 */
void encode_bmp(const std::string& input_bmp, const std::string& output_bmp, std::string message) {
    std::cout << "Membaca gambar sumber...\n";
    std::vector<uint8_t> img_data = read_file(input_bmp);

    // Validasi sederhana header BMP (2 byte pertama harus 'BM')
    if (img_data.size() < BMP_HEADER_SIZE || img_data[0] != 'B' || img_data[1] != 'M') {
        throw std::runtime_error("File bukan format BMP yang valid!");
    }

    // Dapatkan offset di mana data pixel dimulai (biasanya di byte ke-10 header)
    // Kita baca 4 byte integer dari posisi 10
    uint32_t data_offset = *reinterpret_cast<uint32_t*>(&img_data[10]);

    std::cout << "Data pixel dimulai pada byte ke: " << data_offset << "\n";

    // Tambahkan null terminator (\0) ke pesan agar decoder tahu kapan harus berhenti
    message += '\0'; 

    // Cek kapasitas gambar
    // Setiap karakter butuh 8 bit -> 8 byte gambar
    size_t max_capacity = (img_data.size() - data_offset) / 8;
    if (message.length() > max_capacity) {
        throw std::runtime_error("Pesan terlalu panjang untuk gambar ini! Kapasitas maks: " + std::to_string(max_capacity) + " karakter.");
    }

    std::cout << "Menyisipkan pesan (" << message.length() << " bytes)...\n";

    size_t pixel_idx = data_offset; // Mulai dari bagian data pixel

    for (char c : message) {
        // Proses setiap bit dari karakter (8 bit per char)
        for (int bit = 0; bit < 8; ++bit) {
            // Ambil bit ke-'bit' dari karakter c
            // Contoh: c='A' (01000001), bit 0 adalah 1, bit 1 adalah 0, dst (dari kanan/LSB ke kiri)
            // Catatan: Kita ambil dari bit 7 (MSB) ke 0 (LSB) atau sebaliknya.
            // Di sini kita urut dari bit 7 ke 0.
            int bit_val = (c >> (7 - bit)) & 1;

            // Modifikasi byte gambar:
            // 1. Bersihkan bit terakhir (LSB) byte gambar (gunakan AND 0xFE atau 11111110)
            img_data[pixel_idx] &= 0xFE;
            
            // 2. Masukkan bit pesan kita ke posisi LSB itu (gunakan OR)
            img_data[pixel_idx] |= bit_val;

            pixel_idx++; // Pindah ke byte gambar berikutnya
        }
    }

    std::cout << "Menulis ke " << output_bmp << "...\n";
    write_file(output_bmp, img_data);
    std::cout << "Sukses! Pesan tersimpan.\n";
}

/**
Mengekstrak pesan dari gambar BMP LSB.
 */
void decode_bmp(const std::string& input_bmp) {
    std::vector<uint8_t> img_data = read_file(input_bmp);

    if (img_data.size() < BMP_HEADER_SIZE || img_data[0] != 'B' || img_data[1] != 'M') {
        throw std::runtime_error("File bukan format BMP yang valid!");
    }

    uint32_t data_offset = *reinterpret_cast<uint32_t*>(&img_data[10]);
    size_t pixel_idx = data_offset;
    
    std::string extracted_message = "";
    char current_char = 0;
    int bit_count = 0;

    std::cout << "Mencoba mendekode pesan...\n";

    // Loop sampai akhir data gambar
    while (pixel_idx < img_data.size()) {
        // Ambil LSB dari byte gambar saat ini
        int lsb = img_data[pixel_idx] & 1;

        // Masukkan bit ini ke current_char
        // Geser char ke kiri, lalu masukkan LSB di posisi paling kanan
        current_char = (current_char << 1) | lsb;
        
        bit_count++;

        // Jika sudah terkumpul 8 bit, kita punya 1 karakter utuh
        if (bit_count == 8) {
            // Cek apakah ini null terminator (akhir pesan)
            if (current_char == '\0') {
                break; // Stop decoding
            }

            extracted_message += current_char;
            
            // Reset untuk karakter berikutnya
            bit_count = 0;
            current_char = 0;
        }

        pixel_idx++;
    }

    std::cout << "=== Pesan Rahasia ===\n";
    std::cout << extracted_message << "\n";
    std::cout << "=====================\n";
}


/**
Panduan untuk penggunaan.
 */
void print_usage(const char* prog_name) {
    std::cerr << "Penggunaan:\n";
    std::cerr << "  " << prog_name << " encode <input.bmp> <output.bmp> \"Pesan Rahasia\"\n";
    std::cerr << "  " << prog_name << " decode <input_with_secret.bmp>\n";
}

int main(int argc, char* argv[]) {
    try {
        if (argc < 2) {
            print_usage(argv[0]);
            return 1;
        }

        std::string mode = argv[1];
        std::vector<std::string> args;
        for(int i=0; i<argc; i++) args.push_back(argv[i]);

        if (mode == "encode") {
            if (argc != 5) {
                std::cerr << "Error: Argumen encode kurang.\n";
                print_usage(argv[0]);
                return 1;
            }
            encode_bmp(args[2], args[3], args[4]);
        } 
        else if (mode == "decode") {
            if (argc != 3) {
                std::cerr << "Error: Argumen decode kurang.\n";
                print_usage(argv[0]);
                return 1;
            }
            decode_bmp(args[2]);
        } 
        else {
            print_usage(argv[0]);
            return 1;
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }

    return 0;

}
