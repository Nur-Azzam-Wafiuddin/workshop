# %% [markdown]
# # Contoh 4: Sistem Multi-Tool
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/02-tools-function-calling/code/04_multiple_tools.py`
#
# Model diberi tiga tool sekaligus dan memilih sendiri tool yang tepat (atau tidak memakai tool sama sekali)
# untuk setiap pertanyaan.

# %%
# Langkah 1 - Menyiapkan model
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Mendefinisikan tiga tool
# Water cut, konversi satuan, dan status sumur, masing-masing dengan skema masukan sendiri.

# %%
class WaterCutInput(BaseModel):
    oil_bopd: float = Field(ge=0, description="Produksi minyak dalam bopd")
    water_bwpd: float = Field(ge=0, description="Produksi air dalam bwpd")


class KonversiInput(BaseModel):
    nilai: float = Field(description="Angka yang dikonversi")
    dari: Literal["bbl", "m3", "psi", "bar"] = Field(description="Satuan asal")
    ke: Literal["bbl", "m3", "psi", "bar"] = Field(description="Satuan tujuan")


class StatusSumurInput(BaseModel):
    kode_sumur: str = Field(description="Kode sumur, contoh SR-020")


@tool(args_schema=WaterCutInput)
def hitung_water_cut(oil_bopd: float, water_bwpd: float) -> str:
    """Hitung water cut (persen air dalam total cairan produksi) dari produksi minyak dan air."""
    total = oil_bopd + water_bwpd
    return f"Water cut = {water_bwpd / total * 100:.1f}%" if total else "Total produksi 0"


@tool(args_schema=KonversiInput)
def konversi_satuan(nilai: float, dari: str, ke: str) -> str:
    """Konversi satuan volume (bbl dan m3) atau tekanan (psi dan bar)."""
    faktor = {("bbl", "m3"): 0.158987, ("m3", "bbl"): 1 / 0.158987, ("psi", "bar"): 0.0689476, ("bar", "psi"): 14.5038}
    if dari == ke:
        return f"{nilai} {ke}"
    if (dari, ke) not in faktor:
        return f"Konversi {dari} ke {ke} tidak didukung (volume dan tekanan tidak dapat saling dikonversi)."
    return f"{nilai} {dari} = {nilai * faktor[(dari, ke)]:.3f} {ke}"


@tool(args_schema=StatusSumurInput)
def cek_status_sumur(kode_sumur: str) -> str:
    """Cek status operasi sebuah sumur berdasarkan kodenya."""
    return f"Sumur {kode_sumur}: status Produksi"


model_with_tools = model.bind_tools([hitung_water_cut, konversi_satuan, cek_status_sumur])

# %% [markdown]
# ## Langkah 3 - Water cut
# Pertanyaan yang cocok dengan `hitung_water_cut`.

# %%
query = "Produksi minyak 200 bopd dan air 300 bwpd, berapa water cut-nya?"
response = model_with_tools.invoke(query)
print(f"Pertanyaan: {query}")
if response.tool_calls:
    for pemanggilan in response.tool_calls:
        print(f"  Tool dipilih: {pemanggilan['name']}")
        print(f"  Argumen     : {pemanggilan['args']}")
else:
    print("  Tidak memanggil tool (model menjawab langsung)")

# %% [markdown]
# ## Langkah 4 - Konversi satuan
# Pertanyaan yang cocok dengan `konversi_satuan`.

# %%
query = "Tekanan wellhead 1500 psi itu berapa bar?"
response = model_with_tools.invoke(query)
print(f"Pertanyaan: {query}")
if response.tool_calls:
    for pemanggilan in response.tool_calls:
        print(f"  Tool dipilih: {pemanggilan['name']}")
        print(f"  Argumen     : {pemanggilan['args']}")
else:
    print("  Tidak memanggil tool (model menjawab langsung)")

# %% [markdown]
# ## Langkah 5 - Status sumur
# Pertanyaan yang cocok dengan `cek_status_sumur`.

# %%
query = "Apa status sumur KN-033?"
response = model_with_tools.invoke(query)
print(f"Pertanyaan: {query}")
if response.tool_calls:
    for pemanggilan in response.tool_calls:
        print(f"  Tool dipilih: {pemanggilan['name']}")
        print(f"  Argumen     : {pemanggilan['args']}")
else:
    print("  Tidak memanggil tool (model menjawab langsung)")

# %% [markdown]
# ## Langkah 6 - Pertanyaan tanpa tool
# Tidak ada tool yang relevan, jadi model seharusnya menjawab langsung.

# %%
query = "Apa kepanjangan SOP?"
response = model_with_tools.invoke(query)
print(f"Pertanyaan: {query}")
if response.tool_calls:
    for pemanggilan in response.tool_calls:
        print(f"  Tool dipilih: {pemanggilan['name']}")
        print(f"  Argumen     : {pemanggilan['args']}")
else:
    print("  Tidak memanggil tool (model menjawab langsung)")
