"""Agen Anda: tiga keping puzzle. Ubah file ini, aplikasi (app.py) tidak perlu disentuh.

  KEPING 1  TOOLS       : tool apa yang boleh dipakai agen (pilih dari KATALOG di alat_data.py, atau tulis sendiri)
  KEPING 2  INSTRUKSI   : peran dan aturan agen (salin dan ubah dari prompt_bank.py, atau tulis sendiri)
  KEPING 3  PERSETUJUAN : tool mana yang berhenti menunggu manusia (interrupt), dan keputusan apa yang diizinkan

Aplikasi juga membaca empat nama lain dari file ini:

  JUDUL              : judul di bagian atas halaman
  PENGANTAR          : satu atau dua kalimat tentang apa yang bisa dilakukan agen
  CONTOH_PERTANYAAN  : pertanyaan contoh yang tampil di layar kosong
  buat_agen(...)     : fungsi yang mengembalikan agen (hasil create_agent); biasanya tidak diubah
  KASUS_UJI          : (opsional) daftar kasus untuk code/04_uji_cepat.py

Peran pengguna (operator, engineer, hse, management) dipilih di sidebar aplikasi, bukan di file ini.
Melihat semua tool yang tersedia: python hari4/11-mini-project/code/01_katalog_tool.py
"""
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware

from migas_shared.rag_tools import KonteksPengguna

from prompt_bank import PERTANYAAN, susun_prompt

# Keping yang sudah terpasang di bawah adalah contoh agen Perawatan yang hanya membaca. Ganti dengan use case kelompok Anda.
from alat_data import aset_downtime_tertinggi, riwayat_work_order, statistik_kegagalan
# from alat_data import buat_work_order, tutup_work_order            # tool TULIS Perawatan: wajib dipasangi KEPING 3
# from alat_data import KATALOG                                      # semua tool per use case: KATALOG["HSE"], dst.
# from migas_shared.rag_tools import cari_dokumen                    # pencarian SOP, manual, dan laporan

JUDUL = "Agen Saya"
PENGANTAR = "Titik awal mini project: susun tool, prompt, dan aturan persetujuan sesuai use case kelompok Anda."
CONTOH_PERTANYAAN = PERTANYAAN["Perawatan"]["baca"] + PERTANYAAN["Perawatan"]["multi"]

# KEPING 1 - Tool yang boleh dipakai agen.
TOOLS = [riwayat_work_order, statistik_kegagalan, aset_downtime_tertinggi]

# KEPING 2 - Peran dan aturan agen. susun_prompt(use_case, gaya) menggabungkan peran, aturan tool, dan gaya jawaban.
# Gaya yang tersedia: minimal, ketat, ramah, tabel, sitasi, hati_hati. Atau tulis sendiri INSTRUKSI = """..."""
INSTRUKSI = susun_prompt("Perawatan", "ketat")

# KEPING 3 - Tool yang harus disetujui manusia sebelum berjalan. Kosong berarti semua tool berjalan bebas.
# Contoh mengaktifkan (tool harus ada di TOOLS):
#   {"buat_work_order": {"allowed_decisions": ["approve", "edit", "reject"]}}
# Pilihan yang diizinkan per tool: approve (setuju), edit (ubah argumen), reject (tolak). Untuk tindakan yang
# tidak boleh diubah reviewer, hapus "edit".
PERSETUJUAN: dict = {}

# Kasus uji untuk code/04_uji_cepat.py. Tambahkan kasus untuk agen Anda (ambil pertanyaan dari PERTANYAAN).
# Kunci yang tersedia: nama, tanya, harus_tool, tanpa_tool, harus_ada, peran, keputusan ("setuju" atau "tolak"), tercatat.
KASUS_UJI = [
    {"nama": "riwayat aset dibaca dari data", "tanya": "Bagaimana riwayat work order sumur SR-020?",
     "harus_tool": ["riwayat_work_order"], "harus_ada": ["SR-020"]},
    {"nama": "aset tanpa data dijawab jujur", "tanya": PERTANYAAN["Perawatan"]["tanpa_data"][0],
     "harus_tool": ["riwayat_work_order"], "harus_ada": ["Tidak ada"]},
]


def buat_agen(model, checkpointer):
    # Model dan checkpointer disediakan aplikasi. Bagian ini biasanya tidak diubah.
    middleware = [HumanInTheLoopMiddleware(interrupt_on=PERSETUJUAN)] if PERSETUJUAN else []
    return create_agent(
        model,
        tools=TOOLS,
        system_prompt=INSTRUKSI,
        middleware=middleware,
        checkpointer=checkpointer,
        context_schema=KonteksPengguna,  # agen menerima peran pengguna dari aplikasi (dipakai tool cari_dokumen)
    )
