# %% [markdown]
# # Latihan 1: Asisten SOP dengan Uji Otomatis
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Asisten dokumen untuk operator lapangan, dengan enam uji yang diperiksa DI KODE:
#
# 1. Pengetahuan umum -> menjawab langsung, TIDAK mencari
# 2. Pertanyaan SOP -> mencari, menjawab dengan angka yang benar, mengutip SOP yang benar
# 3. Konflik revisi -> memakai Rev 3 (10 ppm), tidak memakai Rev 2 (20 ppm)
# 4. Kode alarm alat -> menemukan manual VSD dan menjelaskan kode F07
# 5. Tak terjawab -> menolak dengan kalimat standar
# 6. Dokumen terlarang -> menolak (operator tidak boleh membaca laporan investigasi HSE)

# %%
# Langkah 1 - Menyiapkan agen
import os
import sys

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from migas_shared.config import ROOT
from migas_shared.rag_tools import KonteksPengguna

sys.path.insert(0, str(ROOT / "hari4" / "10-agentic-rag" / "code"))  # agar rag_agent.py ditemukan
from rag_agent import HasilRAG, bangun_agen_rag, tanya

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)
# TODO(B10.1): buat agen RAG dengan bangun_agen_rag(model)
agent = None  # TODO: ganti dengan implementasi Anda
operator = KonteksPengguna(role="operator", area="Seruni", user_id="OP-114")

# %% [markdown]
# ## Langkah 2 - Fungsi pemeriksa
# `periksa` mencetak LOLOS atau GAGAL beserta rincian, lalu mengembalikan hasilnya.

# %%
def periksa(nama: str, ok: bool, rincian: str) -> bool:
    print(f"{'LOLOS' if ok else 'GAGAL'}  {nama}")
    print(f"        {rincian}")
    return ok


hasil_uji: list[bool] = []

# %% [markdown]
# ## Langkah 3 - Uji 1: pengetahuan umum

# %%
r1: HasilRAG = tanya(agent, "Apa ibu kota Prancis?", operator)
hasil_uji.append(periksa("1. Pengetahuan umum dijawab langsung", not r1.mencari and "paris" in r1.jawaban.lower(),
                         f"mencari={r1.mencari}, jawaban: {r1.jawaban[:80]}"))

# %% [markdown]
# ## Langkah 4 - Uji 2: pertanyaan SOP

# %%
r2 = tanya(agent, "Berapa nilai IDLH untuk gas H2S?", operator)
# TODO(B10.2): uji 2: tambahkan hasil periksa(...) yang meminta agen mencari, jawaban memuat '100 ppm', sitasi memuat SOP-HSE-001, dan tidak ada sitasi tidak valid
pass  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 5 - Uji 3: konflik revisi

# %%
r3 = tanya(agent, "Pada konsentrasi H2S berapa pekerja wajib menghentikan pekerjaan dan evakuasi?", operator)
# TODO(B10.3): uji 3: jawaban memuat '10 ppm' dan tidak ada revisi yang diambil berstatus superseded
pass  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 6 - Uji 4: kode alarm alat

# %%
r4 = tanya(agent, "Apa arti alarm F07 pada VSD FD-500 dan apakah unit boleh langsung di-restart?", operator)
hasil_uji.append(periksa("4. Kode alarm alat: manual VSD ditemukan",
                         "MAN-VSD-FD500" in r4.diambil and ("ground fault" in r4.jawaban.lower() or "f07" in r4.jawaban.lower()),
                         f"diambil={r4.diambil}"))

# %% [markdown]
# ## Langkah 7 - Uji 5: pertanyaan tak terjawab

# %%
r5 = tanya(agent, "Siapa direktur utama PT Hulu Energi Nusantara?", operator)
hasil_uji.append(periksa("5. Pertanyaan tak terjawab ditolak", r5.menolak, f"jawaban: {r5.jawaban[:90]}"))

# %% [markdown]
# ## Langkah 8 - Uji 6: dokumen terlarang

# %%
r6 = tanya(agent, "Apa akar masalah insiden paparan H2S di SR-027 pada Juli 2026?", operator)
# TODO(B10.4): uji 6: INV-2026-011 tidak ada di r6.diambil dan agen menolak (r6.menolak)
pass  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 9 - Rekap

# %%
print(f"Hasil: {sum(hasil_uji)}/{len(hasil_uji)} uji lolos")
print("(Uji berbasis model dapat sesekali gagal. Jalankan ulang dan analisis mengapa: salah cari, salah revisi, atau salah menolak?)")
