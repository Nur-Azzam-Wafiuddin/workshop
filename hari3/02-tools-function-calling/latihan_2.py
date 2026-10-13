# %% [markdown]
# # Bab 2 - Latihan Bonus: Asisten Pemeriksaan Sumur dengan Banyak Tool
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Model memilih sendiri tool yang tepat; kode menjalankannya lewat peta nama -> tool.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from migas_shared.field_tools import TOOL_LAPANGAN

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Menambah tool estimasi kehilangan produksi
# Tool lapangan dari paket bersama digabung dengan satu tool baru, lalu dipetakan nama -> tool.

# %%
# TODO(B2.6): buat skema KehilanganInput (minyak_bopd dan hari_henti, keduanya >= 0) dan tool estimasi_kehilangan_produksi yang mengalikan keduanya
estimasi_kehilangan_produksi = None  # TODO: ganti dengan implementasi Anda


SEMUA_TOOL = [*TOOL_LAPANGAN, estimasi_kehilangan_produksi]
PETA_TOOL = {t.name: t for t in SEMUA_TOOL}

# %% [markdown]
# ## Langkah 3 - Loop pemanggilan tool
# Loop sederhana: model meminta tool, kode menjalankan, ulangi sampai model menjawab dengan teks.

# %%
def jawab(model, pertanyaan: str, maks_putaran: int = 4) -> str:
    """Loop sederhana: model meminta tool, kode menjalankan, ulangi sampai model menjawab dengan teks."""
    model_dengan_tool = model.bind_tools(SEMUA_TOOL)
    messages = [
        SystemMessage(content="Anda asisten pemeriksaan sumur di GS-SR1. Pakai tool bila perlu, jawab ringkas dalam Bahasa Indonesia."),
        HumanMessage(content=pertanyaan),
    ]
    for _ in range(maks_putaran):
        # TODO(B2.7): panggil model yang sudah diikat tool dengan daftar messages
        respons = None  # TODO: ganti dengan implementasi Anda
        if not respons.tool_calls:
            return str(respons.content)
        # TODO(B2.8): simpan permintaan tool dari model ke messages sebagai AIMessage yang membawa tool_calls
        pass  # TODO: ganti dengan implementasi Anda
        for pemanggilan in respons.tool_calls:
            try:
                # TODO(B2.9): cari tool di PETA_TOOL menurut nama pemanggilan, lalu jalankan dengan argumennya
                hasil = None  # TODO: ganti dengan implementasi Anda
            except Exception as error:  # tool yang gagal dilaporkan ke model, bukan menghentikan program
                hasil = f"Error: {error}"
            print(f"   [tool] {pemanggilan['name']}({pemanggilan['args']}) -> {hasil}")
            # TODO(B2.10): kirim hasil tool ke model sebagai ToolMessage
            pass  # TODO: ganti dengan implementasi Anda
    return "Batas putaran tercapai tanpa jawaban akhir."


# %% [markdown]
# ## Langkah 4 - Status sumur dan water cut

# %%
pertanyaan = "Bagaimana kondisi sumur SR-020, dan berapa water cut-nya?"
print(f"Pengguna: {pertanyaan}")
print("Asisten :", jawab(model, pertanyaan), "\n")

# %% [markdown]
# ## Langkah 5 - Estimasi kehilangan produksi

# %%
pertanyaan = "Sumur KN-033 menunggu pulling selama 12 hari. Jika produksi normalnya 45 bopd, berapa produksi yang hilang?"
print(f"Pengguna: {pertanyaan}")
print("Asisten :", jawab(model, pertanyaan), "\n")

# %% [markdown]
# ## Langkah 6 - Konversi tekanan

# %%
pertanyaan = "Tekanan kepala sumur ML-012 tercatat 900 psi. Berapa bar?"
print(f"Pengguna: {pertanyaan}")
print("Asisten :", jawab(model, pertanyaan), "\n")
