# %% [markdown]
# # Retry Bawaan LangChain
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/06_builtin_retry.py`
#
# `with_retry()` membungkus model dengan percobaan ulang otomatis untuk error sementara seperti 429.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Menambahkan retry
# Pakai logika retry bawaan, yang otomatis menangani error sementara seperti 429.

# %%
model_with_retry = model.with_retry(stop_after_attempt=3)  # Maksimal percobaan

# %% [markdown]
# ## Langkah 3 - Memanggil model dengan penanganan error
# Jenis error tertentu (429, 401) diberi petunjuk yang sesuai.

# %%
try:
    print("Memanggil API dengan retry otomatis...\n")
    response = model_with_retry.invoke("Apa kepanjangan SOP dan apa fungsinya di lapangan? Jawab singkat.")
    print("Berhasil.")
    print(response.content)
except Exception as error:
    print(f"Error: {error}")

    # Tangani jenis error tertentu
    pesan = str(error)
    if "429" in pesan:
        print("\nBatas laju terlampaui. Coba lagi beberapa saat lagi.")
    elif "401" in pesan:
        print("\nPeriksa API key Anda di file .env")
