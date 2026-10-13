# %% [markdown]
# # Contoh 2: Mengikat dan Memanggil Tool
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/02-tools-function-calling/code/02_tool_calling.py`
#
# Tool diikat ke model dengan `bind_tools`. Model hanya MEMINTA pemanggilan tool; tool belum dijalankan.

# %%
# Langkah 1 - Menyiapkan model, skema, dan tool
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)


class WaterCutInput(BaseModel):
    oil_bopd: float = Field(ge=0, description="Produksi minyak dalam bopd")
    water_bwpd: float = Field(ge=0, description="Produksi air dalam bwpd")


@tool(args_schema=WaterCutInput)
def hitung_water_cut(oil_bopd: float, water_bwpd: float) -> str:
    """Hitung water cut (persentase air dalam total cairan produksi) sebuah sumur."""
    total = oil_bopd + water_bwpd
    return f"Water cut = {water_bwpd / total * 100:.1f}%" if total else "Total produksi 0"


# %% [markdown]
# ## Langkah 2 - Mengikat tool ke model

# %%
# Ikat tool ke model
model_with_tools = model.bind_tools([hitung_water_cut])

# %% [markdown]
# ## Langkah 3 - Memanggil model dengan sebuah pertanyaan
# Perhatikan isi `tool_calls`: model menyebut tool apa dan argumen apa, tetapi tool belum dijalankan.

# %%
pertanyaan = "Sumur SR-020 memproduksi 120 bopd minyak dan 480 bwpd air. Berapa water cut-nya?"
response = model_with_tools.invoke(pertanyaan)

print("Pertanyaan:", pertanyaan)
print("\nIsi teks (content):", repr(response.content))
print("\nPermintaan tool call (tool_calls):")
for pemanggilan in response.tool_calls:
    print(f"  Nama     : {pemanggilan['name']}")
    print(f"  Argumen  : {pemanggilan['args']}")
    print(f"  ID       : {pemanggilan['id']}")

print("\nPerhatikan: tool BELUM dijalankan. Model hanya menjelaskan tool apa dan argumen apa.")
