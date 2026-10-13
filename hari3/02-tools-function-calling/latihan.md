# Latihan: Function Calling dan Tools

Berlatih membuat tool, mengikatnya ke model, dan menjalankan siklus eksekusi tiga langkah. Anda juga membangun sistem yang memiliki beberapa tool dan membiarkan model memilih yang tepat.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md)
- Sudah menjalankan semua contoh kode
- Memahami pola tiga langkah: membuat, menjalankan, menjawab

---

## Cara Mengerjakan

1. Buka starter latihan di folder bab ini (`.py` atau `.ipynb`). Setiap starter sudah lengkap kecuali bagian bertanda `TODO(B2.m)`.
2. Baca komentar `TODO` untuk tahu apa yang harus Anda isi, lalu coba tulis sendiri dulu.
3. Kalau sudah mencoba atau buntu, buka PDF bab ini (`02-tools-function-calling.pdf` di folder yang sama), bagian **Kode Jawaban Latihan** di akhir. Di sana tertulis cell mana yang diubah dan kode yang harus disalin.
4. Jalankan cell berurutan dari atas ke bawah dan cocokkan hasilnya dengan daftar periksa di bawah.

---

## Latihan 1: Tool Konversi Satuan dengan Siklus Eksekusi Lengkap

**File**: `latihan_1.py` dan `latihan_1.ipynb`

**Tujuan**: Membuat tool konversi satuan dan menjalankan siklus tiga langkah sendiri: model merencanakan pemanggilan, kode menjalankan tool, model menjawab.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B2.1)` | definisikan skema masukan: nilai (float), dari dan ke (Literal bbl, m3, psi, bar, scf) |
| `TODO(B2.2)` | kembalikan teks hasil konversi dari tabel FAKTOR; satuan sama dikembalikan apa adanya; pasangan yang tidak ada di FAKTOR dikembalikan sebagai pesan yang menyebut pasangan yang didukung |
| `TODO(B2.3)` | ikat tool konversi_satuan ke model dengan bind_tools |
| `TODO(B2.4)` | jalankan tool dengan argumen dari pemanggilan model |
| `TODO(B2.5)` | kirim hasil tool kembali ke model sebagai ToolMessage dengan tool_call_id yang sesuai |

**Coba dengan**:

- "Tekanan wellhead SR-020 adalah 1500 psi. Berapa bar?"
- "Ubah 100 bar menjadi bbl." (pasangan tidak valid)

**Kriteria keberhasilan**:

- Dua konversi dalam satu pertanyaan dijalankan keduanya
- Pasangan satuan yang tidak didukung ditolak dengan pesan yang menyebut pasangan yang didukung

---

## Latihan 2 (Bonus): Asisten Pemeriksaan Sumur dengan Banyak Tool

**File**: `latihan_2.py` dan `latihan_2.ipynb`

**Tujuan**: Menggabungkan tool lapangan dari paket bersama dengan satu tool baru, lalu menjalankan loop: model meminta tool, kode menjalankan, ulangi sampai model menjawab dengan teks.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B2.6)` | buat skema KehilanganInput (minyak_bopd dan hari_henti, keduanya >= 0) dan tool estimasi_kehilangan_produksi yang mengalikan keduanya |
| `TODO(B2.7)` | panggil model yang sudah diikat tool dengan daftar messages |
| `TODO(B2.8)` | simpan permintaan tool dari model ke messages sebagai AIMessage yang membawa tool_calls |
| `TODO(B2.9)` | cari tool di PETA_TOOL menurut nama pemanggilan, lalu jalankan dengan argumennya |
| `TODO(B2.10)` | kirim hasil tool ke model sebagai ToolMessage |

**Coba dengan**:

- "Bagaimana kondisi sumur SR-020, dan berapa water cut-nya?"
- "Sumur KN-033 menunggu pulling selama 12 hari. Jika produksi normalnya 45 bopd, berapa produksi yang hilang?"

**Kriteria keberhasilan**:

- Model memilih sendiri tool yang tepat untuk tiap pertanyaan
- Tool yang gagal dilaporkan ke model sebagai teks, bukan menghentikan program

---

## Daftar Periksa Pengumpulan

- [ ] Latihan 1: Tool Konversi Satuan dengan Siklus Eksekusi Lengkap
- [ ] Latihan 2 (bonus, opsional): Asisten Pemeriksaan Sumur dengan Banyak Tool

---

## Butuh Bantuan?

- **Kode jawaban**: bagian Kode Jawaban Latihan pada PDF bab ini
- **Contoh yang mirip**: tinjau skrip di [`code/`](./code/)
- **Konsep belum jelas**: baca ulang [bab ini](./README.md)

---

## Langkah Selanjutnya

Setelah menyelesaikan latihan ini, Anda siap untuk:

**[Bab 3: Memulai dengan Agen](../03-agen/README.md)**

Di bab itu, loop eksekusi yang baru Anda tulis dengan tangan dikerjakan otomatis oleh `create_agent()`.
