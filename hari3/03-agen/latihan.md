# Latihan: Agen dengan Pola ReAct

Berlatih membangun agen AI otonom dengan pola ReAct, dan membuat sistem multi-tool tempat agen memutuskan sendiri tool mana yang dipakai dan kapan.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md)
- Sudah menjalankan semua contoh kode di bab
- Memahami pola ReAct dan loop agen
- Sudah menyelesaikan bab [Function Calling dan Tools](../02-tools-function-calling/README.md)

---

## Cara Mengerjakan

1. Buka starter latihan di folder bab ini (`.py` atau `.ipynb`). Setiap starter sudah lengkap kecuali bagian bertanda `TODO(B3.m)`.
2. Baca komentar `TODO` untuk tahu apa yang harus Anda isi, lalu coba tulis sendiri dulu.
3. Kalau sudah mencoba atau buntu, buka PDF bab ini (`03-agen.pdf` di folder yang sama), bagian **Kode Jawaban Latihan** di akhir. Di sana tertulis cell mana yang diubah dan kode yang harus disalin.
4. Jalankan cell berurutan dari atas ke bawah dan cocokkan hasilnya dengan daftar periksa di bawah.

---

## Latihan 1: Agen Analis Produksi

**File**: `latihan_1.py` dan `latihan_1.ipynb`

**Tujuan**: Membangun agen dengan create_agent() yang menjawab pertanyaan yang butuh data sumur, perhitungan, dan pencarian dokumen.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B3.1)` | buat agen dengan create_agent: model, tools=[*TOOL_LAPANGAN, cari_dokumen], system_prompt analis produksi (angka dari tool, hitungan dari tool, prosedur dari cari_dokumen dengan menyebut ID dokumen), dan context_schema=KonteksPengguna |
| `TODO(B3.2)` | panggil agent.invoke dengan HumanMessage dan context=KonteksPengguna(role="engineer") |

**Coba dengan**:

- "Sumur SR-020 dan ML-012: berapa total produksi minyak keduanya, dan berapa water cut masing-masing?"
- "Berapa produksi minyak SR-020 dalam meter kubik per hari?"
- "Menurut SOP H2S yang berlaku, apa tindakan saat alarm tingkat 2 berbunyi di wellhead?"

**Kriteria keberhasilan**:

- Agen memutuskan sendiri tool mana yang dipakai untuk tiap pertanyaan
- Keluaran konsol memperlihatkan tool yang dipakai
- Jawaban dari dokumen menyebut ID dokumennya

---

## Latihan 2 (Bonus): Agen Perencana Pekerjaan Pulling

**File**: `latihan_2.py` dan `latihan_2.ipynb`

**Tujuan**: Membangun agen dengan beberapa tool khusus yang menuntut reasoning bertahap: jadwal rig, perkiraan biaya, dan produksi yang hilang.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B3.3)` | buat tool cek_jadwal_rig(kode_sumur) yang mengembalikan berapa hari lagi rig tersedia dari JADWAL_RIG, atau pesan bila sumur tidak ada di jadwal |
| `TODO(B3.4)` | buat tool estimasi_kehilangan_produksi(minyak_bopd, hari) yang mengalikan keduanya dan menyebut hasil dalam bbl |
| `TODO(B3.5)` | buat agen dengan keempat tool dan system prompt perencana yang meminta rencana langkah demi langkah serta asumsi bila data tidak ada |

**Coba dengan**:

- "Rencanakan pulling sumur KN-033: kapan rig tersedia, berapa kira-kira biayanya, dan berapa produksi hilang selama menunggu jika produksi normalnya 45 bopd?"

**Kriteria keberhasilan**:

- Agen memakai tiga tool atau lebih untuk satu permintaan
- Urutan pemakaian tool masuk akal (jadwal rig dulu, baru kehilangan produksi)
- Jawaban menyatakan asumsi yang dipakai

---

## Daftar Periksa Pengumpulan

- [ ] Latihan 1: Agen Analis Produksi
- [ ] Latihan 2 (bonus, opsional): Agen Perencana Pekerjaan Pulling

---

## Butuh Bantuan?

- **Kode jawaban**: bagian Kode Jawaban Latihan pada PDF bab ini
- **Contoh yang mirip**: tinjau skrip di [`code/`](./code/)
- **Konsep belum jelas**: baca ulang [bab ini](./README.md)

---

## Langkah Selanjutnya

Setelah menyelesaikan latihan ini, Anda siap untuk:

**[Bab 4: Structured Output pada Agen](../04-keluaran-terstruktur-agen/README.md)**
