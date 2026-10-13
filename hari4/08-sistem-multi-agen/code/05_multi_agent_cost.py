# %% [markdown]
# # Contoh 5: Berapa Biaya Multi-Agen?
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/08-sistem-multi-agen/code/05_multi_agent_cost.py`
#
# Multi-agen tidak gratis. Setiap agen tambahan berarti panggilan model tambahan. Contoh ini menjawab
# pertanyaan sederhana yang SAMA dengan dua cara:
# - A) satu agen yang memegang tool
# - B) supervisor yang mendelegasikan ke spesialis, yang memegang tool
#
# ...lalu mengukur jumlah panggilan model, token, dan waktu. Pakai hasilnya untuk memutuskan kapan sebuah tim layak.

# %%
# Langkah 1 - Menyiapkan model
import os
import time

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from migas_shared.field_tools import cek_status_sumur

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Fungsi pengukur
# `ukur` menjalankan agen sekali, lalu mengembalikan jumlah token dan detik.

# %%
def ukur(label: str, agent, pertanyaan: str) -> dict:
    """Jalankan agen sekali, lalu kembalikan jumlah panggilan model, token, dan detik."""
    handler = UsageMetadataCallbackHandler()
    mulai = time.time()
    response = agent.invoke(
        {"messages": [HumanMessage(content=pertanyaan)]},
        config={"callbacks": [handler]},
    )
    detik = time.time() - mulai

    pemakaian = list(handler.usage_metadata.values())
    return {
        "label": label,
        "jawaban": response["messages"][-1].content,
        "token": sum(u.get("total_tokens", 0) for u in pemakaian),
        "detik": detik,
    }

# %% [markdown]
# ## Langkah 3 - Rancangan A dan B
# A adalah satu agen dengan tool. B adalah supervisor yang mendelegasikan ke spesialis dengan tool yang sama.

# %%
# A) Satu agen dengan tool
tunggal = create_agent(
    model,
    tools=[cek_status_sumur],
    system_prompt="Anda asisten lapangan. Pakai tool. Jawab singkat.",
)

# B) Supervisor yang mendelegasikan ke spesialis dengan tool yang sama
spesialis = create_agent(
    model,
    tools=[cek_status_sumur],
    system_prompt="Anda spesialis Operasi. Pakai tool. Jawab singkat.",
)


@tool
def tanya_spesialis_operasi(permintaan: str) -> str:
    """Tanya spesialis Operasi tentang status sumur."""
    return spesialis.invoke({"messages": [HumanMessage(content=permintaan)]})["messages"][-1].content


supervisor = create_agent(
    model,
    tools=[tanya_spesialis_operasi],
    system_prompt="Anda supervisor. Delegasikan ke spesialis, lalu jawab. Jawab singkat.",
)

# %% [markdown]
# ## Langkah 4 - Ukur rancangan A (satu agen)

# %%
pertanyaan = "Bagaimana status sumur SR-020?"
print(f"Pertanyaan: {pertanyaan}\n")

hasil_a = ukur("A) satu agen", tunggal, pertanyaan)

# %% [markdown]
# ## Langkah 5 - Ukur rancangan B (supervisor + spesialis)

# %%
hasil_b = ukur("B) supervisor + spesialis", supervisor, pertanyaan)

# %% [markdown]
# ## Langkah 6 - Perbandingan

# %%
hasil = [hasil_a, hasil_b]

print(f"{'':<30}{'Token':>10}{'Detik':>10}")
print("-" * 50)
for baris in hasil:
    print(f"{baris['label']:<30}{baris['token']:>10}{baris['detik']:>10.1f}")
rasio = hasil[1]["token"] / max(hasil[0]["token"], 1)
print(f"\n   Multi-agen memakai sekitar {rasio:.1f}x token untuk jawaban yang sama.\n")

# %% [markdown]
# ## Multi-agen layak kalau
# - Satu agen memegang begitu banyak tool atau aturan sampai ia kebingungan
# - Bagian berbeda butuh prompt, model, atau izin akses yang berbeda
# - Sub-tugas yang saling bebas bisa berjalan paralel
# - Tim berbeda memiliki spesialis berbeda dan ingin mengujinya terpisah
#
# ## Tetap dengan satu agen kalau
# - Tugasnya kecil dan muat dalam satu prompt
# - Latensi atau biaya lebih penting daripada modularitas
# - Anda tergoda menambah agen "sekadar karena bisa"
