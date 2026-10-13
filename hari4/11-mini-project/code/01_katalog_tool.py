# %% [markdown]
# # Contoh 1: Katalog Tool (Keping Puzzle 1)
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/11-mini-project/code/01_katalog_tool.py`
#
# Keping puzzle pertama adalah tool. Bab ini menyediakan katalog tool untuk empat use case (Operasi, Perawatan,
# HSE, Engineering) di `aplikasi/alat_data.py`. Anda memilih tool dari katalog, atau menulis sendiri, lalu memberikannya
# ke agen. Contoh ini:
#
# 1. mencetak isi katalog: tool apa saja, dan mana yang BACA dan mana yang TULIS
# 2. memanggil beberapa tool langsung dengan `.invoke()`, tanpa model, dan memeriksa hasilnya di kode
# 3. memastikan masukan yang tidak dikenal menghasilkan pesan jelas, bukan error
# 4. memastikan tool tulis hanya mencatat ke memori (`CATATAN_TINDAKAN`), sehingga aman dicoba berulang kali
#
# Kalau tool salah, agen sebesar apa pun tidak akan menolong. Karena itu tool diuji dulu sebelum diberikan ke agen.

# %%
# Langkah 1 - Mengimpor katalog dan fungsi pemeriksa
import sys

from migas_shared.config import ROOT

sys.path.insert(0, str(ROOT / "hari4" / "11-mini-project" / "aplikasi"))

import alat_data as a


def periksa(nama: str, hasil: str, harus_ada: str) -> None:
    status = "LOLOS" if harus_ada.lower() in hasil.lower() else "GAGAL"
    print(f"   [{status}] {nama}")
    for baris in hasil.splitlines()[:3]:
        print(f"           {baris[:118]}")

# %% [markdown]
# ## Langkah 2 - Isi katalog
# `KATALOG` adalah dictionary: nama use case menjadi daftar tool. `jenis_tool()` menandai tool BACA atau TULIS.
# Tool TULIS mengubah sesuatu, jadi di sistem nyata ia harus dipasangi persetujuan manusia (keping puzzle ke-3).

# %%
for use_case, daftar in a.KATALOG.items():
    print(f"{use_case} ({len(daftar)} tool)")
    for t in daftar:
        print(f"   [{a.jenis_tool(t):<5}] {t.name:<28}{t.description.splitlines()[0][:78]}")

# %% [markdown]
# ## Langkah 3 - Tool yang dipakai bersama
# Satu tool boleh masuk ke banyak use case. Daftar ini dihitung kode dari `KATALOG`.

# %%
dipakai: dict[str, list[str]] = {}
for use_case, daftar in a.KATALOG.items():
    for t in daftar:
        dipakai.setdefault(t.name, []).append(use_case)
print("Tool yang dipakai lebih dari satu use case:")
for nama, daftar_use_case in dipakai.items():
    if len(daftar_use_case) > 1:
        print(f"   {nama:<20}{', '.join(daftar_use_case)}")

# %% [markdown]
# ## Langkah 4 - Tool baca
# Setiap tool dipanggil langsung dengan `.invoke({...})`, lalu hasilnya diperiksa memuat kata kunci yang benar.
# Tool `cari_dokumen` tidak dipanggil di sini karena membutuhkan konteks pengguna dari agen (lihat bab 7).

# %%
print("Tool baca")
periksa("riwayat_work_order(SR-020)", a.riwayat_work_order.invoke({"asset_id": "SR-020", "maks": 2}), "SR-020")
periksa("aset_downtime_tertinggi(3)", a.aset_downtime_tertinggi.invoke({"maks": 3}), "KN-112")
periksa("ringkasan_insiden()", a.ringkasan_insiden.invoke({}), "Total 120 insiden")
periksa("laporan_harian(2026-07-14)", a.laporan_harian.invoke({"tanggal": "2026-07-14"}), "LCV macet")
periksa("bandingkan_produksi(10 dan 14 Juli)", a.bandingkan_produksi.invoke({"tanggal_a": "2026-07-10", "tanggal_b": "2026-07-14"}), "deferred +320")
periksa("hari_berkejadian(3)", a.hari_berkejadian.invoke({"maks": 3}), "12 hari berkejadian")

# %% [markdown]
# ## Langkah 5 - Masukan yang tidak dikenal
# Aset, tanggal, atau nomor yang tidak ada harus menghasilkan pesan jelas, bukan error. Agen akan menyampaikan
# pesan ini apa adanya, jadi pesannya harus dapat dipahami pengguna.

# %%
print("Masukan yang tidak dikenal")
periksa("riwayat_work_order(XX-999)", a.riwayat_work_order.invoke({"asset_id": "XX-999"}), "Tidak ada work order")
periksa("laporan_harian(2026-08-05)", a.laporan_harian.invoke({"tanggal": "2026-08-05"}), "Tidak ada laporan")
periksa("bandingkan_produksi(Agustus)", a.bandingkan_produksi.invoke({"tanggal_a": "2026-07-10", "tanggal_b": "2026-08-14"}), "Tidak ada laporan")
periksa("tutup_work_order(WO-XX)", a.tutup_work_order.invoke({"wo_id": "WO-XX", "catatan": "uji"}), "tidak ditemukan")

# %% [markdown]
# ## Langkah 6 - Tool tulis
# Tool tulis hanya mencatat ke memori, jadi aman dicoba berulang kali. Nomor `-UJI-` menunjukkan bahwa semua tool tulis
# berbagi satu daftar catatan; daftar inilah yang nanti dipakai uji untuk memeriksa apakah sebuah tindakan benar-benar terjadi.

# %%
print("Tool tulis (hanya mencatat di memori)")
sebelum = len(a.CATATAN_TINDAKAN)
periksa("buat_work_order", a.buat_work_order.invoke({"asset_id": "V-SR1-101", "uraian": "Periksa LCV", "prioritas": "sedang"}), "WO-UJI-001")
periksa("tutup_work_order", a.tutup_work_order.invoke({"wo_id": "WO-26-12115", "catatan": "pulling motor selesai"}), "TUTUP-UJI-002")
periksa("kirim_notifikasi_hse", a.kirim_notifikasi_hse.invoke({"penerima": "Supervisor HSE", "pesan": "Alarm H2S SR-027"}), "NOTIF-UJI-003")
periksa("ubah_setpoint_vsd(58 Hz)", a.ubah_setpoint_vsd.invoke({"kode_sumur": "SR-020", "frekuensi_hz": 58}), "PERINGATAN")
print(f"   Catatan tindakan bertambah {len(a.CATATAN_TINDAKAN) - sebelum}: {[c['nomor'] for c in a.CATATAN_TINDAKAN]}")

# %% [markdown]
# ## Ide Utama
# - Katalog memberi keping siap pakai per use case; Anda boleh memilih sebagian, menggabung dari beberapa use case, atau menulis tool sendiri
# - Uji tool dengan `.invoke({...})` sebelum memberikannya ke agen
# - Masukan yang tidak dikenal harus menghasilkan pesan jelas agar agen bisa menyampaikannya apa adanya
# - Tool tulis di mini project hanya mencatat ke memori, tetapi di sistem nyata ia harus dipasangi persetujuan manusia
