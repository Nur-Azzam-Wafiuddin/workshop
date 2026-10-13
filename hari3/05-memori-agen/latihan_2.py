# %% [markdown]
# # Bab 5 - Latihan Bonus: Membandingkan Strategi Memori
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Menjalankan percakapan berskrip YANG SAMA dengan tiga strategi dan mengukur:
# - berapa banyak pesan dan (perkiraan) token yang tersimpan di memori
# - apakah agen masih bisa mengingat fakta awal di akhir percakapan
#
# Strategi: simpan semua, pangkas ke N pesan terakhir, ringkas pesan lama.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, before_model
from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES

load_dotenv()

print("Membandingkan Strategi Memori\n")

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)
prompt = "Anda asisten operasi yang membantu. Jawab singkat dalam Bahasa Indonesia."

# %% [markdown]
# ## Langkah 2 - Percakapan uji dan fungsi evaluasi
# `evaluasi` memutar percakapan berskrip, mengajukan pertanyaan pengingat di akhir, lalu mengukur isi memori.

# %%
SIMPAN_TERAKHIR = 4

PERCAKAPAN = [
    "Nomor Permit to Work yang saya pegang adalah PTW-2026-0714.",
    "Pekerjaan kami adalah penggantian gasket flange pada kompresor K-ML1-201.",
    "Pekan lalu terjadi pemadaman listrik selama 2 jam di GS-ML1.",
    "Generator cadangan menyala otomatis setelah 30 detik.",
    "Kemarin kompresor menangani sekitar 1,2 juta scf gas.",
]
PERTANYAAN_INGAT = "Apa nomor Permit to Work yang saya sebutkan di awal?"
DIHARAPKAN = "PTW-2026-0714"


# TODO(B5.4): buat middleware @before_model simpan_terbaru yang menyisakan SIMPAN_TERAKHIR pesan terakhir (hapus sisanya dengan RemoveMessage(id=REMOVE_ALL_MESSAGES))
simpan_terbaru = None  # TODO: ganti dengan implementasi Anda


def evaluasi(nama: str, agent) -> dict:
    config = {"configurable": {"thread_id": nama}}
    for teks in PERCAKAPAN:
        agent.invoke({"messages": [HumanMessage(content=teks)]}, config)

    jawaban = agent.invoke({"messages": [HumanMessage(content=PERTANYAAN_INGAT)]}, config)
    tersimpan = agent.get_state(config).values["messages"]
    return {
        "strategi": nama,
        "pesan": len(tersimpan),
        "token": count_tokens_approximately(tersimpan),
        "ingat": DIHARAPKAN in jawaban["messages"][-1].content,
        "jawaban": jawaban["messages"][-1].content,
    }


# %% [markdown]
# ## Langkah 3 - Tiga agen dengan strategi berbeda

# %%
# TODO(B5.5): buat tiga agen tanpa tool, masing-masing dengan InMemorySaver: 'simpan semua' (tanpa middleware), 'pangkas ke N' (middleware simpan_terbaru), dan 'ringkas' (SummarizationMiddleware dengan trigger ('messages', 6) dan keep ('messages', 2))
agen = {}  # TODO: ganti dengan implementasi Anda

hasil = []

# %% [markdown]
# ## Langkah 4 - Strategi 1: simpan semua

# %%
nama = "simpan semua"
print(f"Menjalankan: {nama}")
hasil.append(evaluasi(nama, agen[nama]))

# %% [markdown]
# ## Langkah 5 - Strategi 2: pangkas ke pesan terakhir

# %%
nama = f"pangkas ke {SIMPAN_TERAKHIR}"
print(f"Menjalankan: {nama}")
hasil.append(evaluasi(nama, agen[nama]))

# %% [markdown]
# ## Langkah 6 - Strategi 3: ringkas pesan lama

# %%
nama = "ringkas"
print(f"Menjalankan: {nama}")
hasil.append(evaluasi(nama, agen[nama]))

# %% [markdown]
# ## Langkah 7 - Tabel perbandingan

# %%
print(f"{'Strategi':<20}{'Pesan':>8}{'~Token':>10}   Ingat nomor PTW?")
print("-" * 60)
for h in hasil:
    tanda = "ya" if h["ingat"] else "tidak"
    print(f"{h['strategi']:<20}{h['pesan']:>8}{h['token']:>10}   {tanda}")

# %% [markdown]
# ## Membaca tabel
# - Simpan semua: mengingat, tetapi tumbuh tanpa batas
# - Pangkas: kecil, tetapi bisa melupakan fakta awal
# - Ringkas: menjaga fakta kunci, tetapi ringkasannya sendiri memakai token.
#   Pada percakapan PENDEK ringkasan bisa lebih besar dari aslinya; manfaatnya terasa
#   pada percakapan panjang (coba perpanjang daftar `PERCAKAPAN`)
