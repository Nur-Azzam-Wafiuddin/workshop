# Latihan: Persetujuan Manusia

Berlatih menaruh manusia sebagai pengendali tindakan berisiko: aturan persetujuan berbeda untuk setiap tool, audit log, dan persetujuan yang bertahan lebih lama dari program.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md)
- Sudah menjalankan semua contoh kode di bab
- Memahami `HumanInTheLoopMiddleware`, `__interrupt__`, dan `Command(resume=...)`

---

## Cara Mengerjakan

1. Buka starter latihan di folder bab ini (`.py` atau `.ipynb`). Setiap starter sudah lengkap kecuali bagian bertanda `TODO(B6.m)`.
2. Baca komentar `TODO` untuk tahu apa yang harus Anda isi, lalu coba tulis sendiri dulu.
3. Kalau sudah mencoba atau buntu, buka PDF bab ini (`06-persetujuan-manusia.pdf` di folder yang sama), bagian **Kode Jawaban Latihan** di akhir. Di sana tertulis cell mana yang diubah dan kode yang harus disalin.
4. Jalankan cell berurutan dari atas ke bawah dan cocokkan hasilnya dengan daftar periksa di bawah.

---

## Latihan 1: Asisten Operasi yang Aman

**File**: `latihan_1.py` dan `latihan_1.ipynb`

**Tujuan**: Membuat agen operasi dengan empat tool dan aturan persetujuan berbeda untuk masing-masing, dengan reviewer berskrip dan audit log.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B6.1)` | isi KEBIJAKAN per tool: baca_status_peralatan False; jadwalkan_perawatan dan pesan_suku_cadang approve/edit/reject; shutdown_darurat hanya approve/reject |
| `TODO(B6.2)` | kembalikan keputusan reviewer: edit jumlah pesanan menjadi MAKS_JUMLAH_PESANAN bila lebih besar, reject shutdown_darurat dengan pesan agar dikonfirmasi manajer jaga, selain itu approve |
| `TODO(B6.3)` | pasang HumanInTheLoopMiddleware(interrupt_on=KEBIJAKAN) pada agen |
| `TODO(B6.4)` | lanjutkan agen dengan Command(resume={"decisions": keputusan_daftar}) dan config yang sama |

**Coba dengan**:

- "Periksa peralatan di GS-SR1. Lalu jadwalkan perawatan ... pesan 10 unit seal pompa ... dan jika ada yang tampak berbahaya, lakukan shutdown darurat."

**Kriteria keberhasilan**:

- Tool baca tidak pernah bertanya; tool lain berhenti menunggu keputusan
- Pesanan di atas batas diubah (edit) oleh reviewer; shutdown ditolak
- Setiap keputusan tercatat di audit log

---

## Latihan 2 (Bonus): Persetujuan yang Bertahan Lebih Lama dari Program

**File**: `latihan_2.py` dan `latihan_2.ipynb`

**Tujuan**: Memisahkan pengajuan dan persetujuan ke dua proses berbeda: agen berhenti di interrupt, keadaannya tersimpan di SQLite, lalu dilanjutkan oleh objek agen baru.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B6.5)` | buka koneksi SQLite (check_same_thread=False), buat agen dengan tool pesan_suku_cadang, HumanInTheLoopMiddleware(interrupt_on={"pesan_suku_cadang": True}), dan checkpointer=SqliteSaver(connection); kembalikan (agent, connection) |
| `TODO(B6.6)` | ambil aksi pertama yang menunggu dari result["__interrupt__"][0].value["action_requests"] |
| `TODO(B6.7)` | muat antrean, tambahkan entri thread_id berisi tool, args, dan permintaan, lalu simpan kembali |
| `TODO(B6.8)` | lanjutkan thread tersimpan dengan Command(resume={"decisions": [keputusan]}) dan config thread itu |

**Kriteria keberhasilan**:

- submit menyimpan permintaan yang menunggu ke antrean JSON lalu selesai
- decide memakai objek agen baru dan tetap bisa melanjutkan thread tersimpan
- Permintaan pertama disetujui, kedua ditolak dengan alasan

---

## Daftar Periksa Pengumpulan

- [ ] Latihan 1: Asisten Operasi yang Aman
- [ ] Latihan 2 (bonus, opsional): Persetujuan yang Bertahan Lebih Lama dari Program

---

## Butuh Bantuan?

- **Kode jawaban**: bagian Kode Jawaban Latihan pada PDF bab ini
- **Contoh yang mirip**: tinjau skrip di [`code/`](./code/)
- **Konsep belum jelas**: baca ulang [bab ini](./README.md)

---

## Langkah Selanjutnya

Setelah menyelesaikan latihan ini, Anda siap untuk:

**[Bab 7: Guardrails dan Middleware Keamanan](../07-guardrails-middleware/README.md)**
