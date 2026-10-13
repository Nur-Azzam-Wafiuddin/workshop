# %% [markdown]
# # Latihan 2: Agen Multi-Tool dengan MCP
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Menggabungkan tool dari server MCP (lapangan, stdio) dengan tool yang Anda tulis sendiri di Python,
# dalam SATU agen. Agen memilih tool dari deskripsinya, tidak peduli dari mana tool itu berasal.
#
# - Tool MCP: hitung_water_cut, konversi_satuan, cek_status_sumur (`field_stdio_server.py`)
# - Tool lokal: hitung_kerugian_produksi (ditulis di file ini)
#
# Kode async dijalankan lewat `jalankan(...)` dari `migas_shared.tampil`, yang bekerja di skrip biasa maupun
# di Jupyter/Interactive Window.

# %%
# Langkah 1 - Impor dan model
import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from migas_shared.config import ROOT
from migas_shared.tampil import jalankan

load_dotenv()

PATH_SERVER = ROOT / "hari4" / "09-mcp" / "code" / "servers" / "field_stdio_server.py"

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Tool lokal
# Skema masukan Pydantic dan tool `hitung_kerugian_produksi`, ditulis langsung di Python.

# %%
class KerugianInput(BaseModel):
    """Skema masukan tool kerugian produksi."""

    # TODO(B9.4): definisikan field KerugianInput: downtime_jam dan laju_normal_bopd (float, keduanya >= 0, dengan description)
    pass  # TODO: definisikan field


# TODO(B9.5): buat tool hitung_kerugian_produksi yang mencetak panggilannya, lalu menghitung barel hilang = laju_normal_bopd * downtime_jam / 24
hitung_kerugian_produksi = None  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 3 - Menggabungkan tool MCP dan tool lokal
# Klien membuka sesi per panggilan dan menutupnya sendiri, jadi tidak ada yang perlu ditutup antar sel.

# %%
# TODO(B9.6): buat MultiServerMCPClient untuk satu server stdio "lapangan" yang menjalankan PATH_SERVER dengan sys.executable
client = None  # TODO: ganti dengan implementasi Anda
# TODO(B9.7): ambil tool MCP dengan jalankan(client.get_tools()), lalu gabungkan dengan tool lokal menjadi semua_tool
tools_mcp = []  # TODO: ganti dengan implementasi Anda
semua_tool = []  # TODO: ganti dengan implementasi Anda
print(f"Tool MCP:   {[t.name for t in tools_mcp]}")
print(f"Tool lokal: {[hitung_kerugian_produksi.name]}\n")

# %% [markdown]
# ## Langkah 4 - Membuat agen
# Satu agen menerima semua tool, tanpa peduli asalnya.

# %%
# TODO(B9.8): buat agen dari model dan semua_tool dengan system prompt asisten teknis lapangan (pakai tool, jangan menghitung sendiri)
agent = None  # TODO: ganti dengan implementasi Anda


def tanya_agen(pertanyaan: str) -> None:
    print(f"Pengguna: {pertanyaan}")
    response = jalankan(agent.ainvoke({"messages": [("human", pertanyaan)]}))
    panggilan = [c["name"] for m in response["messages"] for c in getattr(m, "tool_calls", [])]
    print(f"   Tool yang dipanggil: {panggilan}")
    print(f"Agen: {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 5 - Pertanyaan 1: memakai tool MCP

# %%
tanya_agen("Berapa water cut sumur dengan produksi 95 bopd minyak dan 380 bwpd air?")  # tool MCP

# %% [markdown]
# ## Langkah 6 - Pertanyaan 2: memakai tool lokal

# %%
tanya_agen("Sumur SR-020 mati 18 jam dengan laju normal 120 bopd. Berapa barel minyak yang hilang?")  # tool lokal

# %% [markdown]
# ## Langkah 7 - Pertanyaan 3: memakai keduanya

# %%
tanya_agen("Cek status sumur SR-027, lalu hitung kehilangan produksinya bila ia mati 10 jam pada laju normalnya.")  # keduanya
