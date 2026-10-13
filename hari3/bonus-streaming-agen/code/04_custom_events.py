# %% [markdown]
# # Contoh 4: Progres Kustom dari Dalam Tool
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/bonus-streaming-agen/code/04_custom_events.py`
#
# Tool yang memakan waktu lama (misalnya membaca laporan harian 31 hari satu per satu) tampak membeku:
# aliran "updates" hanya melapor ketika seluruh tool selesai. Tool bisa mengirim pesan progresnya SENDIRI
# saat berjalan, memakai `get_stream_writer()`. Pesan itu tiba pada `stream_mode="custom"`.
#
# Lalu kita gabungkan tiga mode dalam satu aliran, seperti UI chat sungguhan:
# - `"custom"`: baris status ("Hari ke-12 dari 31...")
# - `"messages"`: teks jawaban langsung
# - `"updates"`: batas antar langkah

# %%
# Langkah 1 - Menyiapkan model
import os
import re
import time

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer

from migas_shared.config import DATA

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Tool yang mengirim progres sendiri
# `writer = get_stream_writer()` mengirim event kustom ke `stream_mode="custom"` pada setiap hari yang dibaca.

# %%
LAPORAN = DATA / "raw" / "daily_reports" / "GS-SR1_2026-07.md"
POLA_MINYAK = re.compile(r"Produksi minyak bersih tercatat ([\d.]+) bopd")
POLA_WC = re.compile(r"water cut ([\d,]+)%")


@tool
def analisis_laporan_harian_juli() -> str:
    """Baca laporan harian GS-SR1 bulan Juli 2026 hari demi hari (31 hari) lalu hitung statistik produksi minyak dan water cut.
    Lambat: pakai hanya bila diminta menganalisis laporan sebulan penuh."""
    writer = get_stream_writer()  # mengirim event kustom ke stream_mode="custom"
    bagian = re.split(r"^## ", LAPORAN.read_text(encoding="utf-8"), flags=re.MULTILINE)[1:]
    minyak, wc = [], []
    for nomor, teks in enumerate(bagian, start=1):
        judul = teks.splitlines()[0]
        writer({"type": "progress", "selesai": nomor - 1, "total": len(bagian), "hari": judul})
        time.sleep(0.15)  # anggap setiap hari memerlukan sedikit waktu untuk dibaca
        m, w = POLA_MINYAK.search(teks), POLA_WC.search(teks)
        if m and w:
            minyak.append((int(m.group(1).replace(".", "")), judul))
            wc.append(float(w.group(1).replace(",", ".")))
    writer({"type": "progress", "selesai": len(bagian), "total": len(bagian), "hari": "-"})
    terendah = min(minyak)
    return (f"Dibaca {len(minyak)} dari {len(bagian)} hari. Produksi minyak rata-rata {sum(v for v, _ in minyak) / len(minyak):,.0f} bopd; "
            f"terendah {terendah[0]:,} bopd pada {terendah[1]}. Water cut rata-rata {sum(wc) / len(wc):.1f}% "
            f"(rentang {min(wc):.1f}% sampai {max(wc):.1f}%).")


def bar_progres(selesai: int, total: int, lebar: int = 20) -> str:
    terisi = int(lebar * selesai / total)
    return "#" * terisi + "." * (lebar - terisi)


agent = create_agent(
    model,
    tools=[analisis_laporan_harian_juli],
    system_prompt="Anda asisten operasi. Pakai tool analisis untuk laporan bulanan. Jawab dalam dua kalimat Bahasa Indonesia.",
)

# %% [markdown]
# ## Langkah 3 - Menggabungkan tiga mode dalam satu aliran
# Dengan daftar mode, setiap item menjadi `(nama_mode, data)`. Baris progres ditimpa dengan `\r`.

# %%
pertanyaan = "Analisis laporan harian GS-SR1 bulan Juli dan beri tahu saya tren produksi dan water cut-nya."
print(f"Pengguna: {pertanyaan}\n")

jawaban_dimulai = False
# Beberapa mode sekaligus: setiap item menjadi (nama_mode, data)
for mode, data in agent.stream(
    {"messages": [HumanMessage(content=pertanyaan)]},
    stream_mode=["custom", "messages", "updates"],
):
    if mode == "custom" and data.get("type") == "progress":
        # Timpa baris terminal yang sama dengan \r
        bar = bar_progres(data["selesai"], data["total"])
        print(f"\r   Membaca [{bar}] {data['selesai']}/{data['total']}  {data['hari'][:28]:<28}", end="", flush=True)
    elif mode == "messages":
        chunk, metadata = data
        if isinstance(chunk, AIMessageChunk) and metadata["langgraph_node"] == "model" and chunk.text:
            if not jawaban_dimulai:
                print("\n\nAgen: ", end="")
                jawaban_dimulai = True
            print(chunk.text, end="", flush=True)
    elif mode == "updates" and "tools" in data:
        print("\n   Tool analisis selesai", end="")

# %% [markdown]
# ## Ide Utama
# - `get_stream_writer()` memungkinkan tool mengirim progres SAAT berjalan
# - `stream_mode='custom'` menyampaikan persis apa yang ditulis tool (dictionary apa pun)
# - Berikan DAFTAR mode untuk mendapat pasangan `(mode, data)` dalam satu loop
# - custom = status/progres, messages = teks langsung, updates = perubahan langkah
# - Kombinasi itu adalah inti UI chat yang responsif
