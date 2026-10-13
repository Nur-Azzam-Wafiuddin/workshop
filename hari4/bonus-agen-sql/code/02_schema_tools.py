# %% [markdown]
# # Contoh 2: Biarkan Agen Menjelajahi Skema
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/bonus-agen-sql/code/02_schema_tools.py`
#
# Obat untuk menebak adalah melihat. Contoh ini memberi agen tiga tool (daftar_tabel, deskripsikan_tabel,
# jalankan_query) dan system prompt yang menyuruhnya memakai tool penjelajah lebih dulu.

# %%
# Langkah 1 - Menyiapkan model dan agen
import os
import sys

from migas_shared.config import ROOT

sys.path.insert(0, str(ROOT / "hari4" / "bonus-agen-sql" / "code"))
from sql_tools import PROMPT_SISTEM_SQL, daftar_tabel, deskripsikan_tabel, jalankan_query
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

agent = create_agent(
    model,
    tools=[daftar_tabel, deskripsikan_tabel, jalankan_query],
    system_prompt=PROMPT_SISTEM_SQL,
)

# %% [markdown]
# ## Langkah 2 - Fungsi untuk menampilkan langkah agen
# `tampilkan_langkah` mencetak urutan panggilan tool yang dilakukan agen.

# %%
def tampilkan_langkah(response) -> None:
    """Cetak urutan panggilan tool yang dilakukan agen."""
    langkah = 0
    for pesan in response["messages"]:
        if isinstance(pesan, AIMessage):
            for panggilan in pesan.tool_calls:
                langkah += 1
                argumen = ", ".join(f"{nilai!r}" for nilai in panggilan["args"].values())
                print(f"   {langkah}. {panggilan['name']}({argumen})")

# %% [markdown]
# ## Langkah 3 - Pertanyaan yang sama dengan Contoh 1
# Kali ini agen menjelajahi skema lebih dulu.

# %%
pertanyaan_1 = "Berapa banyak insiden HSE yang bahayanya terkait gas H2S?"  # pertanyaan yang sama dengan Contoh 1
print(f"Pengguna: {pertanyaan_1}\n")
response_1 = agent.invoke({"messages": [HumanMessage(content=pertanyaan_1)]})
print("Panggilan tool:")
tampilkan_langkah(response_1)
print(f"\nAgen: {response_1['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 4 - Pertanyaan yang lebih menantang
# Mencari bad actor butuh agregasi di tabel work order.

# %%
pertanyaan_2 = "Sebutkan 3 aset dengan total downtime tertinggi (bad actor), beserta total downtime dalam jam."
print(f"Pengguna: {pertanyaan_2}\n")
response_2 = agent.invoke({"messages": [HumanMessage(content=pertanyaan_2)]})
print("Panggilan tool:")
tampilkan_langkah(response_2)
print(f"\nAgen: {response_2['messages'][-1].content}\n")

# %% [markdown]
# ## Yang baru saja terjadi
# - Agen melihat dulu: `daftar_tabel` -> `deskripsikan_tabel` -> `jalankan_query`
# - Nama kolom dalam SQL berasal dari skema, bukan tebakan
# - Baris contoh menunjukkan bentuk nilainya: bahaya H2S tersimpan sebagai `H2S/Gas`
# - Bandingkan dengan Contoh 1: lebih sedikit panggilan sia-sia, dan tanpa menebak
# - System prompt-lah yang membuat agen menjelajah sebelum bertanya
