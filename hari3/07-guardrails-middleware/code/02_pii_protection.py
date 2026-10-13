# %% [markdown]
# # Contoh 2: Melindungi Data Pribadi (PII)
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/07-guardrails-middleware/code/02_pii_protection.py`
#
# Pengguna menempelkan data pribadi ke chat tanpa berpikir: email, nomor HP, NIK, alamat IP perangkat.
# Begitu sampai ke model (juga ke log dan checkpointer Anda), data itu sulit ditarik kembali.
#
# `PIIMiddleware` menemukan nilai sensitif dan menanganinya SEBELUM model melihatnya:
#
# - `redact`: ganti dengan `[REDACTED_EMAIL]`
# - `mask`: sisakan beberapa karakter terakhir (`****7890`)
# - `hash`: ganti dengan sidik jari yang stabil (masukan sama -> hash sama)
# - `block`: tolak seluruh permintaan dengan melempar `PIIDetectionError`
#
# Detektor bawaan: email, credit_card, ip, mac_address, url.
# Anda bisa menambah detektor sendiri dengan regular expression (di sini: NIK 16 digit dan nomor HP Indonesia).

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import PIIDetectionError, PIIMiddleware
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv()

POLA_NIK = r"\b\d{16}\b"                  # NIK: 16 digit
POLA_HP = r"(?:\+62|62|0)8\d{8,11}"        # nomor HP Indonesia

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Bagian 1: redact, mask, dan hash
# Tiga strategi dipakai sekaligus: email memakai redact, nomor HP memakai mask (detektor kustom), alamat IP memakai hash.
# Kita bandingkan apa yang diketik pengguna dengan apa yang benar-benar diterima model.

# %%
print("Bagian 1: redact, mask, dan hash")
print("-" * 60)
agent = create_agent(
    model,
    tools=[],
    system_prompt="Anda asisten dukungan teknis. Jawab singkat dalam Bahasa Indonesia.",
    middleware=[
        PIIMiddleware("email", strategy="redact"),
        PIIMiddleware("hp", detector=POLA_HP, strategy="mask"),
        PIIMiddleware("ip", strategy="hash"),
    ],
)
teks_keluhan = (
    "Halo, saya Dewi (dewi.s@example.com), HP 081234567890. Alarm dari RTU 10.20.1.45 "
    "terus berbunyi sejak pagi. Tolong ringkas masalah saya."
)
print(f"Yang diketik pengguna:\n   {teks_keluhan}\n")
response_bagian_1 = agent.invoke({"messages": [HumanMessage(content=teks_keluhan)]})
print(f"Yang benar-benar diterima model:\n   {response_bagian_1['messages'][0].content}\n")
print(f"Agen: {response_bagian_1['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 3 - Bagian 2: detektor kustom (NIK) yang memblokir
# Dengan `strategy="block"`, permintaan yang memuat NIK dihentikan dengan `PIIDetectionError` sebelum sampai ke model.

# %%
print("Bagian 2: detektor kustom (NIK) yang memblokir permintaan")
print("-" * 60)
agen_ketat = create_agent(
    model,
    tools=[],
    system_prompt="Anda asisten dukungan teknis. Jawab singkat dalam Bahasa Indonesia.",
    middleware=[PIIMiddleware("nik", detector=POLA_NIK, strategy="block")],
)
teks_nik = "Tolong perbarui data saya. NIK saya 3578012345678901."
print(f"Pengguna: {teks_nik}")
try:
    agen_ketat.invoke({"messages": [HumanMessage(content=teks_nik)]})
except PIIDetectionError as error:
    print(f"Diblokir sebelum sampai ke model: {error}\n")

# %% [markdown]
# ## Langkah 4 - Bagian 3: pola NIK yang sama, tetapi dengan strategi redact
# Pola yang sama, tetapi dengan `strategy="redact"` permintaan tetap diteruskan, hanya NIK-nya yang sudah diganti `[REDACTED_NIK]`.

# %%
print("Bagian 3: pola NIK yang sama, tetapi di-redact alih-alih diblokir")
print("-" * 60)
agen_longgar = create_agent(
    model,
    tools=[],
    system_prompt="Anda asisten dukungan teknis. Jawab singkat dalam Bahasa Indonesia.",
    middleware=[PIIMiddleware("nik", detector=POLA_NIK, strategy="redact")],
)
response_bagian_3 = agen_longgar.invoke({"messages": [HumanMessage(content=teks_nik)]})
print(f"Model menerima: {response_bagian_3['messages'][0].content}")
print(f"Agen: {response_bagian_3['messages'][-1].content}\n")

# %% [markdown]
# ## Ide Utama
# - PII dibersihkan SEBELUM panggilan model, sehingga tidak pernah sampai ke penyedia
# - Teks yang sudah bersih itulah yang disimpan di state (juga di checkpoint dan log!)
# - `redact` = sembunyikan, `mask` = sembunyikan tetapi sisakan petunjuk, `hash` = sembunyikan tetapi tetap bisa dibandingkan
# - `block` = hentikan permintaan sepenuhnya (paling ketat)
# - Detektor kustom menerima string regex, misalnya `detector=r'\b\d{16}\b'`
# - Regex menemukan POLA, bukan makna: nama pekerja tidak bisa ditemukan dengan regex
