# %% [markdown]
# # Ekstraksi Work Order dengan Skema WOExtract
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/11_work_order_extraction.py`
#
# Ekstraksi work order dengan skema WOExtract dari paket bersama.
#
# Catatan lapangan work order ditulis bebas dan penuh singkatan. Model membaca dan menstrukturkan teks,
# lalu KODE memverifikasi hasilnya terhadap data acuan (data/eval/work_orders_truth.csv).

# %%
# Langkah 1 - Menyiapkan model dan prompt sistem
import os

import pandas as pd
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from migas_shared.config import DATA
from migas_shared.data import WOExtract

load_dotenv()

SISTEM = """Anda mengekstrak data terstruktur dari catatan work order lapangan minyak (teks bebas Bahasa Indonesia,
penuh singkatan). Aturan:
- asset_id: kode aset pada catatan, huruf kapital
- equipment_type: SR-xxx dan ML-xxx adalah ESP kecuali disebut PCP; KN-xxx adalah SRP; SG-KN-xx Steam Generator;
  FL-... Flowline; V-SR1-101 Separator; K-ML1-201 Gas Compressor; P-SR1-302 Water Injection Pump
- downtime_hours: lama unit berhenti dalam jam ("1 hari" = 24, "45 menit" = 0.75)
- safety_flag: true jika ada kebocoran fluida/gas/uap atau risiko keselamatan lain"""

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    temperature=0,
)

# %% [markdown]
# ## Langkah 2 - Membuat pengekstrak
# `with_structured_output` memaksa keluaran mengikuti skema WOExtract (termasuk validasi Pydantic).

# %%
pengekstrak = ChatPromptTemplate.from_messages([("system", SISTEM), ("human", "{catatan}")]) | model.with_structured_output(WOExtract, method="function_calling")

# %% [markdown]
# ## Langkah 3 - Mengambil catatan nyata beserta jawaban acuannya

# %%
wo = pd.read_csv(DATA / "raw" / "work_orders.csv").merge(
    pd.read_csv(DATA / "eval" / "work_orders_truth.csv"), on="wo_id").head(3)

# %% [markdown]
# ## Langkah 4 - Ekstraksi dan verifikasi oleh kode
# Hasil model dibandingkan field demi field dengan data acuan, bukan dinilai oleh model.

# %%
cocok_total, field_total = 0, 0
for _, baris in wo.iterrows():
    hasil = pengekstrak.invoke({"catatan": baris["deskripsi"]})
    print(f"\n{baris['wo_id']}: {baris['deskripsi']}")
    print(f"   Hasil model : {hasil.model_dump()}")

    # Verifikasi oleh kode, bukan oleh model
    acuan = {
        "asset_id": baris["asset_id"], "equipment_type": baris["equipment_type"],
        "failure_category": baris["failure_category"], "action_category": baris["action_category"],
        "downtime_hours": float(baris["downtime_hours"]), "safety_flag": bool(baris["safety_flag"]),
    }
    cocok = [k for k, v in acuan.items() if getattr(hasil, k) == v]
    cocok_total += len(cocok)
    field_total += len(acuan)
    salah = [k for k in acuan if k not in cocok]
    print(f"   Cocok dengan acuan: {len(cocok)}/{len(acuan)}" + (f" (berbeda: {', '.join(salah)})" if salah else ""))

print(f"\nTotal kecocokan: {cocok_total}/{field_total} field")
