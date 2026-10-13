# %% [markdown]
# # Contoh 5: Penanganan Error dan Pola Produksi pada MCP
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/09-mcp/code/05_mcp_error_handling.py`
#
# Contoh ini memperlihatkan pola yang dipakai di produksi ketika server MCP bermasalah:
#
# - Retry dengan delay yang makin panjang (exponential backoff)
# - Timeout pada setiap operasi jaringan
# - Server utama + server fallback
# - Graceful degradation: aplikasi tetap bekerja walau sebagian server tidak tersedia
# - Error dari tool MCP yang kembali ke model sebagai informasi
# - Pemeriksaan kesehatan (health check)
#
# Pola ini penting untuk integrasi MCP yang andal!
#
# Kode async dijalankan lewat `jalankan(...)` dari `migas_shared.tampil`, yang bekerja di skrip biasa maupun
# di Jupyter/Interactive Window.

# %%
# Langkah 1 - Impor, fungsi bantu retry, dan konfigurasi server
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

SERVER_LAPANGAN = ROOT / "hari4" / "09-mcp" / "code" / "servers" / "field_stdio_server.py"


async def dengan_coba_ulang(fungsi, percobaan: int = 3, delay_awal: float = 1.0):
    """Jalankan fungsi async; bila gagal, tunggu 1 dtk, lalu 2 dtk, lalu 4 dtk... dan coba lagi."""
    for ke in range(1, percobaan + 1):
        try:
            return await fungsi()
        except Exception as error:
            if ke == percobaan:
                raise
            delay = delay_awal * 2 ** (ke - 1)
            print(f"   Percobaan {ke} gagal ({type(error).__name__}); mencoba lagi dalam {delay:.0f} dtk")
            await asyncio.sleep(delay)


async def ambil_tool(konfigurasi: dict, label: str, batas_waktu: float = 20.0) -> list:
    """Ambil tool dari satu server dengan batas waktu dan coba ulang. Mengembalikan [] bila tetap gagal."""
    client = MultiServerMCPClient(konfigurasi)
    try:
        tools = await dengan_coba_ulang(lambda: asyncio.wait_for(client.get_tools(), timeout=batas_waktu), percobaan=2)
        print(f"   {label}: tersambung, {len(tools)} tool")
        return tools
    except Exception as error:
        print(f"   {label}: GAGAL ({type(error).__name__})")
        return []


async def cek_kesehatan(konfigurasi: dict) -> bool:
    """Server dianggap sehat bila daftar tool dapat diambil dalam 5 detik dan tidak kosong."""
    try:
        tools = await asyncio.wait_for(MultiServerMCPClient(konfigurasi).get_tools(), timeout=5.0)
        return len(tools) > 0
    except Exception:
        return False


# Utama: server yang SENGAJA tidak ada (simulasi server mati). Cadangan: server lapangan lokal.
utama = {"gudang_data": {"transport": "streamable_http", "url": "http://127.0.0.1:9/mcp"}}
cadangan = {"lapangan": {"transport": "stdio", "command": sys.executable, "args": [str(SERVER_LAPANGAN)]}}

# %% [markdown]
# ## Langkah 2 - Pola 1: server utama + cadangan, dengan retry dan timeout
# Server utama sengaja tidak aktif. `ambil_tool` mencoba dua kali dengan delay, lalu agen beralih ke server cadangan.
# Klien MCP membuka sesi per panggilan dan menutupnya sendiri, jadi tidak ada yang perlu ditutup.

# %%
print("Mencoba server utama (sengaja tidak aktif)...")
tools = jalankan(ambil_tool(utama, "utama", batas_waktu=5.0))
if not tools:
    print("Server utama gagal, beralih ke server fallback...")
    tools = jalankan(ambil_tool(cadangan, "cadangan"))
print(f"Tool yang tersedia untuk agen: {[t.name for t in tools]}\n")

# %% [markdown]
# ## Langkah 3 - Pola 2: graceful degradation
# Kalau tidak ada tool MCP sama sekali, agen tetap dibuat dan berjalan tanpa tool.

# %%
model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)
if not tools:
    print("Tidak ada tool MCP: agen tetap berjalan tanpa tool (aplikasi tidak mati)\n")
agent = create_agent(model, tools, system_prompt="Anda asisten lapangan migas. Pakai tool bila ada. Jawab singkat.")

# %% [markdown]
# ## Langkah 4 - Pola 3: eksekusi pertanyaan dengan timeout
# Panggilan agen dibungkus `asyncio.wait_for`. Kalau melewati batas, pengguna menerima pesan yang ramah.

# %%
pertanyaan_timeout = "Berapa water cut sumur dengan produksi 150 bopd minyak dan 450 bwpd air?"
print(f"Pengguna: {pertanyaan_timeout}")
try:
    response_timeout = jalankan(asyncio.wait_for(agent.ainvoke({"messages": [("human", pertanyaan_timeout)]}), timeout=120))
    print(f"Agen: {response_timeout['messages'][-1].content}\n")
except asyncio.TimeoutError:
    print("Pertanyaan melewati timeout")
    print("Agen: Saya sedang mengalami gangguan koneksi. Silakan coba lagi nanti.\n")

# %% [markdown]
# ## Langkah 5 - Pola 4: error dari tool MCP kembali ke model sebagai informasi
# Tool `konversi_satuan` diminta melakukan konversi yang tidak valid (psi ke m3). Server membalas dengan error,
# dan model membacanya sebagai informasi.

# %%
pertanyaan_error = ("Panggil tool konversi_satuan dengan dari='psi' dan ke='m3' untuk nilai 450, persis seperti itu, "
                    "lalu laporkan hasilnya.")
print(f"Pengguna: {pertanyaan_error}")
response_error = jalankan(asyncio.wait_for(agent.ainvoke({"messages": [("human", pertanyaan_error)]}), timeout=120))
for pesan in response_error["messages"]:
    for panggilan in getattr(pesan, "tool_calls", []) or []:
        print(f"   Agen memanggil tool: {panggilan['name']}({panggilan['args']})")
    if pesan.type == "tool":
        print(f"   Hasil tool (status {getattr(pesan, 'status', '?')}): {str(pesan.content)[:140]}")
print(f"Agen: {response_error['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 6 - Pola 5: pemeriksaan kesehatan
# Server dianggap sehat kalau daftar tool bisa diambil dalam 5 detik dan tidak kosong.

# %%
async def periksa_semua() -> None:
    for label, konfigurasi in [("utama (gudang_data)", utama), ("cadangan (lapangan)", cadangan)]:
        sehat = await cek_kesehatan(konfigurasi)
        print(f"   Server {label}: {'SEHAT' if sehat else 'TIDAK SEHAT'}")


jalankan(periksa_semua())

# %% [markdown]
# ## Praktik Terbaik Penanganan Error
# - Retry dengan exponential backoff untuk gangguan sementara
# - Beri timeout pada semua operasi jaringan (`asyncio.wait_for`)
# - Siapkan server fallback untuk ketersediaan tinggi
# - Graceful degradation saat MCP tidak tersedia
# - Pemeriksaan kesehatan untuk monitoring
# - Catat error untuk debugging dan peringatan
# - Berikan pesan error yang ramah kepada pengguna
