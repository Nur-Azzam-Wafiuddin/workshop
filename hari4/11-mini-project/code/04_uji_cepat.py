# %% [markdown]
# # Contoh 4: Uji Cepat Agen
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/11-mini-project/code/04_uji_cepat.py`
#
# Agen yang terlihat bagus pada satu pertanyaan belum tentu bagus pada sepuluh pertanyaan. Setiap file di
# `aplikasi/agen/` boleh memuat daftar `KASUS_UJI`. Skrip ini menjalankan semua kasus dan memeriksa HASILNYA DI KODE:
#
# - `harus_tool`: tool-tool ini harus dipanggil
# - `tanpa_tool`: tool-tool ini tidak boleh dipanggil (misalnya tool tulis tanpa diminta)
# - `peran`: peran pengguna untuk kasus ini (default engineer), menentukan dokumen yang boleh dibaca
# - `harus_ada`: kata atau angka yang harus muncul pada jawaban
# - `keputusan`: 'setuju' atau 'tolak' (default tolak): jawaban reviewer berskrip kalau agen meminta persetujuan
# - `tercatat`: berapa catatan tindakan yang harus bertambah (0 berarti tool tulis tidak boleh berjalan)
#
# Kasus "tercatat" memeriksa efek nyata pada data, bukan hanya apa yang diklaim agen dalam jawabannya.
#
# Sel pertama berisi `PILIHAN_AGEN`: daftar agen yang diuji. Bawaannya `saya` (agen Anda di `aplikasi/agen/saya.py`)
# dan `perawatan` (agen contoh jadi di `solusi/agen_contoh/`, sebagai gambaran kasus uji yang lengkap). Ganti dengan
# nama file agen kelompok Anda. Daftar kosong berarti semua agen di `aplikasi/agen/` yang punya `KASUS_UJI`.

# %%
# Langkah 1 - Memilih agen yang diuji
import sys

from langgraph.checkpoint.memory import InMemorySaver

from migas_shared.config import ROOT

sys.path.insert(0, str(ROOT / "hari4" / "11-mini-project" / "aplikasi"))

import kerangka as k

PILIHAN_AGEN = ["saya", "perawatan"]  # nama file agen (tanpa .py); kosong = semua agen di agen/ yang punya KASUS_UJI

pilihan = PILIHAN_AGEN or [n for n in k.daftar_agen() if getattr(k.muat_definisi(n), "KASUS_UJI", [])]
print(f"Agen yang diuji: {pilihan}")

# %% [markdown]
# ## Langkah 2 - Menjalankan semua kasus uji
# Setiap kasus diperiksa di kode: tool yang dipanggil, kata pada jawaban, dan catatan tindakan yang bertambah.

# %%
total = lolos = 0
for nama in pilihan:
    modul, agen = k.bangun_agen(nama, InMemorySaver())
    daftar = getattr(modul, "KASUS_UJI", [])
    print(f"Agen {nama} ({len(daftar)} kasus)")
    if not daftar:
        print("   belum ada KASUS_UJI di file agen ini\n")
        continue
    for i, kasus in enumerate(daftar, 1):
        gagal = k.jalankan_kasus(agen, kasus, f"uji-{nama}-{i}")
        total += 1
        lolos += not gagal
        print(f"   [{'LOLOS' if not gagal else 'GAGAL'}] {kasus['nama']}")
        for g in gagal:
            print(f"           - {g}")
    print()

print(f"Hasil: {lolos} dari {total} kasus lolos")

# %% [markdown]
# ## Ide Utama
# - Uji agen dengan banyak kasus yang diperiksa kode, bukan dengan membaca satu jawaban yang tampak bagus
# - Periksa efek nyata (tool dipanggil, data tercatat), jangan hanya percaya kalimat jawaban
# - Kasus yang gagal menunjukkan apa yang harus diperbaiki: instruksi, deskripsi tool, atau aturan persetujuan
