# %% [markdown]
# # Contoh 3: Setujui, Ubah, Tolak, atau Balas
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/06-persetujuan-manusia/code/03_edit_reject_respond.py`
#
# Reviewer manusia tidak terbatas pada "ya" atau "tidak". Interrupt yang sama mendukung empat keputusan:
#
# - `approve`: jalankan tool call persis seperti diusulkan
# - `edit`: ubah argumen, lalu jalankan
# - `reject`: jangan jalankan, dan beri tahu agen MENGAPA (agar ia bisa bereaksi)
# - `respond`: jangan jalankan, dan berikan hasil tool kepada agen sendiri
#
# Contoh ini menjalankan permintaan yang sama empat kali, sekali untuk tiap keputusan.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Tool, agen, dan fungsi skenario
# `jalankan_skenario` mengirim permintaan, berhenti di interrupt, menerapkan keputusan dari `buat_keputusan`,
# lalu menampilkan hasilnya.

# %%
FREKUENSI_VSD = {"SR-033": 48}


@tool
def ubah_frekuensi_vsd(kode_sumur: str, frekuensi_hz: int) -> str:
    """Ubah setpoint frekuensi VSD sebuah sumur ESP. Perubahan berlaku langsung pada motor di dalam sumur.

    Args:
        kode_sumur: Kode sumur, contoh "SR-033"
        frekuensi_hz: Frekuensi baru dalam Hz
    """
    FREKUENSI_VSD[kode_sumur.upper()] = frekuensi_hz
    return f"Frekuensi VSD {kode_sumur} sekarang {frekuensi_hz} Hz"


def buat_agen(model):
    return create_agent(
        model,
        tools=[ubah_frekuensi_vsd],
        system_prompt="Anda mengelola setpoint VSD. Pakai tool untuk melakukan yang diminta pengguna. Jawab singkat dalam Bahasa Indonesia.",
        middleware=[HumanInTheLoopMiddleware(interrupt_on={"ubah_frekuensi_vsd": True})],
        checkpointer=InMemorySaver(),
    )


def jalankan_skenario(model, judul: str, buat_keputusan) -> None:
    """Jalankan permintaan, berhenti, terapkan keputusan, dan tampilkan hasilnya."""
    FREKUENSI_VSD["SR-033"] = 48  # kembalikan untuk setiap skenario
    agent = buat_agen(model)
    config = {"configurable": {"thread_id": judul}}

    permintaan = "Naikkan frekuensi VSD sumur SR-033 menjadi 58 Hz."
    result = agent.invoke({"messages": [HumanMessage(content=permintaan)]}, config)

    diusulkan = result["__interrupt__"][0].value["action_requests"][0]
    keputusan = buat_keputusan(diusulkan)

    print(f"{judul}")
    print("-" * 60)
    print(f"Agen mengusulkan: {diusulkan['name']}({diusulkan['args']})")
    print(f"Keputusan manusia: {keputusan}")
    final = agent.invoke(Command(resume={"decisions": [keputusan]}), config)
    print(f"Agen: {final['messages'][-1].content}")
    print(f"Frekuensi SR-033: {FREKUENSI_VSD['SR-033']} Hz\n")

# %% [markdown]
# ## Langkah 3 - Skenario 1: APPROVE
# Jalankan persis seperti diusulkan. Keputusan ditulis sebagai fungsi yang menerima usulan agen (`aksi`) dan
# mengembalikan keputusan manusia. Usulan itu baru diketahui setelah agen berhenti, jadi `jalankan_skenario`
# yang memanggil fungsinya pada saat itu.

# %%
def setujui(aksi):
    return {"type": "approve"}


jalankan_skenario(model, "1) APPROVE", setujui)

# %% [markdown]
# ## Langkah 4 - Skenario 2: EDIT
# Idenya benar, tetapi angkanya terlalu tinggi, jadi argumennya diubah menjadi 52 Hz.

# %%
def ubah(aksi):
    argumen_baru = {**aksi["args"], "frekuensi_hz": 52}
    return {"type": "edit", "edited_action": {"name": aksi["name"], "args": argumen_baru}}


jalankan_skenario(model, "2) EDIT", ubah)

# %% [markdown]
# ## Langkah 5 - Skenario 3: REJECT
# Jangan jalankan, dan jelaskan mengapa.

# %%
def tolak(aksi):
    return {
        "type": "reject",
        "message": "Frekuensi di atas 55 Hz memerlukan persetujuan Production Engineer. Jangan ubah setpoint.",
    }


jalankan_skenario(model, "3) REJECT", tolak)

# %% [markdown]
# ## Langkah 6 - Skenario 4: RESPOND
# Jangan jalankan, tetapi berikan "hasil tool" sendiri.

# %%
def balas(aksi):
    return {
        "type": "respond",
        "message": "VSD SR-033 sedang dikunci untuk pengujian megger hingga Jumat.",
    }


jalankan_skenario(model, "4) RESPOND", balas)

# %% [markdown]
# ## Ide Utama
# - `approve`: tool berjalan tanpa perubahan
# - `edit`: tool berjalan dengan argumen dari reviewer (frekuensi menjadi 52 Hz)
# - `reject`: tool TIDAK berjalan; agen menerima alasannya dan bisa menjelaskannya
# - `respond`: tool TIDAK berjalan; teks Anda menjadi hasil tool
