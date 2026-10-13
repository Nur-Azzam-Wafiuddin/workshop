# %% [markdown]
# # Contoh 2: Spesialis sebagai Tool
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/08-sistem-multi-agen/code/02_subagent_as_tool.py`
#
# Rancangan multi-agen paling sederhana: bangun agen spesialis kecil, lalu bungkus masing-masing dalam
# sebuah `@tool`. Agen "supervisor" menerima tool wrapper itu dan memutuskan siapa yang ditanya.
#
#     Pengguna -> Supervisor -> tanya_spesialis_operasi ------> Agen Operasi ------> tool sumur
#                          \--> tanya_spesialis_pemeliharaan -> Agen Pemeliharaan -> tool work order
#
# Bagi supervisor, spesialis hanyalah tool lain. DESKRIPSI spesialis adalah cara supervisor tahu kapan
# memanggilnya.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from migas_shared.field_tools import cek_status_sumur

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Tool tingkat rendah dan agen spesialis
# Tiap spesialis adalah agen biasa dengan sedikit tool dan prompt yang terfokus.

# %%
@tool
def jadwal_pulling() -> str:
    """Jadwal pekerjaan pulling dan workover rig yang akan datang."""
    return "Jadwal rig: KN-033 pulling sucker rod Selasa 08.00; SR-020 ganti motor ESP Kamis 14.00"


@tool
def daftar_wo_terbuka() -> str:
    """Daftar work order pemeliharaan yang masih terbuka."""
    return (
        "WO terbuka: WO-26-12501 sucker rod KN-033 patah, menunggu rig (tinggi); "
        "WO-26-12502 lampu manifold Seruni berkedip (rendah)"
    )


@tool
def ketersediaan_teknisi() -> str:
    """Kapan teknisi pemeliharaan dapat bekerja."""
    return "Teknisi mekanik tersedia Jumat 09.00-15.00"


agen_operasi = create_agent(
    model,
    tools=[cek_status_sumur, jadwal_pulling],
    system_prompt="Anda spesialis Operasi produksi. Pakai tool Anda. Jawab dalam 1-2 kalimat pendek.",
)
agen_pemeliharaan = create_agent(
    model,
    tools=[daftar_wo_terbuka, ketersediaan_teknisi],
    system_prompt="Anda spesialis Pemeliharaan. Pakai tool Anda. Jawab dalam 1-2 kalimat pendek.",
)

# %% [markdown]
# ## Langkah 3 - Membungkus tiap spesialis dalam sebuah tool
# Hanya jawaban AKHIR spesialis yang dikembalikan ke supervisor.

# %%
@tool
def tanya_spesialis_operasi(permintaan: str) -> str:
    """Tanya spesialis Operasi tentang status sumur, produksi, dan jadwal pulling atau workover.
    Tulis pertanyaan sebagai kalimat lengkap."""
    hasil = agen_operasi.invoke({"messages": [HumanMessage(content=permintaan)]})
    return hasil["messages"][-1].content  # hanya jawaban AKHIR yang dikembalikan


@tool
def tanya_spesialis_pemeliharaan(permintaan: str) -> str:
    """Tanya spesialis Pemeliharaan tentang kerusakan peralatan, work order terbuka, dan jadwal teknisi.
    Tulis pertanyaan sebagai kalimat lengkap."""
    hasil = agen_pemeliharaan.invoke({"messages": [HumanMessage(content=permintaan)]})
    return hasil["messages"][-1].content

# %% [markdown]
# ## Langkah 4 - Supervisor
# Supervisor hanya mengenal dua tool wrapper. Fungsi `tampilkan_delegasi` mencetak spesialis mana yang ditanya.

# %%
supervisor = create_agent(
    model,
    tools=[tanya_spesialis_operasi, tanya_spesialis_pemeliharaan],
    system_prompt=(
        "Anda koordinator yang mengoordinasi tim spesialis. Anda tidak memegang data sendiri. "
        "Delegasikan ke spesialis yang tepat, lalu beri pengguna satu jawaban yang jelas."
    ),
)


def tampilkan_delegasi(response) -> None:
    """Cetak spesialis mana yang ditanya supervisor, dan apa yang ditanyakan."""
    for pesan in response["messages"]:
        if isinstance(pesan, AIMessage):
            for panggilan in pesan.tool_calls:
                print(f"   Supervisor -> {panggilan['name']}: \"{panggilan['args']['permintaan']}\"")


def tanya_supervisor(pertanyaan: str) -> None:
    print(f"Pengguna: {pertanyaan}")
    response = supervisor.invoke({"messages": [HumanMessage(content=pertanyaan)]})
    tampilkan_delegasi(response)
    print(f"Supervisor: {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 5 - Pertanyaan 1: satu spesialis (Operasi)

# %%
tanya_supervisor("Bagaimana status sumur SR-020?")

# %% [markdown]
# ## Langkah 6 - Pertanyaan 2: satu spesialis (Pemeliharaan)

# %%
tanya_supervisor("Ada peralatan yang rusak, dan kapan teknisi bisa memperbaikinya?")

# %% [markdown]
# ## Langkah 7 - Pertanyaan 3: butuh kedua spesialis

# %%
tanya_supervisor("Apakah sumur KN-033 bisa segera berproduksi lagi, dan adakah work order yang menahannya?")

# %% [markdown]
# ## Yang baru saja terjadi
# - Tiap spesialis adalah agen biasa dengan sedikit tool dan prompt yang terfokus
# - Membungkusnya dalam `@tool` membuatnya bisa dipanggil oleh agen lain
# - Supervisor memilih spesialis dari DESKRIPSI tool wrapper
# - Pertanyaan ke-3 butuh kedua spesialis, jadi supervisor memanggil dua
# - Hanya jawaban akhir yang naik ke atas. Supervisor tidak pernah melihat panggilan tool mentahnya
