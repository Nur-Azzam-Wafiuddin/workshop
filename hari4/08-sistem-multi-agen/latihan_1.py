# %% [markdown]
# # Latihan 1: Tim Koordinator
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Supervisor mengoordinasi tiga spesialis:
# - operasi: status sumur dan jadwal pulling
# - pemeliharaan: work order terbuka
# - engineering: water cut (HANYA peran engineer dan management, dipasang di kode)
#
# Area dan peran pengguna datang dari konteks runtime, bukan dari model. Skrip juga melaporkan spesialis
# mana yang dipakai tiap permintaan dan berapa token yang dihabiskan tim.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import ToolRuntime
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from migas_shared.rag_tools import KonteksPengguna

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Data fiktif dan tool domain
# Data dua area (Seruni dan Kenanga) beserta empat tool tingkat rendah untuk para spesialis.

# %%
# ---------- Data fiktif untuk dua area ----------
SUMUR = {
    "Seruni": {
        "SR-020": "produksi 120 bopd, air 480 bwpd, ESP trip overload kemarin, stabil sejak 18.00",
        "SR-027": "produksi 95 bopd, air 380 bwpd, pembacaan H2S 12 ppm dalam investigasi HSE",
    },
    "Kenanga": {
        "KN-033": "tidak berproduksi, sucker rod patah, menunggu jadwal rig",
    },
}
JADWAL_PULLING = {
    "Seruni": "SR-020 ganti motor ESP Kamis 14.00",
    "Kenanga": "KN-033 pulling sucker rod Selasa 08.00",
}
WORK_ORDER = {
    "Seruni": "WO-26-12501 kebocoran seal ESP SR-020 (tinggi); WO-26-12502 lampu manifold berkedip (rendah)",
    "Kenanga": "WO-26-12611 sucker rod KN-033 patah, menunggu rig (tinggi)",
}


@tool
def cek_status_sumur(kode_sumur: str, area: str) -> str:
    """Cek status sebuah sumur di sebuah area.

    Args:
        kode_sumur: Kode sumur, contoh "SR-020"
        area: Nama area, contoh "Seruni"
    """
    if area not in SUMUR:
        return f"Area '{area}' tidak dikenal. Area yang ada: {', '.join(SUMUR)}"
    status = SUMUR[area].get(kode_sumur.upper())
    if status is None:
        # Pesan error yang membantu lebih baik daripada angka 0 yang menyesatkan: model bisa memperbaiki dirinya
        return f"Sumur '{kode_sumur}' tidak ada di area {area}. Sumur di area ini: {', '.join(SUMUR[area])}"
    return f"{kode_sumur.upper()} ({area}): {status}"


@tool
def ambil_jadwal_pulling(area: str) -> str:
    """Ambil jadwal pulling atau workover di sebuah area.

    Args:
        area: Nama area
    """
    return f"{area}: {JADWAL_PULLING.get(area, 'tidak ada jadwal')}"


@tool
def daftar_wo_terbuka(area: str) -> str:
    """Daftar work order terbuka di sebuah area.

    Args:
        area: Nama area
    """
    return f"{area}: {WORK_ORDER.get(area, 'tidak ada work order terbuka')}"


@tool
def hitung_water_cut(minyak_bopd: float, air_bwpd: float) -> str:
    """Hitung water cut dari produksi minyak dan air.

    Args:
        minyak_bopd: Produksi minyak (bopd)
        air_bwpd: Produksi air (bwpd)
    """
    total = minyak_bopd + air_bwpd
    if total == 0:
        return "Tidak dapat dihitung: total cairan 0."
    return f"Water cut {air_bwpd / total * 100:.1f}% (total cairan {total:.0f} bpd)"

# %% [markdown]
# ## Langkah 3 - Agen spesialis
# Tiap spesialis memegang tool-nya sendiri. `tanya_spesialis` memanggil agen dan tidak menjatuhkan seluruh tim kalau gagal.

# %%
def tanya_spesialis(agen, teks: str) -> str:
    """Panggil agen spesialis. Jika gagal, kembalikan pesan, jangan menjatuhkan seluruh tim."""
    try:
        return agen.invoke({"messages": [HumanMessage(content=teks)]})["messages"][-1].content
    except Exception as error:  # misalnya model tidak tersedia, bug tool
        return f"Spesialis tidak tersedia ({type(error).__name__}). Minta pengguna mencoba lagi nanti."


agen_operasi = create_agent(
    model,
    tools=[cek_status_sumur, ambil_jadwal_pulling],
    system_prompt="Anda spesialis Operasi. Pakai tool dengan area yang diberikan. 1-2 kalimat.",
)
agen_pemeliharaan = create_agent(
    model,
    tools=[daftar_wo_terbuka],
    system_prompt="Anda spesialis Pemeliharaan. Pakai tool dengan area yang diberikan. 1-2 kalimat.",
)
agen_engineering = create_agent(
    model,
    tools=[hitung_water_cut],
    system_prompt="Anda spesialis Engineering. Hitung dengan tool, jangan menebak. 1-2 kalimat.",
)

# %% [markdown]
# ## Langkah 4 - Tool wrapper dan koordinator
# Area dan peran dibaca dari `runtime.context`. Akses Engineering dibatasi di kode.

# %%
# TODO(B8.1): buat tool tanya_spesialis_operasi(permintaan, runtime: ToolRuntime[KonteksPengguna]) yang meneruskan permintaan ke agen_operasi dengan awalan area dari runtime.context.area
tanya_spesialis_operasi = None  # TODO: ganti dengan implementasi Anda


@tool
def tanya_spesialis_pemeliharaan(permintaan: str, runtime: ToolRuntime[KonteksPengguna]) -> str:
    """Tanya tentang work order terbuka dan peralatan rusak di area pengguna."""
    return tanya_spesialis(agen_pemeliharaan, f"Area {runtime.context.area}. {permintaan}")


# TODO(B8.2): buat tool tanya_spesialis_engineering yang menolak peran selain engineer dan management di kode (kembalikan pesan 'Akses ditolak'), lalu meneruskan permintaan ke agen_engineering
tanya_spesialis_engineering = None  # TODO: ganti dengan implementasi Anda


# TODO(B8.3): buat agen koordinator dengan ketiga tool wrapper, context_schema=KonteksPengguna, dan system prompt: tidak memegang data sendiri, tanya spesialis yang relevan, laporkan akses ditolak, jangan mengarang angka
tim = None  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 5 - Fungsi untuk satu pertanyaan
# `tanya_tim` melaporkan spesialis mana yang ditanya, jumlah token, dan jawabannya.

# %%
def tanya_tim(tim, pertanyaan: str, konteks: KonteksPengguna) -> None:
    handler = UsageMetadataCallbackHandler()
    # TODO(B8.4): panggil tim.invoke dengan pesan pengguna, context=konteks, dan config={"callbacks": [handler]} untuk menghitung token
    response = None  # TODO: ganti dengan implementasi Anda
    ditanya = [
        panggilan["name"].replace("tanya_spesialis_", "")
        for pesan in response["messages"]
        if isinstance(pesan, AIMessage)
        for panggilan in pesan.tool_calls
    ]
    token = sum(u.get("total_tokens", 0) for u in handler.usage_metadata.values())

    print(f"[{konteks.role} @ {konteks.area}] {pertanyaan}")
    print(f"   Spesialis ditanya: {ditanya}   |   token: {token}")
    print(f"   Jawaban: {response['messages'][-1].content}\n")


engineer = KonteksPengguna(role="engineer", area="Seruni", user_id="ENG-208")
operator = KonteksPengguna(role="operator", area="Kenanga", user_id="OP-322")

# %% [markdown]
# ## Langkah 6 - Pertanyaan 1: engineer menanyakan status sumur

# %%
tanya_tim(tim, "Bagaimana status sumur SR-020?", engineer)

# %% [markdown]
# ## Langkah 7 - Pertanyaan 2: operator menanyakan sumur bermasalah dan jadwal pulling

# %%
tanya_tim(tim, "Sumur mana yang bermasalah dan kapan jadwal pulling berikutnya?", operator)

# %% [markdown]
# ## Langkah 8 - Pertanyaan 3: engineer meminta laporan gabungan
# Ketiga spesialis boleh dipakai, termasuk Engineering.

# %%
tanya_tim(tim, "Beri saya status sumur, work order terbuka, dan water cut untuk 120 bopd minyak dan 480 bwpd air.", engineer)

# %% [markdown]
# ## Langkah 9 - Pertanyaan 4: operator meminta laporan gabungan yang sama
# Bagian Engineering ditolak oleh kode karena peran operator.

# %%
tanya_tim(tim, "Beri saya status sumur, work order terbuka, dan water cut untuk 120 bopd minyak dan 480 bwpd air.", operator)
