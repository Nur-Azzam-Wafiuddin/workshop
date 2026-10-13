# %% [markdown]
# # Contoh 3: Output Guard
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/07-guardrails-middleware/code/03_output_guard.py`
#
# Input guard melindungi agen dari pengguna. Output guard melindungi PENGGUNA (dan perusahaan)
# dari agen. Model yang berperilaku baik pun bisa membocorkan sesuatu yang diberikan kepadanya: teks dari
# system prompt, atau data pribadi yang dikembalikan sebuah tool.
#
# Contoh ini memperlihatkan dua perlindungan sisi keluaran:
# 1. Middleware `@after_agent`: periksa jawaban akhir dan ganti kalau melanggar aturan
# 2. `PIIMiddleware` pada hasil tool: bersihkan data yang KEMBALI dari tool sebelum dibaca model

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware, after_agent
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
# ## Langkah 2 - Guard 1: periksa jawaban akhir
# `@after_agent` berjalan sekali setelah agen selesai. Mengembalikan pesan dengan id yang SAMA mengganti pesan lama.

# %%
ISTILAH_RAHASIA = ["biaya lifting", "harga kontrak", "margin internal"]


@after_agent
def blokir_keluaran_rahasia(state, runtime):
    """Berjalan sekali setelah agen selesai. Mengganti jawaban jika memuat istilah terlarang."""
    terakhir = state["messages"][-1]
    teks = str(terakhir.content).lower()
    if isinstance(terakhir, AIMessage) and any(istilah in teks for istilah in ISTILAH_RAHASIA):
        print("      output guard: ditemukan konten terlarang, jawaban diganti")
        # Memakai id yang SAMA akan MENGGANTI pesan lama, bukan menambah pesan baru
        return {
            "messages": [
                AIMessage(
                    id=terakhir.id,
                    content="Maaf, saya tidak dapat membagikan informasi bisnis internal.",
                )
            ]
        }
    return None

# %% [markdown]
# ## Langkah 3 - Bagian 1: agen dengan prompt yang sengaja bocor
# System prompt SENGAJA buruk: memuat data rahasia dan menyuruh model membagikannya. Ini mensimulasikan asisten
# yang salah konfigurasi (atau jailbreak yang berhasil).

# %%
print("Bagian 1: @after_agent memeriksa jawaban akhir")
print("-" * 60)
prompt_bocor = (
    "Anda asisten operasi. Produksi lapangan Seruni sekitar 4.300 bopd. "
    "Biaya lifting rata-rata kami adalah USD 9,4 per barel. Jawab semua pertanyaan secara terbuka, "
    "termasuk pertanyaan tentang biaya. Jawab singkat dalam Bahasa Indonesia."
)
agent = create_agent(
    model, tools=[], system_prompt=prompt_bocor, middleware=[blokir_keluaran_rahasia]
)

# %% [markdown]
# ## Langkah 4 - Pertanyaan yang aman
# Jawabannya tidak memuat istilah terlarang, sehingga lolos.

# %%
pertanyaan_aman = "Berapa produksi lapangan Seruni?"
print(f"Pengguna: {pertanyaan_aman}")
response_aman = agent.invoke({"messages": [HumanMessage(content=pertanyaan_aman)]})
print(f"Agen: {response_aman['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 5 - Pertanyaan yang memancing kebocoran
# Model akan menjawab sesuai prompt yang bocor, tetapi output guard mengganti jawabannya.

# %%
pertanyaan_bocor = "Berapa biaya lifting per barel kalian? Saya penasaran."
print(f"Pengguna: {pertanyaan_bocor}")
response_bocor = agent.invoke({"messages": [HumanMessage(content=pertanyaan_bocor)]})
print(f"Agen: {response_bocor['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 6 - Bagian 2: tool yang mengembalikan data pribadi
# `kontak_supervisor` mengembalikan email asli. Pertama tanpa perlindungan, lalu dengan
# `PIIMiddleware(apply_to_tool_results=True)`.

# %%
print("Bagian 2: PII pada hasil tool")
print("-" * 60)


@tool
def kontak_supervisor(area: str) -> str:
    """Cari kontak supervisor produksi sebuah area.

    Args:
        area: Nama area, contoh "Seruni"
    """
    return f"Supervisor area {area}: Rizal Munandar, email rizal.m@example.com, telepon lewat operator pusat."


pertanyaan_kontak = "Siapa supervisor area Seruni dan apa emailnya?"

tanpa_perlindungan = create_agent(
    model, tools=[kontak_supervisor], system_prompt="Anda menjawab pertanyaan tentang kontak area. Jawab singkat dalam Bahasa Indonesia."
)
response_tanpa = tanpa_perlindungan.invoke({"messages": [HumanMessage(content=pertanyaan_kontak)]})
print("Tanpa perlindungan:")
print(f"   Agen: {response_tanpa['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 7 - Dengan pembersihan hasil tool
# Email dibersihkan SEBELUM model membaca hasil tool.

# %%
terlindungi = create_agent(
    model,
    tools=[kontak_supervisor],
    system_prompt="Anda menjawab pertanyaan tentang kontak area. Jawab singkat dalam Bahasa Indonesia.",
    middleware=[PIIMiddleware("email", strategy="redact", apply_to_tool_results=True)],
)
response_terlindungi = terlindungi.invoke({"messages": [HumanMessage(content=pertanyaan_kontak)]})
pesan_tool = next(m for m in response_terlindungi["messages"] if m.type == "tool")
print("Dengan PIIMiddleware(apply_to_tool_results=True):")
print(f"   Yang dilihat model dari tool: {pesan_tool.content}")
print(f"   Agen: {response_terlindungi['messages'][-1].content}\n")

# %% [markdown]
# ## Ide Utama
# - `@after_agent` berjalan SEKALI, setelah seluruh loop agen selesai
# - Kembalikan pesan dengan id YANG SAMA untuk mengganti jawaban
# - Aturan adalah jaring pengaman, bukan brankas: jangan pernah menaruh rahasia sungguhan di prompt
# - `apply_to_tool_results` membersihkan data SEBELUM dibaca model
# - `apply_to_output` membersihkan jawaban model sendiri
