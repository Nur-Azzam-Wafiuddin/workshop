# %% [markdown]
# # Contoh 1: Menunggu vs Menonton
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/bonus-streaming-agen/code/01_invoke_vs_stream.py`
#
# `agent.invoke()` baru kembali ketika SEMUANYA selesai: setiap panggilan tool dan seluruh jawaban.
# Untuk tugas yang memakan 10 detik, pengguna menatap layar kosong selama 10 detik.
#
# `agent.stream()` memberi hasil SAAT TERJADI. Total waktunya sama, tetapi pengguna langsung melihat kemajuan.
#
# Contoh ini menjalankan pertanyaan yang sama dengan dua cara dan mengukur kapan hal pertama muncul.

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
# ## Langkah 2 - Tool lambat dan agen
# Tool `buat_laporan_sumur` sengaja tidur 3 detik untuk meniru query database yang lambat.

# %%
@tool
def buat_laporan_sumur(kode_sumur: str) -> str:
    """Buat laporan produksi harian sebuah sumur. Perhitungannya memakan waktu.

    Args:
        kode_sumur: Kode sumur, contoh "SR-020"
    """
    time.sleep(3)  # anggap ini query basis data yang lambat
    return f"{kode_sumur}: 120 bopd minyak, 480 bwpd air, water cut 80%, 1 alarm tekanan dalam 24 jam terakhir"


agent = create_agent(
    model,
    tools=[buat_laporan_sumur],
    system_prompt="Anda asisten operasi. Pakai tool untuk menjawab. Jawab singkat dalam Bahasa Indonesia.",
)
request = {"messages": [HumanMessage(content="Bagaimana kinerja sumur SR-020 hari ini?")]}

# %% [markdown]
# ## Langkah 3 - Bagian 1: invoke(), satu jawaban di akhir

# %%
print("Bagian 1: invoke(), satu jawaban di akhir")
print("-" * 60)
mulai = time.time()
response = agent.invoke(request)
total = time.time() - mulai
print("   (layar kosong selama agen bekerja...)")
print(f"   [{total:5.1f} dtk] Agen: {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 4 - Bagian 2: stream(), kemajuan saat terjadi
# `stream_mode="values"` memberi snapshot state penuh setelah setiap langkah.

# %%
print("Bagian 2: stream(stream_mode='values'), snapshot setelah setiap langkah")
print("-" * 60)
mulai = time.time()
output_pertama = None
terlihat = 0
for snapshot in agent.stream(request, stream_mode="values"):
    pesan = snapshot["messages"][-1]
    lewat = time.time() - mulai
    if len(snapshot["messages"]) == terlihat:
        continue  # tidak ada yang baru
    terlihat = len(snapshot["messages"])

    if isinstance(pesan, HumanMessage):
        label = "permintaan diterima"
    elif isinstance(pesan, AIMessage) and pesan.tool_calls:
        label = f"agen memutuskan memanggil {pesan.tool_calls[0]['name']}"
    elif isinstance(pesan, AIMessage):
        label = f"Agen: {pesan.content}"
    else:
        label = f"tool mengembalikan: {pesan.content}"
    if output_pertama is None and not isinstance(pesan, HumanMessage):
        output_pertama = lewat
    print(f"   [{lewat:5.1f} dtk] {label}")
total_stream = time.time() - mulai

# %% [markdown]
# ## Langkah 5 - Perbandingan

# %%
print("Perbandingan")
print(f"   invoke(): hal pertama yang dilihat pengguna muncul setelah {total:.1f} dtk")
print(f"   stream(): hal pertama yang dilihat pengguna muncul setelah {output_pertama:.1f} dtk (total {total_stream:.1f} dtk)")

# %% [markdown]
# ## Ide Utama
# - Total pekerjaannya sama. Yang berubah adalah KAPAN pengguna melihat sesuatu
# - `stream()` adalah generator: loop `for` menerima satu pembaruan setiap kali
# - `stream_mode='values'` memberi state penuh setelah setiap langkah
# - Berikutnya: alirkan kata-kata jawaban dan pilih seberapa rinci yang Anda perlukan
