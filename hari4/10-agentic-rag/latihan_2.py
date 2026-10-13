# %% [markdown]
# # Latihan Bonus: RAG Percakapan
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Menambahkan memori (bab 5) ke agen RAG agar pengguna bisa mengajukan follow-up question yang merujuk
# jawaban sebelumnya, tanpa mengulang konteks:
#
# - "Berapa lama fire watch harus berjaga setelah pekerjaan panas?" -> 30 menit
# - "Dan bagaimana dengan batas LEL-nya?" -> (masih soal pekerjaan panas)
# - "Dokumen mana yang tadi kamu rujuk?" -> menjawab dari riwayat, tanpa mencari

# %%
# Langkah 1 - Menyiapkan agen dengan memori percakapan
import os
import re
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from migas_shared.config import ROOT
from migas_shared.rag_tools import KonteksPengguna, cari_dokumen

sys.path.insert(0, str(ROOT / "hari4" / "10-agentic-rag" / "code"))  # agar rag_agent.py ditemukan
from rag_agent import PROMPT_RAG

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)
# TODO(B10.5): buat agen RAG percakapan: tool cari_dokumen, PROMPT_RAG ditambah izin pertanyaan lanjutan, context_schema=KonteksPengguna, dan checkpointer=InMemorySaver()
agent = None  # TODO: ganti dengan implementasi Anda
konteks = KonteksPengguna(role="operator", area="Seruni", user_id="OP-114")
config = {"configurable": {"thread_id": "sesi-operator-114"}}

# %% [markdown]
# ## Langkah 2 - Fungsi satu giliran
# `giliran` mengirim satu pertanyaan ke utas yang sama dan menghitung berapa kali agen mencari pada giliran itu.

# %%
jumlah_pencarian = []


def giliran(pertanyaan: str) -> None:
    print(f"Pengguna: {pertanyaan}")
    sebelum = len(agent.get_state(config).values.get("messages", [])) if jumlah_pencarian else 0
    # TODO(B10.6): panggil agent.invoke dengan HumanMessage, config thread yang sama, dan context=konteks
    response = None  # TODO: ganti dengan implementasi Anda
    baru = response["messages"][sebelum:]
    # TODO(B10.7): hitung berapa kali cari_dokumen dipanggil pada pesan baru (AIMessage dengan tool_calls bernama cari_dokumen)
    mencari = 0  # TODO: ganti dengan implementasi Anda
    jumlah_pencarian.append(mencari)
    print(f"   Pencarian pada giliran ini: {mencari}")
    print(f"Agen: {response['messages'][-1].content}")

# %% [markdown]
# ## Langkah 3 - Giliran 1: pertanyaan awal

# %%
giliran("Berapa lama fire watch harus tetap berjaga setelah pekerjaan panas selesai?")

# %% [markdown]
# ## Langkah 4 - Giliran 2: pertanyaan lanjutan
# Pertanyaan ini bergantung pada konteks giliran sebelumnya.

# %%
giliran("Dan bagaimana dengan batas LEL yang disyaratkan?")

# %% [markdown]
# ## Langkah 5 - Giliran 3: merujuk riwayat

# %%
giliran("Dokumen apa yang tadi kamu rujuk untuk dua jawaban itu?")

# %% [markdown]
# ## Langkah 6 - Pemeriksaan di kode

# %%
status = agent.get_state(config)
print(f"Utas menyimpan {len(status.values['messages'])} pesan (pertanyaan, pencarian, hasil, dan jawaban).")
teks_akhir = str(status.values["messages"][-1].content)
ok_ingatan = bool(re.search(r"SOP-HSE-004|LL-2026-03", teks_akhir))
print(f"{'LOLOS' if ok_ingatan else 'GAGAL'}  pertanyaan ke-3 menyebut dokumen dari giliran sebelumnya (SOP-HSE-004)")
print(f"{'LOLOS' if jumlah_pencarian[0] >= 1 else 'GAGAL'}  pertanyaan pertama mencari di dokumen")
