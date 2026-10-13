# %% [markdown]
# # Structured Output
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/01-dasar-langchain/code/10_structured_output.py`
#
# Keluaran model dipaksa mengikuti skema Pydantic sehingga field bisa diakses langsung sebagai atribut bertipe.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Menentukan skema keluaran
# Skema ditulis dengan Pydantic.

# %%
class InfoSumur(BaseModel):
    """Skema informasi sumur produksi."""
    kode_sumur: str = Field(description="Kode sumur, contoh SR-020")
    jenis_pompa: str = Field(description="Jenis pompa angkat buatan, contoh ESP, SRP atau PCP")
    produksi_minyak_bopd: float = Field(description="Produksi minyak dalam barel per hari (bopd)")
    water_cut_persen: float = Field(description="Water cut dalam persen, antara 0 dan 100")


# Buat model dengan structured output
structured_model = model.with_structured_output(InfoSumur, method="function_calling")

# %% [markdown]
# ## Langkah 3 - Mengekstrak informasi dari teks

# %%
teks = "Sumur SR-020 memakai ESP dan saat ini berproduksi 120 bopd minyak dengan water cut sekitar 80 persen."

hasil = structured_model.invoke(f"Ekstrak informasi sumur dari teks berikut: {teks}")

# Akses field bertipe secara langsung
print(f"Kode sumur: {hasil.kode_sumur}")
print(f"Jenis pompa: {hasil.jenis_pompa}")
print(f"Produksi minyak (bopd): {hasil.produksi_minyak_bopd}")
print(f"Water cut (%): {hasil.water_cut_persen}")
print(f"Tipe objek hasil: {type(hasil).__name__}")
