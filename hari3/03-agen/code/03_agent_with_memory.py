# %% [markdown]
# # Contoh 3: Agen dengan checkpointer untuk memori
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/03-agen/code/03_agent_with_memory.py`
#
# Checkpointer menyimpan keadaan percakapan agar agen mengingat giliran sebelumnya.
# Dipakai untuk:
# - Menyimpan riwayat percakapan
# - Percakapan multi-giliran
# - Menyimpan keadaan agen antar pemanggilan

# %%
# Langkah 1 - Menyiapkan model dan agen dengan checkpointer
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from migas_shared.field_tools import cek_status_sumur, hitung_water_cut

load_dotenv()

print("Contoh Agen dengan Memori (Checkpointer)\n")

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# Penyimpan memori untuk percakapan (hilang saat program berhenti)
memory = MemorySaver()

agent = create_agent(
    model,
    tools=[cek_status_sumur, hitung_water_cut],
    system_prompt="Anda adalah asisten operasi produksi migas. Jawab ringkas dalam Bahasa Indonesia.",
    checkpointer=memory,
)

# Konfigurasi untuk satu thread percakapan
config = {"configurable": {"thread_id": "operator-17-shift-malam"}}

# %% [markdown]
# ## Langkah 2 - Tes 1: pertanyaan pertama

# %%
query1 = "Cek status sumur SR-020."
print(f"Pengguna: {query1}\n")
response1 = agent.invoke({"messages": [HumanMessage(content=query1)]}, config)
print(f"Agen: {response1['messages'][-1].content}\n\n")

# %% [markdown]
# ## Langkah 3 - Tes 2: pertanyaan lanjutan
# Agen mengingat konteks karena memakai `thread_id` yang sama.

# %%
query2 = "Berapa water cut-nya?"
print(f"Pengguna: {query2}\n")
response2 = agent.invoke({"messages": [HumanMessage(content=query2)]}, config)
print(f"Agen: {response2['messages'][-1].content}\n\n")

# %% [markdown]
# ## Langkah 4 - Tes 3: pertanyaan lanjutan lagi

# %%
query3 = "Sumur mana yang tadi saya tanyakan, dan apa catatannya?"
print(f"Pengguna: {query3}\n")
response3 = agent.invoke({"messages": [HumanMessage(content=query3)]}, config)
print(f"Agen: {response3['messages'][-1].content}\n\n")

# %% [markdown]
# ## Langkah 5 - Tes 4: thread berbeda tidak berbagi memori

# %%
query4 = "Sumur mana yang tadi saya tanyakan?"
print(f"Pengguna (thread lain): {query4}\n")
response4 = agent.invoke({"messages": [HumanMessage(content=query4)]}, {"configurable": {"thread_id": "operator-22-shift-pagi"}})
print(f"Agen: {response4['messages'][-1].content}\n\n")

# %% [markdown]
# ## Manfaat memori
# - Menjaga konteks percakapan antar giliran
# - Agen mengingat sumur dan angka yang disebut sebelumnya
# - Setiap `thread_id` memiliki riwayat percakapan sendiri
# - Cocok untuk asisten serah terima shift dan sesi analisis interaktif
