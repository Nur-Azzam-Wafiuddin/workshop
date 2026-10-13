# %% [markdown]
# # Bab 1 - Latihan 3: Ekstraktor Data Suku Cadang
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Structured output: mengubah deskripsi bebas dalam berbagai format menjadi objek Pydantic yang tervalidasi.

# %%
# Langkah 1 - Menyiapkan model
import os
from typing import Literal, Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    temperature=0,
)

# %% [markdown]
# ## Langkah 2 - Skema dan pengekstrak
# Field opsional dibiarkan kosong kalau informasinya tidak disebut dalam teks.

# %%
class SparePart(BaseModel):
    """Data suku cadang dari deskripsi katalog atau pesan vendor."""
    # TODO(B1.8): definisikan field: nama, harga_juta_rupiah (opsional), kategori (Literal Elektrikal, Mekanikal, Instrumentasi, Kimia, Lainnya), stok_tersedia (opsional), peringkat_vendor (opsional, 1 sampai 5), dan spesifikasi (daftar string)
    pass  # TODO: definisikan field


prompt = ChatPromptTemplate.from_messages([
    ("system", "Ekstrak data suku cadang dari teks. Jika suatu informasi tidak disebut, biarkan kosong. Jangan menebak."),
    ("human", "{teks}"),
])

# TODO(B1.9): hubungkan prompt ke model.with_structured_output(SparePart, method="function_calling")
pengekstrak = None  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 3 - Mengekstrak dari tiga format deskripsi
# Katalog resmi, pesan santai dari vendor, dan informasi yang tidak lengkap.

# %%
deskripsi = [
    # Format katalog resmi
    "Modul VSD FD500 untuk ESP 75 kW, harga Rp 185 juta. Stok tersedia. Peringkat vendor 4,6/5. "
    "Spesifikasi: 380-480 VAC, proteksi overload, komunikasi Modbus.",
    # Format pesan santai dari vendor
    "Flame scanner steam generator, merk lokal, 12 juta aja. Barang ready di gudang Cilacap. "
    "Vendornya lumayan, bintang 4. Tahan sampai 1200 derajat C.",
    # Informasi tidak lengkap
    "Gasket flange 6 inch class 300 spiral wound, butuh 20 buah untuk turnaround.",
]

for teks in deskripsi:
    print(f"Teks: {teks[:90]}...")
    try:
        hasil = pengekstrak.invoke({"teks": teks})
        print(hasil.model_dump_json(indent=2))
    except Exception as error:
        print(f"Gagal diekstrak atau divalidasi: {error}")
    print()
