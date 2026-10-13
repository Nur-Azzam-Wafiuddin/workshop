# %% [markdown]
# # Contoh 1: Agen SQL yang Naif
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/bonus-agen-sql/code/01_naive_sql_tool.py`
#
# Agen SQL paling sederhana punya SATU tool: jalankan_query(sql). Model harus menulis SQL untuk database
# yang belum pernah ia lihat. Perhatikan apa yang terjadi: ia menebak nama tabel dan kolom, dan database
# membalas dengan error.
#
# (Koneksinya hanya-baca, sehingga percobaan ini tidak bisa merusak data. Perlindungan yang Anda tambahkan
# nanti di bab ini jauh lebih penting ketika koneksinya BUKAN hanya-baca.)

# %%
# Langkah 1 - Menyiapkan model dan database
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from migas_shared.data import DB_DEFAULT, buat_database_migas

load_dotenv()

DB_PATH = Path(DB_DEFAULT)
if not DB_PATH.exists():
    buat_database_migas(DB_PATH)  # dibangun dari CSV pelatihan, isinya selalu sama

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Satu tool SQL dan agennya
# Tool `jalankan_query` menerima SQL apa saja dan mengembalikan hingga 20 baris. Agen tidak diberi tool
# untuk melihat skema.

# %%
@tool
def jalankan_query(sql: str) -> str:
    """Jalankan query SQL pada basis data dan kembalikan hasilnya.

    Args:
        sql: Query SQL yang dijalankan
    """
    try:
        with closing(sqlite3.connect(f"file:{DB_PATH.resolve().as_posix()}?mode=ro", uri=True)) as sambungan:
            baris = sambungan.execute(sql).fetchmany(20)
        return str(baris)
    except sqlite3.Error as error:
        return f"Error SQL: {error}"


agent = create_agent(
    model,
    tools=[jalankan_query],
    system_prompt="Anda menjawab pertanyaan tentang basis data operasi migas dengan SQL. Jawab singkat.",
)

# %% [markdown]
# ## Langkah 3 - Menanyakan agen
# Pertanyaan ini mensyaratkan pengetahuan tentang skema yang tidak dimiliki agen.

# %%
pertanyaan = "Berapa banyak insiden HSE yang bahayanya terkait gas H2S?"
print(f"Pengguna: {pertanyaan}\n")
response = agent.invoke({"messages": [HumanMessage(content=pertanyaan)]})

# %% [markdown]
# ## Langkah 4 - Melihat SQL yang dicoba agen
# `tampilkan_query` mencetak setiap query beserta statusnya dan menghitung percobaan yang gagal.

# %%
def tampilkan_query(response) -> tuple[int, int]:
    """Cetak setiap query SQL yang dicoba agen. Mengembalikan (percobaan, percobaan_gagal)."""
    percobaan = 0
    gagal = 0
    pesan_semua = response["messages"]
    for indeks, pesan in enumerate(pesan_semua):
        if isinstance(pesan, AIMessage):
            for panggilan in pesan.tool_calls:
                percobaan += 1
                hasil = next(
                    (m.content for m in pesan_semua[indeks + 1:] if getattr(m, "tool_call_id", None) == panggilan["id"]),
                    "",
                )
                status = "GAGAL" if str(hasil).startswith("Error SQL") else "OK   "
                gagal += status == "GAGAL"
                print(f"   {status} Percobaan {percobaan}: {panggilan['args']['sql']}")
                if status == "GAGAL":
                    print(f"         -> {hasil}")
    return percobaan, gagal


print("SQL yang dicoba agen:")
percobaan, gagal = tampilkan_query(response)
print(f"\nAgen: {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 5 - Yang baru saja terjadi

# %%
print("Yang baru saja terjadi:")
print(f"   - Agen memakai {percobaan} panggilan query; {gagal} di antaranya gagal")

# %% [markdown]
# ## Ide Utama
# - Agen harus MENEBAK nama tabel dan kolom sebelum bisa bertanya apa pun
# - Setiap tebakan salah adalah panggilan model tambahan: lebih lambat dan lebih mahal
# - Model yang cerdik mungkin pulih dengan mengintip `sqlite_master`, tetapi tidak ada jaminan
# - Lebih buruk lagi, tebakan salah bisa tampak benar: `WHERE hazard = 'H2S'` menghasilkan 0 baris tanpa
#   error apa pun (datanya tertulis `H2S/Gas`)
# - Berikutnya: beri agen tool untuk MENJELAJAHI database sebelum bertanya
