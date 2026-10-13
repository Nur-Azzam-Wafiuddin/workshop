# %% [markdown]
# # Contoh 2: Checkpointer dan Thread
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/05-memori-agen/code/02_checkpointer_thread.py`
#
# Checkpointer adalah lemari arsip agen. `thread_id` menentukan percakapan mana yang dibuka: thread yang sama
# berbagi memori, thread berbeda mulai dari nol.

# %%
# Langkah 1 - Menyiapkan model dan agen dengan checkpointer
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
import os

load_dotenv()

print("Checkpointer dan Thread\n")

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# Checkpointer adalah lemari arsip agen
agent = create_agent(
    model,
    tools=[],
    system_prompt="Anda asisten operasi yang ramah. Jawab singkat dalam Bahasa Indonesia.",
    checkpointer=InMemorySaver(),
)


def tanya(agent, teks: str, thread_id: str) -> str:
    """Kirim satu pesan pada thread tertentu dan kembalikan jawaban teks agen."""
    config = {"configurable": {"thread_id": thread_id}}
    response = agent.invoke({"messages": [HumanMessage(content=teks)]}, config)
    return response["messages"][-1].content


# %% [markdown]
# ## Langkah 2 - Thread 'rina', giliran 1

# %%
print("Thread 'rina', giliran 1")
print("-" * 60)
pesan = "Halo! Nama saya Rina, saya operator shift malam di GS-SR1."
print(f"Pengguna: {pesan}")
print(f"Agen: {tanya(agent, pesan, 'rina')}")

# %% [markdown]
# ## Langkah 3 - Thread 'rina', giliran 2
# Thread sama, jadi agen ingat.

# %%
print("Thread 'rina', giliran 2 (thread sama, agen ingat)")
print("-" * 60)
pesan = "Siapa nama saya dan di mana saya bertugas?"
print(f"Pengguna: {pesan}")
print(f"Agen: {tanya(agent, pesan, 'rina')}")

# %% [markdown]
# ## Langkah 4 - Thread 'agus', giliran 1
# Thread berbeda, jadi agen mulai dari nol dan tidak tahu apa pun tentang Rina.

# %%
print("Thread 'agus', giliran 1 (thread berbeda, mulai dari nol)")
print("-" * 60)
print(f"Pengguna: {pesan}")
print(f"Agen: {tanya(agent, pesan, 'agus')}")

# %% [markdown]
# ## Langkah 5 - Thread 'rina', giliran 3
# Kembali ke thread pertama: memorinya masih utuh.

# %%
print("Thread 'rina', giliran 3 (kembali ke thread pertama)")
print("-" * 60)
pesan = "Tadi saya menyebut gathering station yang mana?"
print(f"Pengguna: {pesan}")
print(f"Agen: {tanya(agent, pesan, 'rina')}")
