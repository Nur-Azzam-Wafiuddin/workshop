# %% [markdown]
# # Contoh 1: Agen Dasar dengan create_agent()
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/03-agen/code/01_basic_agent.py`
#
# `create_agent()` membuat agen yang memutuskan sendiri kapan memanggil tool, menjalankannya, dan menyusun
# jawaban akhir.

# %%
# Langkah 1 - Menyiapkan model dan tool
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from migas_shared.tampil import jejak_tool

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)


# Tool untuk agen. Docstring dibaca model untuk memutuskan kapan tool dipakai.
@tool
def hitung_water_cut(oil_bopd: float, water_bwpd: float) -> str:
    """Hitung water cut (persentase air dalam total cairan produksi) sebuah sumur.

    Args:
        oil_bopd: Produksi minyak dalam barel per hari (bopd)
        water_bwpd: Produksi air dalam barel per hari (bwpd)
    """
    total = oil_bopd + water_bwpd
    if total == 0:
        return "Total produksi 0, water cut tidak dapat dihitung."
    return f"Water cut = {water_bwpd / total * 100:.1f}%"


# %% [markdown]
# ## Langkah 2 - Membuat agen
# Cukup satu panggilan `create_agent()`; tidak perlu menulis loop sendiri.

# %%
# Buat agen dengan create_agent(), selesai
agent = create_agent(
    model,
    tools=[hitung_water_cut],
    system_prompt="Anda adalah asisten operasi produksi migas. Jawab ringkas dalam Bahasa Indonesia.",
)

# %% [markdown]
# ## Langkah 3 - Menjalankan agen
# Agen dipanggil dengan daftar pesan. Jawaban akhir ada di pesan terakhir.

# %%
# Pakai agen dengan daftar pesan
query = "Sumur SR-020 memproduksi 120 bopd minyak dan 480 bwpd air. Berapa water cut-nya?"
print(f"Pengguna: {query}\n")
response = agent.invoke({"messages": [HumanMessage(content=query)]})

# Jawaban akhir ada di pesan terakhir
last_message = response["messages"][-1]
print(f"Agen: {last_message.content}")

# %% [markdown]
# ## Langkah 4 - Melihat jejak tool

# %%
print("Tool yang dipanggil agen:")
for baris in jejak_tool(response["messages"]):
    print("  -", baris)

print("\nDi balik layar:")
print("   create_agent() menjalankan pola ReAct (Thought, Action, Observation)")
print(f"   dan mengurus semua kode loop untuk Anda. Jumlah pesan dalam hasil: {len(response['messages'])}")
