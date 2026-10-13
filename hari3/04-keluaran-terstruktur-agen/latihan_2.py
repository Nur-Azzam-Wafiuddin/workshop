# %% [markdown]
# # Bab 4 - Latihan Bonus: Agen Triase Cerdas
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Menggabungkan tool pencari riwayat, Union skema (`WOExtract` atau `KlasifikasiInsiden`), dan keputusan eskalasi
# yang diambil oleh kode Python biasa.

# %%
# Langkah 1 - Menyiapkan model
import os
from typing import Union

import pandas as pd
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from migas_shared.config import DATA
from migas_shared.data import KlasifikasiInsiden, WOExtract

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    temperature=0,
)

# %% [markdown]
# ## Langkah 2 - Tool riwayat work order dan agen triase
# Tool menghitung riwayat work order sebuah aset dari data nyata. Agen memilih skema `WOExtract` atau
# `KlasifikasiInsiden` sesuai isi pesan.

# %%
_WO = pd.read_csv(DATA / "eval" / "work_orders_truth.csv")


# TODO(B4.5): buat tool riwayat_work_order(asset_id) yang menghitung jumlah work order, total downtime, dan kategori kegagalan terbanyak dari _WO; kembalikan pesan bila aset tidak punya riwayat
riwayat_work_order = None  # TODO: ganti dengan implementasi Anda


# TODO(B4.6): buat agen dengan tool riwayat_work_order, system prompt pemilah pesan, dan response_format=ToolStrategy(Union[WOExtract, KlasifikasiInsiden])
agent = None  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 3 - Keputusan eskalasi oleh kode
# Keputusan eskalasi diambil oleh kode Python biasa, bukan oleh model.

# %%
def keputusan(hasil) -> str:
    """Keputusan eskalasi oleh kode, bukan oleh model."""
    # TODO(B4.7): kembalikan keputusan eskalasi dengan kode biasa: WOExtract dengan safety_flag atau downtime 24 jam ke atas, KlasifikasiInsiden dengan severity Tinggi, selain itu rutin
    raise NotImplementedError("TODO(B4.7)")


# %% [markdown]
# ## Langkah 4 - Pesan 1: ESP trip, motor terbakar

# %%
teks = "ESP SR-020 trip OL, coba restart 2x gagal. Megger motor 0 Mohm, motor burnt. Usul pulling ganti motor. downtime 5 jam."
print(f"Pesan: {teks}")
response = agent.invoke({"messages": [HumanMessage(content=teks)]})
hasil = response.get("structured_response")
print(f"   Skema terpilih : {type(hasil).__name__ if hasil else 'None'}")
print(f"   Isi            : {hasil}")
print(f"   Keputusan kode : {keputusan(hasil)}\n")

# %% [markdown]
# ## Langkah 5 - Pesan 2: gasket bocor dengan alarm LEL

# %%
teks = "K-ML1-201 gasket flange bocor, ada alarm LEL menyala, diganti, downtime 6 jam."
print(f"Pesan: {teks}")
response = agent.invoke({"messages": [HumanMessage(content=teks)]})
hasil = response.get("structured_response")
print(f"   Skema terpilih : {type(hasil).__name__ if hasil else 'None'}")
print(f"   Isi            : {hasil}")
print(f"   Keputusan kode : {keputusan(hasil)}\n")

# %% [markdown]
# ## Langkah 6 - Pesan 3: pekerja jatuh dari scaffold

# %%
teks = "Pekerja kontraktor jatuh dari scaffold setinggi 3 meter di workshop, patah tulang lengan, tidak dapat bekerja beberapa minggu."
print(f"Pesan: {teks}")
response = agent.invoke({"messages": [HumanMessage(content=teks)]})
hasil = response.get("structured_response")
print(f"   Skema terpilih : {type(hasil).__name__ if hasil else 'None'}")
print(f"   Isi            : {hasil}")
print(f"   Keputusan kode : {keputusan(hasil)}\n")
