# %% [markdown]
# # Latihan Bonus: Tim yang Mengembalikan Hasil Bertipe
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Menggabungkan bab 4 (structured output) dengan bab 8 (multi-agen):
# - Tiap spesialis mengembalikan TEMUAN BERTIPE (objek Pydantic), bukan paragraf
# - Supervisor menggabungkan temuan menjadi `LaporanShift` bertipe
# - Python biasa lalu memutuskan apa yang dilakukan dengan laporan itu

# %%
# Langkah 1 - Menyiapkan model
import os
from typing import Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Skema keluaran bertipe
# Dua skema temuan untuk spesialis dan satu `LaporanShift` untuk supervisor.

# %%
class TemuanOperasi(BaseModel):
    """Yang ditemukan spesialis Operasi."""

    # TODO(B8.5): definisikan field TemuanOperasi: sumur_bermasalah (daftar kode sumur) dan jadwal_pulling_berikutnya (satu frasa pendek)
    pass  # TODO: definisikan field


class TemuanPemeliharaan(BaseModel):
    """Yang ditemukan spesialis Pemeliharaan."""

    # TODO(B8.6): definisikan field TemuanPemeliharaan: wo_prioritas_tinggi (daftar deskripsi singkat) dan total_wo_terbuka (int)
    pass  # TODO: definisikan field


class LaporanShift(BaseModel):
    """Laporan gabungan supervisor."""

    # TODO(B8.7): definisikan field LaporanShift: prioritas_keseluruhan (Literal normal, perhatian, mendesak dengan aturan di description), isu_utama, dan tindakan_disarankan (daftar string)
    pass  # TODO: definisikan field

# %% [markdown]
# ## Langkah 3 - Tool domain dan agen spesialis bertipe
# `temuan_bertipe` menjalankan spesialis dan mengembalikan temuannya sebagai teks JSON, karena tool hanya bisa mengembalikan teks.

# %%
@tool
def daftar_sumur_bermasalah() -> str:
    """Daftar sumur yang sedang bermasalah di semua area."""
    return "KN-033 menunggu pulling (sucker rod patah); SR-027 dalam investigasi H2S; sumur lain normal"


@tool
def ambil_jadwal_pulling() -> str:
    """Jadwal pulling dan workover yang akan datang."""
    return "KN-033 pulling Selasa 08.00; SR-020 ganti motor ESP Kamis 14.00"


@tool
def daftar_wo_terbuka() -> str:
    """Daftar work order terbuka beserta prioritasnya."""
    return "WO-26-12611 sucker rod KN-033 patah (tinggi); WO-26-12502 lampu manifold berkedip (rendah)"


def temuan_bertipe(agen, permintaan: str) -> str:
    """Jalankan spesialis dan kembalikan temuan bertipenya sebagai teks JSON.

    Tool hanya dapat mengembalikan teks, jadi model_dump_json() menjaga strukturnya. Jika spesialis lupa
    menghasilkan hasil bertipe (structured_response bernilai None, lihat pemecahan masalah bab 4), kembalikan
    jawaban biasanya daripada menjatuhkan seluruh tim.
    """
    hasil = agen.invoke({"messages": [HumanMessage(content=permintaan)]})
    temuan = hasil.get("structured_response")
    if temuan is None:
        return "Spesialis tidak memberi hasil bertipe. Jawaban biasa: " + str(hasil["messages"][-1].content)
    return temuan.model_dump_json()


# TODO(B8.8): buat spesialis Operasi dengan dua tool-nya dan response_format=TemuanOperasi
agen_operasi = None  # TODO: ganti dengan implementasi Anda
agen_pemeliharaan = create_agent(
    model,
    tools=[daftar_wo_terbuka],
    system_prompt="Anda spesialis Pemeliharaan. Pakai tool Anda, lalu beri jawaban akhir sebagai TemuanPemeliharaan.",
    response_format=TemuanPemeliharaan,
)

# %% [markdown]
# ## Langkah 4 - Tool wrapper dan supervisor bertipe
# Supervisor menggabungkan kedua temuan menjadi `LaporanShift`.

# %%
@tool
def tanya_spesialis_operasi(permintaan: str) -> str:
    """Dapatkan temuan Operasi bertipe: sumur bermasalah dan jadwal pulling berikutnya."""
    return temuan_bertipe(agen_operasi, permintaan)


@tool
def tanya_spesialis_pemeliharaan(permintaan: str) -> str:
    """Dapatkan temuan Pemeliharaan bertipe: work order prioritas tinggi dan jumlah work order terbuka."""
    return temuan_bertipe(agen_pemeliharaan, permintaan)


# TODO(B8.9): buat supervisor dengan kedua tool wrapper dan response_format=LaporanShift; system prompt meminta menanyakan KEDUA spesialis dan memuat aturan prioritas mendesak
tim = None  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 5 - Meminta laporan shift

# %%
response = tim.invoke({"messages": [HumanMessage(content="Susun laporan status shift ini.")]})
laporan = response.get("structured_response")

# %% [markdown]
# ## Langkah 6 - Menampilkan laporan bertipe
# Kalau tidak ada laporan terstruktur, tampilkan jawaban mentah.

# %%
if laporan is None:
    print("Tidak ada laporan terstruktur. Jawaban mentah:", response["messages"][-1].content)
else:
    print(f"Prioritas: {laporan.prioritas_keseluruhan.upper()}")
    print("Isu utama:")
    for isu in laporan.isu_utama:
        print(f"  - {isu}")
    print("Tindakan disarankan:")
    for tindakan in laporan.tindakan_disarankan:
        print(f"  - {tindakan}")

# %% [markdown]
# ## Langkah 7 - Keputusan oleh Python biasa
# Karena laporan bertipe, keputusan cukup berupa `if` biasa pada nilai `prioritas_keseluruhan`.

# %%
if laporan is not None:
    print()
    if laporan.prioritas_keseluruhan == "mendesak":
        print("Beri tahu manajer area sekarang juga")
    elif laporan.prioritas_keseluruhan == "perhatian":
        print("Tambahkan ke daftar periksa hari ini")
    else:
        print("Tidak ada yang perlu dilakukan")
