# %% [markdown]
# # Contoh 2: Interrupt, Tinjau, Setujui
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/06-persetujuan-manusia/code/02_approve_with_interrupt.py`
#
# `HumanInTheLoopMiddleware` menghentikan sementara agen sebelum tool berisiko dijalankan. Agen berhenti, manusia
# meninjau tindakan yang diusulkan, lalu thread yang sama dilanjutkan dengan `Command(resume=...)`.
# Perlu checkpointer agar status interrupt tersimpan.

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
# ## Langkah 2 - Agen dengan persetujuan manusia
# Tool hanya-baca berjalan bebas (`False`), tool yang mengubah setpoint berhenti dulu (`True`).

# %%
FREKUENSI_VSD = {"SR-020": 50, "SR-033": 48, "ML-012": 50}


@tool
def baca_frekuensi_vsd(kode_sumur: str) -> str:
    """Baca frekuensi VSD saat ini pada sebuah sumur ESP (hanya baca).

    Args:
        kode_sumur: Kode sumur, contoh "SR-033"
    """
    frekuensi = FREKUENSI_VSD.get(kode_sumur.upper())
    return f"{kode_sumur}: {frekuensi} Hz" if frekuensi else f"Sumur tidak dikenal: {kode_sumur}"


@tool
def ubah_frekuensi_vsd(kode_sumur: str, frekuensi_hz: int) -> str:
    """Ubah setpoint frekuensi VSD sebuah sumur ESP. Perubahan berlaku langsung pada motor di dalam sumur.

    Args:
        kode_sumur: Kode sumur, contoh "SR-033"
        frekuensi_hz: Frekuensi baru dalam Hz
    """
    FREKUENSI_VSD[kode_sumur.upper()] = frekuensi_hz
    return f"Frekuensi VSD {kode_sumur} sekarang {frekuensi_hz} Hz"


agent = create_agent(
    model,
    tools=[baca_frekuensi_vsd, ubah_frekuensi_vsd],
    system_prompt="Anda asisten operasi. Pakai tool untuk melakukan yang diminta pengguna. Jawab singkat dalam Bahasa Indonesia.",
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={"baca_frekuensi_vsd": False, "ubah_frekuensi_vsd": True},
            description_prefix="Perubahan setpoint memerlukan persetujuan",
        )
    ],
    checkpointer=InMemorySaver(),
)
config = {"configurable": {"thread_id": "tinjau-vsd-1"}}

# %% [markdown]
# ## Langkah 3 - Pengguna membuat permintaan
# Jalankan sampai agen ingin mengubah frekuensi. Frekuensi belum berubah karena agen berhenti lebih dulu.

# %%
print("Langkah 1: pengguna membuat permintaan")
print("-" * 60)
permintaan = "Tolong atur frekuensi VSD sumur SR-033 menjadi 50 Hz."
print(f"Pengguna: {permintaan}")
result = agent.invoke({"messages": [HumanMessage(content=permintaan)]}, config)
print(f"Frekuensi SR-033 saat ini: {FREKUENSI_VSD['SR-033']} Hz (belum berubah)")

# %% [markdown]
# ## Langkah 4 - Agen berhenti dan menunggu keputusan
# Lihat apa yang ingin dilakukan agen lewat `result["__interrupt__"]`.

# %%
print("Langkah 2: agen BERHENTI dan menunggu keputusan")
print("-" * 60)
interrupt = result["__interrupt__"][0]
aksi = interrupt.value["action_requests"][0]
print(f"Tool call yang diusulkan: {aksi['name']}")
print(f"   Argumen            : {aksi['args']}")
print(f"   Keputusan yang boleh: {interrupt.value['review_configs'][0]['allowed_decisions']}")

# %% [markdown]
# ## Langkah 5 - Manusia menyetujui, agen dilanjutkan
# Thread YANG SAMA dilanjutkan dengan `Command(resume=...)`.

# %%
print("Langkah 3: manusia menyetujui, agen dilanjutkan")
print("-" * 60)
keputusan = {"type": "approve"}
print(f"Keputusan manusia: {keputusan}")
final = agent.invoke(Command(resume={"decisions": [keputusan]}), config)
print(f"Agen: {final['messages'][-1].content}")
print(f"Frekuensi SR-033 sekarang: {FREKUENSI_VSD['SR-033']} Hz")
