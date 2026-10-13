# %% [markdown]
# # Contoh 5: Tool Pencarian Dokumen
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/02-tools-function-calling/code/05_document_search_tool.py`
#
# Tool pencarian dokumen: pipeline retrieval workshop dibungkus menjadi tool.
#
# Siklus 3 langkah sama seperti contoh sebelumnya (model merencanakan, kode menjalankan, model menjawab),
# hanya kali ini tool-nya mencari di SOP dan manual.
#
# Di sini role pengguna ditulis tetap di dalam kode ("engineer"). Di bab 3 dan seterusnya, role dibaca dari
# konteks runtime sehingga tidak bisa diubah oleh model.

# %%
# Langkah 1 - Menyiapkan model
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

from migas_shared import rag_pipeline as rp
from migas_shared.rag_tools import build_retriever

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Membuat tool pencarian
# Role pengguna ditetapkan oleh program, bukan oleh model.

# %%
ROLE_PENGGUNA = "engineer"  # ditetapkan oleh program, bukan oleh model


class CariInput(BaseModel):
    query: str = Field(description="Kalimat pencarian dengan istilah teknis, contoh 'alarm H2S tindakan'")


@tool(args_schema=CariInput)
def cari_prosedur(query: str) -> str:
    """Cari chunk SOP, manual, dan laporan yang berstatus aktif. Hasil berupa blok <dokumen id=... revisi=... bagian=...>
    yang dapat dikutip. Pakai untuk pertanyaan tentang prosedur, batas alarm, dan langkah kerja."""
    docs = build_retriever().search(query, k=3, mode="hybrid", role=ROLE_PENGGUNA, active_only=True)
    return rp.format_context(docs) if docs else "Tidak ada dokumen yang relevan."


model_with_tools = model.bind_tools([cari_prosedur])

# %% [markdown]
# ## Langkah 3 - Model merencanakan pencarian
# Model boleh meminta lebih dari satu pencarian sekaligus; setiap permintaan WAJIB dijawab dengan `ToolMessage`.

# %%
query = "Berapa jarak minimal muster point dari sumber gas H2S menurut SOP yang berlaku?"
print("Pengguna:", query)

response1 = model_with_tools.invoke(query)
for tool_call in response1.tool_calls:
    print("\nLangkah 1 - Model meminta tool:", tool_call["name"], tool_call["args"])

# %% [markdown]
# ## Langkah 4 - Kode menjalankan setiap pencarian di basis dokumen

# %%
messages = [
    HumanMessage(content="Jawab hanya berdasarkan dokumen dan sebut ID dokumennya. " + query),
    AIMessage(content="", tool_calls=response1.tool_calls),
]
for tool_call in response1.tool_calls:
    hasil = cari_prosedur.invoke(tool_call["args"])
    print(f"\nLangkah 2 - Hasil pencarian ({len(hasil)} karakter), chunk awal:")
    print(hasil[:400] + " ...")
    messages.append(ToolMessage(content=hasil, tool_call_id=tool_call["id"]))

# %% [markdown]
# ## Langkah 5 - Model menjawab berdasarkan dokumen yang ditemukan

# %%
jawaban = model.invoke(messages)
print("Langkah 3 - Jawaban akhir:")
print(jawaban.content)
