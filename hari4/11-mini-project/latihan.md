# Latihan: Mini Project

## Gambaran Umum

Tugas bab ini adalah mini project itu sendiri, dikerjakan secara mandiri atau berkelompok: memilih use case, lalu menyusun agen sederhana dari tiga keping puzzle (tool, prompt, interrupt) di template aplikasi dan mengujinya. Semua bagian yang sudah Anda pelajari (tool, agen, memori, streaming, persetujuan manusia, guardrails, dan pencarian dokumen) dipakai lagi di sini.

## Prasyarat

- Sudah menyelesaikan [bab ini](./README.md) dan menjalankan keempat contoh kodenya
- Template aplikasi berjalan di laptop Anda: `streamlit run hari4/11-mini-project/aplikasi/app.py`
- Memahami tool dan agen ([bab 2](../../hari3/02-tools-function-calling/README.md) dan [bab 3](../../hari3/03-agen/README.md)), persetujuan manusia ([bab 6](../../hari3/06-persetujuan-manusia/README.md)), dan guardrails ([bab 7](../../hari3/07-guardrails-middleware/README.md))

---

## Tantangan 1: Lembar Rancangan

**Tujuan**: memilih use case dengan tiga pertanyaan (data, integrasi, keamanan), lalu menuliskan rancangannya sebelum menyusun agen.

**Tugas**:

1. Salin [lembar_rancangan.md](./lembar_rancangan.md) dan isi bersama kelompok
2. Pilih satu use case dari katalog (Operasi, Perawatan, HSE, atau Engineering), atau gabungkan tool dari beberapa use case
3. Jawab tiga pertanyaan di bagian 3 lembar: datanya ada, tool dari katalog mana yang dipakai, dan apa akibatnya kalau agen salah
4. Tetapkan tool tulis yang akan dipakai, dan keputusan persetujuan yang diizinkan untuk tiap tool tulis

**Kriteria keberhasilan**: lembar terisi lengkap, setiap jawaban punya alasan satu kalimat, dan setiap tool tulis punya aturan persetujuan.

---

## Tantangan 2: Rakit Agen dari Katalog

**Tujuan**: menyusun agen kelompok dengan hanya mengubah satu file di `aplikasi/agen/`, tanpa menyentuh `app.py`.

**Tugas**:

1. Salin `aplikasi/agen/saya.py` menjadi `aplikasi/agen/<nama_kelompok>.py`
2. **Keping 1:** ganti `TOOLS` dengan tool dari katalog yang sesuai lembar rancangan. Uji dulu tool yang belum Anda kenal dengan `.invoke({...})` seperti di [contoh 1](./README.md#contoh-1-katalog-tool)
3. **Keping 2:** ganti `INSTRUKSI`. Mulai dari `susun_prompt("<use case>", "<gaya>")`, lalu tambahkan sedikitnya satu kalimat aturan buatan kelompok yang menjawab risiko di lembar rancangan
4. **Keping 3:** isi `PERSETUJUAN` untuk setiap tool tulis. Pilih keputusan yang diizinkan berdasarkan tabel di bab (apakah reviewer boleh mengubah argumennya?)
5. Ubah `JUDUL`, `PENGANTAR`, dan `CONTOH_PERTANYAAN` (ambil dari `PERTANYAAN` di `prompt_bank.py` atau tulis sendiri)
6. Jalankan aplikasi, pilih agen kelompok di sidebar, dan coba ketiga contoh pertanyaan
7. Pastikan satu tool tulis berhenti di formulir persetujuan, dan coba keputusan yang diizinkan: Setujui, Ubah (bila diizinkan), dan Tolak

**Kriteria keberhasilan**: agen kelompok muncul di pilihan agen, tool tulis tidak berjalan sebelum disetujui, dan Anda bisa menjelaskan apa yang terjadi pada argumen saat memilih Ubah.

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

Docstring dibaca model untuk memutuskan kapan tool dipakai. Uji tool baru lebih dulu dengan `nama_tool.invoke({...})` sebelum memberikannya ke agen.

---

## Tantangan 3: Variasi Prompt dan Uji

**Tujuan**: membuktikan bahwa agen kelompok bekerja pada banyak kasus, dan memilih prompt dengan bukti.

**Tugas**:

1. Bandingkan dua gaya prompt pada agen kelompok: ubah `INSTRUKSI`, ajukan pertanyaan yang sama di aplikasi, dan catat perbedaan tool yang dipanggil dan isi jawaban. [Contoh 3](./README.md#contoh-3-variasi-prompt) bisa dijadikan acuan
2. Isi `KASUS_UJI` pada file agen kelompok dengan lima kasus dari lembar rancangan
3. Jalankan `python hari4/11-mini-project/code/04_uji_cepat.py` (isi `PILIHAN_AGEN = ["<nama_kelompok>"]` di sel pertama) dan perbaiki sampai semua lolos. Perbaiki yang tepat: prompt, deskripsi tool, atau aturan persetujuan
4. Jalankan skrip uji sekali lagi. Kalau hasilnya berbeda dari yang pertama, catat kasus yang tidak konsisten

**Kriteria keberhasilan**: semua kasus uji lolos (atau kasus yang gagal dijelaskan penyebabnya), dan kelompok bisa menyebut gaya prompt yang dipilih beserta alasannya.

---

## Tantangan Bonus: Riwayat yang Bertahan

**Tujuan**: membuat riwayat percakapan di sidebar tetap ada setelah aplikasi dihentikan.

**Tugas**:

1. Di `aplikasi/kerangka.py`, ganti `InMemorySaver` pada kelas `Penyimpanan` dengan checkpointer SQLite dari [bab 5](../../hari3/05-memori-agen/README.md)
2. Simpan juga daftar percakapan (`judul`, `agen`) ke file, misalnya JSON
3. Hentikan aplikasi, jalankan lagi, dan pastikan riwayat serta daftar percakapan masih ada

**Kriteria keberhasilan**: setelah restart, klik pada percakapan lama memuat kembali pesan-pesannya.

---

## Daftar Periksa Pengumpulan

- [ ] Lembar rancangan terisi, termasuk jawaban data, integrasi, dan keamanan
- [ ] File agen kelompok ada di `aplikasi/agen/` dan muncul di aplikasi
- [ ] Tool dipilih dari katalog (atau ditulis sendiri), prompt punya aturan buatan kelompok
- [ ] Setiap tool tulis memiliki aturan persetujuan
- [ ] Minimal lima `KASUS_UJI`, termasuk satu penolakan dan satu tool tulis ditolak
- [ ] `04_uji_cepat.py` dijalankan dan hasilnya dicatat

---

## Solusi

Agen contoh yang sudah jadi ada di [`solusi/agen_contoh/`](./solusi/agen_contoh/) (operasi, perawatan, hse, engineering) dan [`solusi/investigasi_sumur.py`](./solusi/investigasi_sumur.py): tool baru yang menggabungkan tiga sumber data, pencarian dokumen, dan persetujuan manusia. Coba kerjakan sendiri dulu.

---

## Butuh Bantuan?

- **Template tidak mau jalan**: lihat bagian Pemecahan Masalah di [bab ini](./README.md)
- **Agen memilih tool yang salah**: tinjau deskripsi tool dan prompt, lalu baca ulang [bab 2](../../hari3/02-tools-function-calling/README.md)
- **Persetujuan tidak muncul**: tinjau [bab 6](../../hari3/06-persetujuan-manusia/README.md)

---

## Langkah Selanjutnya

Bab ini adalah bab terakhir kursus. Setelah agen Anda berjalan, tulis tiga hal dari proyek Anda: apa yang berhasil, apa yang masih rapuh, dan apa yang akan Anda tambahkan lebih dulu sebelum agen dipakai di lapangan.

[Kembali ke Mini Project](./README.md)
