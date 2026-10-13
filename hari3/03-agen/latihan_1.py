# %% [markdown]
# # Bab 3 - Latihan: Agen Analis Produksi
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Agen dengan `create_agent()` yang menjawab pertanyaan multi-langkah dengan memadukan
# pencarian dokumen, status sumur, perhitungan water cut, dan konversi satuan.

# %%
# Langkah 1 - Menyiapkan model dan agen
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from migas_shared.rag_tools import KonteksPengguna, cari_dokumen
from migas_shared.tampil import jejak_tool
from migas_shared.field_tools import TOOL_LAPANGAN

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# TODO(B3.1): buat agen dengan create_agent: model, tools=[*TOOL_LAPANGAN, cari_dokumen], system_prompt analis produksi (angka dari tool, hitungan dari tool, prosedur dari cari_dokumen dengan menyebut ID dokumen), dan context_schema=KonteksPengguna
agent = None  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 2 - Status sumur lalu perhitungan

# %%
query = "Sumur SR-020 dan ML-012: berapa total produksi minyak keduanya, dan berapa water cut masing-masing?"
print(f"Pengguna: {query}")
# TODO(B3.2): panggil agent.invoke dengan HumanMessage dan context=KonteksPengguna(role="engineer")
response = None  # TODO: ganti dengan implementasi Anda
print("  Langkah  :")
for baris in jejak_tool(response["messages"]):
    print("    -", baris)
print(f"  Jawaban  : {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 3 - Status sumur lalu konversi satuan

# %%
query = "Berapa produksi minyak SR-020 dalam meter kubik per hari?"
print(f"Pengguna: {query}")
response = agent.invoke({"messages": [HumanMessage(content=query)]}, context=KonteksPengguna(role="engineer"))
print("  Langkah  :")
for baris in jejak_tool(response["messages"]):
    print("    -", baris)
print(f"  Jawaban  : {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 4 - Pencarian dokumen lalu ringkasan

# %%
query = "Menurut SOP H2S yang berlaku, apa tindakan saat alarm tingkat 2 berbunyi di wellhead?"
print(f"Pengguna: {query}")
response = agent.invoke({"messages": [HumanMessage(content=query)]}, context=KonteksPengguna(role="engineer"))
print("  Langkah  :")
for baris in jejak_tool(response["messages"]):
    print("    -", baris)
print(f"  Jawaban  : {response['messages'][-1].content}\n")
