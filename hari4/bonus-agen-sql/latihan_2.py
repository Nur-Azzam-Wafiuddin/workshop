# %% [markdown]
# # Latihan Bonus: Analis Percakapan
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Menggabungkan agen SQL dengan memori (bab 5). Checkpointer memungkinkan pengguna mengajukan pertanyaan
# LANJUTAN yang baru masuk akal setelah pertanyaan sebelumnya:
#
# - "Sumur mana yang paling banyak memproduksi minyak?" -> sumur A
# - "Bagaimana dengan air?" -> (pertanyaan sama, produk berbeda)
# - "Berapa barel selisih total semua produk keduanya?" -> butuh kedua jawaban sebelumnya

# %%
# Langkah 1 - Impor, database produksi, dan model
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from migas_shared.config import ROOT

sys.path.insert(0, str(ROOT / "hari4" / "bonus-agen-sql" / "code"))  # agar sql_tools.py ditemukan
# production_db.py ada di folder code/, yang sudah termasuk path di atas
from sql_tools import PROMPT_SISTEM_SQL, bangun_alat_sql  # noqa: E402
from production_db import buat_database_produksi  # noqa: E402

load_dotenv()

folder_kerja = tempfile.TemporaryDirectory()
db_path = buat_database_produksi(Path(folder_kerja.name) / "produksi.db")
daftar_tabel, deskripsikan_tabel, jalankan_query = bangun_alat_sql(db_path)

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Agen dengan memori
# `InMemorySaver` menyimpan riwayat utas, sehingga pertanyaan lanjutan bisa merujuk jawaban sebelumnya.

# %%
# TODO(BQ.4): buat agen SQL dengan tiga tool, prompt yang memperbolehkan pertanyaan lanjutan, ModelCallLimitMiddleware(run_limit=15, exit_behavior="end"), dan checkpointer=InMemorySaver()
agent = None  # TODO: ganti dengan implementasi Anda
config = {"configurable": {"thread_id": "sesi-analis"}}

# %% [markdown]
# ## Langkah 3 - Pertanyaan pertama
# Sumur dengan produksi minyak terbanyak.

# %%
pertanyaan_1 = "Sumur mana yang paling banyak memproduksi minyak secara total?"
print(f"Pengguna: {pertanyaan_1}")
# TODO(BQ.5): panggil agent.invoke dengan HumanMessage dan config thread yang sama
response_1 = None  # TODO: ganti dengan implementasi Anda
print(f"Agen: {response_1['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 4 - Pertanyaan lanjutan
# "Bagaimana dengan air?" hanya masuk akal karena agen mengingat pertanyaan sebelumnya.

# %%
pertanyaan_2 = "Bagaimana dengan air?"
print(f"Pengguna: {pertanyaan_2}")
response_2 = agent.invoke({"messages": [HumanMessage(content=pertanyaan_2)]}, config)
print(f"Agen: {response_2['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 5 - Pertanyaan yang butuh kedua jawaban sebelumnya

# %%
pertanyaan_3 = "Berapa barel lebih banyak total semua produk milik pemenang minyak dibanding pemenang air?"
print(f"Pengguna: {pertanyaan_3}")
response_3 = agent.invoke({"messages": [HumanMessage(content=pertanyaan_3)]}, config)
print(f"Agen: {response_3['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 6 - Memeriksa utas dan jawaban pembanding
# `hitung_selisih` menghitung sendiri jawaban pertanyaan ke-3 dengan SQL, sebagai pembanding.

# %%
def hitung_selisih(db_path: Path) -> str:
    """Hitung sendiri jawaban pertanyaan ke-3 dengan SQL, sebagai pembanding."""
    with closing(sqlite3.connect(db_path)) as sambungan:
        def pemenang(produk: str) -> int:
            return sambungan.execute(
                "SELECT SumurId FROM ProduksiHarian JOIN Produk USING (ProdukId) WHERE Produk.Nama = ? "
                "GROUP BY SumurId ORDER BY SUM(Barel) DESC LIMIT 1", (produk,)
            ).fetchone()[0]

        def total(sumur_id: int) -> int:
            return sambungan.execute(
                "SELECT SUM(Barel) FROM ProduksiHarian WHERE SumurId = ?", (sumur_id,)
            ).fetchone()[0]

        return str(total(pemenang("Minyak")) - total(pemenang("Air")))


# TODO(BQ.6): ambil state utas dengan agent.get_state(config)
status = None  # TODO: ganti dengan implementasi Anda
print(f"Utas menyimpan {len(status.values['messages'])} pesan (pertanyaan, panggilan SQL, dan hasilnya).")
print(f"Jawaban benar pertanyaan ke-3, dihitung sendiri dengan SQL: {hitung_selisih(db_path)}")

# %% [markdown]
# ## Langkah 7 - Membersihkan folder sementara

# %%
folder_kerja.cleanup()
