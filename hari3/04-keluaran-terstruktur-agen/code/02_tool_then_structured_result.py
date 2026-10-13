# %% [markdown]
# # Contoh 2: Tool Dulu, Hasil Terstruktur Terakhir
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/04-keluaran-terstruktur-agen/code/02_tool_then_structured_result.py`
#
# Agen memanggil tool seperti biasa untuk mengambil data, lalu jawaban AKHIR-nya dibentuk sesuai skema Pydantic.

# %%
# Langkah 1 - Menyiapkan model dan skema laporan
from typing import Literal

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

from migas_shared.field_tools import cek_status_sumur

load_dotenv()

print("Tool Dulu, Hasil Terstruktur Terakhir\n")

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)


class LaporanStatusSumur(BaseModel):
    """Laporan status satu sumur untuk dimasukkan ke sistem pemantauan."""
    kode_sumur: str = Field(description="Kode sumur, contoh SR-020")
    status: Literal["Produksi", "Shut-in", "Menunggu pulling", "Lainnya"] = Field(description="Status operasi sumur")
    minyak_bopd: float = Field(description="Produksi minyak dalam bopd")
    air_bwpd: float = Field(description="Produksi air dalam bwpd")
    perlu_perhatian: bool = Field(description="True jika ada catatan yang memerlukan tindak lanjut")
    saran: str = Field(description="Satu kalimat saran tindak lanjut")


# %% [markdown]
# ## Langkah 2 - Membuat agen dengan tool dan response_format

# %%
agent = create_agent(
    model,
    tools=[cek_status_sumur],  # tool bekerja persis seperti sebelumnya
    system_prompt=(
        "Anda adalah asisten pemantau sumur. Selalu pakai tool cek_status_sumur untuk data. "
        "Setelah data diperoleh, berikan jawaban akhir sebagai LaporanStatusSumur."
    ),
    response_format=LaporanStatusSumur,  # bentuk jawaban AKHIR
)

# %% [markdown]
# ## Langkah 3 - Menjalankan agen dan memeriksa tool yang dipanggil

# %%
query = "Bagaimana kondisi sumur SR-027? Perlu tindak lanjut apa?"
print(f"Pengguna: {query}\n")
response = agent.invoke({"messages": [HumanMessage(content=query)]})

# Tool apa saja yang dipanggil agen?
tools_dipakai = [
    call["name"]
    for message in response["messages"]
    if isinstance(message, AIMessage)
    for call in message.tool_calls
]
print(f"Tool yang dipanggil agen: {tools_dipakai}")

# %% [markdown]
# ## Langkah 4 - Membaca hasil terstruktur
# Selalu jaga kemungkinan model tidak menghasilkan struktur.

# %%
laporan = response.get("structured_response")
if laporan is None:
    print("Tidak ada hasil terstruktur. Jawaban teks:", response["messages"][-1].content)
else:
    print(f"structured_response: {laporan}\n")
    print(f"   kode_sumur      = {laporan.kode_sumur}")
    print(f"   status          = {laporan.status}")
    print(f"   minyak_bopd     = {laporan.minyak_bopd}")
    print(f"   air_bwpd        = {laporan.air_bwpd}")
    print(f"   perlu_perhatian = {laporan.perlu_perhatian}")
    print(f"   saran           = {laporan.saran}")

    if laporan.perlu_perhatian:
        print("\nSumur ditandai perlu perhatian (diputuskan oleh `if` pada nilai bool, tanpa mengurai teks)")
