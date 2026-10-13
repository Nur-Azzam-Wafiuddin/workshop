# %% [markdown]
# # Contoh 4: Integrasi Beberapa Server MCP Sekaligus
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/09-mcp/code/04_mcp_multi_server.py`
#
# Contoh ini menghubungkan satu agen ke BEBERAPA server MCP bersamaan. Agen menerima tool dari semua server
# dan memilih sendiri tool yang cocok untuk setiap pertanyaan.
#
# Server yang dipakai:
#
# - lapangan: perhitungan water cut, konversi satuan, status sumur (stdio, lokal)
# - dokumen: pencarian SOP dan laporan perusahaan (stdio, lokal, peran 'engineer')
# - context7: dokumentasi library software (HTTP, jarak jauh, OPSIONAL)
#
# Server yang gagal dihubungi dilewati dan agen tetap berjalan dengan server yang tersisa.
#
# Kekuatan MCP: satu klien, banyak server, interface seragam!
#
# Catatan: tool diambil per server dengan `client.get_tools(server_name=...)`. Setiap tool call membuka sesi
# sendiri (untuk server stdio berarti subproses baru) dan menutupnya sesudah selesai, sehingga tidak ada sesi
# yang perlu dijaga tetap terbuka antar sel. Untuk sesi tunggal yang bertahan lama, lihat Contoh 3.
#
# Kode async dijalankan lewat `jalankan(...)` dari `migas_shared.tampil`, yang bekerja di skrip biasa maupun
# di Jupyter/Interactive Window.

# %%
# Langkah 1 - Menyiapkan konfigurasi server, klien, dan model
import asyncio
import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from migas_shared.config import ROOT
from migas_shared.tampil import jalankan

load_dotenv()

FOLDER_SERVER = ROOT / "hari4" / "09-mcp" / "code" / "servers"


def konfigurasi_server() -> dict:
    env_dokumen = {"PERAN_PENGGUNA": "engineer", "PYTHONUTF8": "1"}
    for nama in ("EMBED_PROVIDER", "EMBED_MODEL", "EMBED_CACHE_DIR", "EMBED_BASE_URL", "EMBED_API_KEY"):
        if os.getenv(nama):
            env_dokumen[nama] = os.environ[nama]
    return {
        "lapangan": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(FOLDER_SERVER / "field_stdio_server.py")],
        },
        "dokumen": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(FOLDER_SERVER / "documents_stdio_server.py")],
            "env": env_dokumen,
        },
        "context7": {
            "transport": "streamable_http",
            "url": "https://mcp.context7.com/mcp",
        },
    }


client = MultiServerMCPClient(konfigurasi_server())

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Mengambil tool dari SEMUA server
# `ambil_semua_tool` mencoba tiap server satu per satu. Server yang gagal dilewati (graceful degradation).

# %%
async def ambil_semua_tool(client: MultiServerMCPClient) -> dict[str, list]:
    """Ambil tool per server. Server yang gagal dilewati. Mengembalikan {server: [tool]}."""
    tool_per_server: dict[str, list] = {}
    for nama in client.connections:
        try:
            tool_per_server[nama] = await asyncio.wait_for(client.get_tools(server_name=nama), timeout=60)
        except Exception as error:
            print(f"   Server '{nama}' dilewati: {type(error).__name__}")
    return tool_per_server


print("Mengambil tool dari semua server...")
tool_per_server = jalankan(ambil_semua_tool(client))
semua_tool = [t for daftar in tool_per_server.values() for t in daftar]

print(f"\nBerhasil mengambil {len(semua_tool)} tool dari {len(tool_per_server)} server:")
for server, daftar in tool_per_server.items():
    print(f"   Dari {server}:")
    for tool in daftar:
        print(f"      - {tool.name}")
print()

# %% [markdown]
# ## Langkah 3 - Membuat agen dengan tool dari SEMUA server
# Pola `create_agent()` yang sama. Agen memilih tool dari nama dan deskripsinya, apa pun servernya.

# %%
agent = create_agent(
    model,
    semua_tool,
    system_prompt=(
        "Anda asisten teknis lapangan migas. Pakai tool yang tersedia, jangan menebak angka, dan jawab "
        "singkat dalam Bahasa Indonesia. Untuk prosedur, rujuk id dokumennya."
    ),
)


def uji(judul: str, pertanyaan: str) -> None:
    print(f"{judul}\n")
    print(f"Pengguna: {pertanyaan}")
    response = jalankan(agent.ainvoke({"messages": [("human", pertanyaan)]}))
    panggilan = [c["name"] for m in response["messages"] for c in getattr(m, "tool_calls", [])]
    print(f"   Tool yang dipanggil: {panggilan}")
    print(f"Agen: {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 4 - Uji 1: pertanyaan hitungan
# Seharusnya memakai server lapangan.

# %%
uji("Uji 1: pertanyaan hitungan (seharusnya server lapangan)",
    "Sumur dengan produksi 120 bopd minyak dan 480 bwpd air, berapa water cut-nya?")

# %% [markdown]
# ## Langkah 5 - Uji 2: pertanyaan prosedur
# Seharusnya memakai server dokumen.

# %%
uji("Uji 2: pertanyaan prosedur (seharusnya server dokumen)",
    "Bagaimana prosedur bump test detektor gas portabel menurut SOP yang berlaku?")

# %% [markdown]
# ## Langkah 6 - Uji 3: pertanyaan gabungan
# Seharusnya memakai KEDUA server.

# %%
uji("Uji 3: pertanyaan gabungan (seharusnya KEDUA server)",
    "Cek status sumur SR-027, lalu cari di dokumen apa yang harus dilakukan bila alarm H2S berbunyi di sumur itu.")

# %% [markdown]
# ## Konsep Utama
# - `MultiServerMCPClient` menghubungkan banyak server sekaligus
# - Agen menerima tool dari SEMUA server yang tersambung
# - Agen memilih tool yang tepat dari nama dan deskripsinya, apa pun servernya
# - Campur transport berbeda (HTTP + stdio) tanpa mengubah kode agen
# - Server yang gagal dilewati: agen tetap bekerja dengan sisanya (graceful degradation)
# - Skala ke puluhan server tanpa mengubah kode agen!
#
# ## Kasus Penggunaan Nyata
# - Data produksi (SCADA) + dokumen SOP + sistem work order dalam satu agen
# - Alat internal perusahaan + layanan eksternal dalam satu interface
