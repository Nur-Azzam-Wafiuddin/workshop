# Latihan: Sistem Multi-Agen

Berlatih membangun tim agen: spesialis yang dibungkus sebagai tool, konteks tepercaya yang diteruskan tanpa disentuh model, izin akses yang dipasang di kode, dan pengukuran biaya tim.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md)
- Sudah menjalankan semua contoh kode di bab
- Memahami agen supervisor dan spesialis, `ToolRuntime`, dan konteks runtime
- Sudah menyelesaikan bab [Memulai dengan Agen](../../hari3/03-agen/README.md)

---

## Cara Mengerjakan

1. Buka starter latihan di folder bab ini (`.py` atau `.ipynb`). Setiap starter sudah lengkap kecuali bagian bertanda `TODO(B8.m)`.
2. Baca komentar `TODO` untuk tahu apa yang harus Anda isi, lalu coba tulis sendiri dulu.
3. Kalau sudah mencoba atau buntu, buka PDF bab ini (`08-sistem-multi-agen.pdf` di folder yang sama), bagian **Kode Jawaban Latihan** di akhir. Di sana tertulis cell mana yang diubah dan kode yang harus disalin.
4. Jalankan cell berurutan dari atas ke bawah dan cocokkan hasilnya dengan daftar periksa di bawah.

---

## Latihan 1: Tim Koordinator

**File**: `latihan_1.py` dan `latihan_1.ipynb`

**Tujuan**: Membangun koordinator yang memakai tiga agen spesialis sebagai tool, dengan area dan peran pengguna dari konteks runtime serta akses Engineering yang dibatasi di kode.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B8.1)` | buat tool tanya_spesialis_operasi(permintaan, runtime: ToolRuntime[KonteksPengguna]) yang meneruskan permintaan ke agen_operasi dengan awalan area dari runtime.context.area |
| `TODO(B8.2)` | buat tool tanya_spesialis_engineering yang menolak peran selain engineer dan management di kode (kembalikan pesan 'Akses ditolak'), lalu meneruskan permintaan ke agen_engineering |
| `TODO(B8.3)` | buat agen koordinator dengan ketiga tool wrapper, context_schema=KonteksPengguna, dan system prompt: tidak memegang data sendiri, tanya spesialis yang relevan, laporkan akses ditolak, jangan mengarang angka |
| `TODO(B8.4)` | panggil tim.invoke dengan pesan pengguna, context=konteks, dan config={"callbacks": [handler]} untuk menghitung token |

**Coba dengan**:

- Engineer: "Bagaimana status sumur SR-020?"
- Operator: "Sumur mana yang bermasalah dan kapan jadwal pulling berikutnya?"
- Engineer dan operator: "Beri saya status sumur, work order terbuka, dan water cut ..."

**Kriteria keberhasilan**:

- Koordinator hanya menanyakan spesialis yang relevan
- Operator ditolak oleh kode saat meminta analisis Engineering
- Jumlah token tim dilaporkan untuk tiap pertanyaan

---

## Latihan 2 (Bonus): Tim yang Mengembalikan Hasil Bertipe

**File**: `latihan_2.py` dan `latihan_2.ipynb`

**Tujuan**: Menggabungkan structured output dengan multi-agen: tiap spesialis mengembalikan temuan bertipe, supervisor menggabungkannya menjadi LaporanShift, lalu Python biasa memutuskan tindakannya.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B8.5)` | definisikan field TemuanOperasi: sumur_bermasalah (daftar kode sumur) dan jadwal_pulling_berikutnya (satu frasa pendek) |
| `TODO(B8.6)` | definisikan field TemuanPemeliharaan: wo_prioritas_tinggi (daftar deskripsi singkat) dan total_wo_terbuka (int) |
| `TODO(B8.7)` | definisikan field LaporanShift: prioritas_keseluruhan (Literal normal, perhatian, mendesak dengan aturan di description), isu_utama, dan tindakan_disarankan (daftar string) |
| `TODO(B8.8)` | buat spesialis Operasi dengan dua tool-nya dan response_format=TemuanOperasi |
| `TODO(B8.9)` | buat supervisor dengan kedua tool wrapper dan response_format=LaporanShift; system prompt meminta menanyakan KEDUA spesialis dan memuat aturan prioritas mendesak |

**Kriteria keberhasilan**:

- Laporan berupa objek LaporanShift dengan prioritas normal, perhatian, atau mendesak
- Spesialis yang lupa menghasilkan hasil bertipe tidak menjatuhkan seluruh tim
- Keputusan akhir diambil dengan if biasa pada prioritas_keseluruhan

---

## Daftar Periksa Pengumpulan

- [ ] Latihan 1: Tim Koordinator
- [ ] Latihan 2 (bonus, opsional): Tim yang Mengembalikan Hasil Bertipe

---

## Butuh Bantuan?

- **Kode jawaban**: bagian Kode Jawaban Latihan pada PDF bab ini
- **Contoh yang mirip**: tinjau skrip di [`code/`](./code/)
- **Konsep belum jelas**: baca ulang [bab ini](./README.md)

---

## Langkah Selanjutnya

Setelah menyelesaikan latihan ini, Anda siap untuk:

**[Bab 9: Model Context Protocol (MCP)](../09-mcp/README.md)**

Di bab berikutnya Anda menghubungkan agen ke layanan eksternal. Bab bonus [Agen SQL](../bonus-agen-sql/README.md) (agen yang menjelajahi database dan menulis SQL dengan aman) bisa dikerjakan kapan saja.

[Kembali ke Sistem Multi-Agen](./README.md)
