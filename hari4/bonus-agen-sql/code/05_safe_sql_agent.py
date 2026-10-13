# %% [markdown]
# # Contoh 5: Agen SQL yang Aman (Menggabungkan Semuanya)
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/bonus-agen-sql/code/05_safe_sql_agent.py`
#
# Agen ini memakai hampir semua yang sudah dipelajari:
#
# - Bab 4 structured output: jawaban kembali sebagai JawabanQuery bertipe
# - Bab 6 persetujuan manusia: mengekspor data ke file perlu persetujuan orang
# - Bab 7 guardrails: nama pelapor pada hasil query diganti placeholder (redaction) SEBELUM dibaca model, dan batas
#   panggilan model menghentikan loop liar
# - Bab ini, tool SQL aman: penjelajahan skema, hanya SELECT, koneksi hanya-baca, batas baris

# %%
# Langkah 1 - Impor dan model
import csv
import os
import sys
import tempfile
from pathlib import Path

from migas_shared.config import ROOT

sys.path.insert(0, str(ROOT / "hari4" / "bonus-agen-sql" / "code"))
from sql_tools import (
    DB_PATH,
    MAKS_BARIS,
    PROMPT_SISTEM_SQL,
    daftar_tabel,
    deskripsikan_tabel,
    jalankan_query,
    koneksi_hanya_baca,
    validasi_query,
)
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    PIIMiddleware,
)
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from pydantic import BaseModel, Field

load_dotenv()

FOLDER_EKSPOR = Path(tempfile.mkdtemp(prefix="ekspor_agen_sql_"))

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Guardrail nama pelapor dan skema jawaban
# `pola_nama_pelapor` membangun pola regex dari nama pelapor yang benar-benar ada di database.
# `JawabanQuery` adalah bentuk jawaban akhir agen yang bertipe.

# %%
def pola_nama_pelapor() -> str:
    """Bangun pola regex dari nama pelapor yang benar-benar ada di basis data."""
    with koneksi_hanya_baca() as sambungan:
        nama = [b[0] for b in sambungan.execute("SELECT DISTINCT dilaporkan_oleh FROM work_order WHERE dilaporkan_oleh IS NOT NULL")]
    return r"\b(?:" + "|".join(sorted(nama)) + r")\b"


class JawabanQuery(BaseModel):
    """Jawaban akhir agen yang bertipe."""

    jawaban: str = Field(description="Jawaban dalam bahasa sehari-hari untuk pertanyaan pengguna")
    sql_dipakai: str = Field(description="Query SQL akhir yang menghasilkan jawaban ('tidak ada' bila tidak ada query)")
    jumlah_baris: int = Field(description="Berapa baris yang dikembalikan query itu (0 bila tidak ada query)")

# %% [markdown]
# ## Langkah 3 - Tool ekspor
# `ekspor_hasil` menyimpan SEMUA baris hasil query ke file CSV. Karena menulis file, tool ini nanti
# butuh persetujuan manusia.

# %%
@tool
def ekspor_hasil(sql: str, nama_file: str) -> str:
    """Jalankan query SELECT hanya-baca dan simpan SEMUA barisnya ke file CSV untuk pengguna.
    Pakai hanya bila pengguna secara eksplisit meminta file atau ekspor.

    Args:
        sql: Satu pernyataan SELECT
        nama_file: Nama file berakhiran .csv, contoh "wo_keselamatan.csv"
    """
    masalah = validasi_query(sql)
    if masalah:
        return f"Ekspor ditolak: {masalah}"
    nama_aman = Path(nama_file).name  # buang bagian folder: jangan pernah menulis di luar FOLDER_EKSPOR
    if not nama_aman.endswith(".csv"):
        return "Ekspor ditolak: nama file harus berakhiran .csv"

    with koneksi_hanya_baca() as sambungan:
        kursor = sambungan.execute(sql)
        kolom = [d[0] for d in kursor.description]
        baris = kursor.fetchall()

    target = FOLDER_EKSPOR / nama_aman
    with open(target, "w", newline="", encoding="utf-8") as file_csv:
        penulis = csv.writer(file_csv)
        penulis.writerow(kolom)
        penulis.writerows(baris)
    return f"Tersimpan {len(baris)} baris ke {nama_aman}"

# %% [markdown]
# ## Langkah 4 - Merakit agen aman
# Tiga pengaman dipasang sebagai middleware: redaction nama pada hasil tool, batas panggilan model, dan
# persetujuan manusia khusus untuk tool ekspor. Checkpointer dibutuhkan oleh persetujuan manusia.

# %%
def bangun_agen(model):
    return create_agent(
        model,
        tools=[daftar_tabel, deskripsikan_tabel, jalankan_query, ekspor_hasil],
        system_prompt=PROMPT_SISTEM_SQL
        + " Bila pengguna meminta file, pakai ekspor_hasil. Beri jawaban akhir sebagai JawabanQuery.",
        response_format=JawabanQuery,
        middleware=[
            # Guardrail: nama pelapor pada HASIL tool dibersihkan sebelum model melihatnya
            PIIMiddleware("nama_pelapor", detector=pola_nama_pelapor(), strategy="redact", apply_to_tool_results=True),
            # Guardrail: hentikan loop liar
            ModelCallLimitMiddleware(run_limit=15, exit_behavior="end"),
            # Persetujuan manusia: hanya tool ekspor, yang menulis file
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "daftar_tabel": False,
                    "deskripsikan_tabel": False,
                    "jalankan_query": False,
                    "ekspor_hasil": {"allowed_decisions": ["approve", "reject"]},
                },
                description_prefix="Ekspor perlu persetujuan",
            ),
        ],
        checkpointer=InMemorySaver(),  # diperlukan oleh persetujuan manusia
    )


agent = bangun_agen(model)

# %% [markdown]
# ## Langkah 5 - Fungsi untuk satu pertanyaan
# `tanya` mengirim pertanyaan, menangani permintaan persetujuan (disetujui atau ditolak), lalu mencetak
# jawaban bertipe.

# %%
def tanya(agent, pertanyaan: str, thread_id: str, setujui: bool = True):
    config = {"configurable": {"thread_id": thread_id}}
    print(f"Pengguna: {pertanyaan}\n")
    hasil = agent.invoke({"messages": [HumanMessage(content=pertanyaan)]}, config)

    while "__interrupt__" in hasil:
        for permintaan in hasil["__interrupt__"][0].value["action_requests"]:
            print(f"   Perlu persetujuan: {permintaan['name']}")
            print(f"       sql:       {permintaan['args'].get('sql')}")
            print(f"       nama_file: {permintaan['args'].get('nama_file')}")
        keputusan = (
            {"type": "approve"}
            if setujui
            else {"type": "reject", "message": "Ekspor tidak diizinkan saat ini."}
        )
        print(f"   Reviewer: {keputusan['type']}\n")
        hasil = agent.invoke(Command(resume={"decisions": [keputusan]}), config)

    jawaban = hasil.get("structured_response")
    if jawaban is None:
        print(f"(tanpa jawaban bertipe) {hasil['messages'][-1].content}\n")
        return None
    print(f"jawaban:       {jawaban.jawaban}")
    print(f"sql_dipakai:   {jawaban.sql_dipakai}")
    print(f"jumlah_baris:  {jawaban.jumlah_baris}\n")
    return hasil

# %% [markdown]
# ## Langkah 6 - Skenario 1: pertanyaan yang menyentuh data pribadi
# Nama pelapor harus melalui redaction pada hasil tool sebelum model membacanya.

# %%
hasil_s1 = tanya(agent, "Siapa 3 pelapor yang paling banyak membuat work order? Sebutkan namanya dan jumlah work order masing-masing.", "s1")
teks_tool = " ".join(m.content for m in hasil_s1["messages"] if m.type == "tool") if hasil_s1 else ""
print(f"   'REDACTED' muncul pada apa yang dibaca model dari basis data: {'REDACTED' in teks_tool}\n")

# %% [markdown]
# ## Langkah 7 - Skenario 2: ekspor yang harus disetujui orang
# Reviewer menyetujui ekspor, lalu file CSV diperiksa.

# %%
tanya(agent, "Ekspor id work order dan aset untuk semua work order dengan safety_flag = 1 ke wo_keselamatan.csv", "s2")
hasil_ekspor = FOLDER_EKSPOR / "wo_keselamatan.csv"
if hasil_ekspor.exists():
    baris_csv = hasil_ekspor.read_text(encoding="utf-8").splitlines()
    print(f"   File dibuat: {hasil_ekspor.name} dengan {len(baris_csv) - 1} baris data. Beberapa baris pertama:")
    for b in baris_csv[:3]:
        print(f"      {b}")
else:
    print("   Tidak ada file yang dibuat")

# %% [markdown]
# ## Langkah 8 - Skenario 3: ekspor yang sama, tetapi reviewer menolak
# Tidak boleh ada file baru yang dibuat.

# %%
sebelum = set(p.name for p in FOLDER_EKSPOR.iterdir())
tanya(agent, "Ekspor semua kode aset beserta area-nya ke aset_area.csv", "s3", setujui=False)
dibuat = set(p.name for p in FOLDER_EKSPOR.iterdir()) - sebelum
print(f"   File yang dibuat: {sorted(dibuat) or 'tidak ada'}\n")

# %% [markdown]
# ## Ide Utama
# - Membaca aman untuk diotomatiskan (hanya SELECT, database hanya-baca); menulis file perlu persetujuan
# - Nama pelapor diganti placeholder (redaction) sebelum model melihatnya, sehingga ia tidak bisa mengulanginya
# - `response_format` mengubah jawaban akhir menjadi objek bertipe yang bisa dicatat atau diuji
# - Batas baris (`MAKS_BARIS`, nilainya dicetak di sel berikut) melindungi model; tool ekspor menyimpan SEMUA baris ke disk
# - Tiap pengaman adalah lapisan terpisah, sehingga bisa dipakai ulang untuk database apa pun

# %%
print(f"Batas baris (MAKS_BARIS) = {MAKS_BARIS}")
