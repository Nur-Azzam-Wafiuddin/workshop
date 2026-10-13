# %% [markdown]
# # Contoh 4: Error adalah Informasi
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/bonus-agen-sql/code/04_error_recovery.py`
#
# Agen SQL bisa keliru: kolom salah eja, GROUP BY terlewat, query yang mengembalikan 10.000 baris. Yang
# DIKATAKAN tool kepada model menentukan apakah agen bisa pulih.
#
# Bagian 1 memperlihatkan pesan yang dibaca model dalam lima situasi. Bagian 2 menjalankan agen pada
# pertanyaan yang lebih sulit dengan ModelCallLimitMiddleware sebagai jaring pengaman.

# %%
# Langkah 1 - Impor dan model
import os
import sys

from migas_shared.config import ROOT

sys.path.insert(0, str(ROOT / "hari4" / "bonus-agen-sql" / "code"))
from sql_tools import MAKS_BARIS, PROMPT_SISTEM_SQL, daftar_tabel, deskripsikan_tabel, jalankan_query
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Bagian 1: apa yang dibaca model ketika ada yang salah
# Lima situasi dijalankan langsung lewat tool, tanpa model: kolom salah, tabel salah, ditolak guard,
# hasil kosong, dan terlalu banyak baris.

# %%
kasus = [
    ("Kolom salah", "SELECT nama_aset FROM work_order LIMIT 3"),
    ("Tabel salah", "SELECT * FROM work_orders LIMIT 3"),
    ("Ditolak guard", "DROP TABLE work_order"),
    ("Hasil kosong", "SELECT * FROM work_order WHERE asset_id = 'TIDAK-ADA'"),
    (f"Terlalu banyak baris (batasnya {MAKS_BARIS})", "SELECT wo_id, deskripsi FROM work_order"),
]
for label, sql in kasus:
    hasil = jalankan_query.invoke({"sql": sql})
    baris = hasil.splitlines()
    ditampilkan = baris[0] if len(baris) == 1 else f"{baris[0][:40]} ... (+{len(baris) - 1} baris lagi) ... {baris[-1]}"
    print(f"   {label}")
    print(f"      SQL:  {sql}")
    print(f"      Tool: {ditampilkan}\n")

print("   deskripsikan_tabel juga membantu model pulih dari salah ketik nama tabel:")
print(f"      Tool: {deskripsikan_tabel.invoke({'tabel': 'work_orders'})}\n")

# %% [markdown]
# ## Langkah 3 - Bagian 2: agen dengan batas panggilan model
# `ModelCallLimitMiddleware` menjadi jaring pengaman: agen yang bingung berhenti setelah 12 panggilan model.

# %%
agent = create_agent(
    model,
    tools=[daftar_tabel, deskripsikan_tabel, jalankan_query],
    system_prompt=PROMPT_SISTEM_SQL,
    middleware=[ModelCallLimitMiddleware(run_limit=12, exit_behavior="end")],
)

# %% [markdown]
# ## Langkah 4 - Pertanyaan yang lebih sulit
# Setelah agen menjawab, setiap panggilan tool ditandai OK atau GAGAL.

# %%
pertanyaan = "Jenis peralatan mana yang punya rata-rata downtime per work order tertinggi? Sebutkan 3 teratas, dalam jam."
print(f"Pengguna: {pertanyaan}\n")
response = agent.invoke({"messages": [HumanMessage(content=pertanyaan)]})

pesan_semua = response["messages"]
for indeks, pesan in enumerate(pesan_semua):
    if isinstance(pesan, AIMessage):
        for panggilan in pesan.tool_calls:
            hasil = next(
                m.content for m in pesan_semua[indeks + 1:] if getattr(m, "tool_call_id", None) == panggilan["id"]
            )
            gagal = str(hasil).startswith(("Error SQL", "Query ditolak")) or "tidak dikenal" in str(hasil)[:60]
            label = ", ".join(f"{nilai!r}" for nilai in panggilan["args"].values())
            print(f"   {'GAGAL' if gagal else 'OK   '} {panggilan['name']}({label[:110]})")
            if gagal:
                print(f"         -> {str(hasil)[:120]}")
print(f"\nAgen: {response['messages'][-1].content}\n")

# %% [markdown]
# ## Ide Utama
# - Pesan tool harus menyatakan apa yang salah DAN apa yang dilakukan berikutnya
# - "Tidak ada baris" dan "terlalu banyak baris" sama-sama dilaporkan jujur, tidak pernah senyap
# - Karena error dikembalikan (bukan dilempar), agen bisa membacanya dan mencoba lagi
# - Batas panggilan model memastikan agen yang bingung berhenti, bukan berputar selamanya
