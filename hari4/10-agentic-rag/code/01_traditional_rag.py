# %% [markdown]
# # Contoh 1: RAG Tradisional (Pola Selalu-Mencari)
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/10-agentic-rag/code/01_traditional_rag.py`
#
# Pada RAG tradisional, SETIAP pertanyaan memicu pencarian dokumen, lalu hasilnya ditempel ke prompt:
#
# `pertanyaan -> SELALU cari -> ambil dokumen -> hasilkan jawaban`
#
# Itu sederhana dan mudah diprediksi, tetapi boros: pertanyaan "Berapa 2 + 2?" pun menjalankan pencarian
# dan membawa chunk SOP yang tidak relevan ke model.

# %%
# Langkah 1 - Menyiapkan model dan retriever
import os
import time

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from migas_shared.rag_pipeline import format_context
from migas_shared.rag_tools import build_retriever

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)
retriever = build_retriever()
jumlah_pencarian = 0

# %% [markdown]
# ## Langkah 2 - Fungsi RAG tradisional
# Langkah pertama SELALU mencari dokumen (walau tidak dibutuhkan), langkah kedua menghasilkan jawaban dengan konteks itu.

# %%
def rag_tradisional(pertanyaan: str) -> tuple[str, list[str]]:
    global jumlah_pencarian
    # Langkah 1: SELALU cari dokumen (walau tidak dibutuhkan!)
    dokumen = retriever.search(pertanyaan, k=5, mode="hybrid", role="operator", active_only=True)
    jumlah_pencarian += 1
    konteks = format_context(dokumen)
    # Langkah 2: hasilkan jawaban dengan konteks itu
    pesan = [
        SystemMessage(content="Jawab berdasarkan konteks yang diberikan. Jawab singkat dalam Bahasa Indonesia."),
        HumanMessage(content=f"<konteks>\n{konteks}\n</konteks>\n\nPertanyaan: {pertanyaan}"),
    ]
    return model.invoke(pesan).content, sorted({d.metadata["doc_id"] for d in dokumen})


def coba(label: str, pertanyaan: str) -> None:
    print(f"[{label}] Pertanyaan: {pertanyaan}")
    mulai = time.time()
    jawaban, id_dokumen = rag_tradisional(pertanyaan)
    print(f"   Pencarian dijalankan: ya, dokumen yang dibawa ke model: {id_dokumen}")
    print(f"   Jawaban: {jawaban[:220]}")
    print(f"   Waktu: {time.time() - mulai:.1f} dtk")

# %% [markdown]
# ## Langkah 3 - Pertanyaan pengetahuan umum: 2 + 2

# %%
coba("Pengetahuan umum", "Berapa 2 + 2?")

# %% [markdown]
# ## Langkah 4 - Pertanyaan yang butuh dokumen

# %%
coba("Butuh dokumen", "Pada konsentrasi H2S berapa pekerja wajib menghentikan pekerjaan dan evakuasi?")

# %% [markdown]
# ## Langkah 5 - Pertanyaan pengetahuan umum: ibu kota

# %%
coba("Pengetahuan umum", "Apa ibu kota Prancis?")

# %% [markdown]
# ## Langkah 6 - Rekap

# %%
print(f"Total pencarian: {jumlah_pencarian} dari 3 pertanyaan")

# %% [markdown]
# ## Masalahnya
# - Pertanyaan pengetahuan umum tetap menjalankan pencarian, dan chunk SOP yang tidak relevan ikut ke model
# - Setiap pertanyaan membayar biaya pencarian dan token konteks tambahan
# - Konteks yang tidak relevan bisa membingungkan model
# - Tetapi pola ini sederhana, bisa diprediksi, dan tepat kalau SETIAP pertanyaan memang butuh dokumen
