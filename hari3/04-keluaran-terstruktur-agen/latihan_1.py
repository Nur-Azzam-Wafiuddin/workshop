# %% [markdown]
# # Bab 4 - Latihan: Ekstraktor Laporan Insiden
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Mengubah catatan lapangan yang berantakan menjadi `LaporanInsiden` nested yang tervalidasi.

# %%
# Langkah 1 - Menyiapkan model
import os
from typing import Literal, Optional

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from migas_shared.data import KlasifikasiInsiden

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    temperature=0,
)

# %% [markdown]
# ## Langkah 2 - Skema laporan insiden
# `LaporanInsiden` memuat daftar `Korban` dan klasifikasi `KlasifikasiInsiden`.

# %%
class Korban(BaseModel):
    """Seseorang yang terlibat atau terdampak insiden."""
    # TODO(B4.1): definisikan field Korban: peran (str) dan cedera (Literal Tidak ada, Pertolongan pertama, Perawatan medis, Hilang hari kerja)
    pass  # TODO: definisikan field


class LaporanInsiden(BaseModel):
    """Laporan insiden terstruktur dari catatan lapangan."""
    # TODO(B4.2): definisikan field LaporanInsiden: lokasi, jam_kejadian (opsional), uraian (maksimal 200 karakter), korban (daftar Korban), tindakan_segera (daftar string), dan klasifikasi (KlasifikasiInsiden)
    pass  # TODO: definisikan field


# TODO(B4.3): buat agen tanpa tool dengan system prompt yang melarang menebak jam atau korban, dan response_format=LaporanInsiden
agent = None  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 3 - Catatan 1: baut jatuh tanpa korban

# %%
teks = (
    "kmrn sore sekitar jam 4an di GS-SR1 ada baut jatuh dr pipe rack pas lifting. ga ada yg luka. "
    "area dibarikade, kerjaan distop dulu, spv udah dilapor."
)
print(f"Catatan : {teks}")
response = agent.invoke({"messages": [HumanMessage(content=teks)]})
# TODO(B4.4): ambil hasil terstruktur dari response (kunci structured_response)
laporan = None  # TODO: ganti dengan implementasi Anda
if laporan is None:
    print("   Tidak ada hasil terstruktur\n")
else:
    print(laporan.model_dump_json(indent=2))
    print()

# %% [markdown]
# ## Langkah 4 - Catatan 2: hose pecah dengan korban

# %%
teks = (
    "Pad sumur KN-061 pagi 09.40, hose hidrolik pecah, oli panas kena tangan operator (Pak Dedi). "
    "Dikasih P3K lalu dibawa ke klinik lapangan, dirawat dan boleh kembali bertugas. Area dibersihkan pakai absorbent."
)
print(f"Catatan : {teks}")
response = agent.invoke({"messages": [HumanMessage(content=teks)]})
laporan = response.get("structured_response")
if laporan is None:
    print("   Tidak ada hasil terstruktur\n")
else:
    print(laporan.model_dump_json(indent=2))
    print()
