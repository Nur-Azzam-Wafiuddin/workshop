# %% [markdown]
# # Bab 2 - Latihan: Tool Konversi Satuan dengan Siklus Eksekusi Lengkap
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Siklus 3 langkah: model merencanakan pemanggilan, kode menjalankan tool, model menjawab.

# %%
# Langkah 1 - Menyiapkan model
import os
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
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
# ## Langkah 2 - Tool konversi satuan
# Tabel faktor konversi, skema masukan, dan tool. Pasangan satuan yang tidak didukung ditolak dengan pesan yang jelas.

# %%
FAKTOR = {
    ("bbl", "m3"): 0.158987, ("m3", "bbl"): 1 / 0.158987,
    ("psi", "bar"): 0.0689476, ("bar", "psi"): 14.5038,
    ("scf", "m3"): 0.0283168, ("m3", "scf"): 1 / 0.0283168,
}


class KonversiInput(BaseModel):
    # TODO(B2.1): definisikan skema masukan: nilai (float), dari dan ke (Literal bbl, m3, psi, bar, scf)
    pass  # TODO: definisikan field


@tool(args_schema=KonversiInput)
def konversi_satuan(nilai: float, dari: str, ke: str) -> str:
    """Konversi satuan volume (bbl, m3, scf) atau tekanan (psi, bar). Pakai untuk setiap pertanyaan konversi satuan."""
    # TODO(B2.2): kembalikan teks hasil konversi dari tabel FAKTOR; satuan sama dikembalikan apa adanya; pasangan yang tidak ada di FAKTOR dikembalikan sebagai pesan yang menyebut pasangan yang didukung
    raise NotImplementedError("TODO(B2.2)")


# TODO(B2.3): ikat tool konversi_satuan ke model dengan bind_tools
model_dengan_tool = None  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 3 - Fungsi siklus tiga langkah
# `jalankan_siklus` menjalankan satu pertanyaan: model merencanakan, kode menjalankan setiap pemanggilan
# (model bisa meminta lebih dari satu), lalu model menyusun jawaban akhir.

# %%
def jalankan_siklus(model_dengan_tool, model, query: str):
    print(f"Pengguna: {query}")

    # Langkah 1: model merencanakan
    respons = model_dengan_tool.invoke(query)
    if not respons.tool_calls:
        print("  Model menjawab langsung tanpa tool:", respons.content, "\n")
        return

    messages = [HumanMessage(content=query), AIMessage(content=respons.content or "", tool_calls=respons.tool_calls)]

    # Langkah 2: kode menjalankan setiap pemanggilan (model bisa meminta lebih dari satu)
    for pemanggilan in respons.tool_calls:
        # TODO(B2.4): jalankan tool dengan argumen dari pemanggilan model
        hasil = None  # TODO: ganti dengan implementasi Anda
        print(f"  Tool {pemanggilan['name']}({pemanggilan['args']}) -> {hasil}")
        # TODO(B2.5): kirim hasil tool kembali ke model sebagai ToolMessage dengan tool_call_id yang sesuai
        pass  # TODO: ganti dengan implementasi Anda

    # Langkah 3: model menyusun jawaban akhir
    print("  Jawaban akhir:", model.invoke(messages).content, "\n")


# %% [markdown]
# ## Langkah 4 - Konversi tekanan

# %%
jalankan_siklus(model_dengan_tool, model, "Tekanan wellhead SR-020 adalah 1500 psi. Berapa bar?")

# %% [markdown]
# ## Langkah 5 - Konversi volume

# %%
jalankan_siklus(model_dengan_tool, model, "Tangki penampung berisi 2500 bbl. Berapa meter kubik?")

# %% [markdown]
# ## Langkah 6 - Dua konversi dalam satu pertanyaan

# %%
jalankan_siklus(model_dengan_tool, model, "Berapa psi dalam 20 bar, dan berapa bbl dalam 10 m3?")

# %% [markdown]
# ## Langkah 7 - Pasangan satuan tidak valid
# Tool harus menolak dengan sopan.

# %%
jalankan_siklus(model_dengan_tool, model, "Ubah 100 bar menjadi bbl.")
