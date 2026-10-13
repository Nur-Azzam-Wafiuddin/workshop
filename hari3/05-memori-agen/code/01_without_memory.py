# %% [markdown]
# # Contoh 1: Agen Tanpa Memori
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/05-memori-agen/code/01_without_memory.py`
#
# Tanpa checkpointer, setiap pemanggilan `invoke()` berdiri sendiri: agen tidak mengingat giliran sebelumnya.

# %%
# Langkah 1 - Menyiapkan model dan agen
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

print("Agen Tanpa Memori\n")

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# Tanpa checkpointer, tidak ada memori antar pemanggilan invoke()
agent = create_agent(model, tools=[], system_prompt="Anda asisten operasi yang ramah. Jawab singkat dalam Bahasa Indonesia.")


def tanya(agent, teks: str) -> str:
    """Kirim satu pesan dan kembalikan jawaban teks agen."""
    response = agent.invoke({"messages": [HumanMessage(content=teks)]})
    return response["messages"][-1].content


# %% [markdown]
# ## Langkah 2 - Giliran 1
# Pengguna memperkenalkan diri.

# %%
print("Giliran 1")
print("-" * 60)
pertama = "Halo! Nama saya Rina, saya operator shift malam di GS-SR1."
print(f"Pengguna: {pertama}")
print(f"Agen: {tanya(agent, pertama)}")

# %% [markdown]
# ## Langkah 3 - Giliran 2
# Pemanggilan `invoke()` yang terpisah: agen tidak tahu apa yang dikatakan pada giliran 1.

# %%
print("Giliran 2 (pemanggilan invoke() yang terpisah)")
print("-" * 60)
kedua = "Siapa nama saya dan di mana saya bertugas?"
print(f"Pengguna: {kedua}")
print(f"Agen: {tanya(agent, kedua)}")
