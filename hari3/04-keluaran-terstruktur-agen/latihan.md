# Latihan: Structured Output pada Agen

Berlatih membuat agen yang mengembalikan data bertipe dan tervalidasi: nested model, aturan validasi, dan memilih skema yang tepat dengan `Union`.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md)
- Sudah menjalankan semua contoh kode di bab
- Memahami `response_format`, `Literal`, dan nested model Pydantic

---

## Cara Mengerjakan

1. Buka starter latihan di folder bab ini (`.py` atau `.ipynb`). Setiap starter sudah lengkap kecuali bagian bertanda `TODO(B4.m)`.
2. Baca komentar `TODO` untuk tahu apa yang harus Anda isi, lalu coba tulis sendiri dulu.
3. Kalau sudah mencoba atau buntu, buka PDF bab ini (`04-keluaran-terstruktur-agen.pdf` di folder yang sama), bagian **Kode Jawaban Latihan** di akhir. Di sana tertulis cell mana yang diubah dan kode yang harus disalin.
4. Jalankan cell berurutan dari atas ke bawah dan cocokkan hasilnya dengan daftar periksa di bawah.

---

## Latihan 1: Ekstraktor Laporan Insiden

**File**: `latihan_1.py` dan `latihan_1.ipynb`

**Tujuan**: Mengubah catatan lapangan yang berantakan menjadi LaporanInsiden nested yang tervalidasi, lewat agen dengan response_format.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B4.1)` | definisikan field Korban: peran (str) dan cedera (Literal Tidak ada, Pertolongan pertama, Perawatan medis, Hilang hari kerja) |
| `TODO(B4.2)` | definisikan field LaporanInsiden: lokasi, jam_kejadian (opsional), uraian (maksimal 200 karakter), korban (daftar Korban), tindakan_segera (daftar string), dan klasifikasi (KlasifikasiInsiden) |
| `TODO(B4.3)` | buat agen tanpa tool dengan system prompt yang melarang menebak jam atau korban, dan response_format=LaporanInsiden |
| `TODO(B4.4)` | ambil hasil terstruktur dari response (kunci structured_response) |

**Coba dengan**:

- Baut jatuh dari pipe rack tanpa korban (jam disebut samar)
- Hose hidrolik pecah di KN-061 dengan satu korban luka bakar ringan

**Kriteria keberhasilan**:

- Hasil berupa objek LaporanInsiden dengan daftar Korban dan KlasifikasiInsiden
- Jam atau korban yang tidak disebut dibiarkan kosong, bukan ditebak
- Uraian tidak lebih dari 200 karakter

---

## Latihan 2 (Bonus): Agen Triase Cerdas

**File**: `latihan_2.py` dan `latihan_2.ipynb`

**Tujuan**: Menggabungkan tool pencari riwayat, Union skema (WOExtract atau KlasifikasiInsiden), dan keputusan eskalasi yang diambil oleh kode Python biasa.

| TODO | Yang Anda isi |
|---|---|
| `TODO(B4.5)` | buat tool riwayat_work_order(asset_id) yang menghitung jumlah work order, total downtime, dan kategori kegagalan terbanyak dari _WO; kembalikan pesan bila aset tidak punya riwayat |
| `TODO(B4.6)` | buat agen dengan tool riwayat_work_order, system prompt pemilah pesan, dan response_format=ToolStrategy(Union[WOExtract, KlasifikasiInsiden]) |
| `TODO(B4.7)` | kembalikan keputusan eskalasi dengan kode biasa: WOExtract dengan safety_flag atau downtime 24 jam ke atas, KlasifikasiInsiden dengan severity Tinggi, selain itu rutin |

**Coba dengan**:

- ESP SR-020 trip OL, motor burnt, downtime 5 jam
- K-ML1-201 gasket flange bocor dengan alarm LEL menyala
- Pekerja jatuh dari scaffold, patah tulang lengan

**Kriteria keberhasilan**:

- Agen memilih skema yang sesuai isi pesan
- Keputusan eskalasi diambil oleh kode, bukan oleh model
- Pesan perbaikan memanggil riwayat_work_order lebih dulu

---

## Daftar Periksa Pengumpulan

- [ ] Latihan 1: Ekstraktor Laporan Insiden
- [ ] Latihan 2 (bonus, opsional): Agen Triase Cerdas

---

## Butuh Bantuan?

- **Kode jawaban**: bagian Kode Jawaban Latihan pada PDF bab ini
- **Contoh yang mirip**: tinjau skrip di [`code/`](./code/)
- **Konsep belum jelas**: baca ulang [bab ini](./README.md)

---

## Langkah Selanjutnya

Setelah menyelesaikan latihan ini, Anda siap untuk:

**[Bab 5: Memori Agen dan Checkpointer](../05-memori-agen/README.md)**
