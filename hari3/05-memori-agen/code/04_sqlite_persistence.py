# %% [markdown]
# # Contoh 4: Memori yang Bertahan Setelah Restart
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/05-memori-agen/code/04_sqlite_persistence.py`
#
# `SqliteSaver` menyimpan checkpoint di file SQLite, sehingga percakapan bertahan walau program dihentikan dan
# dijalankan lagi. Contoh ini menirukan dua kali menjalankan program dengan file database yang sama.

# %%
# Langkah 1 - Impor dan fungsi bantu
import os
import sqlite3
import tempfile

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv

load_dotenv()

print("Memori yang Bertahan Setelah Restart\n")


def buat_agen(db_path: str):
    """Buat agen yang memorinya disimpan di file SQLite."""
    model = ChatOpenAI(
        model=os.getenv("ONLINE_MODEL"),
        base_url=os.getenv("ONLINE_BASE_URL"),
        api_key=os.getenv("ONLINE_API_KEY"),
        reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    )
    connection = sqlite3.connect(db_path, check_same_thread=False)
    agent = create_agent(
        model,
        tools=[],
        system_prompt="Anda asisten operasi yang ramah. Jawab singkat dalam Bahasa Indonesia.",
        checkpointer=SqliteSaver(connection),
    )
    return agent, connection


def tanya(agent, teks: str) -> str:
    config = {"configurable": {"thread_id": "rina-shift-malam"}}
    response = agent.invoke({"messages": [HumanMessage(content=teks)]}, config)
    return response["messages"][-1].content


def jumlah_pesan(agent) -> int:
    config = {"configurable": {"thread_id": "rina-shift-malam"}}
    return len(agent.get_state(config).values.get("messages", []))


# Folder sementara untuk file database; dibersihkan di sel terakhir
folder = tempfile.TemporaryDirectory()
db_path = os.path.join(folder.name, "memori_agen.db")

# %% [markdown]
# ## Langkah 2 - Fase 1: program dijalankan pertama kali
# Agen menyimpan percakapan ke file SQLite, lalu koneksi ditutup untuk menirukan program berhenti.

# %%
print("Fase 1: program dijalankan pertama kali")
print("-" * 60)
agent, connection = buat_agen(db_path)
pesan = "Halo, saya Rina. Tolong ingat: sumur yang saya awasi malam ini adalah SR-020 dan ML-012."
print(f"Pengguna: {pesan}")
print(f"Agen: {tanya(agent, pesan)}")
connection.close()  # "program" berakhir di sini
print(f"\n   Ukuran file database: {os.path.getsize(db_path):,} byte")
print("   Program 'berhenti'. Semua yang ada di RAM hilang.")

# %% [markdown]
# ## Langkah 3 - Fase 2: program dijalankan lagi
# Agen dan koneksi yang benar-benar baru, file yang sama. Riwayat masih ada di disk.

# %%
print("Fase 2: program dijalankan lagi (agen baru, koneksi baru)")
print("-" * 60)
agent, connection = buat_agen(db_path)
print(f"   Pesan yang sudah ada di disk sebelum bertanya: {jumlah_pesan(agent)}\n")
pesan = "Sumur mana saja yang saya awasi malam ini?"
print(f"Pengguna: {pesan}")
print(f"Agen: {tanya(agent, pesan)}")
connection.close()

# %% [markdown]
# ## Langkah 4 - Membersihkan folder sementara

# %%
folder.cleanup()
