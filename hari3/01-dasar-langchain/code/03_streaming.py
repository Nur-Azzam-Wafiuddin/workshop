# %% [markdown]
# # Streaming Jawaban
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/03_streaming.py`
#
# Membandingkan pemanggilan biasa (`invoke`) dengan streaming (`stream`).

# %%
# Langkah 1 - Menyiapkan model
import os
import time

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Muat variabel lingkungan
load_dotenv()

PROMPT = "Jelaskan cara kerja Electrical Submersible Pump (ESP) pada sumur minyak dalam 2 paragraf."

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Tanpa streaming (cara biasa)
# Jawaban baru tampil setelah seluruh teks selesai dibuat.

# %%
print("Tanpa streaming (cara biasa):\n")

mulai = time.time()
response = model.invoke(PROMPT)
selesai = time.time()

print(response.content)
print(f"\nJawaban lengkap diterima setelah: {(selesai - mulai) * 1000:.0f} ms\n")

# %% [markdown]
# ## Langkah 3 - Dengan streaming
# Jawaban dialirkan chunk demi chunk dan ditulis begitu tiba.

# %%
print("=" * 80)
print("AI (streaming):")

mulai = time.time()
waktu_chunk_pertama = 0

# Alirkan jawaban chunk demi chunk
for chunk in model.stream(PROMPT):
    if waktu_chunk_pertama == 0:
        waktu_chunk_pertama = time.time()
    # Tulis setiap chunk begitu tiba (tanpa baris baru)
    print(chunk.content, end="", flush=True)

print("\n\nStreaming selesai.")
selesai = time.time()

print("\n")
print(f"Chunk pertama tiba setelah: {(waktu_chunk_pertama - mulai) * 1000:.0f} ms")
print(f"Streaming selesai setelah: {(selesai - mulai) * 1000:.0f} ms")
print("\nPerhatikan bahwa streaming terasa lebih responsif.")

# %% [markdown]
# ## Intinya
# Streaming memberi feedback langsung, sehingga aplikasi terasa lebih cepat.
