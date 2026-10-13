# Latihan: Memori Agen dan Checkpointer

Berlatih memberi agen memori yang bertahan lintas sesi, memisahkan pengguna dengan thread, dan menjaga percakapan panjang tetap terkendali.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md)
- Sudah menjalankan semua contoh kode di bab
- Memahami checkpointer, `thread_id`, trimming, dan summarization

---

## Cara Mengerjakan

1. Buka starter latihan di folder bab ini (`.py` atau `.ipynb`). Setiap starter sudah lengkap kecuali bagian bertanda `TODO(B5.m)`.
2. Baca komentar `TODO` untuk tahu apa yang harus Anda isi, lalu coba tulis sendiri dulu.
3. Kalau sudah mencoba atau buntu, buka PDF bab ini (`05-memori-agen.pdf` di folder yang sama), bagian **Kode Jawaban Latihan** di akhir. Di sana tertulis cell mana yang diubah dan kode yang harus disalin.
4. Jalankan cell berurutan dari atas ke bawah dan cocokkan hasilnya dengan daftar periksa di bawah.

---

## Latihan 1: Asisten Serah Terima Shift dengan Memori Persisten

**File**: `latihan_1.py` dan `latihan_1.ipynb`

**Tujuan**: Membuat asisten yang mengingat setiap operator bahkan setelah program dimulai ulang, dengan memori di file SQLite (SqliteSaver) dan satu thread per operator.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B5.1)` | buka koneksi SQLite (check_same_thread=False), buat agen tanpa tool dengan checkpointer=SqliteSaver(connection), lalu kembalikan (agent, connection) |
| `TODO(B5.2)` | buat config dengan thread_id '<user>:<sesi>', panggil agent.invoke, dan kembalikan teks jawaban terakhir |
| `TODO(B5.3)` | kembalikan jumlah pesan pada state thread itu lewat agent.get_state(config) |

**Coba dengan**:

- Jalan 1: Rina memperkenalkan diri dan menyebut jam tersibuknya
- Jalan 2: program dimulai ulang, Rina bertanya apa yang tadi ia katakan

**Kriteria keberhasilan**:

- Setelah dimulai ulang, riwayat Rina dimuat dan pertanyaan dijawab dari ingatan
- Agus belum punya riwayat; sesi baru Rina juga kosong
- Jumlah pesan tersimpan bisa dibaca dari state thread

---

## Latihan 2 (Bonus): Membandingkan Strategi Memori

**File**: `latihan_2.py` dan `latihan_2.ipynb`

**Tujuan**: Menjalankan percakapan berskrip yang sama dengan tiga strategi memori (simpan semua, pangkas, ringkas) lalu membandingkan jumlah pesan, token, dan apakah fakta awal masih diingat.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B5.4)` | buat middleware @before_model simpan_terbaru yang menyisakan SIMPAN_TERAKHIR pesan terakhir (hapus sisanya dengan RemoveMessage(id=REMOVE_ALL_MESSAGES)) |
| `TODO(B5.5)` | buat tiga agen tanpa tool, masing-masing dengan InMemorySaver: 'simpan semua' (tanpa middleware), 'pangkas ke N' (middleware simpan_terbaru), dan 'ringkas' (SummarizationMiddleware dengan trigger ('messages', 6) dan keep ('messages', 2)) |

**Kriteria keberhasilan**:

- Tiga agen berjalan dengan percakapan yang sama
- Tabel perbandingan memperlihatkan pesan, perkiraan token, dan ingatan nomor PTW
- Strategi pangkas menyisakan SIMPAN_TERAKHIR pesan

---

## Daftar Periksa Pengumpulan

- [ ] Latihan 1: Asisten Serah Terima Shift dengan Memori Persisten
- [ ] Latihan 2 (bonus, opsional): Membandingkan Strategi Memori

---

## Butuh Bantuan?

- **Kode jawaban**: bagian Kode Jawaban Latihan pada PDF bab ini
- **Contoh yang mirip**: tinjau skrip di [`code/`](./code/)
- **Konsep belum jelas**: baca ulang [bab ini](./README.md)

---

## Langkah Selanjutnya

Setelah menyelesaikan latihan ini, Anda siap untuk:

**[Bab 6: Persetujuan Manusia](../06-persetujuan-manusia/README.md)**

Bab bonus [Streaming Agen](../bonus-streaming-agen/README.md) (mengalirkan token dan langkah tool) bisa dikerjakan kapan saja setelah bab ini.
