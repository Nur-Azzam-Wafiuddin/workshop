# %% [markdown]
# # Contoh 4: Menjalankan Spesialis Secara Paralel
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/08-sistem-multi-agen/code/04_parallel_subagents.py`
#
# Kalau sebuah pertanyaan butuh beberapa spesialis yang saling bebas, supervisor bisa bertanya ke
# semuanya pada langkah yang SAMA. LangChain menjalankan panggilan tool itu bersamaan, sehingga empat
# pekerjaan 3 detik selesai dalam sekitar 3 detik, bukan 12.
#
# Agar waktunya terlihat, setiap spesialis di sini adalah pengganti yang tidur 3 detik dan mencatat kapan
# ia mulai dan selesai. (Agen spesialis sungguhan berperilaku sama.)

# %%
# Langkah 1 - Menyiapkan model
import os
import time

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
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
# ## Langkah 2 - Empat spesialis pengganti yang lambat
# `spesialis_lambat` tidur 3 detik dan mencatat waktu mulai dan selesai ke `LINIMASA`.

# %%
LINIMASA: list[tuple[str, float, float]] = []  # (spesialis, mulai, selesai)
T0 = 0.0


def spesialis_lambat(nama: str, jawaban: str) -> str:
    """Pura-pura bekerja 3 detik (misalnya subagent yang memanggil tool) dan catat waktunya."""
    mulai = time.time() - T0
    time.sleep(3)
    LINIMASA.append((nama, mulai, time.time() - T0))
    return jawaban


@tool
def tanya_spesialis_operasi(permintaan: str) -> str:
    """Tanya spesialis Operasi tentang produksi dan status sumur."""
    return spesialis_lambat("operasi", "SR-020 produksi 120 bopd minyak, KN-033 menunggu pulling, SR-027 dalam investigasi H2S")


@tool
def tanya_spesialis_pemeliharaan(permintaan: str) -> str:
    """Tanya spesialis Pemeliharaan tentang work order yang terbuka."""
    return spesialis_lambat("pemeliharaan", "2 WO terbuka: WO-26-12501 sucker rod KN-033 patah (tinggi), WO-26-12502 lampu manifold (rendah)")


@tool
def tanya_spesialis_hse(permintaan: str) -> str:
    """Tanya spesialis HSE tentang insiden dan investigasi yang sedang berjalan."""
    return spesialis_lambat("hse", "1 investigasi aktif: INV-2026-011 paparan H2S di SR-027, tindakan korektif berjalan")


@tool
def tanya_spesialis_engineering(permintaan: str) -> str:
    """Tanya spesialis Engineering tentang kondisi teknis dan water cut sumur."""
    return spesialis_lambat("engineering", "Water cut SR-020 sekitar 80%, perlu evaluasi ukuran pompa ESP")


def cetak_linimasa() -> None:
    """Gambar waktu kerja tiap spesialis sebagai batang. Batang yang tumpang tindih = kerja paralel."""
    if not LINIMASA:
        return
    skala = 4  # karakter per detik
    awal = min(mulai for _, mulai, _ in LINIMASA)
    for nama, mulai, selesai in sorted(LINIMASA, key=lambda baris: baris[1]):
        geser = int((mulai - awal) * skala)
        panjang = max(1, int((selesai - mulai) * skala))
        print(f"   {nama:<13}|{' ' * geser}{'#' * panjang}  ({selesai - mulai:.1f} dtk)")
    total = max(selesai for _, _, selesai in LINIMASA) - awal
    kerja = sum(selesai - mulai for _, mulai, selesai in LINIMASA)
    print(f"\n   Total kerja spesialis: {kerja:.1f} dtk   Waktu jam dinding: {total:.1f} dtk")

# %% [markdown]
# ## Langkah 3 - Supervisor yang bertanya ke semua spesialis sekaligus
# Prompt meminta supervisor memanggil semua tool pada langkah yang sama.

# %%
supervisor = create_agent(
    model,
    tools=[tanya_spesialis_operasi, tanya_spesialis_pemeliharaan, tanya_spesialis_hse, tanya_spesialis_engineering],
    system_prompt=(
        "Anda koordinator. Untuk laporan status, tanya SEMUA spesialis yang relevan pada langkah "
        "yang sama (panggil tool-nya bersamaan), lalu ringkas dalam 4 butir."
    ),
)

pertanyaan = "Beri saya laporan status shift ini: produksi, work order, HSE, dan kondisi teknis."
print(f"Pengguna: {pertanyaan}\n")
T0 = time.time()
response = supervisor.invoke({"messages": [HumanMessage(content=pertanyaan)]})

panggilan_per_langkah = [len(m.tool_calls) for m in response["messages"] if isinstance(m, AIMessage) and m.tool_calls]
print(f"Panggilan tool per langkah supervisor: {panggilan_per_langkah}\n")

# %% [markdown]
# ## Langkah 4 - Timeline kerja spesialis
# Batang yang tumpang tindih berarti spesialis berjalan bersamaan.

# %%
print("Timeline kerja spesialis (setiap # = sekitar 0,25 detik):")
cetak_linimasa()

print(f"\nSupervisor:\n{response['messages'][-1].content}\n")

# %% [markdown]
# ## Yang baru saja terjadi
# - Supervisor bertanya ke keempat spesialis dalam SATU langkah
# - Batang mereka tumpang tindih pada timeline: mereka berjalan bersamaan
# - Waktu jam dinding sekitar spesialis TERLAMBAT, bukan jumlah semuanya
# - Ini hanya berlaku untuk pertanyaan yang SALING BEBAS; kalau B butuh jawaban A, B harus menunggu
