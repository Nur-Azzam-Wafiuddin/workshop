# Latihan: Streaming Agen

Berlatih membangun interface yang menampilkan pekerjaan agen secara langsung: teks mengalir, baris status, progres dari dalam tool, dan layanan HTTP yang mengalirkan jawaban ke banyak klien.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md)
- Sudah menjalankan semua contoh kode di bab
- Memahami empat mode stream dan `get_stream_writer()`

---

## Cara Mengerjakan

1. Buka starter latihan di folder bab ini (`.py` atau `.ipynb`). Setiap starter sudah lengkap kecuali bagian bertanda `TODO(BS.m)`.
2. Baca komentar `TODO` untuk tahu apa yang harus Anda isi, lalu coba tulis sendiri dulu.
3. Kalau sudah mencoba atau buntu, buka PDF bab ini (`bonus-streaming-agen.pdf` di folder yang sama), bagian **Kode Jawaban Latihan** di akhir. Di sana tertulis cell mana yang diubah dan kode yang harus disalin.
4. Jalankan cell berurutan dari atas ke bawah dan cocokkan hasilnya dengan daftar periksa di bawah.

---

## Latihan 1: Asisten Operasi Langsung

**File**: `latihan_1.py` dan `latihan_1.ipynb`

**Tujuan**: Membuat asisten terminal dengan streaming: teks muncul kata demi kata, status tool tampil langsung, dan follow-up question berfungsi lewat memori.

| TODO | Yang Anda isi |
|---|---|
| `TODO(BS.1)` | buat tool audit_water_cut yang mengirim progres per sumur lewat get_stream_writer() (tunggu 0,7 detik per sumur) dan melaporkan sumur dengan water cut di atas 75% |
| `TODO(BS.2)` | buat agen dengan tool cek_status_sumur dan audit_water_cut, serta checkpointer=InMemorySaver() agar follow-up question berfungsi |
| `TODO(BS.3)` | alirkan agent.stream({"messages": [HumanMessage(content=teks)]}, config, stream_mode=["updates", "messages", "custom"]) |

**Coba dengan**:

- "Bagaimana status sumur SR-020?" lalu "Dan sumur ML-012?"
- "Jalankan audit water cut semua sumur dan beri tahu yang tinggi."
- "Dari dua sumur yang pertama saya tanyakan, mana yang produksi minyaknya lebih besar?"

**Kriteria keberhasilan**:

- Baris status tool muncul sebelum jawaban
- Progres audit tampil per sumur lewat aliran custom
- Pertanyaan lanjutan dijawab dari memori

---

## Latihan 2 (Bonus): Endpoint HTTP Streaming (SSE)

**File**: `latihan_2.py`

**Tujuan**: Membuat server web kecil, hanya dengan library standar Python, yang mengalirkan jawaban agen ke klien sebagai Server-Sent Events (SSE).

| TODO | Yang Anda isi |
|---|---|
| `TODO(BS.4)` | kembalikan satu Server-Sent Event: teks 'data: <JSON>' diakhiri dua baris baru, dalam bytes UTF-8 |
| `TODO(BS.5)` | alirkan AGEN.stream(..., stream_mode="messages"); untuk setiap chunk teks dari node model tulis event token ke self.wfile lalu flush; setelah selesai tulis event done |

**Coba dengan**:

- python hari3/bonus-streaming-agen/latihan_2.py --demo

**Kriteria keberhasilan**:

- Klien menerima event token satu per satu, lalu event done
- Setiap event didorong keluar segera (flush)
- Klien yang menutup koneksi tidak membuat server error

---

## Daftar Periksa Pengumpulan

- [ ] Latihan 1: Asisten Operasi Langsung
- [ ] Latihan 2 (bonus, opsional): Endpoint HTTP Streaming (SSE)

---

## Butuh Bantuan?

- **Kode jawaban**: bagian Kode Jawaban Latihan pada PDF bab ini
- **Contoh yang mirip**: tinjau skrip di [`code/`](./code/)
- **Konsep belum jelas**: baca ulang [bab ini](./README.md)

---

## Langkah Selanjutnya

Setelah menyelesaikan latihan ini, Anda siap untuk:

**[Bab 6: Persetujuan Manusia](../06-persetujuan-manusia/README.md)**
