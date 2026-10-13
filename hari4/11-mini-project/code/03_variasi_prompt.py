# %% [markdown]
# # Contoh 3: Variasi Prompt (Keping Puzzle 2)
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/11-mini-project/code/03_variasi_prompt.py`
#
# Keping puzzle ke-2 adalah prompt (`INSTRUKSI`). `aplikasi/prompt_bank.py` menyediakan variasi gaya jawaban:
# `minimal` (hanya peran), `ketat`, `ramah`, `tabel`, dan `hati_hati`. Contoh ini membangun lima agen dengan TOOLS dan
# PERSETUJUAN yang SAMA, hanya prompt-nya yang berbeda, lalu mengajukan tiga pertanyaan yang sama ke semuanya:
#
# 1. pertanyaan multi-langkah: apakah semua agen memakai tool yang sama, dan seberapa panjang jawabannya?
# 2. pertanyaan di luar cakupan: bagaimana cara agen menolak?
# 3. permintaan tindakan tulis yang kurang detail: apakah agen menebak lalu memanggil tool tulis, mencari tahu sendiri, atau bertanya dulu?
#
# Hasil dilihat dari kode (tool yang dipanggil, panjang jawaban, ada tabel atau tidak) dan dari awal jawabannya.
# Model yang kuat sering sudah berhati-hati bahkan tanpa aturan, jadi perbedaannya bisa halus: lihat terutama tool yang
# dipanggil dan panjang jawaban.
# Ini bukan lomba mencari prompt terbaik. Tujuannya melihat bahwa perubahan prompt mengubah perilaku, lalu memilih
# variasi yang cocok dengan use case Anda. Jawaban model dapat berbeda setiap kali dijalankan.

# %%
# Langkah 1 - Mengimpor komponen
import sys

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from migas_shared.config import ROOT
from migas_shared.llm import get_chat_model
from migas_shared.rag_tools import KonteksPengguna

sys.path.insert(0, str(ROOT / "hari4" / "11-mini-project" / "aplikasi"))

import alat_data as a
import kerangka as k
from prompt_bank import GAYA, PERTANYAAN, susun_prompt

# %% [markdown]
# ## Langkah 2 - Isi bank gaya
# Setiap gaya adalah teks pendek yang ditambahkan ke peran dan aturan tool. Gaya `minimal` kosong: hanya peran.

# %%
for nama, teks in GAYA.items():
    print(f"{nama}: {teks.splitlines()[0][:100] if teks else '(kosong: hanya peran)'}")

# %% [markdown]
# ## Langkah 3 - Satu agen per gaya
# TOOLS dan PERSETUJUAN sama untuk semua. Hanya `system_prompt` yang berbeda.

# %%
VARIASI = ["minimal", "ketat", "ramah", "tabel", "hati_hati"]
TOOLS = [a.riwayat_work_order, a.aset_downtime_tertinggi, a.buat_work_order]
PERSETUJUAN = {"buat_work_order": {"allowed_decisions": ["approve", "edit", "reject"]}}

model = get_chat_model()
saver = InMemorySaver()
agen_per_gaya = {
    gaya: create_agent(
        model,
        tools=TOOLS,
        system_prompt=susun_prompt("Perawatan", gaya),
        middleware=[HumanInTheLoopMiddleware(interrupt_on=PERSETUJUAN)],
        checkpointer=saver,
        context_schema=KonteksPengguna,
    )
    for gaya in VARIASI
}
konteks = k.konteks_untuk("engineer")
print(f"   {len(agen_per_gaya)} agen dibuat: {', '.join(VARIASI)}")


def bandingkan(nama_pertanyaan: str, pertanyaan: str) -> None:
    """Ajukan pertanyaan yang sama ke semua agen. Permintaan persetujuan selalu ditolak agar tidak ada yang tercatat."""
    print(f"Pertanyaan ({nama_pertanyaan}): {pertanyaan}")
    print(f"   {'gaya':<11}{'tool dipanggil':<30}{'panjang':>8}{'tabel':>7}  awal jawaban")
    for gaya, agen in agen_per_gaya.items():
        hasil = k.tanya(agen, pertanyaan, f"variasi-{nama_pertanyaan}-{gaya}", konteks, k.keputusan_tolak)
        tool = ", ".join(dict.fromkeys(hasil.tool)) or "-"
        ada_tabel = "ya" if "|" in hasil.jawaban else "-"
        awal = " ".join(hasil.jawaban.split())[:60]
        print(f"   {gaya:<11}{tool:<30}{len(hasil.jawaban):>8}{ada_tabel:>7}  {awal}")

# %% [markdown]
# ## Langkah 4 - Pertanyaan multi-langkah
# Perbandingan angka sering berbentuk tabel apa pun gayanya, jadi kolom `tabel` tidak banyak membedakan di sini.
# Perhatikan kolom `tool dipanggil` dan `panjang`.

# %%
bandingkan("multi", PERTANYAAN["Perawatan"]["multi"][0])

# %% [markdown]
# ## Langkah 5 - Pertanyaan di luar cakupan
# Tidak ada tool untuk memesan suku cadang. Lihat bagaimana tiap gaya menolak dan seberapa panjang penolakannya.

# %%
bandingkan("di_luar", PERTANYAAN["Perawatan"]["di_luar"][0])

# %% [markdown]
# ## Langkah 6 - Tindakan tulis yang kurang detail
# Permintaan ini tidak menyebut aset, prioritas, atau uraian. Gaya `hati_hati` diminta bertanya dulu. Lihat kolom
# `tool dipanggil`: siapa yang memanggil `buat_work_order` dengan menebak, siapa yang memanggil tool baca untuk mencari
# tahu sendiri, dan siapa yang langsung bertanya.

# %%
bandingkan("tulis_kurang_detail", "Buatkan work order untuk pompa yang rusak.")

# %% [markdown]
# ## Ide Utama
# - Dengan tool dan persetujuan yang sama, prompt saja sudah mengubah perilaku: tool yang dipilih, panjang jawaban, format, dan keputusan menolak atau menebak
# - Prompt `minimal` adalah pembanding yang berguna: bandingkan dengan prompt Anda untuk melihat apa yang sebenarnya ditambahkan aturan
# - Salin kalimat dari bank, ubah, dan campur sesuai use case kelompok Anda; uji hasilnya dengan kasus uji (contoh 4)
