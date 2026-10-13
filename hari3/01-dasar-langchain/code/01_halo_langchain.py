# %% [markdown]
# # Halo LangChain
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/01_halo_langchain.py`
#
# Panggilan LangChain pertama Anda: membuat objek model chat lalu mengirim satu pertanyaan.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# Buat objek model chat
model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Panggilan AI pertama Anda
# `model.invoke()` mengirim pertanyaan dan mengembalikan satu pesan jawaban.

# %%
response = model.invoke("Apa fungsi separator pada fasilitas produksi minyak dan gas? Jawab dalam satu kalimat.")

print("Jawaban AI:", response.content)
print("\nBerhasil! Anda baru saja membuat panggilan LangChain pertama.")
