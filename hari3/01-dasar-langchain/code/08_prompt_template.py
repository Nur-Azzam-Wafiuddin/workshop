# %% [markdown]
# # Prompt Template
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/08_prompt_template.py`
#
# Template prompt bisa dipakai ulang dengan nilai berbeda, lalu dirangkai dengan model memakai operator `|`.

# %%
# Langkah 1 - Menyiapkan template dan model
import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

# Buat template yang bisa dipakai ulang
template = ChatPromptTemplate.from_messages([
    ("system", "Anda adalah asisten yang meringkas catatan shift migas untuk {audiens}. Maksimal dua kalimat."),
    ("human", "{catatan}"),
])

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Merangkai template dengan model
# Pakai template berkali-kali dengan nilai berbeda.

# %%
chain = template | model

catatan = (
    "Shift malam GS-SR1: ESP SR-020 trip overload pukul 02.10, restart 2 kali gagal, "
    "megger motor menunjukkan 0 Mohm. Produksi SR-020 hilang sekitar 120 bopd. "
    "Usulan pulling job untuk ganti motor. Separator V-SR1-101 normal."
)

# %% [markdown]
# ## Langkah 3 - Ringkasan untuk supervisor lapangan

# %%
hasil_1 = chain.invoke({"audiens": "supervisor lapangan", "catatan": catatan})
print("Untuk supervisor lapangan:", hasil_1.content)

# %% [markdown]
# ## Langkah 4 - Ringkasan untuk manajer asset
# Catatan sama, audiens berbeda.

# %%
hasil_2 = chain.invoke({"audiens": "manajer asset (fokus dampak produksi dan biaya)", "catatan": catatan})
print("\nUntuk manajer asset:", hasil_2.content)
