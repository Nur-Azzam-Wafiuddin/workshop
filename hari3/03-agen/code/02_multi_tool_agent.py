# %% [markdown]
# # Contoh 2: Agen dengan Banyak Tool
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/03-agen/code/02_multi_tool_agent.py`
#
# Agen diberi empat tool: tiga tool lapangan dari bab 2 dan satu tool pencarian dokumen. Agen memilih tool
# yang tepat untuk setiap pertanyaan.

# %%
# Langkah 1 - Menyiapkan model dan agen
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from migas_shared.rag_tools import KonteksPengguna, cari_dokumen
from migas_shared.tampil import jejak_tool
from migas_shared.field_tools import hitung_water_cut, konversi_satuan, cek_status_sumur

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# Empat tool: tiga tool lapangan dari bab 2 dan satu tool pencarian dokumen.
# context_schema memberi tahu agen bentuk konteks tepercaya (peran pengguna) yang dikirim program.
agent = create_agent(
    model,
    tools=[hitung_water_cut, konversi_satuan, cek_status_sumur, cari_dokumen],
    system_prompt=(
        "Anda adalah asisten operasi produksi migas di Gathering Station GS-SR1. "
        "Pakai tool bila perlu. Untuk pertanyaan prosedur, cari di dokumen dan sebut ID dokumennya. "
        "Jawab ringkas dalam Bahasa Indonesia."
    ),
    context_schema=KonteksPengguna,
)

# Peran dikirim oleh PROGRAM lewat context, bukan oleh model
konteks = KonteksPengguna(role="operator", area="Seruni", user_id="op-17")

# %% [markdown]
# ## Langkah 2 - Pertanyaan status sumur
# Agen memilih tool yang tepat untuk setiap pertanyaan.

# %%
query = "Apa status sumur SR-020?"
response = agent.invoke({"messages": [HumanMessage(content=query)]}, context=konteks)
print(f"Pengguna: {query}")
print("  Tool    :", "; ".join(jejak_tool(response["messages"])) or "(tidak ada)")
print(f"  Agen    : {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 3 - Pertanyaan konversi satuan

# %%
query = "Tekanan wellhead ML-012 tercatat 900 psi. Berapa bar?"
response = agent.invoke({"messages": [HumanMessage(content=query)]}, context=konteks)
print(f"Pengguna: {query}")
print("  Tool    :", "; ".join(jejak_tool(response["messages"])) or "(tidak ada)")
print(f"  Agen    : {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 4 - Pertanyaan prosedur (pencarian dokumen)

# %%
query = "Berapa jarak minimal muster point dari sumber gas H2S menurut SOP yang berlaku?"
response = agent.invoke({"messages": [HumanMessage(content=query)]}, context=konteks)
print(f"Pengguna: {query}")
print("  Tool    :", "; ".join(jejak_tool(response["messages"])) or "(tidak ada)")
print(f"  Agen    : {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 5 - Pertanyaan yang butuh dua tool berurutan

# %%
query = "Cek sumur ML-012, lalu hitung water cut-nya."
response = agent.invoke({"messages": [HumanMessage(content=query)]}, context=konteks)
print(f"Pengguna: {query}")
print("  Tool    :", "; ".join(jejak_tool(response["messages"])) or "(tidak ada)")
print(f"  Agen    : {response['messages'][-1].content}\n")
