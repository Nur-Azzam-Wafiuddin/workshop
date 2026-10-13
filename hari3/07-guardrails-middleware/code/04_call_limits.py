# %% [markdown]
# # Contoh 4: Batas Panggilan Model dan Tool
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/07-guardrails-middleware/code/04_call_limits.py`
#
# Agen berputar. Biasanya itu fitur; kadang itu bug yang menghabiskan uang.
# Batas adalah jaring pengaman yang bekerja apa pun keputusan model:
#
# - `ModelCallLimitMiddleware`: jumlah maksimum panggilan model (per proses atau per thread)
# - `ToolCallLimitMiddleware`: jumlah maksimum panggilan tool (semua tool, atau satu tool)
#
# Di sini tool yang rusak selalu menjawab "masih diproses, coba lagi", sehingga agen yang naif akan terus
# memanggilnya. Batas menghentikannya.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain_core.messages import HumanMessage
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
# ## Langkah 2 - Tool yang rusak dan fungsi bantu
# `cek_status_laporan` tidak pernah selesai, dan menghitung berapa kali ia dipanggil di `PANGGILAN`.

# %%
PANGGILAN = {"cek_status_laporan": 0}


@tool
def cek_status_laporan(id_job: str) -> str:
    """Periksa apakah job pembuatan laporan produksi sudah selesai.

    Args:
        id_job: ID job, contoh "JOB-1"
    """
    PANGGILAN["cek_status_laporan"] += 1
    # Backend rusak: job tidak pernah selesai
    return f"Job {id_job} masih diproses. Periksa lagi."


def buat_agen(model, middleware):
    return create_agent(
        model,
        tools=[cek_status_laporan],
        system_prompt=(
            "Anda menunggu job laporan. Panggil cek_status_laporan berulang sampai job selesai, "
            "lalu laporkan hasilnya. Jangan menyerah sebelum selesai. Jawab dalam Bahasa Indonesia."
        ),
        middleware=middleware,
    )


def jalankan(label: str, agent) -> None:
    PANGGILAN["cek_status_laporan"] = 0
    print(label)
    print("-" * 60)
    response = agent.invoke(
        {"messages": [HumanMessage(content="Tunggu JOB-1 selesai dan beri tahu saya hasilnya.")]},
        {"recursion_limit": 60},
    )
    print(f"   cek_status_laporan dipanggil {PANGGILAN['cek_status_laporan']} kali")
    print(f"   Agen: {str(response['messages'][-1].content)[:200]}\n")

# %% [markdown]
# ## Langkah 3 - Skenario A: batas panggilan model
# `run_limit=4` dengan `exit_behavior="end"` menghentikan agen dengan pesan setelah empat panggilan model.

# %%
jalankan(
    "A) ModelCallLimitMiddleware(run_limit=4): maksimal 4 panggilan model per proses",
    buat_agen(model, [ModelCallLimitMiddleware(run_limit=4, exit_behavior="end")]),
)

# %% [markdown]
# ## Langkah 4 - Skenario B: batas panggilan tool
# Panggilan tool berlebih mendapat `ToolMessage` error dan agen melanjutkan.

# %%
jalankan(
    "B) ToolCallLimitMiddleware(tool_name='cek_status_laporan', run_limit=3): maksimal 3 pemeriksaan status",
    buat_agen(model, [ToolCallLimitMiddleware(tool_name="cek_status_laporan", run_limit=3)]),
)

# %% [markdown]
# ## Ide Utama
# - `run_limit` menghitung panggilan dalam SATU `invoke()`; `thread_limit` menghitung di seluruh
#   percakapan (butuh checkpointer)
# - Batas panggilan model: `exit_behavior='end'` berhenti dengan pesan, `'error'` melempar exception
# - Batas panggilan tool: panggilan berlebih mendapat `ToolMessage` error dan agen melanjutkan
# - Batas tidak bergantung pada perilaku model: dijamin oleh kode
