# %% [markdown]
# # Bab 3 - Latihan Bonus: Agen Perencana Pekerjaan Pulling
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Agen dengan beberapa tool khusus yang butuh reasoning multi-langkah:
# jadwal rig, perkiraan biaya, dan perkiraan produksi yang hilang.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from migas_shared.tampil import jejak_tool
from migas_shared.field_tools import cek_status_sumur

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Tool perencana pulling
# Data fiktif untuk simulasi, lalu tiga tool: jadwal rig, biaya pulling, dan kehilangan produksi.

# %%
# Data fiktif untuk simulasi
JADWAL_RIG = {"KN-033": 12, "SR-020": 5, "ML-012": 20}  # hari menunggu rig tersedia
BIAYA_PULLING_JUTA = {"SRP": 350, "ESP": 1200}  # juta rupiah per pekerjaan


# TODO(B3.3): buat tool cek_jadwal_rig(kode_sumur) yang mengembalikan berapa hari lagi rig tersedia dari JADWAL_RIG, atau pesan bila sumur tidak ada di jadwal
cek_jadwal_rig = None  # TODO: ganti dengan implementasi Anda


@tool
def estimasi_biaya_pulling(jenis_pompa: str) -> str:
    """Perkirakan biaya satu pekerjaan pulling berdasarkan jenis pompa (SRP atau ESP), dalam juta rupiah.

    Args:
        jenis_pompa: SRP atau ESP
    """
    biaya = BIAYA_PULLING_JUTA.get(jenis_pompa.upper())
    if biaya is None:
        return f"Jenis pompa {jenis_pompa} tidak dikenal. Pilihan: {', '.join(BIAYA_PULLING_JUTA)}"
    return f"Biaya pulling {jenis_pompa.upper()}: sekitar Rp {biaya} juta"


# TODO(B3.4): buat tool estimasi_kehilangan_produksi(minyak_bopd, hari) yang mengalikan keduanya dan menyebut hasil dalam bbl
estimasi_kehilangan_produksi = None  # TODO: ganti dengan implementasi Anda


# %% [markdown]
# ## Langkah 3 - Membuat agen perencana

# %%
# TODO(B3.5): buat agen dengan keempat tool dan system prompt perencana yang meminta rencana langkah demi langkah serta asumsi bila data tidak ada
agent = None  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 4 - Rencana pulling satu sumur

# %%
query = (
    "Rencanakan pulling sumur KN-033: kapan rig tersedia, berapa kira-kira biayanya, "
    "dan berapa produksi hilang selama menunggu jika produksi normalnya 45 bopd?"
)
print(f"Pengguna: {query}")
response = agent.invoke({"messages": [HumanMessage(content=query)]})
print("  Langkah:")
for baris in jejak_tool(response["messages"]):
    print("    -", baris)
print(f"  Rencana: {response['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 5 - Membandingkan dua sumur

# %%
query = "Bandingkan KN-033 dan SR-020: sumur mana yang rig-nya lebih cepat tersedia dan berapa biaya pulling masing-masing?"
print(f"Pengguna: {query}")
response = agent.invoke({"messages": [HumanMessage(content=query)]})
print("  Langkah:")
for baris in jejak_tool(response["messages"]):
    print("    -", baris)
print(f"  Rencana: {response['messages'][-1].content}\n")
