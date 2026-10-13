# %% [markdown]
# # Contoh 1: Tool Sederhana
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/02-tools-function-calling/code/01_simple_tool.py`
#
# Membuat tool dengan decorator `@tool` dan skema masukan Pydantic, lalu mengujinya langsung tanpa model.

# %%
# Langkah 1 - Impor dan skema masukan
from langchain_core.tools import tool
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

load_dotenv()


# Tentukan skema masukan dengan Pydantic
class WaterCutInput(BaseModel):
    """Skema masukan untuk tool water cut."""
    oil_bopd: float = Field(ge=0, description="Produksi minyak dalam barel per hari (bopd), contoh 120")
    water_bwpd: float = Field(ge=0, description="Produksi air dalam barel per hari (bwpd), contoh 480")


# %% [markdown]
# ## Langkah 2 - Membuat tool
# Decorator `@tool` mengubah fungsi menjadi tool. Docstring-nya menjadi deskripsi yang dibaca model.

# %%
# Buat tool dengan decorator @tool
@tool(args_schema=WaterCutInput)
def hitung_water_cut(oil_bopd: float, water_bwpd: float) -> str:
    """Hitung water cut (persentase air dalam total cairan produksi) sebuah sumur.
    Pakai tool ini bila perlu mengetahui water cut dari angka produksi minyak dan air."""
    total = oil_bopd + water_bwpd
    if total == 0:
        return "Tidak dapat dihitung: total produksi cairan adalah 0."
    water_cut = water_bwpd / total * 100
    return f"Water cut = {water_cut:.1f}% (total cairan {total:.0f} bpd)"


print("Tool dibuat:", hitung_water_cut.name)
print("Deskripsi:", hitung_water_cut.description)
print("Skema argumen:", list(hitung_water_cut.args))

# %% [markdown]
# ## Langkah 3 - Menguji tool secara langsung

# %%
hasil = hitung_water_cut.invoke({"oil_bopd": 120, "water_bwpd": 480})
print("Hasil:", hasil)

# %% [markdown]
# ## Langkah 4 - Skema menolak masukan yang tidak masuk akal
# Skema Pydantic menolak masukan sebelum fungsi berjalan.

# %%
try:
    hitung_water_cut.invoke({"oil_bopd": -10, "water_bwpd": 480})
except ValidationError as error:
    print("Masukan ditolak oleh skema:", error.errors()[0]["msg"])
