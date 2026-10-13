# %% [markdown]
# # Contoh 1: Teks Bebas vs Structured Output
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/04-keluaran-terstruktur-agen/code/01_free_text_vs_structured.py`
#
# Agen yang sama dijalankan dua kali: tanpa `response_format` (jawaban berupa teks bebas) dan dengan
# `response_format=WOExtract` (jawaban berupa objek bertipe).

# %%
# Langkah 1 - Menyiapkan model, catatan, dan prompt sistem
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from migas_shared.data import WOExtract

load_dotenv()

CATATAN = (
    "ESP SR-020 trip OL, coba restart 2x gagal. Megger motor phase-to-ground 0 Mohm -> motor burnt. "
    "Usul pulling job ganti motor. downtime 5 jam."
)

SISTEM = (
    "Anda mengekstrak data work order lapangan. Konvensi: SR-xxx dan ML-xxx adalah ESP, KN-xxx adalah SRP. "
    "Pulling dengan rig dikategorikan Workover. Berikan jawaban akhir sebagai WOExtract."
)

print("Teks Bebas vs Structured Output\n")

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

query = f"Ekstrak data dari catatan work order ini: '{CATATAN}'"

# %% [markdown]
# ## Langkah 2 - Bagian 1: agen biasa (teks bebas)
# Tanpa `response_format`, jawaban berupa teks yang harus diurai sendiri.

# %%
print("Bagian 1: agen TANPA response_format")
print("-" * 60)
agen_biasa = create_agent(model, tools=[], system_prompt=SISTEM)
respons_biasa = agen_biasa.invoke({"messages": [HumanMessage(content=query)]})
teks = respons_biasa["messages"][-1].content
print(f"Agen berkata:\n{teks}")
print(f"\n   Tipe Python jawaban: {type(teks).__name__}")
print("   Untuk memakai downtime di kode, Anda harus mengurai teks ini sendiri.")

# %% [markdown]
# ## Langkah 3 - Bagian 2: agen yang sama dengan response_format
# Dengan `response_format=WOExtract`, jawaban akhir berupa objek `WOExtract` dengan field bertipe.

# %%
print("Bagian 2: agen DENGAN response_format=WOExtract")
print("-" * 60)
agen_terstruktur = create_agent(model, tools=[], system_prompt=SISTEM, response_format=WOExtract)
respons = agen_terstruktur.invoke({"messages": [HumanMessage(content=query)]})
wo = respons.get("structured_response")
if wo is None:
    print("Tidak ada hasil terstruktur. Jawaban teks:", respons["messages"][-1].content)
else:
    print(f"Hasil terstruktur: {wo}")
    print(f"\n   Tipe Python jawaban: {type(wo).__name__}")
    print(f"   wo.asset_id       = {wo.asset_id}")
    print(f"   wo.equipment_type = {wo.equipment_type}")
    print(f"   wo.downtime_hours = {wo.downtime_hours} ({type(wo.downtime_hours).__name__})")
    print(f"   wo.safety_flag    = {wo.safety_flag}")
