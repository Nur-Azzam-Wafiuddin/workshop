# %% [markdown]
# # Token Usage Tracking
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/07_token_usage.py`
#
# Jumlah token masukan dan keluaran dibaca dari metadata respons.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

print("Contoh Token Usage Tracking\n")

# %% [markdown]
# ## Langkah 2 - Mengirim satu permintaan

# %%
response = model.invoke("Jelaskan apa itu water cut dalam 2 kalimat.")

# %% [markdown]
# ## Langkah 3 - Membaca pemakaian token dari metadata

# %%
# Ambil pemakaian token dari metadata
usage = response.usage_metadata

if usage:
    print("Rincian token:")
    print(f"  Token prompt (masukan):   {usage.get('input_tokens', 'N/A')}")
    print(f"  Token jawaban (keluaran): {usage.get('output_tokens', 'N/A')}")
    print(f"  Total token:              {usage.get('total_tokens', 'N/A')}")
else:
    print("Informasi pemakaian token tidak tersedia di metadata respons.")

print("\nJawaban:")
print(response.content)
