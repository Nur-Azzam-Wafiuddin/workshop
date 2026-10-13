# %% [markdown]
# # Bab bonus Streaming Agen - Latihan 1: Asisten Operasi Langsung
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Asisten terminal dengan streaming yang menggabungkan tiga ide:
# - Teks langsung: jawaban muncul kata demi kata (`stream_mode="messages"`)
# - Status langsung: baris status ketika tool mulai atau melapor progres (`stream_mode="updates"` dan `"custom"`)
# - Memori: follow-up question berfungsi (checkpointer dari bab 5)
#
# Bagian utama memakai empat pertanyaan berskrip, satu sel per giliran. Sel terakhir membuka mode
# interaktif (ketik pertanyaan sendiri) setelah `INTERAKTIF` diubah menjadi `True`.

# %%
# Langkah 1 - Menyiapkan model
import os
import time

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer

from migas_shared.field_tools import DATA_SUMUR, cek_status_sumur

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Tool audit dan agen dengan memori
# `audit_water_cut` melapor progres lewat `get_stream_writer()`. `InMemorySaver` menjaga riwayat per `thread_id`.

# %%
NAMA_RAMAH = {
    "cek_status_sumur": "Memeriksa status sumur",
    "audit_water_cut": "Mengaudit water cut semua sumur",
}


# TODO(BS.1): buat tool audit_water_cut yang mengirim progres per sumur lewat get_stream_writer() (tunggu 0,7 detik per sumur) dan melaporkan sumur dengan water cut di atas 75%
audit_water_cut = None  # TODO: ganti dengan implementasi Anda


# TODO(BS.2): buat agen dengan tool cek_status_sumur dan audit_water_cut, serta checkpointer=InMemorySaver() agar follow-up question berfungsi
agent = None  # TODO: ganti dengan implementasi Anda
config = {"configurable": {"thread_id": "sesi-langsung"}}

# %% [markdown]
# ## Langkah 3 - Fungsi untuk satu giliran
# `tanya_langsung` mengalirkan satu jawaban ke terminal dengan status langsung dan teks langsung.

# %%
def tanya_langsung(agent, teks: str, config: dict) -> None:
    """Alirkan satu jawaban ke terminal dengan status langsung dan teks langsung."""
    dalam_jawaban = False
    # TODO(BS.3): alirkan agent.stream({"messages": [HumanMessage(content=teks)]}, config, stream_mode=["updates", "messages", "custom"])
    for mode, data in []:  # TODO: ganti dengan implementasi Anda
        if mode == "updates":
            for node, isi in data.items():
                for pesan in isi.get("messages", []) if isinstance(isi, dict) else []:
                    if isinstance(pesan, AIMessage) and pesan.tool_calls:
                        for call in pesan.tool_calls:
                            print(f"   {NAMA_RAMAH.get(call['name'], call['name'])}...")
                    elif node == "tools":
                        print(f"   {pesan.name} selesai")
        elif mode == "custom":
            print(f"      -> {data.get('progres', data)}")
        elif mode == "messages":
            chunk, metadata = data
            if isinstance(chunk, AIMessageChunk) and metadata["langgraph_node"] == "model" and chunk.text:
                if not dalam_jawaban:
                    print("Agen: ", end="", flush=True)
                    dalam_jawaban = True
                print(chunk.text, end="", flush=True)
    print("\n")

# %% [markdown]
# ## Langkah 4 - Giliran 1: status sumur pertama

# %%
teks_1 = "Bagaimana status sumur SR-020?"
print(f"Pengguna: {teks_1}")
tanya_langsung(agent, teks_1, config)

# %% [markdown]
# ## Langkah 5 - Giliran 2: status sumur kedua

# %%
teks_2 = "Dan sumur ML-012?"
print(f"Pengguna: {teks_2}")
tanya_langsung(agent, teks_2, config)

# %% [markdown]
# ## Langkah 6 - Giliran 3: audit water cut semua sumur
# Tool ini lambat dan melapor progres lewat aliran `custom`.

# %%
teks_3 = "Jalankan audit water cut semua sumur dan beri tahu yang tinggi."
print(f"Pengguna: {teks_3}")
tanya_langsung(agent, teks_3, config)

# %% [markdown]
# ## Langkah 7 - Giliran 4: pertanyaan lanjutan
# Berkat checkpointer, agen mengingat dua sumur yang ditanyakan di awal.

# %%
teks_4 = "Dari dua sumur yang pertama saya tanyakan, mana yang produksi minyaknya lebih besar?"
print(f"Pengguna: {teks_4}")
tanya_langsung(agent, teks_4, config)

# %% [markdown]
# ## Langkah 8 - Mencoba sendiri (opsional)
# Ubah `INTERAKTIF` menjadi `True`, jalankan sel, lalu ketik pertanyaan. Ketik `keluar` (atau kosongkan) untuk berhenti.
# Percakapan melanjutkan thread yang sama.

# %%
INTERAKTIF = False  # ubah ke True untuk mencoba sendiri

if INTERAKTIF:
    print("Tanyakan status sumur atau minta audit water cut. Ketik 'keluar' untuk berhenti.\n")
    while True:
        teks = input("Pengguna: ").strip()
        if teks.lower() in {"keluar", "exit", ""}:
            break
        tanya_langsung(agent, teks, config)
