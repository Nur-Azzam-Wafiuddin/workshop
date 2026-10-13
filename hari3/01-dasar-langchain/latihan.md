# Latihan: Dasar LangChain

Berlatih dengan tiga komponen dasar LangChain: percakapan dengan riwayat pesan, few-shot dengan template, dan structured output. Konsep umumnya sudah Anda pegang dari hari 1; fokus tugas ini adalah menuliskannya dengan LangChain.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md) dan menjalankan semua contoh kodenya
- Memahami daftar pesan, `ChatPromptTemplate`, dan `with_structured_output()`

---

## Cara Mengerjakan

1. Buka starter latihan di folder bab ini (`.py` atau `.ipynb`). Setiap starter sudah lengkap kecuali bagian bertanda `TODO(B1.m)`.
2. Baca komentar `TODO` untuk tahu apa yang harus Anda isi, lalu coba tulis sendiri dulu.
3. Kalau sudah mencoba atau buntu, buka PDF bab ini (`01-dasar-langchain.pdf` di folder yang sama), bagian **Kode Jawaban Latihan** di akhir. Di sana tertulis cell mana yang diubah dan kode yang harus disalin.
4. Jalankan cell berurutan dari atas ke bawah dan cocokkan hasilnya dengan daftar periksa di bawah.

---

## Latihan 1: Chatbot Serah Terima Shift

**File**: `latihan_1.py` dan `latihan_1.ipynb`

**Tujuan**: Membuat chatbot yang mengingat percakapan: setiap giliran ditambahkan ke daftar pesan lalu seluruhnya dikirim ke model.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B1.1)` | buat daftar messages berisi satu SystemMessage yang meminta asisten mencatat laporan operator, mengingatnya, dan menjawab ringkas dalam Bahasa Indonesia |
| `TODO(B1.2)` | tambahkan pesan pengguna (HumanMessage) ke riwayat messages |
| `TODO(B1.3)` | panggil model dengan seluruh riwayat messages |
| `TODO(B1.4)` | simpan jawaban model ke riwayat sebagai AIMessage agar giliran berikutnya bisa mengingatnya |

**Coba dengan**:

- Giliran 1: "Shift pagi: separator V-SR1-101 level controller hunting, ESP SR-020 stabil."
- Giliran 2: "Apa saja yang tadi saya laporkan?"

**Kriteria keberhasilan**:

- Giliran kedua dijawab dengan benar karena riwayat ikut dikirim
- Panjang percakapan bertambah dua pesan tiap giliran (pengguna dan asisten)

---

## Latihan 2: Few-Shot Format Teacher

**File**: `latihan_2.py` dan `latihan_2.ipynb`

**Tujuan**: Mengajari model format JSON khusus dari catatan work order lewat contoh (few-shot), lalu memvalidasi hasilnya dengan kode.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B1.5)` | buat template satu contoh (pesan human {input} dan pesan ai {output}), lalu bungkus bersama daftar contoh dengan FewShotChatMessagePromptTemplate |
| `TODO(B1.6)` | gabungkan prompt dan model dengan operator | |
| `TODO(B1.7)` | parse JSON, pastikan semua kunci di KUNCI_WAJIB ada dan downtime_jam berupa angka; raise ValueError bila tidak sesuai |

**Kriteria keberhasilan**:

- Model menghasilkan JSON dengan kunci aset, masalah, tindakan, dan downtime_jam untuk catatan baru
- Fungsi validasi menolak JSON yang kuncinya kurang atau downtime_jam bukan angka

---

## Latihan 3: Ekstraktor Data Suku Cadang

**File**: `latihan_3.py` dan `latihan_3.ipynb`

**Tujuan**: Mengubah deskripsi bebas dalam berbagai format menjadi objek Pydantic yang tervalidasi dengan structured output.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B1.8)` | definisikan field: nama, harga_juta_rupiah (opsional), kategori (Literal Elektrikal, Mekanikal, Instrumentasi, Kimia, Lainnya), stok_tersedia (opsional), peringkat_vendor (opsional, 1 sampai 5), dan spesifikasi (daftar string) |
| `TODO(B1.9)` | hubungkan prompt ke model.with_structured_output(SparePart, method="function_calling") |

**Kriteria keberhasilan**:

- Tiga deskripsi (katalog, pesan santai, informasi tidak lengkap) menjadi objek SparePart
- Informasi yang tidak disebut dibiarkan kosong, bukan ditebak

---

## Daftar Periksa Pengumpulan

- [ ] Latihan 1: Chatbot Serah Terima Shift
- [ ] Latihan 2: Few-Shot Format Teacher
- [ ] Latihan 3: Ekstraktor Data Suku Cadang

---

## Butuh Bantuan?

- **Kode jawaban**: bagian Kode Jawaban Latihan pada PDF bab ini
- **Contoh yang mirip**: tinjau skrip di [`code/`](./code/)
- **Konsep belum jelas**: baca ulang [bab ini](./README.md)

---

## Langkah Selanjutnya

Setelah menyelesaikan latihan ini, Anda siap untuk:

**[Function Calling dan Tools](../02-tools-function-calling/README.md)**
