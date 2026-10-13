# %% [markdown]
# # Contoh 3: Memeriksa state yang tersimpan
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/05-memori-agen/code/03_inspect_state.py`
#
# Checkpointer bukan kotak hitam. Anda bisa meminta state terkini sebuah thread dan
# menelusuri riwayatnya, satu checkpoint demi satu.

# %%
# Langkah 1 - Menyiapkan model dan agen dengan checkpointer
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from migas_shared.field_tools import cek_status_sumur

load_dotenv()

print("Memeriksa State yang Tersimpan\n")

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

agent = create_agent(
    model,
    tools=[cek_status_sumur],
    system_prompt="Anda menjawab status sumur dengan tool. Jawab singkat dalam Bahasa Indonesia.",
    checkpointer=InMemorySaver(),
)
config = {"configurable": {"thread_id": "periksa-demo"}}

# %% [markdown]
# ## Langkah 2 - Dua percakapan pada thread yang sama
# Dua pertanyaan dikirim agar ada riwayat yang bisa diperiksa.

# %%
agent.invoke({"messages": [HumanMessage(content="Bagaimana status sumur SR-020?")]}, config)
agent.invoke({"messages": [HumanMessage(content="Dan sumur ML-012?")]}, config)

# %% [markdown]
# ## Langkah 3 - State terkini sebuah thread

# %%
snapshot = agent.get_state(config)
messages = snapshot.values["messages"]
print(f"1. State terkini: {len(messages)} pesan tersimpan\n")
for message in messages:
    jenis = type(message).__name__
    if message.content:
        teks = str(message.content).replace("\n", " ")[:60]
    else:
        teks = f"(panggilan tool: {[call['name'] for call in message.tool_calls]})"
    print(f"   - {jenis:13} {teks}")

# %% [markdown]
# ## Langkah 4 - Apa yang berjalan berikutnya?
# Tuple kosong berarti agen sudah selesai.

# %%
print(f"2. Langkah berikutnya: {snapshot.next or 'tidak ada - proses sudah selesai'}")

# %% [markdown]
# ## Langkah 5 - Riwayat checkpoint
# Terbaru lebih dulu.

# %%
riwayat = list(agent.get_state_history(config))
print(f"3. Thread memiliki {len(riwayat)} checkpoint. Terbaru lebih dulu:")
for checkpoint in riwayat[:4]:
    jumlah = len(checkpoint.values.get("messages", []))
    print(f"   - langkah {checkpoint.metadata.get('step'):>2} -> {jumlah} pesan")

# %% [markdown]
# ## Ide Utama
# - `agent.get_state(config)` mengembalikan state tersimpan satu thread
# - `snapshot.values['messages']` adalah percakapan penuh, termasuk panggilan tool
# - `get_state_history()` memungkinkan Anda memeriksa setiap checkpoint (bagus untuk debugging)
# - Data yang sama itulah yang dibaca agen pada `invoke()` berikutnya
