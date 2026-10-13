# %% [markdown]
# # Contoh 6: Kalau Interrupt Diabaikan
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/06-persetujuan-manusia/code/06_ignored_interrupt.py`
#
# Agen yang berhenti di interrupt menunggu `Command(resume=...)`. Contoh ini memperlihatkan apa yang terjadi bila
# thread itu dilanjutkan dengan cara lain:
#
# - Skenario A: `invoke(None, config)`, tanpa keputusan
# - Skenario B: pesan pengguna baru pada thread yang sama
# - Skenario C: cara yang benar untuk membatalkan, yaitu keputusan `reject`

# %%
# Langkah 1 - Menyiapkan model, tool, dan fungsi bantu
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import HumanMessage, ToolMessage
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


def agen_menunggu(nama_thread: str):
    """Buat agen baru, kirim permintaan, dan kembalikan (agent, config) saat agen berhenti di interrupt."""
    FREKUENSI_VSD["SR-033"] = 48
    agent = create_agent(
        model,
        tools=[ubah_frekuensi_vsd],
        system_prompt="Pakai tool untuk melakukan yang diminta pengguna. Jawab singkat dalam Bahasa Indonesia.",
        middleware=[HumanInTheLoopMiddleware(interrupt_on={"ubah_frekuensi_vsd": True})],
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": nama_thread}}
    permintaan = "Tolong atur frekuensi VSD sumur SR-033 menjadi 50 Hz."
    result = agent.invoke({"messages": [HumanMessage(content=permintaan)]}, config)
    assert "__interrupt__" in result, "agen seharusnya berhenti di interrupt"
    return agent, config


def tool_call_tanpa_hasil(agent, config) -> int:
    """Hitung usulan tool call di riwayat yang tidak pernah mendapat ToolMessage (tidak pernah berjalan)."""
    pesan = agent.get_state(config).values["messages"]
    sudah_dijawab = {m.tool_call_id for m in pesan if isinstance(m, ToolMessage)}
    diusulkan = [panggilan["id"] for m in pesan for panggilan in getattr(m, "tool_calls", []) or []]
    return len([i for i in diusulkan if i not in sudah_dijawab])


# %% [markdown]
# ## Langkah 2 - Skenario A: `invoke(None, config)`
# Melanjutkan thread tanpa keputusan apa pun.

# %%
print("Skenario A: invoke(None, config), tanpa keputusan")
print("-" * 60)
agent, config = agen_menunggu("skenario-a")
hasil = agent.invoke(None, config)
print(f"Masih berhenti di interrupt : {'__interrupt__' in hasil}")
print(f"Langkah berikutnya (next)   : {agent.get_state(config).next}")
print(f"Frekuensi SR-033            : {FREKUENSI_VSD['SR-033']} Hz\n")

# %% [markdown]
# ## Langkah 3 - Skenario B: pesan pengguna baru
# Thread yang sama diberi pesan biasa, bukan keputusan.

# %%
print("Skenario B: pesan pengguna baru pada thread yang sama")
print("-" * 60)
agent, config = agen_menunggu("skenario-b")
pesan_baru = "Halo, apakah permintaan tadi sudah selesai?"
print(f"Pengguna: {pesan_baru}")
hasil = agent.invoke({"messages": [HumanMessage(content=pesan_baru)]}, config)
print(f"Agen: {hasil['messages'][-1].content}")
print(f"Masih menunggu keputusan    : {bool(agent.get_state(config).next)}")
print(f"Usulan tool tanpa hasil     : {tool_call_tanpa_hasil(agent, config)} (tool tidak pernah berjalan)")
print(f"Frekuensi SR-033 sebenarnya : {FREKUENSI_VSD['SR-033']} Hz\n")

# %% [markdown]
# ## Langkah 4 - Skenario C: membatalkan dengan benar
# Thread yang sama dilanjutkan dengan keputusan `reject` beserta alasannya.

# %%
print("Skenario C: keputusan reject")
print("-" * 60)
agent, config = agen_menunggu("skenario-c")
keputusan = {"type": "reject", "message": "Dibatalkan oleh pengguna. Jangan ubah setpoint."}
print(f"Keputusan manusia: {keputusan}")
hasil = agent.invoke(Command(resume={"decisions": [keputusan]}), config)
print(f"Agen: {hasil['messages'][-1].content}")
print(f"Masih menunggu keputusan    : {bool(agent.get_state(config).next)}")
print(f"Frekuensi SR-033            : {FREKUENSI_VSD['SR-033']} Hz")

# %% [markdown]
# ## Ide Utama
# - `invoke(None, config)` tidak melanjutkan apa pun: agen tetap berhenti di interrupt yang sama
# - Pesan baru membuat interrupt DITINGGALKAN: tool tidak pernah berjalan dan tidak ada jejak keputusan
# - Setelah itu agen bisa menjawab seolah-olah tindakannya selesai, padahal data tidak berubah
# - Hanya `Command(resume=...)` yang menyelesaikan interrupt dengan benar; `reject` memberi agen alasannya
# - Periksa `get_state(config).next` atau `.interrupts` sebelum menerima pesan baru pada thread yang sama
