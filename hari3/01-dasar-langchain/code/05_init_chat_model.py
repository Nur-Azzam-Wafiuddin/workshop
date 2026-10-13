# %% [markdown]
# # Inisialisasi Model Lintas Penyedia dengan init_chat_model()
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/05_init_chat_model.py`
#
# `init_chat_model()` membuat model dari nama penyedia sehingga berpindah penyedia cukup mengganti string.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

load_dotenv()

nama_model = os.getenv("ONLINE_MODEL")

# init_chat_model() memilih kelas model yang tepat dari nama penyedia (model_provider).
# Server yang kompatibel OpenAI (OpenRouter, Ollama, vLLM) dipakai dengan model_provider="openai"
# dan base_url masing-masing.
model = init_chat_model(
    nama_model,
    model_provider="openai",
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

print("Inisialisasi Model Lintas Penyedia dengan init_chat_model()\n")

# %% [markdown]
# ## Langkah 2 - Memanggil model
# Interface pemanggilan sama seperti `ChatOpenAI`.

# %%
response = model.invoke([
    HumanMessage(content="Apa kepanjangan HSE dalam industri migas? Jawab dalam satu kalimat.")
])

print("Jawaban:", response.content)

# %% [markdown]
# ## Konsep Berpindah Penyedia
# `init_chat_model()` membuat perpindahan penyedia menjadi sederhana:
#
#     # Endpoint kompatibel OpenAI (OpenRouter, Ollama, vLLM)
#     model = init_chat_model("nama-model", model_provider="openai", base_url="...", api_key="...")
#
#     # OpenAI langsung
#     model = init_chat_model("openai:gpt-5-mini")
#
#     # Anthropic (butuh paket langchain-anthropic)
#     model = init_chat_model("anthropic:claude-sonnet-4-5")
#
#     # Google (butuh paket langchain-google-genai)
#     model = init_chat_model("google_genai:gemini-2.5-flash")
#
# Interface sama, penyedia berbeda: cukup ganti string model.
