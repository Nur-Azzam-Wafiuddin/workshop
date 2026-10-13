# %% [markdown]
# # Contoh 1: Agen dengan Integrasi Server MCP (Context7)
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/09-mcp/code/01_mcp_context7.py`
#
# Contoh ini menghubungkan agen ke server MCP Context7, penyedia dokumentasi library software
# yang terkini dan spesifik versi, langsung ke agen Anda. Ini server MCP JARAK JAUH publik, diakses lewat
# transport Streamable HTTP, sehingga butuh koneksi internet.
#
# Tool Context7 yang diambil klien (nama dan jumlahnya bisa berubah mengikuti pembaruan server):
#
# - `resolve-library-id`: mengubah nama library menjadi ID Context7
# - `query-docs`: mengambil dokumentasi library untuk sebuah pertanyaan
#
# Prasyarat:
#
# 1. Pasang langchain-mcp-adapters: `pip install langchain-mcp-adapters`
# 2. Opsional: API key Context7 untuk rate limit lebih tinggi (https://context7.com)
#
# Kode async dijalankan lewat `jalankan(...)` dari `migas_shared.tampil`, yang bekerja di skrip biasa maupun
# di Jupyter/Interactive Window.

# %%
# Langkah 1 - Menyiapkan klien MCP dan model
import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from migas_shared.tampil import jalankan

load_dotenv()

# Server MCP Context7 - menyediakan dokumentasi library
# Jarak jauh (HTTP): https://mcp.context7.com/mcp (disarankan)
# Lokal (HTTP): http://localhost:3000/mcp (kalau Context7 dijalankan sendiri)
url_server_mcp = os.getenv("MCP_SERVER_URL", "https://mcp.context7.com/mcp")

print(f"Menghubungkan ke server MCP di: {url_server_mcp}\n")

# Buat klien MCP dengan transport HTTP ke Context7.
# Klien membuka sesi per panggilan dan menutupnya sendiri, jadi tidak ada yang perlu ditutup antar sel.
client = MultiServerMCPClient(
    {
        "context7": {
            "transport": "streamable_http",
            "url": url_server_mcp,
            # Opsional: tambahkan API key Context7 untuk rate limit lebih tinggi
            # "headers": {
            #     "Authorization": f"Bearer {os.getenv('CONTEXT7_API_KEY')}"
            # }
        },
    }
)

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Mengambil tool dari server Context7
# `client.get_tools()` menghubungi server dan mengembalikan tool MCP sebagai tool LangChain biasa.
# Kalau koneksi gagal (misalnya tanpa internet), pesan error dicetak dan daftar tool dibiarkan kosong.

# %%
print("Mengambil tool dari server MCP Context7...")
try:
    tools = jalankan(asyncio.wait_for(client.get_tools(), timeout=30))

    print(f"Berhasil mengambil {len(tools)} tool dari Context7:")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description[:90].strip()}...")
    print()
except Exception as error:
    tools = []
    print(f"Error saat menghubungi server MCP Context7: {type(error).__name__}: {error}")
    print("Periksa koneksi internet Anda. Contoh berikutnya memakai server lokal dan tidak butuh internet.")

# %% [markdown]
# ## Langkah 3 - Membuat agen dengan tool MCP
# Pola `create_agent()` yang sama. Tool dari server MCP adalah satu-satunya perbedaan.

# %%
print("Membuat agen dengan tool MCP...\n")
agent = create_agent(model, tools)

# %% [markdown]
# ## Langkah 4 - Meminta dokumentasi lewat agen
# Pertanyaan yang berguna bagi analis data lapangan. Agen memutuskan sendiri tool Context7 mana yang dipanggil.

# %%
pertanyaan = (
    "Bagaimana cara membaca file CSV dengan pustaka pandas lalu menghitung rata-rata per kolom? "
    "Ambil dokumentasi terbaru. Jawab singkat dalam Bahasa Indonesia."
)
print(f"Pengguna: {pertanyaan}\n")

try:
    response = jalankan(asyncio.wait_for(agent.ainvoke({"messages": [("human", pertanyaan)]}), timeout=180))
    panggilan = [c["name"] for m in response["messages"] for c in getattr(m, "tool_calls", [])]
    print(f"Tool MCP yang dipanggil agen: {panggilan}\n")
    print(f"Agen: {response['messages'][-1].content}\n")
except Exception as error:
    print(f"Error saat menghubungi server MCP Context7: {type(error).__name__}: {error}")
    print("Periksa koneksi internet Anda. Contoh berikutnya memakai server lokal dan tidak butuh internet.")

# %% [markdown]
# ## Konsep Utama
# - MCP menyediakan akses terstandar ke tool eksternal
# - `MultiServerMCPClient` menghubungkan ke satu atau lebih server MCP
# - Transport HTTP bekerja dengan server jarak jauh seperti Context7
# - Tool dari server MCP bekerja mulus dengan `create_agent()`
# - Pola `create_agent()` yang sama, sumber tool yang berbeda!
