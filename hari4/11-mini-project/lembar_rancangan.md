# Lembar Rancangan Mini Project

Salin lembar ini, isi sendiri atau bersama kelompok sebelum menyusun agen. Satu halaman cukup. Contoh isian ada pada baris berhuruf miring.

## 1. Identitas

| Isian | Jawaban kelompok |
|-------|------------------|
| Nama kelompok dan anggota | |
| Nama agen (nama file di `aplikasi/agen/`) | *contoh: `kelompok_a`* |

## 2. Use case

| Isian | Jawaban kelompok |
|-------|------------------|
| Bidang | Operations, Maintenance, HSE, atau Engineering |
| Masalah yang diselesaikan, satu kalimat | *contoh: perencana menghabiskan 30 menit membuka riwayat work order sebelum menyusun pekerjaan baru* |
| Pengguna agen dan perannya | *contoh: perencana pemeliharaan (peran `engineer`)* |
| Hasil yang diharapkan pengguna | *contoh: ringkasan riwayat aset dalam kurang dari satu menit, dan draf work order* |

## 3. Data, integrasi, keamanan

Jawab dengan jujur, satu atau dua kalimat. Penjelasan dan contohnya ada di [bab Mini Project](./README.md#bagian-1-memilih-use-case).

| Hal | Jawaban kelompok |
|-----|------------------|
| **Data**: data apa yang dipakai dan apakah sudah ada di `data/`? | *contoh: riwayat work order, `data/raw/work_orders.csv` sudah ada* |
| **Integrasi**: tool dari katalog mana yang dipakai, dan tool baru apa yang perlu ditulis? | *contoh: `riwayat_work_order` dan `buat_work_order` dari katalog; tidak perlu tool baru* |
| **Keamanan**: apa akibatnya kalau agen salah, dan tindakan mana yang bisa mengubah sesuatu? | *contoh: work order salah aset; hanya `buat_work_order` yang menulis, dan wajib persetujuan* |

## 4. Tiga keping puzzle

### Keping 1: Tool

| Tool | Membaca atau menulis | Sumber data | Dari katalog atau ditulis sendiri |
|------|----------------------|-------------|-----------------------------------|
| *contoh: `riwayat_work_order`* | *membaca* | *`data/raw/work_orders.csv`* | *katalog* |
| | | | |
| | | | |

Dokumen yang perlu dicari agen (SOP, manual, laporan), bila ada:

### Keping 2: Prompt

| Isian | Jawaban kelompok |
|-------|------------------|
| Gaya dari bank prompt yang dipilih (minimal, ketat, ramah, tabel, sitasi, hati_hati) | *contoh: `hati_hati`* |
| Kalimat yang ditambahkan atau diubah sendiri | *contoh: "Selalu sebut nomor aset di awal jawaban."* |
| Gaya lain yang dicoba dan hasil perbandingannya | |

### Keping 3: Interrupt

| Tool tulis | Keputusan yang diizinkan (approve, edit, reject) | Alasan |
|------------|--------------------------------------------------|--------|
| *contoh: `buat_work_order`* | *approve, edit, reject* | *uraian dan prioritas bisa diperbaiki reviewer* |
| | | |

## 5. Risiko dan guardrail

| Risiko bila agen salah | Pagar yang dipasang (prompt, interrupt, batas tool, peran dokumen) |
|------------------------|--------------------------------------------------------------------|
| *contoh: work order dibuat untuk aset yang salah* | *persetujuan manusia, tampilkan argumen sebelum disetujui* |
| | |

## 6. Kasus uji (minimal 5 untuk `KASUS_UJI`)

Sertakan sedikitnya: satu pertanyaan yang dijawab dari data, satu pertanyaan yang harus dijawab "tidak ada" atau ditolak, satu tool tulis yang ditolak (`tercatat: 0`), dan satu tool tulis yang disetujui (`tercatat: 1`). Pertanyaan bisa diambil dari `PERTANYAAN` di `prompt_bank.py`.

| No | Pertanyaan | Tool yang harus dipanggil | Kata yang harus muncul atau efek yang diperiksa |
|----|------------|---------------------------|------------------------------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

## 7. Kriteria berhasil

Tuliskan satu kalimat yang bisa diperiksa, misalnya: "Semua kasus uji lolos dan satu permintaan work order bisa diubah reviewer sebelum disetujui."

---

[Kembali ke bab Mini Project](./README.md)
