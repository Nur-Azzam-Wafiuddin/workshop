# %% [markdown]
# # Parameter Model: temperature, max_tokens, dan Model Reasoning
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/04_parameters_and_reasoning.py`
#
# Konsep temperature dan token sudah dibahas di workshop hari 1 (unit 2). Di sini yang dilihat adalah:
# - parameter diberikan lewat konstruktor ChatOpenAI
# - `reasoning_effort` mengatur seberapa banyak model berpikir; nilai bawaannya diambil dari LLM_REASONING_EFFORT di `.env`
# - model reasoning menghitung token berpikirnya ke dalam batas max_tokens

# %%
# Langkah 1 - Menyiapkan fungsi pembuat model
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def buat_model(**parameter):
    """Buat ChatOpenAI dengan parameter tambahan (temperature, max_tokens, reasoning_effort, dan lain-lain)."""
    parameter.setdefault("reasoning_effort", os.getenv("LLM_REASONING_EFFORT", "none"))
    return ChatOpenAI(
        model=os.getenv("ONLINE_MODEL"),
        base_url=os.getenv("ONLINE_BASE_URL"),
        api_key=os.getenv("ONLINE_API_KEY"),
        **parameter,
    )


print(f"Parameter model untuk {os.getenv('ONLINE_MODEL')}\n")

# %% [markdown]
# ## Langkah 2 - Parameter diberikan sekali saat model dibuat

# %%
model = buat_model(temperature=0)
print("Model dibuat dengan temperature=0")
print(f"   temperature terbaca: {model.temperature}")

# %% [markdown]
# ## Langkah 3 - max_tokens pada model reasoning
# Token berpikir ikut dihitung dalam `max_tokens`. Di sini `reasoning_effort="high"` dipakai secara eksplisit supaya
# model berpikir panjang. Batas yang kecil bisa menghasilkan jawaban kosong.

# %%
prompt = "Jelaskan proses pemisahan minyak, gas, dan air di separator tiga fasa dalam 3 paragraf."
print("Batas max_tokens dan hasilnya")
print("=" * 80)
print(f"{'max_tokens':>10} | {'karakter jawaban':>16} | {'token keluar':>12} | {'token berpikir':>14} | finish_reason")
print("-" * 80)

for batas in (60, 400, 2000):
    response = buat_model(max_tokens=batas, reasoning_effort="high").invoke(prompt)
    usage = response.usage_metadata or {}
    berpikir = (usage.get("output_token_details") or {}).get("reasoning")
    alasan = response.response_metadata.get("finish_reason")
    print(f"{batas:>10} | {len(str(response.content)):>16} | {usage.get('output_tokens', '-'):>12} | "
          f"{berpikir if berpikir is not None else '-':>14} | {alasan}")
    if not str(response.content).strip():
        print("           -> jawaban KOSONG: token habis dipakai untuk berpikir sebelum ada teks yang terlihat")

# %% [markdown]
# ## Langkah 4 - Bandingkan dengan reasoning dimatikan
# `reasoning_effort="none"` membuat model langsung menulis jawaban. Batas yang sama kini menghasilkan jawaban terpotong,
# bukan kosong.

# %%
print(f"{'max_tokens':>10} | {'karakter jawaban':>16} | {'token keluar':>12} | {'token berpikir':>14} | finish_reason")
print("-" * 80)

for batas in (60, 400, 2000):
    response = buat_model(max_tokens=batas, reasoning_effort="none").invoke(prompt)
    usage = response.usage_metadata or {}
    berpikir = (usage.get("output_token_details") or {}).get("reasoning")
    alasan = response.response_metadata.get("finish_reason")
    print(f"{batas:>10} | {len(str(response.content)):>16} | {usage.get('output_tokens', '-'):>12} | "
          f"{berpikir if berpikir is not None else '-':>14} | {alasan}")

# %% [markdown]
# ## Pengamatan
# - Parameter seperti temperature, max_tokens, dan reasoning_effort diberikan lewat konstruktor ChatOpenAI
# - Pada model reasoning, token berpikir ikut dihitung dalam max_tokens
# - Batas yang terlalu kecil bisa menghasilkan jawaban kosong, bukan jawaban terpotong
# - Periksa finish_reason dan jumlah karakter sebelum memakai jawaban di kode
