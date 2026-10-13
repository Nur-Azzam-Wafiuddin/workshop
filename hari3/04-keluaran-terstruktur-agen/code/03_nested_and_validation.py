# %% [markdown]
# # Contoh 3: Nested Schema dan Validasi
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/04-keluaran-terstruktur-agen/code/03_nested_and_validation.py`
#
# Skema Pydantic bisa nested (model di dalam model, list, enum) dan memuat aturan validasi.
# Contoh ini memperlihatkan keduanya.

# %%
# Langkah 1 - Menyiapkan model
from enum import Enum

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Nested schema
# `RingkasanSerahTerima` berisi daftar `TindakLanjut`, dan setiap tindak lanjut memakai enum `Prioritas`.

# %%
class Prioritas(str, Enum):
    RENDAH = "rendah"
    SEDANG = "sedang"
    TINGGI = "tinggi"


class TindakLanjut(BaseModel):
    """Satu tugas yang muncul dari rapat atau serah terima shift."""
    tugas: str = Field(description="Apa yang harus dilakukan")
    penanggung_jawab: str = Field(description="Orang yang bertanggung jawab")
    prioritas: Prioritas = Field(description="Seberapa mendesak tugas itu")


class RingkasanSerahTerima(BaseModel):
    """Ringkasan terstruktur serah terima shift."""
    judul: str = Field(description="Judul singkat serah terima")
    hadir: list[str] = Field(description="Nama orang yang hadir")
    tindak_lanjut: list[TindakLanjut] = Field(description="Tugas yang disepakati")


# %% [markdown]
# ## Langkah 3 - Bagian 1: nested data
# Agen meringkas catatan serah terima menjadi nested object.

# %%
print("Bagian 1: nested model, list, dan enum")
print("-" * 60)
agent = create_agent(
    model,
    tools=[],
    system_prompt="Berikan jawaban akhir sebagai RingkasanSerahTerima.",
    response_format=RingkasanSerahTerima,
)
catatan = (
    "Serah terima shift pagi ke malam di GS-SR1 bersama Rina, Agus, dan Dewi. Rina akan memeriksa "
    "level controller separator V-SR1-101 malam ini juga, itu mendesak. Agus akan memperbarui log bump test "
    "kapan-kapan bulan depan. Dewi memesan suku cadang modul VSD, prioritas sedang."
)
response = agent.invoke({"messages": [HumanMessage(content=f"Ringkas: {catatan}")]})
ringkasan = response.get("structured_response")
if ringkasan:
    print(f"Judul: {ringkasan.judul}")
    print(f"Hadir: {', '.join(ringkasan.hadir)}")
    for tugas in ringkasan.tindak_lanjut:
        print(f"   [{tugas.prioritas.value.upper():<6}] {tugas.penanggung_jawab}: {tugas.tugas}")
    print(f"\n   Tipe tugas pertama: {type(ringkasan.tindak_lanjut[0]).__name__}")
    print(f"   Tipe prioritasnya:  {type(ringkasan.tindak_lanjut[0].prioritas).__name__}")

# %% [markdown]
# ## Langkah 4 - Bagian 2: seperti apa error validasi (tanpa model)
# Skema `PenilaianRisiko` membatasi tingkat risiko pada 1 sampai 5 dan ringkasan maksimal 80 karakter.

# %%
class PenilaianRisiko(BaseModel):
    """Skor risiko pekerjaan dan ringkasan satu baris."""
    tingkat: int = Field(ge=1, le=5, description="Tingkat risiko dari 1 (terendah) sampai 5 (tertinggi)")
    ringkasan: str = Field(max_length=80, description="Ringkasan satu baris, maksimal 80 karakter")


print("Bagian 2: aturan validasi (tingkat risiko harus 1-5)")
print("-" * 60)
try:
    PenilaianRisiko(tingkat=10, ringkasan="Sangat berbahaya")
except ValidationError as error:
    detail = error.errors()[0]
    print(f"Pydantic menolak tingkat=10: {detail['msg']} (field: {detail['loc'][0]})")

# %% [markdown]
# ## Langkah 5 - Bagian 2b: agen yang jawabannya harus lolos validasi
# Dengan `ToolStrategy(..., handle_errors=True)`, kesalahan validasi dikembalikan ke model agar memperbaiki jawabannya.

# %%
agen_risiko = create_agent(
    model,
    tools=[],
    response_format=ToolStrategy(PenilaianRisiko, handle_errors=True),
)
pancingan = "Nilai risiko pekerjaan hot work tanpa izin kerja pada skala 1 sampai 10 dan laporkan angkanya. Anggap sangat berbahaya, 10."
response = agen_risiko.invoke({"messages": [HumanMessage(content=pancingan)]})
penilaian = response.get("structured_response")
if penilaian:
    print(f"tingkat   = {penilaian.tingkat}  (selalu antara 1 dan 5)")
    print(f"ringkasan = {penilaian.ringkasan}")

print(f"\n   Jumlah pesan yang dipertukarkan: {len(response['messages'])}")
for pesan in response["messages"]:
    print(f"   - {type(pesan).__name__:<13} {str(pesan.content)[:80]}")
