# %% [markdown]
# # Contoh 3: Server MCP Buatan Sendiri untuk Dokumen Perusahaan
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/09-mcp/code/03_mcp_local_documents.py`
#
# Pencarian dokumen yang Anda kenal dari bab sebelumnya dibungkus sebagai SERVER MCP (code/servers/
# documents_stdio_server.py). Agen tidak lagi mengimpor kode pencarian: ia hanya menghubungi server lewat
# protokol, seperti ke server mana pun di internet.
#
# Dua hal baru di contoh ini:
#
# 1. PERSISTENT SESSION. `client.get_tools()` biasa memulai sesi baru (artinya subproses baru) untuk SETIAP
#    tool call. Untuk server yang mahal dijalankan, buka satu sesi dengan `client.session(...)`.
# 2. IDENTITAS ada di konfigurasi server. Server MCP tidak melihat konteks LangChain, jadi peran pengguna
#    dikirim lewat variabel lingkungan subproses (`env`), bukan lewat argumen yang bisa diisi model.
#
# Kode async dijalankan lewat `jalankan(...)` dari `migas_shared.tampil`, yang bekerja di skrip biasa maupun
# di Jupyter/Interactive Window.

# %%
# Langkah 1 - Menyiapkan model dan fungsi bantu
import os
import re
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI

from migas_shared.config import ROOT
from migas_shared.tampil import jalankan

load_dotenv()

PATH_SERVER = ROOT / "hari4" / "09-mcp" / "code" / "servers" / "documents_stdio_server.py"

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)
pertanyaan = "Apa temuan utama laporan investigasi INV-2026-011? Jawab singkat dan sebut id dokumen sumbernya."


def klien_untuk_peran(peran: str) -> MultiServerMCPClient:
    """Klien MCP yang menjalankan server dokumen dengan peran pengguna tertentu."""
    # Subproses hanya mewarisi variabel dasar; teruskan sendiri yang dibutuhkan server
    env = {"PERAN_PENGGUNA": peran, "PYTHONUTF8": "1"}
    for nama in ("EMBED_PROVIDER", "EMBED_MODEL", "EMBED_CACHE_DIR", "EMBED_BASE_URL", "EMBED_API_KEY"):
        if os.getenv(nama):
            env[nama] = os.environ[nama]
    return MultiServerMCPClient(
        {"dokumen": {"transport": "stdio", "command": sys.executable, "args": [str(PATH_SERVER)], "env": env}}
    )


def id_dokumen(teks: str) -> list[str]:
    """Ambil id dokumen unik (SOP-..., INV-..., RPT-...) dari teks hasil pencarian."""
    return sorted(set(re.findall(r"\b(?:SOP|INV|RPT|LL|MAN)-[A-Z0-9-]+\d\b", teks)))

# %% [markdown]
# ## Langkah 2 - Bagian 1: tool MCP dipanggil langsung, tanpa model
# `cari_langsung` membuka satu sesi persisten (`client.session`) untuk satu peran, lalu memanggil tool
# `cari_dokumen` langsung. Satu subproses dipakai untuk seluruh blok `async with`.

# %%
async def cari_langsung(peran: str) -> None:
    client = klien_untuk_peran(peran)
    async with client.session("dokumen") as sesi:  # satu subproses untuk seluruh blok ini
        tools = await load_mcp_tools(sesi)
        if peran == "operator":
            print(f"Tool yang ditawarkan server: {[t.name for t in tools]}")
        cari = next(t for t in tools if t.name == "cari_dokumen")
        hasil = await cari.ainvoke({"pertanyaan": "investigasi paparan H2S sumur SR-027 INV-2026-011", "k": 6})
        print(f"   peran {peran:<8} -> dokumen yang terlihat: {id_dokumen(str(hasil))}")


jalankan(cari_langsung("operator"))

# %% [markdown]
# ## Langkah 3 - Bagian 1: peran HSE
# Pencarian yang sama dari peran `hse`. Bandingkan dokumen yang terlihat dengan peran operator.

# %%
jalankan(cari_langsung("hse"))

# %% [markdown]
# ## Langkah 4 - Bagian 2: agen yang sama, dua peran berbeda
# `tanya_dengan_peran` membuka sesi persisten untuk satu peran, membangun agen dari tool server, lalu
# mengajukan pertanyaan yang sama.

# %%
async def tanya_dengan_peran(peran: str) -> None:
    client = klien_untuk_peran(peran)
    async with client.session("dokumen") as sesi:
        tools = await load_mcp_tools(sesi)
        agent = create_agent(
            model,
            tools,
            system_prompt=(
                "Anda asisten dokumen perusahaan. Jawab HANYA dari hasil cari_dokumen dan sebut id dokumennya. "
                "Jika tidak ada dokumen yang relevan, katakan terus terang. Jawab maksimal 4 kalimat."
            ),
        )
        print(f"Peran {peran} | Pengguna: {pertanyaan}")
        response = await agent.ainvoke({"messages": [("human", pertanyaan)]})
        print(f"Agen: {response['messages'][-1].content}\n")


jalankan(tanya_dengan_peran("operator"))

# %% [markdown]
# ## Langkah 5 - Bagian 2: agen dengan peran HSE

# %%
jalankan(tanya_dengan_peran("hse"))

# %% [markdown]
# ## Konsep Utama
# - Pencarian dokumen kini server MCP: agen mana pun yang bisa 'berbicara MCP' bisa memakainya
# - Peran pengguna ditentukan oleh konfigurasi server (env), bukan argumen tool yang diisi model
# - Operator tidak pernah melihat INV-2026-011; petugas HSE melihatnya
# - `client.session(...)` menjaga satu subproses tetap hidup, berguna untuk server yang berat
