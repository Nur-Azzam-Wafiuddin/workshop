# %% [markdown]
# # Latihan 1: Menghubungkan ke Server MCP Context7
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Skrip ini:
#
# - Menghubungkan ke server publik Context7 (https://mcp.context7.com/mcp)
# - Mendaftar semua tool yang ditawarkan server
# - Membuat agen yang memakai tool itu
# - Meminta dokumentasi sebuah library dan menampilkan jawabannya
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

# Klien membuka sesi per panggilan dan menutupnya sendiri, jadi tidak ada yang perlu ditutup antar sel.
# TODO(B9.1): buat MultiServerMCPClient dengan satu server "context7": transport "streamable_http" ke https://mcp.context7.com/mcp
client = None  # TODO: ganti dengan implementasi Anda

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Mendaftar tool dari Context7
# Kalau koneksi gagal (misalnya tanpa internet), pesan error dicetak dan daftar tool dibiarkan kosong.

# %%
try:
    # TODO(B9.2): ambil daftar tool lewat client.get_tools(), dijalankan dengan jalankan(...) dan batas waktu 30 detik (asyncio.wait_for)
    tools = []  # TODO: ganti dengan implementasi Anda
    print("Tool yang tersedia dari Context7:")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description.strip().splitlines()[0][:100]}")
    print()
except Exception as error:
    tools = []
    print(f"Tidak dapat menyelesaikan: {type(error).__name__}: {error}")
    print("Periksa koneksi internet Anda atau coba lagi nanti.")

# %% [markdown]
# ## Langkah 3 - Membuat agen dan meminta dokumentasi
# Agen memutuskan sendiri tool Context7 mana yang dipanggil untuk mengambil dokumentasi FastAPI terbaru.

# %%
# TODO(B9.3): buat agen dari model dan tool MCP
agent = None  # TODO: ganti dengan implementasi Anda

pertanyaan = (
    "Bagaimana cara membuat endpoint POST dengan FastAPI yang menerima JSON dan divalidasi dengan model Pydantic? "
    "Ambil dokumentasi terbaru. Jawab singkat dalam Bahasa Indonesia dengan satu contoh kode pendek."
)
print(f"Pengguna: {pertanyaan}\n")
try:
    response = jalankan(asyncio.wait_for(agent.ainvoke({"messages": [("human", pertanyaan)]}), timeout=180))
    panggilan = [c["name"] for m in response["messages"] for c in getattr(m, "tool_calls", [])]
    print(f"Tool MCP yang dipanggil: {panggilan}\n")
    print(f"Agen: {response['messages'][-1].content}")
except Exception as error:
    print(f"Tidak dapat menyelesaikan: {type(error).__name__}: {error}")
    print("Periksa koneksi internet Anda atau coba lagi nanti.")
