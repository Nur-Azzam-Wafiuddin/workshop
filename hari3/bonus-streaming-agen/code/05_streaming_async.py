# %% [markdown]
# # Contoh 5: Streaming Async untuk Banyak Pengguna
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/bonus-streaming-agen/code/05_streaming_async.py`
#
# Server melayani banyak pengguna sekaligus. Kalau setiap panggilan agen MEMBLOKIR sambil menunggu model,
# satu jawaban lambat menahan semua yang lain. Dengan kode async (`astream`), server menunggu banyak
# respons model pada saat yang sama.
#
# - Bagian 1: dua "pengguna" dilayani bersamaan. Chunk jawaban mereka berselang-seling dalam waktu.
# - Bagian 2: aliran yang sama diubah menjadi Server-Sent Events (SSE), format teks yang dipakai browser
#   untuk menerima aliran langsung. Generator inilah yang dikembalikan endpoint web (misalnya di FastAPI).
#
# Kode async dijalankan lewat `jalankan(...)` dari `migas_shared.tampil`. Pembantu ini bekerja di skrip biasa
# maupun di Jupyter/Interactive Window, yang sudah memiliki event loop sendiri.

# %%
# Langkah 1 - Menyiapkan agen
import asyncio
import json
import os
import time

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_openai import ChatOpenAI

from migas_shared.tampil import jalankan

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)
agent = create_agent(
    model,
    tools=[],
    system_prompt="Anda asisten operasi produksi migas. Jawab dalam 3 kalimat pendek Bahasa Indonesia.",
)

# %% [markdown]
# ## Langkah 2 - Dua pengguna pada saat yang sama
# `alirkan_satu_pengguna` mengalirkan jawaban satu pengguna dan mencatat (waktu, pengguna, teks) tiap chunk.
# `asyncio.gather` menjalankan dua aliran sekaligus.

# %%
async def alirkan_satu_pengguna(pengguna: str, pertanyaan: str, kejadian: list, mulai: float) -> float:
    """Alirkan jawaban satu pengguna, catat (waktu, pengguna, teks) untuk setiap chunk."""
    async for chunk, metadata in agent.astream(
        {"messages": [HumanMessage(content=pertanyaan)]}, stream_mode="messages"
    ):
        if isinstance(chunk, AIMessageChunk) and chunk.text:
            kejadian.append((time.time() - mulai, pengguna, chunk.text))
    return time.time() - mulai


async def layani_dua_pengguna():
    kejadian: list[tuple[float, str, str]] = []
    mulai = time.time()
    selesai = await asyncio.gather(
        alirkan_satu_pengguna("Rina", "Apa itu water cut? Singkat saja.", kejadian, mulai),
        alirkan_satu_pengguna("Agus", "Apa itu bump test? Singkat saja.", kejadian, mulai),
    )
    return kejadian, selesai


print("Bagian 1: dua pengguna, dilayani bersamaan")
print("-" * 60)
kejadian, selesai = jalankan(layani_dua_pengguna())

# %% [markdown]
# ## Langkah 3 - Apakah aliran mereka tumpang tindih?

# %%
jendela = {}
for pengguna in ("Rina", "Agus"):
    waktu = [w for w, siapa, _ in kejadian if siapa == pengguna]
    jendela[pengguna] = (min(waktu), max(waktu))
    print(f"   {pengguna:<5} teks mengalir dari {min(waktu):4.1f} dtk sampai {max(waktu):4.1f} dtk ({len(waktu)} chunk)")

awal_tumpang = max(awal for awal, _ in jendela.values())
akhir_tumpang = min(akhir for _, akhir in jendela.values())
if akhir_tumpang > awal_tumpang:
    print(f"   Kedua jawaban mengalir bersamaan antara {awal_tumpang:.1f} dtk dan {akhir_tumpang:.1f} dtk")
print(f"\n   Total waktu nyata: {max(selesai):.1f} dtk")
print(f"   Dilayani satu per satu akan memakan sekitar {sum(selesai):.1f} dtk\n")

# %% [markdown]
# ## Langkah 4 - Server-Sent Events (SSE)
# Setiap event berupa teks dengan bentuk `data: <json>\n\n`. Kerangka kerja web bisa mengirim generator ini
# langsung ke browser.

# %%
async def aliran_sse(pertanyaan: str):
    """Async generator yang menghasilkan Server-Sent Events (SSE)."""
    async for chunk, metadata in agent.astream(
        {"messages": [HumanMessage(content=pertanyaan)]}, stream_mode="messages"
    ):
        if isinstance(chunk, AIMessageChunk) and chunk.text:
            yield f"data: {json.dumps({'type': 'token', 'text': chunk.text})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


async def kumpulkan_event(pertanyaan: str) -> list[str]:
    return [event async for event in aliran_sse(pertanyaan)]


events = jalankan(kumpulkan_event("Sebutkan satu manfaat LOTO dalam satu kalimat."))
for event in events[:5]:
    print(f"   {event.strip()!r}")
print(f"   ... total {len(events)} event, diakhiri event 'done'")

# %% [markdown]
# ## Ide Utama
# - `astream()` / `ainvoke()` adalah versi async; pakai di dalam `async def`
# - `asyncio.gather()` menjalankan beberapa aliran sekaligus tanpa thread tambahan
# - Panggilan model yang lambat sebagian besar MENUNGGU, sehingga satu proses bisa melayani banyak pengguna
# - SSE (baris `data: ...`) adalah cara termudah mendorong aliran langsung ke browser
