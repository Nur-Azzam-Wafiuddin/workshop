# %% [markdown]
# # Contoh 1: Masalah Satu Agen Raksasa
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/08-sistem-multi-agen/code/01_too_many_tools.py`
#
# Satu agen dengan semua tool adalah rancangan paling sederhana, dan ia berhasil... sampai ia membesar.
# Contoh ini membangun agen "monolit" dengan sembilan tool dari tiga departemen, lalu mengukur
# biayanya dibandingkan dengan seorang spesialis yang hanya memegang tiga tool miliknya sendiri.

# %%
# Langkah 1 - Menyiapkan model
import json
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_openai import ChatOpenAI

from migas_shared.field_tools import cek_status_sumur, hitung_water_cut, konversi_satuan

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Sembilan tool dari tiga departemen
# Departemen Operasi, Pemeliharaan, dan Engineering masing-masing punya tiga tool.

# %%
# ---------- Departemen Operasi ----------
@tool
def daftar_sumur_bermasalah() -> str:
    """Daftar sumur yang sedang bermasalah atau tidak berproduksi normal di semua area."""
    return "Sumur bermasalah: KN-033 (menunggu pulling), SR-027 (investigasi H2S)"


@tool
def jadwal_pulling() -> str:
    """Jadwal pekerjaan pulling dan workover rig yang akan datang."""
    return "Jadwal rig: KN-033 pulling sucker rod Selasa 08.00; SR-020 ganti motor ESP Kamis 14.00"


# ---------- Departemen Pemeliharaan ----------
@tool
def daftar_wo_terbuka() -> str:
    """Daftar work order pemeliharaan yang masih terbuka."""
    return "WO terbuka: WO-26-12501 kebocoran seal ESP SR-020 (tinggi), WO-26-12502 lampu manifold Seruni (rendah)"


@tool
def cek_status_peralatan(kode_peralatan: str) -> str:
    """Cek kondisi satu peralatan (pompa, separator, kompresor).

    Args:
        kode_peralatan: Kode peralatan, contoh "P-SR1-101"
    """
    return f"{kode_peralatan}: {'tekanan discharge rendah' if kode_peralatan.endswith('101') else 'normal'}"


@tool
def ketersediaan_teknisi() -> str:
    """Kapan teknisi pemeliharaan dapat bekerja."""
    return "Teknisi mekanik tersedia Jumat 09.00-15.00"


# ---------- Departemen Engineering ----------
@tool
def cek_tekanan_vs_desain(tekanan_psi: float, mawp_psi: float) -> str:
    """Bandingkan tekanan operasi dengan tekanan kerja maksimum yang diizinkan (MAWP).

    Args:
        tekanan_psi: Tekanan operasi dalam psi
        mawp_psi: MAWP peralatan dalam psi
    """
    persen = tekanan_psi / mawp_psi * 100
    return f"Tekanan operasi {persen:.0f}% dari MAWP ({'AMAN' if persen < 90 else 'MENDEKATI BATAS'})"


TOOL_OPERASI = [cek_status_sumur, daftar_sumur_bermasalah, jadwal_pulling]
TOOL_PEMELIHARAAN = [daftar_wo_terbuka, cek_status_peralatan, ketersediaan_teknisi]
TOOL_ENGINEERING = [hitung_water_cut, konversi_satuan, cek_tekanan_vs_desain]

# %% [markdown]
# ## Langkah 3 - Seberapa besar definisi tool?
# Definisi setiap tool dikirim ke model pada SETIAP panggilan. `token_skema_tool` memperkirakan ukurannya.

# %%
def token_skema_tool(tools) -> int:
    """Perkiraan token yang dipakai definisi tool pada SETIAP panggilan ke model."""
    skema = [convert_to_openai_tool(t) for t in tools]
    return count_tokens_approximately([json.dumps(skema)])


def token_masukan_panggilan_pertama(response) -> int:
    """Token masukan pada panggilan model pertama dalam satu proses (sudah termasuk prompt dan definisi tool)."""
    ai_pertama = next(m for m in response["messages"] if isinstance(m, AIMessage))
    return (ai_pertama.usage_metadata or {}).get("input_tokens", 0)


semua_tool = TOOL_OPERASI + TOOL_PEMELIHARAAN + TOOL_ENGINEERING

print("1. Seberapa besar definisi tool?")
print("-" * 60)
print(f"   Spesialis Operasi: {len(TOOL_OPERASI)} tool  = sekitar {token_skema_tool(TOOL_OPERASI):>4} token per panggilan")
print(f"   Agen monolit:      {len(semua_tool)} tool  = sekitar {token_skema_tool(semua_tool):>4} token per panggilan\n")

# %% [markdown]
# ## Langkah 4 - Agen monolit dan spesialis
# Monolit memegang kesembilan tool; spesialis Operasi hanya tiga.

# %%
monolit = create_agent(
    model, tools=semua_tool, system_prompt="Anda asisten koordinator. Pakai tool. Jawab singkat."
)
spesialis_operasi = create_agent(
    model,
    tools=TOOL_OPERASI,
    system_prompt="Anda spesialis Operasi. Pakai tool. Jawab singkat.",
)

# %% [markdown]
# ## Langkah 5 - Pertanyaan yang sama untuk keduanya
# Bandingkan token masukan pada panggilan model pertama.

# %%
pertanyaan = "Bagaimana status sumur SR-020?"
print(f"2. Pertanyaan yang sama untuk keduanya: \"{pertanyaan}\"")
print("-" * 60)
besar = monolit.invoke({"messages": [HumanMessage(content=pertanyaan)]})
kecil = spesialis_operasi.invoke({"messages": [HumanMessage(content=pertanyaan)]})
print(f"   Monolit:           {besar['messages'][-1].content}")
print(f"      token masukan pada panggilan model pertama: {token_masukan_panggilan_pertama(besar)}")
print(f"   Spesialis Operasi: {kecil['messages'][-1].content}")
print(f"      token masukan pada panggilan model pertama: {token_masukan_panggilan_pertama(kecil)}\n")

# %% [markdown]
# ## Yang ditunjukkan contoh ini
# - Kedua agen menjawab dengan benar: monolit BERHASIL pada ukuran ini
# - Tetapi setiap panggilan membawa kesembilan definisi tool, bahkan untuk pertanyaan Operasi
# - Lebih banyak tool berarti lebih banyak token, lebih mahal, dan lebih besar peluang salah pilih tool
# - Satu system prompt panjang untuk tiga pekerjaan juga makin sulit dirawat
# - Solusinya: spesialis dengan sedikit tool, dan seorang koordinator yang mendelegasikan
