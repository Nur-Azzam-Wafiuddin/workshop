# %% [markdown]
# # Contoh 5: Tetap Berjalan Saat Ada yang Rusak
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/07-guardrails-middleware/code/05_resilience.py`
#
# Model mengalami timeout. API mengembalikan error. Tool kadang gagal. Agen produksi harus bertahan
# menghadapi kegagalan sehari-hari ini tanpa mengganggu pengguna.
#
# Dua middleware bawaan membantu:
#
# - `ToolRetryMiddleware`: retry tool yang gagal beberapa kali, menunggu makin lama setiap kali
# - `ModelFallbackMiddleware`: kalau model utama gagal, coba fallback model

# %%
# Langkah 1 - Menyiapkan fungsi pembuat model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelFallbackMiddleware, ToolRetryMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()


def buat_model(nama: str | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=nama or os.getenv("ONLINE_MODEL"),
        base_url=os.getenv("ONLINE_BASE_URL"),
        api_key=os.getenv("ONLINE_API_KEY"),
        reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
        max_retries=0,  # fail fast agar demo singkat
    )

# %% [markdown]
# ## Langkah 2 - Bagian 1: tool yang tidak stabil
# `baca_tekanan_scada` gagal dua kali lalu berhasil. `ToolRetryMiddleware` mengulangnya dengan exponential backoff
# sehingga model tidak melihat gangguan kecil itu.

# %%
PERCOBAAN = {"jumlah": 0}


@tool
def baca_tekanan_scada(kode_sumur: str) -> str:
    """Baca tekanan wellhead terakhir sebuah sumur dari gateway SCADA.

    Args:
        kode_sumur: Kode sumur, contoh "SR-020"
    """
    PERCOBAAN["jumlah"] += 1
    # API gateway yang tidak stabil: dua panggilan pertama gagal, yang ketiga berhasil
    if PERCOBAAN["jumlah"] <= 2:
        raise ConnectionError("Gateway SCADA timeout")
    return f"{kode_sumur}: tekanan wellhead 420 psi, tekanan flowline 180 psi"


pertanyaan = "Berapa tekanan wellhead sumur SR-020?"

print("Bagian 1: ToolRetryMiddleware (tool tidak stabil: gagal dua kali, lalu berhasil)")
print("-" * 60)
agent = create_agent(
    buat_model(),
    tools=[baca_tekanan_scada],
    system_prompt="Anda melaporkan tekanan sumur. Pakai tool. Jawab singkat dalam Bahasa Indonesia.",
    middleware=[
        ToolRetryMiddleware(
            max_retries=3,        # hingga 3 kali retry setelah kegagalan pertama
            initial_delay=0.2,    # tunggu 0,2 dtk sebelum retry pertama
            backoff_factor=2.0,   # lalu 0,4 dtk, 0,8 dtk ... (exponential backoff)
            jitter=False,         # buat pewaktuan dapat diprediksi untuk demo
        )
    ],
)
PERCOBAAN["jumlah"] = 0
response_retry = agent.invoke({"messages": [HumanMessage(content=pertanyaan)]})
print(f"   Tool dipanggil {PERCOBAAN['jumlah']} kali oleh middleware")
print(f"   Agen: {response_retry['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 3 - Bagian 2: model utama yang rusak
# Pertama tanpa cadangan (gagal), lalu dengan `ModelFallbackMiddleware` yang beralih ke model yang berfungsi.

# %%
print("Bagian 2: ModelFallbackMiddleware (model utama tidak ada)")
print("-" * 60)
utama_rusak = buat_model("model-ini-tidak-ada")
cadangan_berfungsi = buat_model()

try:
    create_agent(utama_rusak, tools=[]).invoke(
        {"messages": [HumanMessage(content="Ucapkan halo dalam dua kata.")]}
    )
except Exception as error:
    print(f"   Tanpa cadangan: {type(error).__name__}")

agen_cadangan = create_agent(
    utama_rusak,
    tools=[],
    middleware=[ModelFallbackMiddleware(cadangan_berfungsi)],
)
response_fallback = agen_cadangan.invoke({"messages": [HumanMessage(content="Ucapkan halo dalam dua kata.")]})
print(f"   Dengan cadangan: {response_fallback['messages'][-1].content}\n")

# %% [markdown]
# ## Ide Utama
# - `ToolRetryMiddleware` retry tool call yang gagal agar MODEL tidak melihat gangguan kecil
# - Backoff (0,2 dtk -> 0,4 dtk -> 0,8 dtk) mencegah membanjiri layanan yang sedang kesulitan
# - `ModelFallbackMiddleware` mencoba model berikutnya pada daftar ketika panggilan gagal
# - Hanya retry tool yang aman diulang (membaca sensor, ya; "menutup katup", hati-hati!)
