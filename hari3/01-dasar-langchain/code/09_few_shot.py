# %% [markdown]
# # Few-Shot Prompting
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/09_few_shot.py`
#
# Model diajari lewat contoh pasangan masukan dan keluaran sebelum diminta menjawab masukan baru.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    temperature=0,
)

# %% [markdown]
# ## Langkah 2 - Contoh pengajaran
# Catatan work order dan tingkat prioritasnya.

# %%
contoh = [
    {"input": "Gas bocor di flange kompresor K-ML1-201, alarm LEL menyala", "output": "TINGGI"},
    {"input": "PM rutin greasing bearing pompa P-SR1-302 sesuai jadwal", "output": "RENDAH"},
    {"input": "ESP SR-020 trip overload, sudah restart dan stabil, perlu pemeriksaan lanjutan", "output": "SEDANG"},
]

# Template untuk satu contoh
template_contoh = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}"),
])

# Template few-shot
template_few_shot = FewShotChatMessagePromptTemplate(
    example_prompt=template_contoh,
    examples=contoh,
)

# %% [markdown]
# ## Langkah 3 - Template akhir dan chain
# Pesan sistem, contoh, lalu masukan pengguna.

# %%
template_akhir = ChatPromptTemplate.from_messages([
    ("system", "Anda menetapkan prioritas work order migas. Jawab hanya dengan satu kata: TINGGI, SEDANG, atau RENDAH."),
    template_few_shot,
    ("human", "{input}"),
])

chain = template_akhir | model

# %% [markdown]
# ## Langkah 4 - Menguji dengan catatan baru

# %%
catatan_uji = [
    "Ceceran minyak di sekitar wellhead KN-061, sumur sudah di-shut in",
    "Penggantian V-belt pumping unit KN-033 sesuai rencana bulan depan",
    "Level controller separator V-SR1-101 hunting, produksi sempat di-cut",
]
for catatan in catatan_uji:
    hasil = chain.invoke({"input": catatan})
    print(f"{catatan}\n   -> {hasil.content}")
