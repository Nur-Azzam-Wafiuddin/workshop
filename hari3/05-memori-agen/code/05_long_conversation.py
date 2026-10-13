# %% [markdown]
# # Contoh 5: Menjaga percakapan panjang tetap terkendali
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/05-memori-agen/code/05_long_conversation.py`
#
# Memori bertambah dengan setiap pesan. Dibiarkan, percakapan panjang menjadi lambat, mahal, dan akhirnya
# terlalu besar untuk context window model. Dua solusi umum:
#
# 1. Trimming       : simpan hanya pesan terbaru
# 2. Summarization  : ganti pesan lama dengan ringkasan singkat (SummarizationMiddleware)

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, before_model
from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES

load_dotenv()

print("Menjaga Percakapan Panjang Tetap Terkendali\n")

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)
system_prompt = "Anda asisten operasi yang ramah. Jawab singkat dalam Bahasa Indonesia."

# %% [markdown]
# ## Langkah 2 - Percakapan uji dan middleware trimming
# Percakapan yang sama dipakai untuk ketiga strategi. `simpan_pesan_terbaru` berjalan sebelum setiap panggilan model
# dan membuang semua pesan kecuali beberapa yang terakhir.

# %%
SIMPAN_TERAKHIR = 4  # jumlah pesan yang dipertahankan oleh middleware trimming


@before_model
def simpan_pesan_terbaru(state, runtime):
    """Berjalan sebelum setiap panggilan model. Membuang semua kecuali beberapa pesan terakhir."""
    messages = state["messages"]
    if len(messages) <= SIMPAN_TERAKHIR:
        return None  # tidak ada yang diubah
    # REMOVE_ALL_MESSAGES mengosongkan daftar, lalu kita kembalikan hanya pesan terbaru
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *messages[-SIMPAN_TERAKHIR:]]}


PERCAKAPAN = [
    "Halo, saya Rina. Saya supervisor produksi di GS-SR1.",
    "Kami mengelola sumur ESP dan SRP di tiga area: Seruni, Kenanga, dan Melati.",
    "Kemarin sore ESP SR-020 trip overload saat jam sibuk.",
    "Teknisi datang hari Jumat untuk mengganti motor ESP.",
    "Ingatkan saya: siapa nama saya, gathering station mana yang saya awasi, dan apa yang rusak?",
]


def jalankan_percakapan(agent, label: str):
    config = {"configurable": {"thread_id": label}}
    for nomor, teks in enumerate(PERCAKAPAN, start=1):
        response = agent.invoke({"messages": [HumanMessage(content=teks)]}, config)
        tersimpan = agent.get_state(config).values["messages"]
        print(f"   Giliran {nomor}: {len(tersimpan):>2} pesan di memori")
    print(f"\n   Jawaban akhir: {response['messages'][-1].content}\n")
    return agent.get_state(config).values["messages"]


# %% [markdown]
# ## Langkah 3 - A) Tanpa batas
# Pembanding: memori bertambah di setiap giliran.

# %%
print("A) Tanpa batas: memori bertambah di setiap giliran")
print("-" * 60)
biasa = create_agent(model, tools=[], system_prompt=system_prompt, checkpointer=InMemorySaver())
jalankan_percakapan(biasa, "biasa")

# %% [markdown]
# ## Langkah 4 - B) Trimming
# Hanya beberapa pesan terakhir yang disimpan.

# %%
print(f"B) Trimming: hanya simpan {SIMPAN_TERAKHIR} pesan terakhir")
print("-" * 60)
dipangkas = create_agent(
    model,
    tools=[],
    system_prompt=system_prompt,
    middleware=[simpan_pesan_terbaru],
    checkpointer=InMemorySaver(),
)
jalankan_percakapan(dipangkas, "dipangkas")
print("   Trimming sederhana tetapi pelupa: fakta awal bisa hilang.\n")

# %% [markdown]
# ## Langkah 5 - C) Summarization
# Pesan lama diringkas menjadi satu ringkasan oleh `SummarizationMiddleware`.

# %%
print("C) Summarization: ringkas pesan lama menjadi satu ringkasan")
print("-" * 60)
meringkas = create_agent(
    model,
    tools=[],
    system_prompt=system_prompt,
    middleware=[
        SummarizationMiddleware(
            model=model,
            trigger=("messages", 6),  # mulai meringkas setelah 6 pesan atau lebih
            keep=("messages", 2),     # pertahankan 2 pesan terbaru apa adanya
        )
    ],
    checkpointer=InMemorySaver(),
)
tersimpan = jalankan_percakapan(meringkas, "meringkas")
pertama = tersimpan[0]
print("   Pesan tertua di memori kini berupa ringkasan:")
print(f"      {str(pertama.content)[:160].replace(chr(10), ' ')}...\n")

# %% [markdown]
# ## Ide Utama
# - Setiap pesan tetap berada di checkpoint kecuali Anda menghapusnya
# - Middleware `@before_model` bisa mengubah pesan sebelum tiap panggilan model
# - `RemoveMessage` memberi tahu LangGraph pesan mana yang dihapus dari state
# - `SummarizationMiddleware` menjaga inti giliran lama dan menghemat token
