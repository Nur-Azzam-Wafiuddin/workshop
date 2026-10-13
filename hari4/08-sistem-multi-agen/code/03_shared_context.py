# %% [markdown]
# # Contoh 3: Meneruskan Konteks ke Spesialis
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/08-sistem-multi-agen/code/03_shared_context.py`
#
# Ada fakta yang tidak boleh diputuskan model: peran pengguna dan area kerjanya. Kalau model harus
# mengetik `role="hse"` di setiap panggilan, ia bisa keliru, atau dibujuk untuk bertanya tentang area lain.
#
# Karena itu fakta itu diteruskan sebagai KONTEKS RUNTIME. Model tidak melihatnya dan tidak bisa
# mengubahnya. Tool membaca konteks lewat `ToolRuntime`. Pada tim multi-agen ada satu langkah tambahan:
# tool wrapper harus MENERUSKAN konteks itu ke agen spesialis (`context=runtime.context`), supaya tool di
# dalam spesialis juga bisa membacanya.
#
# Tiga aturan akses dipasang di KODE pada contoh ini:
# 1. Operator hanya boleh melihat sumur di areanya sendiri (cek di dalam tool sumur)
# 2. Spesialis Engineering hanya melayani peran engineer dan management (cek di tool wrapper)
# 3. Dokumen berstatus akses hse hanya terlihat oleh peran hse dan management (cek di pencarian dokumen)

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import ToolRuntime
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from migas_shared.rag_tools import KonteksPengguna, cari_dokumen
from migas_shared.field_tools import DATA_SUMUR, hitung_water_cut

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Tool tingkat rendah dengan aturan akses di kode
# `cek_sumur_di_area` membaca konteks lewat `ToolRuntime`: operator hanya melihat sumur di areanya.

# %%
@tool
def cek_sumur_di_area(kode_sumur: str, runtime: ToolRuntime[KonteksPengguna]) -> str:
    """Cek status operasi sebuah sumur.

    Args:
        kode_sumur: Kode sumur, contoh "SR-020"
    """
    data = DATA_SUMUR.get(kode_sumur.strip().upper())
    if data is None:
        return f"Sumur {kode_sumur} tidak ditemukan. Sumur yang terdaftar: {', '.join(DATA_SUMUR)}"
    # Aturan akses di KODE: operator hanya melihat sumur di areanya
    if runtime.context.role == "operator" and data["area"] != runtime.context.area:
        return f"Akses ditolak: sumur {kode_sumur} berada di area {data['area']}, bukan area Anda ({runtime.context.area})."
    return (f"Sumur {kode_sumur} ({data['area']}): status {data['status']}, minyak {data['minyak_bopd']} bopd, "
            f"air {data['air_bwpd']} bwpd. Catatan: {data['catatan']}")

# %% [markdown]
# ## Langkah 3 - Agen spesialis
# Spesialis Operasi dan HSE memakai `context_schema=KonteksPengguna` agar tool-nya bisa membaca konteks.

# %%
agen_operasi = create_agent(
    model,
    tools=[cek_sumur_di_area],
    context_schema=KonteksPengguna,
    system_prompt="Anda spesialis Operasi. Pakai cek_sumur_di_area untuk setiap sumur yang ditanyakan. Jawab 1-2 kalimat.",
)
agen_hse = create_agent(
    model,
    tools=[cari_dokumen],
    context_schema=KonteksPengguna,
    system_prompt=(
        "Anda spesialis HSE. Jawab HANYA dari hasil cari_dokumen dan sebutkan id dokumen sumbernya. "
        "Jika tidak ada dokumen yang relevan, katakan terus terang. Jawab 2-3 kalimat."
    ),
)
agen_engineering = create_agent(
    model,
    tools=[hitung_water_cut],
    system_prompt="Anda spesialis Engineering. Hitung dengan tool, jangan menebak. Jawab 1-2 kalimat.",
)

# %% [markdown]
# ## Langkah 4 - Tool wrapper yang meneruskan konteks
# Tiap wrapper meneruskan `context=runtime.context` ke spesialisnya. Wrapper Engineering juga memeriksa peran di kode.

# %%
@tool
def tanya_spesialis_operasi(permintaan: str, runtime: ToolRuntime[KonteksPengguna]) -> str:
    """Tanya spesialis Operasi tentang status dan produksi sumur."""
    hasil = agen_operasi.invoke(
        {"messages": [HumanMessage(content=permintaan)]},
        context=runtime.context,  # konteks diteruskan ke dalam spesialis
    )
    return hasil["messages"][-1].content


@tool
def tanya_spesialis_hse(permintaan: str, runtime: ToolRuntime[KonteksPengguna]) -> str:
    """Tanya spesialis HSE tentang prosedur keselamatan (SOP) dan laporan insiden atau investigasi."""
    hasil = agen_hse.invoke(
        {"messages": [HumanMessage(content=permintaan)]},
        context=runtime.context,  # peran pengguna menentukan dokumen yang terlihat
    )
    return hasil["messages"][-1].content


@tool
def tanya_spesialis_engineering(permintaan: str, runtime: ToolRuntime[KonteksPengguna]) -> str:
    """Tanya spesialis Engineering untuk perhitungan teknis, misalnya water cut dari angka produksi.
    Sertakan angka produksinya dalam permintaan."""
    # Aturan akses di KODE: model tidak bisa membujuk if ini
    if runtime.context.role not in ("engineer", "management"):
        return "Akses ditolak: analisis Engineering hanya untuk peran engineer dan management."
    hasil = agen_engineering.invoke({"messages": [HumanMessage(content=permintaan)]})
    return hasil["messages"][-1].content

# %% [markdown]
# ## Langkah 5 - Supervisor dan fungsi skenario
# `context_schema` memberi tahu agen bentuk konteksnya. Konteks dikirim bersama pesan saat `invoke`.

# %%
supervisor = create_agent(
    model,
    tools=[tanya_spesialis_operasi, tanya_spesialis_hse, tanya_spesialis_engineering],
    context_schema=KonteksPengguna,  # memberi tahu agen bentuk konteksnya
    system_prompt=(
        "Anda koordinator yang mengoordinasi spesialis. Delegasikan ke spesialis yang tepat dan "
        "minta SEMUA yang relevan pada langkah yang sama. Jika spesialis menolak akses, sampaikan "
        "dengan jelas kepada pengguna dan jangan mencoba menyiasatinya. Jawab ringkas."
    ),
)


def jalankan_skenario(label: str, konteks: KonteksPengguna, pertanyaan: str) -> None:
    print(f"{label}")
    print("-" * 60)
    print(f"Pengguna: {pertanyaan}")
    response = supervisor.invoke(
        {"messages": [HumanMessage(content=pertanyaan)]},
        context=konteks,  # diteruskan bersama pesan
    )
    print(f"Supervisor: {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 6 - Skenario 1: operator menanyakan dua sumur
# SR-027 ada di areanya (Seruni), KN-033 di area lain.

# %%
jalankan_skenario(
    "Operator, area Seruni",
    KonteksPengguna(role="operator", area="Seruni", user_id="OP-114"),
    "Bagaimana status sumur SR-027 dan sumur KN-033?",
)

# %% [markdown]
# ## Langkah 7 - Skenario 2: operator menanyakan laporan investigasi
# Dokumen berakses HSE tidak terlihat oleh operator.

# %%
jalankan_skenario(
    "Operator, area Seruni",
    KonteksPengguna(role="operator", area="Seruni", user_id="OP-114"),
    "Apa temuan utama laporan investigasi INV-2026-011?",
)

# %% [markdown]
# ## Langkah 8 - Skenario 3: petugas HSE menanyakan hal yang sama

# %%
jalankan_skenario(
    "Petugas HSE, area Seruni",
    KonteksPengguna(role="hse", area="Seruni", user_id="HSE-031"),
    "Apa temuan utama laporan investigasi INV-2026-011?",
)

# %% [markdown]
# ## Langkah 9 - Skenario 4: operator meminta analisis Engineering
# Wrapper Engineering menolak karena peran bukan engineer atau management.

# %%
jalankan_skenario(
    "Operator, area Seruni",
    KonteksPengguna(role="operator", area="Seruni", user_id="OP-114"),
    "Hitung water cut untuk produksi 120 bopd minyak dan 480 bwpd air.",
)

# %% [markdown]
# ## Langkah 10 - Skenario 5: engineer meminta analisis yang sama

# %%
jalankan_skenario(
    "Engineer, area Kenanga",
    KonteksPengguna(role="engineer", area="Kenanga", user_id="ENG-208"),
    "Hitung water cut untuk produksi 120 bopd minyak dan 480 bwpd air.",
)

# %% [markdown]
# ## Yang baru saja terjadi
# - Pertanyaan yang sama memberi jawaban berbeda karena KONTEKS-nya berbeda
# - Peran dan area tidak pernah diketik model, jadi tidak bisa keliru atau dipalsukan
# - Penolakan datang dari kode di dalam tool, bukan dari kebaikan hati model
# - Konteks tidak terlihat oleh model; hanya tool Anda yang bisa membacanya
