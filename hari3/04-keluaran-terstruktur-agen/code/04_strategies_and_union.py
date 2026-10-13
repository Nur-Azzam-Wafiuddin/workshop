# %% [markdown]
# # Contoh 4: Strategi Structured Output dan Union
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/04-keluaran-terstruktur-agen/code/04_strategies_and_union.py`
#
# `response_format` bisa dibungkus `ToolStrategy` (skema ditawarkan ke model sebagai tool) atau
# `ProviderStrategy` (structured output asli penyedia). `Union` membiarkan agen memilih skema yang cocok.

# %%
# Langkah 1 - Menyiapkan model dan data contoh
from typing import Union

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy, ToolStrategy
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from migas_shared.data import KlasifikasiInsiden, WOExtract

load_dotenv()

NARASI_HSE = (
    "Pada 30/01/2026 pukul 14.15 di GS-SR1, baut jatuh dari pipe rack ketika lifting. "
    "Beruntung tidak ada yang cedera dan tidak ada aset rusak. Dilaporkan sebagai pembelajaran."
)
CATATAN_WO = "K-ML1-201 gasket flange bocor, diganti baru, downtime 6 jam. Ada ceceran kondensat kecil."

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Bagian 1: ToolStrategy eksplisit
# Skema ditawarkan ke model sebagai tool.

# %%
print("Bagian 1: ToolStrategy (skema ditawarkan ke model sebagai tool)")
print("-" * 60)
agen_tool = create_agent(
    model,
    tools=[],
    system_prompt="Klasifikasikan laporan insiden HSE. Berikan jawaban akhir sebagai KlasifikasiInsiden.",
    response_format=ToolStrategy(KlasifikasiInsiden),
)
respons = agen_tool.invoke({"messages": [HumanMessage(content=NARASI_HSE)]})
print(respons.get("structured_response"))

# %% [markdown]
# ## Langkah 3 - Bagian 2: Union skema
# Agen memilih `WOExtract` ATAU `KlasifikasiInsiden`, tergantung isi masukan.

# %%
print("Bagian 2: Union skema (agen memilih skema yang cocok dengan masukan)")
print("-" * 60)
agen_triase = create_agent(
    model,
    tools=[],
    system_prompt=(
        "Anda memilah pesan masuk. Catatan perbaikan peralatan diisi sebagai WOExtract. "
        "Laporan kejadian keselamatan (insiden, near miss) diisi sebagai KlasifikasiInsiden."
    ),
    response_format=ToolStrategy(Union[WOExtract, KlasifikasiInsiden]),
)
for teks in [CATATAN_WO, NARASI_HSE]:
    respons = agen_triase.invoke({"messages": [HumanMessage(content=teks)]})
    hasil = respons.get("structured_response")
    print(f"Masukan: {teks[:70]}...")
    print(f"   -> {type(hasil).__name__ if hasil else 'None'}: {hasil}\n")

# %% [markdown]
# ## Langkah 4 - Bagian 3: ProviderStrategy
# Butuh penyedia dengan dukungan JSON-schema asli.

# %%
print("Bagian 3: ProviderStrategy (structured output asli penyedia)")
print("-" * 60)
try:
    agen_asli = create_agent(model, tools=[], response_format=ProviderStrategy(KlasifikasiInsiden))
    respons = agen_asli.invoke({"messages": [HumanMessage(content=NARASI_HSE)]})
    print(respons.get("structured_response"))
except Exception as error:
    print(f"ProviderStrategy tidak didukung oleh endpoint ini: {type(error).__name__}")
