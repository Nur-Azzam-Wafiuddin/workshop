# %% [markdown]
# # Contoh 2: Streaming Token (Efek Mesin Ketik)
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/bonus-streaming-agen/code/02_stream_token.py`
#
# Model menulis jawabannya sepotong kecil demi sepotong (satu "token"). Dengan `stream_mode="messages"`
# Anda menerima setiap chunk begitu dihasilkan, sehingga jawaban bisa ditampilkan tumbuh di layar
# seperti ChatGPT.
#
# Setiap item adalah sepasang: `(message_chunk, metadata)`
# - `message_chunk`: chunk kecil pesan AI
# - `metadata`: antara lain node graf mana yang menghasilkannya

# %%
# Langkah 1 - Menyiapkan model
import os
import time

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk, HumanMessage
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
# ## Langkah 2 - Tool dan agen

# %%
@tool
def info_pompa(jenis: str) -> str:
    """Ambil fakta tentang jenis pompa angkat buatan.

    Args:
        jenis: Jenis pompa, contoh "ESP" atau "SRP"
    """
    fakta = {
        "esp": "ESP (Electrical Submersible Pump): pompa sentrifugal benam di dasar sumur, digerakkan motor listrik, "
               "cocok untuk laju cairan tinggi, sensitif terhadap pasir dan gas bebas",
        "srp": "SRP (Sucker Rod Pump): pompa piston di dasar sumur yang digerakkan batang pompa dari pumping unit di permukaan, "
               "cocok untuk laju rendah sampai sedang, tahan kondisi kasar tetapi dibatasi kedalaman",
    }
    return fakta.get(jenis.lower(), "Tidak ada data")


agent = create_agent(
    model,
    tools=[info_pompa],
    system_prompt="Anda menjelaskan pompa sumur kepada operator baru. Pakai tool untuk setiap jenis pompa, lalu jawab dalam 3-4 kalimat Bahasa Indonesia.",
)
request = {"messages": [HumanMessage(content="Jelaskan perbedaan ESP dan SRP.")]}

# %% [markdown]
# ## Langkah 3 - Bagian 1: seperti apa aliran mentahnya
# Cetak empat chunk pertama beserta node yang menghasilkannya.

# %%
print("Bagian 1: seperti apa aliran mentahnya")
print("-" * 60)
ditampilkan = 0
for chunk, metadata in agent.stream(request, stream_mode="messages"):
    if ditampilkan < 4:
        print(f"   {type(chunk).__name__:<16} text={chunk.text!r:<12} node={metadata['langgraph_node']}")
        ditampilkan += 1
print("   ... (masih banyak chunk kecil lainnya)\n")

# %% [markdown]
# ## Langkah 4 - Bagian 2: efek mesin ketik
# Hanya teks dari node `model` yang dicetak (hasil tool dan chunk kosong dari panggilan tool diabaikan).

# %%
print("Bagian 2: cetak hanya teks jawaban, saat tiba")
print("-" * 60)
print("Agen: ", end="", flush=True)
mulai = time.time()
waktu_token_pertama = None
jumlah_chunk = 0
for chunk, metadata in agent.stream(request, stream_mode="messages"):
    # Hanya teks dari node MODEL (abaikan hasil tool dan chunk kosong dari panggilan tool)
    if isinstance(chunk, AIMessageChunk) and metadata["langgraph_node"] == "model" and chunk.text:
        if waktu_token_pertama is None:
            waktu_token_pertama = time.time() - mulai
        jumlah_chunk += 1
        print(chunk.text, end="", flush=True)  # tanpa baris baru: teks tumbuh pada satu baris
total = time.time() - mulai

print(f"\n\nTeks pertama muncul setelah {waktu_token_pertama:.1f} dtk; "
      f"jawaban penuh selesai dalam {total:.1f} dtk ({jumlah_chunk} chunk)")

# %% [markdown]
# ## Ide Utama
# - `stream_mode='messages'` menghasilkan `(chunk, metadata)` saat model menulis
# - `chunk.text` adalah chunk teks baru; cetak dengan `end=''` dan `flush=True`
# - Filter `metadata['langgraph_node'] == 'model'` untuk melewati keluaran tool
# - Di aplikasi web, Anda mengirim tiap chunk ke browser, bukan `print()`
