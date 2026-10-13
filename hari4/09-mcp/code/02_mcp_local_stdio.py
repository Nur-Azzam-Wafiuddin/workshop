# %% [markdown]
# # Contoh 2: MCP dengan Transport stdio
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/09-mcp/code/02_mcp_local_stdio.py`
#
# Contoh ini memakai transport stdio untuk terhubung ke server MCP yang berjalan sebagai SUBPROSES,
# berkomunikasi lewat aliran input/output standar. Tanpa internet dan tanpa server yang harus dijalankan
# terpisah: klien yang menjalankan dan mengelola prosesnya.
#
# Perbandingan:
#
# - Contoh 1: transport HTTP (komunikasi lewat jaringan)
# - Contoh 2: transport stdio (komunikasi antarproses)
#
# Kode async dijalankan lewat `jalankan(...)` dari `migas_shared.tampil`, yang bekerja di skrip biasa maupun
# di Jupyter/Interactive Window.

# %%
# Langkah 1 - Menyiapkan klien MCP stdio dan model
import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from migas_shared.config import ROOT
from migas_shared.tampil import jalankan

load_dotenv()

# Path ke server lapangan lokal
path_server = ROOT / "hari4" / "09-mcp" / "code" / "servers" / "field_stdio_server.py"

# Buat klien MCP dengan transport stdio - menjalankan server sebagai subproses.
# Klien membuka sesi per panggilan dan menutupnya sendiri, jadi tidak ada yang perlu ditutup antar sel.
client = MultiServerMCPClient(
    {
        "lapangan": {
            "transport": "stdio",
            "command": sys.executable,  # interpreter Python yang sama dengan skrip ini
            "args": [str(path_server)],
        }
    }
)

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Mengambil tool dari server lokal
# Klien menjalankan server sebagai subproses dan meminta daftar tool-nya.

# %%
print("Menghubungkan ke server MCP stdio...")
tools = jalankan(client.get_tools())

print(f"Terhubung! Mengambil {len(tools)} tool dari server lokal:")
for tool in tools:
    print(f"   - {tool.name}: {tool.description.strip().splitlines()[0]}")
print()

# %% [markdown]
# ## Langkah 3 - Membuat agen dengan tool MCP stdio
# Fungsi `tanya_agen` mengirim satu pertanyaan ke agen dan mencetak tool MCP yang dipanggil.

# %%
agent = create_agent(model, tools)


def tanya_agen(pertanyaan: str) -> None:
    print(f"Pengguna: {pertanyaan}")
    response = jalankan(agent.ainvoke({"messages": [("human", pertanyaan)]}))
    panggilan = [c["name"] for m in response["messages"] for c in getattr(m, "tool_calls", [])]
    print(f"   Tool MCP yang dipanggil: {panggilan}")
    print(f"Agen: {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 4 - Pertanyaan 1: water cut
# Agen perlu memanggil tool perhitungan water cut dari server lapangan.

# %%
tanya_agen("Sumur SR-020 memproduksi 120 bopd minyak dan 480 bwpd air. Berapa water cut-nya?")

# %% [markdown]
# ## Langkah 5 - Pertanyaan 2: konversi satuan

# %%
tanya_agen("Ubah tekanan wellhead 450 psi menjadi bar.")

# %% [markdown]
# ## Langkah 6 - Pertanyaan 3: status sumur dan konversi
# Pertanyaan gabungan: status sumur dari server, lalu konversi ke meter kubik per hari.

# %%
tanya_agen("Bagaimana status sumur KN-033, dan berapa produksi hariannya dalam meter kubik per hari bila 1 bbl = 0,159 m3?")

# %% [markdown]
# ## Konsep Utama
# - Transport stdio menjalankan server MCP sebagai subproses
# - Komunikasi lewat aliran input/output standar
# - Server berjalan sebagai proses anak dari klien
# - Transport HTTP memakai komunikasi jaringan
# - Transport stdio memakai komunikasi antarproses
# - Kode agen yang sama bekerja dengan kedua transport!
#
# ## Perbandingan Transport
# - stdio: komunikasi proses lewat stdin/stdout
# - HTTP: komunikasi jaringan lewat permintaan HTTP
# - Pilih sesuai kebutuhan arsitektur Anda!
