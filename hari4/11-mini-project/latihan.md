# Latihan: Mini Project

## Gambaran Umum

Tugas bab ini adalah mini project itu sendiri, dikerjakan secara mandiri atau berkelompok: memilih use case, menjelajahi tool dan prompt, merakit agen sederhana dari tiga keping puzzle (tool, prompt, interrupt) ditambah checkpointer di sel notebook, lalu mengobrol dengannya dan mengujinya. Semua bagian yang sudah Anda pelajari (tool, agen, memori, streaming, persetujuan manusia, guardrails, dan pencarian dokumen) dipakai lagi di sini.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md) dan menjalankan kelima contoh kodenya
- Ketiga aplikasi Streamlit (Penjelajah, Aplikasi agen, Panduan uji) bisa dinyalakan dari sel notebook
- Memahami tool dan agen ([bab 2](../../hari3/02-tools-function-calling/README.md) dan [bab 3](../../hari3/03-agen/README.md)), persetujuan manusia ([bab 6](../../hari3/06-persetujuan-manusia/README.md)), dan guardrails ([bab 7](../../hari3/07-guardrails-middleware/README.md))

---

## Tantangan 1: Lembar Rancangan

**Tujuan**: memilih use case dengan tiga pertanyaan (data, integrasi, keamanan), lalu menuliskan rancangannya sebelum menyusun agen.

**Tugas**:

1. Salin [lembar_rancangan.md](./lembar_rancangan.md) dan isi bersama kelompok
2. Jelajahi tool di aplikasi Penjelajah, lalu pilih satu use case dari katalog (Operasi, Perawatan, HSE, atau Engineering), atau gabungkan tool dari beberapa use case
3. Jawab tiga pertanyaan di bagian 3 lembar: datanya ada, tool dari katalog mana yang dipakai, dan apa akibatnya kalau agen salah
4. Tetapkan tool tulis yang akan dipakai, dan keputusan persetujuan yang diizinkan untuk tiap tool tulis

**Kriteria keberhasilan**: lembar terisi lengkap, setiap jawaban punya alasan satu kalimat, dan setiap tool tulis punya aturan persetujuan.

---

## Tantangan 2: Rakit Agen dari Katalog

**Tujuan**: menyusun agen kelompok dengan mengisi ketiga TODO di [contoh 3](./README.md#contoh-3-merakit-agen-anda-sendiri-todo), tanpa menyentuh file aplikasi.

**Tugas**:

1. **TODO(M.1) TOOLS:** di tab **Pilih tool** pada Penjelajah, centang tool sesuai lembar rancangan, lalu tempel snippet kodenya. Uji tool yang belum Anda kenal lewat formulir **Coba sendiri**
2. **TODO(M.2) checkpointer:** buat checkpointer penyimpan memori (lihat Contoh 2)
3. **TODO(M.3) agen:** rakit agen dengan `create_agent(...)`. Tempel teks system prompt dari tab **Prompt** (atau tulis sendiri, dengan sedikitnya satu kalimat aturan buatan kelompok yang menjawab risiko di lembar rancangan), dan tuliskan sendiri `HumanInTheLoopMiddleware(interrupt_on={...})` untuk tool tulis. Pilih keputusan yang diizinkan berdasarkan tabel di bab (apakah reviewer boleh mengubah argumennya?)
4. Baca keluaran sel `Periksa` dan perbaiki semua yang bertanda `BELUM`
5. Daftarkan agen (ubah `JUDUL`, `PENGANTAR`, dan `CONTOH_PERTANYAAN` bila perlu), lalu nyalakan aplikasi agen di Contoh 4
6. Ajukan satu pertanyaan baca. Buka **Aksi 1** dan cocokkan argumennya dengan pertanyaan Anda
7. Minta satu tindakan tulis dan pastikan formulir persetujuan muncul sebelum tool berjalan. Coba Setujui, Ubah (bila diizinkan), dan Tolak pada tiga percakapan berbeda

**Kriteria keberhasilan**: agen muncul di aplikasi, tool tulis tidak berjalan sebelum disetujui, dan Anda bisa menjelaskan apa yang terjadi pada argumen saat memilih Ubah serta apa yang dibaca model saat memilih Tolak.

**Bonus**: tulis satu tool buatan sendiri dengan `@tool`, misalnya tool yang menggabungkan dua sumber data (lihat `solusi/investigasi_sumur.py`), lalu tambahkan ke `TOOLS`.

**Petunjuk**:

```python
from langchain.tools import tool

@tool(parse_docstring=True)
def nama_tool(argumen: str) -> str:
    """Satu kalimat yang menjelaskan KAPAN tool ini dipakai.

    Args:
        argumen: Penjelasan argumen dengan contoh nilai.
    """
    ...
```

Docstring dibaca model untuk memutuskan kapan tool dipakai. Uji tool baru lebih dulu dengan `nama_tool.invoke({...})` sebelum memberikannya ke agen. Tool buatan sendiri tidak muncul di Penjelajah atau Panduan uji; tambahkan saja ke `TOOLS`.

---

## Tantangan 3: Variasi Prompt dan Uji

**Tujuan**: membuktikan bahwa agen kelompok bekerja pada banyak pertanyaan, dan memilih prompt dengan bukti.

**Tugas**:

1. Buka Panduan uji dan pilih tool yang sama dengan `TOOLS` agen Anda
2. Jalankan sedikitnya satu pertanyaan dari setiap jenis (baca, gabungan, tulis, data tidak ada, di luar cakupan) di aplikasi agen, dan centang kriteria yang terpenuhi
3. Untuk setiap kriteria yang tidak terpenuhi, catat penyebabnya: prompt, deskripsi tool, aturan persetujuan, atau tool yang kurang
4. Lakukan satu eksperimen di bagian bawah Panduan uji (misalnya mengganti gaya prompt). Daftarkan ulang agen dan ajukan pertanyaan yang sama pada dua versi. Catat perbedaan jejaknya (tool yang dipanggil, urutan Aksi, panjang dan isi jawaban)
5. Perbaiki sampai kriteria terpenuhi, atau jelaskan mengapa kriteria tertentu tidak realistis untuk rancangan Anda
6. Ulangi pertanyaan yang sama dua kali. Bila hasilnya berbeda, catat sebagai kelemahan yang perlu dijaga

**Kriteria keberhasilan**: kelompok bisa menunjukkan kriteria yang sebelumnya gagal lalu terpenuhi setelah perbaikan, menyebut gaya prompt yang dipilih beserta bukti dari jejak, dan menjelaskan satu kelemahan yang belum teratasi.

---

## Tantangan Bonus: Riwayat yang Bertahan

**Tujuan**: membuat riwayat percakapan tetap ada setelah notebook dimulai ulang.

**Tugas**:

1. Di sel TODO(M.2), ganti `InMemorySaver` dengan checkpointer SQLite dari [bab 5](../../hari3/05-memori-agen/README.md)
2. Daftarkan agen, mengobrol, lalu mulai ulang kernel dan jalankan sel TODO lagi
3. Pastikan `thread_id` percakapan lama masih bisa dibaca dengan `agen.get_state(...)`

**Kriteria keberhasilan**: setelah restart, state percakapan lama dapat dibaca kembali. Menampilkannya di sidebar aplikasi butuh menyimpan daftar percakapan juga; itu bagian dari tantangan lanjutan.

---

## Daftar Periksa Pengumpulan

- [ ] Lembar rancangan terisi, termasuk jawaban data, integrasi, dan keamanan
- [ ] Sel TODO terisi dan keluaran sel `Periksa` tidak menampilkan `BELUM`
- [ ] Tool dipilih dari katalog (atau ditulis sendiri), prompt punya aturan buatan kelompok
- [ ] Setiap tool tulis memiliki aturan persetujuan
- [ ] Sedikitnya satu pertanyaan dari tiap jenis di Panduan uji dijalankan, dengan kriteria yang dicentang
- [ ] Satu eksperimen dilakukan dan perbandingan dua versi agen dicatat

---

## Solusi

Kunci jawaban TODO ada di bagian **Kode Jawaban Latihan** pada akhir PDF bab ini, dan versi lengkapnya di [`solusi/agen_saya.py`](./solusi/agen_saya.py). Agen contoh lain ada di [`solusi/agen_contoh/`](./solusi/agen_contoh/) (operasi, perawatan, hse, engineering) dan [`solusi/investigasi_sumur.py`](./solusi/investigasi_sumur.py): tool baru yang menggabungkan tiga sumber data, pencarian dokumen, dan persetujuan manusia. Coba kerjakan sendiri dulu.

---

## Butuh Bantuan?

- **Aplikasi tidak mau menyala**: lihat bagian Pemecahan Masalah di [bab ini](./README.md)
- **Agen memilih tool yang salah**: buka jejaknya, lalu tinjau deskripsi tool dan prompt, dan baca ulang [bab 2](../../hari3/02-tools-function-calling/README.md)
- **Persetujuan tidak muncul**: periksa nama tool pada `interrupt_on` dan pastikan `HumanInTheLoopMiddleware` ada di `middleware`, lalu tinjau [bab 6](../../hari3/06-persetujuan-manusia/README.md)

---

## Langkah Selanjutnya

Bab ini adalah bab terakhir kursus. Setelah agen Anda berjalan, tulis tiga hal dari proyek Anda: apa yang berhasil, apa yang masih rapuh, dan apa yang akan Anda tambahkan lebih dulu sebelum agen dipakai di lapangan.

[Kembali ke Mini Project](./README.md)
