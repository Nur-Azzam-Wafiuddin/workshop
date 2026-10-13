# %% [markdown]
# # Contoh 5: Persetujuan sebelum mengubah knowledge base
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/06-persetujuan-manusia/code/05_document_upload_approval.py`
#
# Meng-upload revisi SOP baru ke knowledge base adalah tindakan TULIS: revisi lama otomatis menjadi
# superseded dan semua pengguna langsung melihat isi yang baru. Karena itu tindakan ini diberi gerbang
# persetujuan manusia.
#
# Dua lapis perlindungan bekerja bersama:
# 1. Persetujuan manusia (`HumanInTheLoopMiddleware`): seseorang melihat usulan sebelum dijalankan
# 2. Gerbang kualitas di dalam `ingest_document`: peran uploader, metadata wajib, duplikat, nomor revisi
#
# Persetujuan BUKAN pengganti izin: kalau peran pengguna tidak berhak, gerbang kualitas tetap menolaknya
# walaupun manusia sudah menyetujui.
#
# Latihan ini berjalan di dalam knowledge base SEMENTARA (`sandbox_knowledge`), sehingga `data/` yang asli
# tidak berubah.

# %%
# Langkah 1 - Menyiapkan model
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import HumanMessage
from langchain.tools import ToolRuntime, tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from migas_shared import rag_tools as rt
from migas_shared.config import DATA
from migas_shared.rag_tools import KonteksPengguna, daftar_dokumen_aktif

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Tool upload dan fungsi pembuat agen
# `upload_revisi_sop` adalah tindakan tulis; hanya `approve` atau `reject` yang diizinkan untuknya.

# %%
METADATA_REV4 = {
    "doc_id": "SOP-HSE-001", "title": "SOP-HSE-001 Rev. 4 - Penanganan Bahaya Gas H2S", "doc_type": "SOP",
    "revision": "4", "status": "active", "owner": "Departemen HSE", "access_group": "all",
}


@tool
def upload_revisi_sop(nama_file: str, runtime: ToolRuntime[KonteksPengguna]) -> str:
    """Upload file revisi SOP dari folder contoh_upload ke knowledge base bersama. TINDAKAN TULIS.

    Args:
        nama_file: Nama file di data/contoh_upload, contoh "SOP-HSE-001_rev4_H2S.md"
    """
    jalur = DATA / "contoh_upload" / nama_file
    if not jalur.exists():
        return f"File {nama_file} tidak ditemukan di data/contoh_upload."
    return rt._ingest(nama_file, jalur.read_text(encoding="utf-8"), METADATA_REV4, runtime.context.role)


def buat_agen(model):
    return create_agent(
        model,
        tools=[upload_revisi_sop, daftar_dokumen_aktif],
        system_prompt=(
            "Anda asisten dokumen. Untuk meng-upload revisi, pakai upload_revisi_sop dan tunggu hasilnya. "
            "Baru sesudah itu, bila diminta, panggil daftar_dokumen_aktif (jangan memanggil keduanya sekaligus). "
            "Jawab singkat dalam Bahasa Indonesia."
        ),
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "upload_revisi_sop": {"allowed_decisions": ["approve", "reject"],
                                          "description": "UPLOAD DOKUMEN mengubah knowledge base bersama"},
                    "daftar_dokumen_aktif": False,
                }
            )
        ],
        checkpointer=InMemorySaver(),
        context_schema=KonteksPengguna,
    )

# %% [markdown]
# ## Langkah 3 - Fungsi skenario
# `skenario` menjalankan permintaan upload, berhenti di interrupt, lalu menerapkan keputusan manusia.
# Saat melanjutkan, konteks (peran pengguna) harus dikirim lagi.

# %%
def skenario(model, judul: str, peran: str, keputusan: dict) -> None:
    print(judul)
    print("-" * 60)
    agent = buat_agen(model)
    config = {"configurable": {"thread_id": judul}}
    konteks = KonteksPengguna(role=peran, area="Seruni", user_id=f"{peran}-1")
    permintaan = "Upload revisi SOP-HSE-001 dari file SOP-HSE-001_rev4_H2S.md, lalu tampilkan dokumen SOP-HSE-001 yang aktif."

    result = agent.invoke({"messages": [HumanMessage(content=permintaan)]}, config, context=konteks)
    aksi = result["__interrupt__"][0].value["action_requests"][0]
    print(f"Peran pengguna  : {peran}")
    print(f"Usulan agen     : {aksi['name']}({aksi['args']})")
    print(f"Keputusan manusia: {keputusan}")

    # Saat melanjutkan, konteks harus dikirim lagi
    final = agent.invoke(Command(resume={"decisions": [keputusan]}), config, context=konteks)
    print(f"Agen: {final['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 4 - Skenario 1: peran HSE, manusia menyetujui
# Berhasil, Rev 3 menjadi superseded.

# %%
with rt.sandbox_knowledge():
    skenario(model, "1) HSE, disetujui", "hse", {"type": "approve"})

# %% [markdown]
# ## Langkah 5 - Skenario 2: peran operator, manusia menyetujui
# Manusia menyetujui, tetapi gerbang kualitas menolak karena peran tidak berhak.

# %%
with rt.sandbox_knowledge():
    skenario(model, "2) Operator, disetujui manusia", "operator", {"type": "approve"})

# %% [markdown]
# ## Langkah 6 - Skenario 3: peran HSE, manusia menolak
# Tool tidak berjalan sama sekali.

# %%
with rt.sandbox_knowledge():
    skenario(model, "3) HSE, ditolak manusia", "hse",
             {"type": "reject", "message": "Revisi belum ditandatangani manajer HSE. Jangan upload."})

# %% [markdown]
# ## Ide Utama
# - Tindakan tulis pada knowledge base bersama layak diberi gerbang persetujuan manusia
# - Persetujuan bukan pengganti izin: operator tetap ditolak oleh gerbang kualitas di dalam kode
# - Konteks (peran) harus dikirim lagi saat melanjutkan dengan `Command(resume=...)`
# - Knowledge base asli tidak berubah selama latihan karena memakai `sandbox_knowledge()`
