# %% [markdown]
# # Percakapan Multi-Giliran: Serah Terima Shift
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/02_multi_turn_chat.py`
#
# Model tidak menyimpan percakapan. Agar asisten "mengingat", seluruh riwayat pesan dikirim ulang pada setiap giliran.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Giliran pertama
# Riwayat dimulai dengan pesan sistem dan laporan pertama dari operator shift pagi.

# %%
pertanyaan_1 = (
    "Catatan serah terima dari shift pagi di GS-SR1: ESP SR-020 sempat trip overload kemarin sore, "
    "sudah restart dan stabil sejak pukul 18.00. Level controller separator V-SR1-101 masih hunting. "
    "Tolong catat."
)
messages = [
    SystemMessage(content="Anda adalah asisten serah terima shift di Gathering Station GS-SR1. "
                          "Jawab ringkas dan jelas dalam Bahasa Indonesia."),
    HumanMessage(content=pertanyaan_1),
]

print("Operator:", pertanyaan_1)
response_1 = model.invoke(messages)
print("\nAsisten:", response_1.content)
messages.append(AIMessage(content=response_1.content))

# %% [markdown]
# ## Langkah 3 - Giliran kedua
# Asisten mengingat isi catatan karena seluruh riwayat dikirim ulang.

# %%
pertanyaan_2 = "Apa saja yang perlu dipantau oleh shift malam?"
messages.append(HumanMessage(content=pertanyaan_2))

print("Operator:", pertanyaan_2)
response_2 = model.invoke(messages)
print("\nAsisten:", response_2.content)
messages.append(AIMessage(content=response_2.content))

# %% [markdown]
# ## Langkah 4 - Giliran ketiga
# Asisten masih mengingat semuanya.

# %%
pertanyaan_3 = "Buat ringkasannya dalam tiga butir untuk dicatat di buku log."
messages.append(HumanMessage(content=pertanyaan_3))

print("Operator:", pertanyaan_3)
response_3 = model.invoke(messages)
print("\nAsisten:", response_3.content)
# Jawaban ketiga tidak ditambahkan ke riwayat karena percakapan berakhir di sini

# %% [markdown]
# ## Langkah 5 - Memeriksa riwayat
# Jalankan sel ini untuk melihat isi riwayat setelah tiga giliran.

# %%
print(f"Total pesan dalam riwayat: {len(messages)} pesan, terdiri dari 1 pesan sistem, 3 pesan pengguna, dan 2 jawaban AI")
for pesan in messages:
    print(f"  {pesan.type:<6} | {str(pesan.content)[:60]}")

# %% [markdown]
# Perhatikan bagaimana asisten mengingat konteks sepanjang percakapan.
