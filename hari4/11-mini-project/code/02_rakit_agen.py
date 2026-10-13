# %% [markdown]
# # Contoh 2: Merakit Agen dari Tiga Keping
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/11-mini-project/code/02_rakit_agen.py`
#
# Agen mini project selalu disusun dari tiga keping yang Anda pilih sendiri:
#
# 1. TOOLS: tool apa yang boleh dipakai agen (dari katalog di contoh 1)
# 2. INSTRUKSI: peran dan aturan agen (dari bank prompt di `aplikasi/prompt_bank.py`, atau tulis sendiri)
# 3. PERSETUJUAN: tool tulis mana yang berhenti menunggu manusia (interrupt), dan keputusan apa yang diizinkan
#
# Contoh ini merakit agen Perawatan langkah demi langkah, lalu menjalankannya dari terminal tanpa UI. Reviewer-nya
# berupa fungsi berskrip: menyetujui, mengubah, dan menolak. Hasilnya diperiksa di kode, yaitu isi `CATATAN_TINDAKAN`,
# bukan kalimat jawaban agen. Agen bisa saja menulis "work order dibuat" tanpa benar-benar memanggil tool.
#
# Kalau agen sudah bekerja di terminal, menyalin ketiga keping ke `aplikasi/agen/saya.py` akan membuatnya tampil di aplikasi.

# %%
# Langkah 1 - Mengimpor kerangka aplikasi dan komponen agen
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
from prompt_bank import PERTANYAAN, susun_prompt

# %% [markdown]
# ## Langkah 2 - Keping 1: TOOLS
# Dua tool baca dan dua tool tulis dari katalog Perawatan. Tool yang sama bisa juga Anda tulis sendiri dengan `@tool`.

# %%
TOOLS = [a.riwayat_work_order, a.aset_downtime_tertinggi, a.buat_work_order, a.tutup_work_order]
for t in TOOLS:
    print(f"   [{a.jenis_tool(t):<5}] {t.name}")

# %% [markdown]
# ## Langkah 3 - Keping 2: INSTRUKSI
# `susun_prompt(use_case, gaya)` menggabungkan peran, aturan yang menyebut tool dengan namanya, dan gaya jawaban.
# Gaya `ketat` hanya menjawab dari tool dan menolak yang di luar cakupan. Contoh 3 membandingkan gaya lainnya.

# %%
INSTRUKSI = susun_prompt("Perawatan", "ketat")
print(INSTRUKSI)

# %% [markdown]
# ## Langkah 4 - Keping 3: PERSETUJUAN
# Membuat work order boleh disetujui, diubah, atau ditolak. Menutup work order hanya boleh disetujui atau ditolak,
# karena yang diperiksa reviewer adalah nomornya, bukan isinya. Kode memeriksa bahwa setiap tool tulis punya aturan.

# %%
PERSETUJUAN = {
    "buat_work_order": {"allowed_decisions": ["approve", "edit", "reject"]},
    "tutup_work_order": {"allowed_decisions": ["approve", "reject"]},
}
tanpa_aturan = [t.name for t in TOOLS if a.jenis_tool(t) == "tulis" and t.name not in PERSETUJUAN]
print(f"   Tool tulis tanpa aturan persetujuan: {tanpa_aturan or 'tidak ada'} -> {'LOLOS' if not tanpa_aturan else 'GAGAL'}")

# %% [markdown]
# ## Langkah 5 - Merakit agen
# Tiga keping masuk ke `create_agent()`. `HumanInTheLoopMiddleware` mengubah PERSETUJUAN menjadi interrupt,
# dan `InMemorySaver` menyimpan keadaan agen selama menunggu keputusan (lihat bab 6).

# %%
agen = create_agent(
    get_chat_model(),
    tools=TOOLS,
    system_prompt=INSTRUKSI,
    middleware=[HumanInTheLoopMiddleware(interrupt_on=PERSETUJUAN)],
    checkpointer=InMemorySaver(),
    context_schema=KonteksPengguna,
)
konteks = k.konteks_untuk("engineer")
print("   Agen siap.")

# %% [markdown]
# ## Langkah 6 - Pertanyaan baca: tidak ada persetujuan
# Tool baca berjalan bebas, jadi reviewer tidak pernah ditanya.

# %%
pertanyaan = PERTANYAAN["Perawatan"]["baca"][0]
print(f"   Pengguna: {pertanyaan}")
hasil_baca = k.tanya(agen, pertanyaan, "rakit-baca", konteks)
print(f"   Tool dipanggil : {hasil_baca.tool}")
print(f"   Keputusan      : {hasil_baca.keputusan or 'tidak ada (tidak ada tool tulis)'}")
print(f"   Jawaban agen   : {hasil_baca.jawaban[:150].replace(chr(10), ' ')}...")

# %% [markdown]
# ## Langkah 7 - Pertanyaan tulis: reviewer menyetujui
# `k.tanya()` menjalankan agen sampai selesai dan menjawab setiap permintaan persetujuan dengan fungsi `reviewer`.
# Di aplikasi, reviewer-nya adalah Anda lewat formulir.

# %%
def setuju(permintaan: dict, boleh: list[str]) -> dict:
    print(f"   Reviewer menerima usulan {permintaan['name']} {permintaan['args']}")
    print(f"   Pilihan yang diizinkan: {', '.join(boleh)} -> approve")
    return {"type": "approve"}


pertanyaan = PERTANYAAN["Perawatan"]["tulis"][0]
print(f"   Pengguna: {pertanyaan}")
sebelum = len(a.CATATAN_TINDAKAN)
hasil_setuju = k.tanya(agen, pertanyaan, "rakit-setuju", konteks, setuju)
print(f"   Tool dipanggil : {hasil_setuju.tool}")
bertambah = len(a.CATATAN_TINDAKAN) - sebelum
print(f"   Dicatat di kode: {[c['nomor'] for c in a.CATATAN_TINDAKAN[sebelum:]]} -> {'LOLOS' if bertambah == 1 else 'GAGAL'}")

# %% [markdown]
# ## Langkah 8 - Reviewer mengubah argumen
# Pada keputusan `edit`, tool berjalan dengan argumen baru dari reviewer. Di sini prioritas diubah menjadi `tinggi`.
# Kode memeriksa catatan terakhir, bukan jawaban agen.

# %%
def ubah_prioritas(permintaan: dict, boleh: list[str]) -> dict:
    print(f"   Reviewer mengubah prioritas {permintaan['args'].get('prioritas')} -> tinggi")
    args_baru = {**permintaan["args"], "prioritas": "tinggi"}
    return {"type": "edit", "edited_action": {"name": permintaan["name"], "args": args_baru}}


hasil_ubah = k.tanya(agen, pertanyaan, "rakit-ubah", konteks, ubah_prioritas)
terakhir = a.CATATAN_TINDAKAN[-1]
print(f"   Keputusan      : {hasil_ubah.keputusan}")
print(f"   Dicatat di kode: {terakhir['nomor']} prioritas {terakhir.get('prioritas')} -> {'LOLOS' if terakhir.get('prioritas') == 'tinggi' else 'GAGAL'}")

# %% [markdown]
# ## Langkah 9 - Reviewer menolak
# Tool tidak berjalan dan agen menerima alasan penolakan. Tidak ada catatan baru.

# %%
sebelum = len(a.CATATAN_TINDAKAN)
hasil_tolak = k.tanya(agen, pertanyaan, "rakit-tolak", konteks, k.keputusan_tolak)
print(f"   Keputusan      : {hasil_tolak.keputusan}")
print(f"   Dicatat di kode: bertambah {len(a.CATATAN_TINDAKAN) - sebelum} -> {'LOLOS' if len(a.CATATAN_TINDAKAN) == sebelum else 'GAGAL'}")
print(f"   Jawaban agen   : {hasil_tolak.jawaban[:150].replace(chr(10), ' ')}...")

# %% [markdown]
# ## Ide Utama
# - Agen mini project = tiga keping: TOOLS, INSTRUKSI, dan PERSETUJUAN, lalu `create_agent()`
# - Setiap tool tulis harus punya aturan persetujuan; kode bisa memeriksanya
# - Reviewer berskrip (`k.tanya`) menguji jalur setuju, ubah, dan tolak tanpa membuka aplikasi
# - Periksa efek nyata di data (`CATATAN_TINDAKAN`), jangan hanya percaya kalimat jawaban
