# Latihan: RAG Agentik

Berlatih membangun asisten dokumen yang tahu kapan mencari, mengutip sumbernya, memilih revisi yang benar, menolak kalau tidak tahu, dan membuktikan semua itu dengan uji otomatis.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md)
- Sudah menjalankan kedua contoh kode di bab
- Memahami agen dan tool ([bab 2](../../hari3/02-tools-function-calling/README.md) dan [bab 3](../../hari3/03-agen/README.md)) serta konsep RAG dari workshop hari 2 (khususnya unit 3 tentang sitasi dan unit 5 tentang akses dokumen)

---

## Cara Mengerjakan

1. Buka starter latihan di folder bab ini (`.py` atau `.ipynb`). Setiap starter sudah lengkap kecuali bagian bertanda `TODO(B10.m)`.
2. Baca komentar `TODO` untuk tahu apa yang harus Anda isi, lalu coba tulis sendiri dulu.
3. Kalau sudah mencoba atau buntu, buka PDF bab ini (`10-agentic-rag.pdf` di folder yang sama), bagian **Kode Jawaban Latihan** di akhir. Di sana tertulis cell mana yang diubah dan kode yang harus disalin.
4. Jalankan cell berurutan dari atas ke bawah dan cocokkan hasilnya dengan daftar periksa di bawah.

---

## Latihan 1: Asisten SOP dengan Uji Otomatis

**File**: `latihan_1.py` dan `latihan_1.ipynb`

**Tujuan**: Membuat asisten dokumen untuk operator lapangan dan menguji perilakunya dengan enam pemeriksaan yang dilakukan di kode, bukan oleh model.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B10.1)` | buat agen RAG dengan bangun_agen_rag(model) |
| `TODO(B10.2)` | uji 2: tambahkan hasil periksa(...) yang meminta agen mencari, jawaban memuat '100 ppm', sitasi memuat SOP-HSE-001, dan tidak ada sitasi tidak valid |
| `TODO(B10.3)` | uji 3: jawaban memuat '10 ppm' dan tidak ada revisi yang diambil berstatus superseded |
| `TODO(B10.4)` | uji 6: INV-2026-011 tidak ada di r6.diambil dan agen menolak (r6.menolak) |

**Coba dengan**:

- Pengetahuan umum (tanpa mencari)
- Nilai IDLH H2S
- Konflik revisi SOP (Rev 3 vs Rev 2)
- Kode alarm F07 pada VSD
- Pertanyaan tak terjawab
- Dokumen terlarang untuk operator

**Kriteria keberhasilan**:

- Enam uji dicetak LOLOS atau GAGAL beserta rinciannya
- Uji SOP memeriksa angka, sitasi, dan revisi yang benar-benar diambil
- Dokumen investigasi HSE tidak pernah diambil untuk operator

---

## Latihan 2 (Bonus): RAG Percakapan

**File**: `latihan_2.py` dan `latihan_2.ipynb`

**Tujuan**: Menambahkan memori ke agen RAG agar pengguna bisa mengajukan follow-up question yang merujuk jawaban sebelumnya tanpa mengulang konteks.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B10.5)` | buat agen RAG percakapan: tool cari_dokumen, PROMPT_RAG ditambah izin pertanyaan lanjutan, context_schema=KonteksPengguna, dan checkpointer=InMemorySaver() |
| `TODO(B10.6)` | panggil agent.invoke dengan HumanMessage, config thread yang sama, dan context=konteks |
| `TODO(B10.7)` | hitung berapa kali cari_dokumen dipanggil pada pesan baru (AIMessage dengan tool_calls bernama cari_dokumen) |

**Kriteria keberhasilan**:

- Pertanyaan pertama mencari di dokumen
- "Dan bagaimana dengan batas LEL?" dijawab dalam konteks pekerjaan panas
- Pertanyaan ketiga menyebut dokumen dari giliran sebelumnya

---

## Daftar Periksa Pengumpulan

- [ ] Latihan 1: Asisten SOP dengan Uji Otomatis
- [ ] Latihan 2 (bonus, opsional): RAG Percakapan

---

## Butuh Bantuan?

- **Kode jawaban**: bagian Kode Jawaban Latihan pada PDF bab ini
- **Contoh yang mirip**: tinjau skrip di [`code/`](./code/)
- **Konsep belum jelas**: baca ulang [bab ini](./README.md)

---

## Langkah Selanjutnya

Setelah menyelesaikan latihan ini, Anda siap untuk:

**[Bab 11: Mini Project](../11-mini-project/README.md)**

Di bab terakhir Anda memilih use case dan membangun prototipe agen secara berkelompok pada template aplikasi chat.

[Kembali ke RAG Agentik](./README.md)
