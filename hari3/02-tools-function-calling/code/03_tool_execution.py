# %% [markdown]
# # Contoh 3: Siklus Tool Call Lengkap
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/02-tools-function-calling/code/03_tool_execution.py`
#
# Siklus tiga langkah: model merencanakan pemanggilan tool, KODE ANDA menjalankan tool, lalu hasilnya
# dikirim kembali ke model untuk menyusun jawaban akhir.

# %%
# Langkah 1 - Menyiapkan model
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from pydantic import BaseModel, Field
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
# ## Langkah 2 - Data dan tool status sumur
# Data status sumur bersifat fiktif. Pada sistem nyata, ini akan berasal dari database atau SCADA.

# %%
# Data status sumur (fiktif). Pada sistem nyata, ini akan berasal dari database atau SCADA.
DATA_SUMUR = {
    "SR-020": {"area": "Seruni", "pompa": "ESP", "status": "Produksi", "minyak_bopd": 120, "air_bwpd": 480,
               "catatan": "ESP trip overload kemarin sore, stabil sejak pukul 18.00"},
    "SR-027": {"area": "Seruni", "pompa": "ESP", "status": "Produksi", "minyak_bopd": 95, "air_bwpd": 380,
               "catatan": "Pembacaan H2S 12 ppm pada 22 Juli 2026, dalam investigasi HSE"},
    "KN-033": {"area": "Kenanga", "pompa": "SRP", "status": "Menunggu pulling", "minyak_bopd": 0, "air_bwpd": 0,
               "catatan": "Sucker rod patah, menunggu jadwal rig"},
}


class StatusSumurInput(BaseModel):
    kode_sumur: str = Field(description="Kode sumur, contoh SR-020 atau KN-033")


@tool(args_schema=StatusSumurInput)
def cek_status_sumur(kode_sumur: str) -> str:
    """Cek status operasi sebuah sumur: area, jenis pompa, status, produksi minyak dan air, serta catatan terakhir."""
    data = DATA_SUMUR.get(kode_sumur.strip().upper())
    if not data:
        return f"Sumur {kode_sumur} tidak ditemukan. Sumur yang terdaftar: {', '.join(DATA_SUMUR)}"
    return (f"Sumur {kode_sumur} ({data['area']}, {data['pompa']}): status {data['status']}, "
            f"minyak {data['minyak_bopd']} bopd, air {data['air_bwpd']} bwpd. Catatan: {data['catatan']}")


model_with_tools = model.bind_tools([cek_status_sumur])

# %% [markdown]
# ## Langkah 3 - Model membuat permintaan tool call (perencanaan)

# %%
query = "Bagaimana kondisi sumur SR-020 saat ini?"
print("Pengguna:", query)
response1 = model_with_tools.invoke(query)
tool_call = response1.tool_calls[0]
print("\nLangkah 1 - Permintaan tool dari model:")
print(f"  Tool : {tool_call['name']}")
print(f"  Args : {tool_call['args']}")
print(f"  ID   : {tool_call['id']}")

# %% [markdown]
# ## Langkah 4 - Kode Anda menjalankan tool (pelaksanaan)

# %%
tool_result = cek_status_sumur.invoke(tool_call["args"])
print("Langkah 2 - Hasil eksekusi tool:")
print(f"  {tool_result}")

# %% [markdown]
# ## Langkah 5 - Mengirim hasil kembali ke model (komunikasi)

# %%
messages = [
    HumanMessage(content=query),
    AIMessage(content="", tool_calls=response1.tool_calls),
    ToolMessage(content=tool_result, tool_call_id=tool_call["id"]),
]

final_response = model.invoke(messages)
print("Langkah 3 - Jawaban akhir:")
print(f"  {final_response.content}")
