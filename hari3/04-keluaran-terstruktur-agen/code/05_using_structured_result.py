# %% [markdown]
# # Contoh 5: Memakai Hasil Terstruktur di Kode Anda
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/04-keluaran-terstruktur-agen/code/05_using_structured_result.py`
#
# Memakai hasil terstruktur di kode Anda: percabangan, database, dan JSON.
# Laporan insiden HSE nyata dari data/raw/hse_incidents.csv diklasifikasikan oleh agen.

# %%
# Langkah 1 - Menyiapkan model dan agen
import os
import sqlite3
from contextlib import closing

import pandas as pd
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from migas_shared.config import DATA
from migas_shared.data import KlasifikasiInsiden

load_dotenv()

print("Memakai Hasil Terstruktur di Kode Anda\n")

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    temperature=0,
)
agent = create_agent(
    model,
    tools=[],
    system_prompt=(
        "Anda mengklasifikasikan laporan insiden HSE migas. severity: Tinggi bila ada cedera hilang hari kerja, "
        "semburan/kebakaran, atau potensi fatalitas; Sedang bila ada cedera berobat atau kerusakan aset; "
        "Rendah bila near miss atau tanpa dampak. Berikan jawaban akhir sebagai KlasifikasiInsiden."
    ),
    response_format=KlasifikasiInsiden,
)

# %% [markdown]
# ## Langkah 2 - Mengambil satu insiden nyata dan mengklasifikasikannya
# Satu insiden beserta label acuannya diambil dan diurutkan agar hasilnya sama setiap kali.

# %%
# Ambil satu insiden nyata beserta label acuannya (diurutkan agar hasilnya sama setiap kali)
insiden = pd.read_csv(DATA / "raw" / "hse_incidents.csv").merge(
    pd.read_csv(DATA / "eval" / "hse_incidents_truth.csv"), on="incident_id").sort_values("incident_id")
baris = insiden[insiden["severity"] == "Tinggi"].iloc[0]
print(f"Laporan {baris['incident_id']} di {baris['lokasi']}:\n   {baris['narasi']}\n")

response = agent.invoke({"messages": [HumanMessage(content=baris["narasi"])]})
hasil = response.get("structured_response")
if hasil is None:
    print("Tidak ada hasil terstruktur:", response["messages"][-1].content)

# %% [markdown]
# ## Langkah 3 - Percabangan pada nilai bertipe
# Karena `severity` bertipe, keputusan bisa diambil dengan `if` biasa.

# %%
print("1. Percabangan pada nilai bertipe")
if hasil.severity == "Tinggi":
    print("   Eskalasi: kirim notifikasi ke manajer HSE dan mulai investigasi")
else:
    print(f"   Severity {hasil.severity}: catat di log harian")
print(f"   (acuan data: {baris['incident_type']}, {baris['hazard']}, {baris['severity']};"
      f" model: {hasil.incident_type}, {hasil.hazard}, {hasil.severity})")

# %% [markdown]
# ## Langkah 4 - Menyimpan ke SQLite

# %%
print("2. Menyimpan ke SQLite")
with closing(sqlite3.connect(":memory:")) as conn:
    conn.execute("CREATE TABLE klasifikasi (id TEXT, tipe TEXT, bahaya TEXT, severity TEXT, ringkasan TEXT)")
    conn.execute(
        "INSERT INTO klasifikasi VALUES (?, ?, ?, ?, ?)",
        (baris["incident_id"], hasil.incident_type, hasil.hazard, hasil.severity, hasil.ringkasan),
    )
    print("   Baris tersimpan:", conn.execute("SELECT * FROM klasifikasi").fetchone())

# %% [markdown]
# ## Langkah 5 - Mengubah ke dict dan JSON

# %%
print("3. Mengubah ke dict dan JSON")
print("   dict:", hasil.model_dump())
print("   json:", hasil.model_dump_json())
