# %% [markdown]
# # Contoh 3: Menampilkan Progres dengan stream_mode="updates"
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/bonus-streaming-agen/code/03_stream_progress.py`
#
# Token menjawab "apa yang DIKATAKAN model?". Sering pengguna juga ingin tahu "apa yang DIKERJAKAN agen?".
# `stream_mode="updates"` memancarkan satu item per LANGKAH, dengan nama node yang berjalan:
#
# - `{"model": {...}}`: model berjalan (mungkin memutuskan memanggil tool)
# - `{"tools": {...}}`: satu atau lebih tool berjalan dan mengembalikan hasil
#
# Itulah yang dibutuhkan untuk tampilan progres: "Memeriksa status sumur... selesai".

# %%
# Langkah 1 - Menyiapkan model
import os
import time

import pandas as pd
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from migas_shared.config import DATA
from migas_shared.field_tools import cek_status_sumur

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Dua tool lambat dan agen
# Kedua tool diberi `time.sleep` agar progresnya terlihat. Nama teknis tool dipetakan ke label ramah di `NAMA_RAMAH`.

# %%
_WO = pd.read_csv(DATA / "eval" / "work_orders_truth.csv")


@tool
def riwayat_work_order(kode_aset: str) -> str:
    """Hitung jumlah work order dan total downtime sebuah aset sepanjang data yang tersedia.

    Args:
        kode_aset: Kode aset, contoh "SR-020"
    """
    time.sleep(1.5)  # anggap query ke sistem pemeliharaan
    baris = _WO[_WO["asset_id"] == kode_aset.strip().upper()]
    if baris.empty:
        return f"{kode_aset}: tidak ada work order"
    return f"{kode_aset}: {len(baris)} work order, total downtime {baris['downtime_hours'].sum():.1f} jam"


@tool
def status_sumur_lambat(kode_sumur: str) -> str:
    """Cek status operasi sebuah sumur (data real-time, sedikit lambat).

    Args:
        kode_sumur: Kode sumur, contoh "SR-020"
    """
    time.sleep(1.5)
    return cek_status_sumur.invoke({"kode_sumur": kode_sumur})


NAMA_RAMAH = {
    "status_sumur_lambat": "Memeriksa status sumur",
    "riwayat_work_order": "Membuka riwayat work order",
}

agent = create_agent(
    model,
    tools=[status_sumur_lambat, riwayat_work_order],
    system_prompt=(
        "Anda asisten operasi. Untuk laporan kondisi sumur, panggil KEDUA tool dalam langkah yang sama, "
        "lalu ringkas dalam dua kalimat Bahasa Indonesia."
    ),
)

# %% [markdown]
# ## Langkah 3 - Menampilkan progres per langkah
# Setiap update berbentuk `{"<nama node>": {"messages": [...]}}`. Kita tampilkan tool yang diminta,
# tool yang selesai, dan jawaban akhir.

# %%
pertanyaan = "Berikan laporan kondisi sumur SR-020 lengkap dengan riwayat perbaikannya."
print(f"Pengguna: {pertanyaan}\n")
mulai = time.time()

for update in agent.stream({"messages": [HumanMessage(content=pertanyaan)]}, stream_mode="updates"):
    # Setiap update berbentuk {"<nama node>": {"messages": [...]}}
    for node, isi in update.items():
        lewat = time.time() - mulai
        if not isinstance(isi, dict):
            continue  # sebagian langkah (misalnya hook middleware) melaporkan None
        for pesan in isi.get("messages", []):
            if node == "model" and isinstance(pesan, AIMessage) and pesan.tool_calls:
                for call in pesan.tool_calls:
                    langkah = NAMA_RAMAH.get(call["name"], call["name"])
                    print(f"   [{lewat:4.1f} dtk] {langkah}...  args={call['args']}")
            elif node == "tools":
                print(f"   [{lewat:4.1f} dtk] {pesan.name} selesai")
            elif node == "model":
                print(f"   [{lewat:4.1f} dtk] Menulis jawaban...\n")
                print(f"Agen: {pesan.content}")

# %% [markdown]
# ## Ide Utama
# - `stream_mode='updates'` memancarkan satu item per langkah: `{nama_node: pembaruan_state}`
# - node `model` = model berjalan; pesannya bisa berisi `tool_calls` (apa yang akan terjadi)
# - node `tools` = tool selesai; pesannya berisi hasil
# - Petakan nama tool teknis ke label yang ramah untuk pengguna
# - Kedua tool diminta bersamaan, sehingga berjalan paralel
