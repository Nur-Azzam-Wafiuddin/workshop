# %% [markdown]
# # Contoh 1: Agen yang Tidak Pernah Bertanya Dulu
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/06-persetujuan-manusia/code/01_agent_without_approval.py`
#
# Agen tanpa middleware apa pun mengeksekusi setiap tool call yang diputuskan model, langsung dan tanpa
# bertanya. Contoh ini memperlihatkan dua permintaan: salah ketik yang tampak jelas keliru, dan permintaan
# wajar yang melanggar aturan perusahaan yang tidak diketahui model.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Tool dan agen tanpa persetujuan
# Tool `ubah_frekuensi_vsd` mengubah setpoint langsung. Tanpa middleware, tidak ada yang menghalangi agen.

# %%
# Frekuensi VSD (Hz) beberapa sumur ESP. Pada sistem nyata ini adalah setpoint di panel VSD.
FREKUENSI_VSD = {"SR-020": 50, "SR-033": 48, "ML-012": 50}


@tool
def baca_frekuensi_vsd(kode_sumur: str) -> str:
    """Baca frekuensi VSD saat ini pada sebuah sumur ESP (hanya baca).

    Args:
        kode_sumur: Kode sumur, contoh "SR-033"
    """
    frekuensi = FREKUENSI_VSD.get(kode_sumur.upper())
    return f"{kode_sumur}: {frekuensi} Hz" if frekuensi else f"Sumur tidak dikenal: {kode_sumur}"


@tool
def ubah_frekuensi_vsd(kode_sumur: str, frekuensi_hz: int) -> str:
    """Ubah setpoint frekuensi VSD sebuah sumur ESP. Perubahan berlaku langsung pada motor di dalam sumur.

    Args:
        kode_sumur: Kode sumur, contoh "SR-033"
        frekuensi_hz: Frekuensi baru dalam Hz
    """
    FREKUENSI_VSD[kode_sumur.upper()] = frekuensi_hz
    return f"Frekuensi VSD {kode_sumur} sekarang {frekuensi_hz} Hz"


# Tanpa middleware: tidak ada yang menghalangi agen
agent = create_agent(
    model,
    tools=[baca_frekuensi_vsd, ubah_frekuensi_vsd],
    system_prompt="Anda asisten operasi. Pakai tool untuk melakukan yang diminta pengguna. Jawab singkat dalam Bahasa Indonesia.",
)

# %% [markdown]
# ## Langkah 3 - Fungsi untuk satu permintaan
# `jalankan_permintaan` mencetak frekuensi sebelum, permintaan, jawaban agen, dan frekuensi sesudah.

# %%
def jalankan_permintaan(no: int, catatan: str, teks: str) -> None:
    print(f"Permintaan {no} ({catatan})")
    print("-" * 60)
    print(f"Frekuensi SR-033 SEBELUM: {FREKUENSI_VSD['SR-033']} Hz")
    print(f"Pengguna: {teks}")
    response = agent.invoke({"messages": [HumanMessage(content=teks)]})
    print(f"Agen: {response['messages'][-1].content}")
    print(f"Frekuensi SR-033 SESUDAH:  {FREKUENSI_VSD['SR-033']} Hz\n")

# %% [markdown]
# ## Langkah 4 - Permintaan 1: salah ketik yang tampak jelas keliru
# Pengguna meminta 500 Hz padahal maksudnya 50 Hz.

# %%
jalankan_permintaan(1, "salah ketik, maksudnya 50 Hz", "Tolong atur frekuensi VSD sumur SR-033 menjadi 500 Hz.")

# %% [markdown]
# ## Langkah 5 - Permintaan 2: tampak wajar, tetapi melanggar aturan perusahaan
# Di atas 55 Hz perlu persetujuan Production Engineer, aturan yang tidak diketahui model.

# %%
jalankan_permintaan(2, "tampak wajar, tetapi di atas batas 55 Hz", "Tolong atur frekuensi VSD sumur SR-033 menjadi 58 Hz.")

# %% [markdown]
# ## Ide Utama
# - Pada permintaan yang tampak jelas keliru, model kadang menolak sendiri, kadang tidak. Itu penilaian model, bukan jaminan
# - Permintaan yang tampak wajar tetapi melanggar aturan perusahaan berjalan SEGERA: model tidak tahu aturan itu
# - Model juga bisa membuat kesalahan sendiri (argumen salah, tool salah, salah baca angka)
# - Prompt bukan perlindungan: menulis "hati-hati" di system prompt hanya petunjuk, bukan jaminan
