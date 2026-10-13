# %% [markdown]
# # Bab 1 - Latihan 2: Few-Shot Format Teacher
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Mengajari model format JSON khusus dari catatan work order lewat contoh, lalu memvalidasi hasilnya.

# %%
# Langkah 1 - Menyiapkan model
import json
import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    temperature=0,
)

# %% [markdown]
# ## Langkah 2 - Contoh pengajaran dan prompt few-shot
# Setiap contoh berisi catatan (input) dan keluaran JSON yang diinginkan.

# %%
# Format JSON yang diajarkan
KUNCI_WAJIB = {"aset", "masalah", "tindakan", "downtime_jam"}

# Contoh pengajaran (input dan keluaran JSON)
contoh = [
    {
        "input": "ESP SR-020 trip OL, megger motor 0 Mohm, motor terbakar. Usul pulling ganti motor. downtime 5 jam.",
        "output": json.dumps({"aset": "SR-020", "masalah": "motor ESP terbakar", "tindakan": "pulling dan ganti motor", "downtime_jam": 5}, ensure_ascii=False),
    },
    {
        "input": "V-SR1-101 level control hunting, positioner LCV rusak, diganti. downtime 1 hari.",
        "output": json.dumps({"aset": "V-SR1-101", "masalah": "level control hunting karena positioner LCV rusak", "tindakan": "ganti positioner LCV", "downtime_jam": 24}, ensure_ascii=False),
    },
    {
        "input": "KN-033 V-belt pumping unit putus, ganti baru, selesai 45 menit.",
        "output": json.dumps({"aset": "KN-033", "masalah": "V-belt pumping unit putus", "tindakan": "ganti V-belt", "downtime_jam": 0.75}, ensure_ascii=False),
    },
]

# TODO(B1.5): buat template satu contoh (pesan human {input} dan pesan ai {output}), lalu bungkus bersama daftar contoh dengan FewShotChatMessagePromptTemplate
few_shot = None  # TODO: ganti dengan implementasi Anda

prompt = ChatPromptTemplate.from_messages([
    ("system", "Anda mengubah catatan work order menjadi satu objek JSON dengan kunci aset, masalah, tindakan, downtime_jam. "
               "Jawab hanya dengan JSON, tanpa teks lain."),
    few_shot,
    ("human", "{input}"),
])

# TODO(B1.6): gabungkan prompt dan model dengan operator |
chain = None  # TODO: ganti dengan implementasi Anda

# %% [markdown]
# ## Langkah 3 - Fungsi validasi
# Kode memeriksa kunci dan tipe data, bukan model.

# %%
def validasi(teks: str) -> dict:
    """Parse JSON dan periksa kunci serta tipe data. Raise ValueError bila tidak sesuai."""
    # TODO(B1.7): parse JSON, pastikan semua kunci di KUNCI_WAJIB ada dan downtime_jam berupa angka; raise ValueError bila tidak sesuai
    raise NotImplementedError("TODO(B1.7)")


# %% [markdown]
# ## Langkah 4 - Menguji dengan catatan baru

# %%
uji = [
    "ESP ML-012 trip underload karena gas lock, restart manual setelah 2 jam, kembali normal.",
    "Flame scanner steam generator SG-KN-02 rusak, diganti. Unit berhenti dari 07.30 s/d 15.00.",
    "K-ML1-201 gasket flange bocor, diganti, downtime 6 jam.",
]

for catatan in uji:
    hasil = chain.invoke({"input": catatan}).content.strip()
    print(f"Catatan : {catatan}")
    try:
        data = validasi(hasil)
        print(f"   JSON valid : {json.dumps(data, ensure_ascii=False)}")
    except (json.JSONDecodeError, ValueError) as error:
        print(f"   TIDAK VALID: {error} | keluaran mentah: {hasil[:80]}")
    print()
