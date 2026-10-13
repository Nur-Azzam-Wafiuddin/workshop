# %% [markdown]
# # Bab 6 - Latihan Bonus: Persetujuan yang Bertahan Lebih Lama dari Program
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Di sistem nyata, manusia jarang duduk di depan terminal. Seorang manajer mungkin menyetujui permintaan
# satu jam kemudian, dari proses yang berbeda. Solusi ini membagi pekerjaan:
#
# - `submit`: jalankan agen sampai perlu persetujuan, lalu KELUAR. Permintaan yang menunggu disimpan oleh
#   checkpointer (`SqliteSaver`) dan dicatat dalam file JSON kecil.
# - `decide`: proses yang sepenuhnya terpisah memuat thread tersimpan dan melanjutkannya.
#
# Karena agen yang berhenti tersimpan di SQLite (bab 5), kedua langkah bisa berjalan berjam-jam berselang.
#
# Demo di bawah memakai folder sementara dan membuat objek agen BARU untuk setiap langkah. Fungsi `submit`,
# `pending`, dan `decide` juga bisa dipanggil sendiri-sendiri (lihat sel opsional di akhir) dengan
# file tetap yang bertahan setelah program selesai.

# %%
# Langkah 1 - Menyiapkan model dan alat bantu
import json
import os
import sqlite3
import tempfile
import uuid

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from migas_shared.config import ROOT

load_dotenv()

# %% [markdown]
# ## Langkah 2 - Tool dan pembuat agen
# `buat_agen` membuat objek agen BARU setiap kali: seluruh memori berasal dari file SQLite.

# %%
@tool
def pesan_suku_cadang(asset_id: str, nama_barang: str, jumlah: int) -> str:
    """Buat permintaan pengadaan suku cadang untuk sebuah aset.

    Args:
        asset_id: Kode aset
        nama_barang: Nama suku cadang
        jumlah: Jumlah unit
    """
    return f"Dipesan {jumlah} unit {nama_barang} untuk {asset_id}"


def buat_agen(db_path: str):
    """Objek agen BARU setiap kali: seluruh memori berasal dari file SQLite."""
    model = ChatOpenAI(
        model=os.getenv("ONLINE_MODEL"),
        base_url=os.getenv("ONLINE_BASE_URL"),
        api_key=os.getenv("ONLINE_API_KEY"),
        reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    )
    # TODO(B6.5): buka koneksi SQLite (check_same_thread=False), buat agen dengan tool pesan_suku_cadang, HumanInTheLoopMiddleware(interrupt_on={"pesan_suku_cadang": True}), dan checkpointer=SqliteSaver(connection); kembalikan (agent, connection)
    raise NotImplementedError("TODO(B6.5)")

# %% [markdown]
# ## Langkah 3 - Antrean persetujuan: submit, pending, decide
# Antrean disimpan sebagai file JSON. `submit` menaruh permintaan yang berhenti ke antrean, `pending` menampilkannya,
# dan `decide` melanjutkan thread tersimpan dengan sebuah keputusan.

# %%
def muat_antrean(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def simpan_antrean(path: str, antrean: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(antrean, f, indent=2, ensure_ascii=False)


def submit(db_path: str, antrean_path: str, teks: str) -> str:
    """Jalankan agen. Bila berhenti, simpan permintaan ke antrean dan kembalikan id thread."""
    thread_id = uuid.uuid4().hex[:8]
    agent, connection = buat_agen(db_path)
    config = {"configurable": {"thread_id": thread_id}}

    result = agent.invoke({"messages": [HumanMessage(content=teks)]}, config)
    connection.close()

    if "__interrupt__" not in result:
        print(f"Tidak perlu persetujuan. Agen berkata: {result['messages'][-1].content}")
        return thread_id

    # TODO(B6.6): ambil aksi pertama yang menunggu dari result["__interrupt__"][0].value["action_requests"]
    aksi = None  # TODO: ganti dengan implementasi Anda
    # TODO(B6.7): muat antrean, tambahkan entri thread_id berisi tool, args, dan permintaan, lalu simpan kembali
    pass  # TODO: ganti dengan implementasi Anda
    print(f"Permintaan {thread_id} menunggu persetujuan: {aksi['name']}({aksi['args']})")
    return thread_id


def pending(antrean_path: str) -> None:
    antrean = muat_antrean(antrean_path)
    if not antrean:
        print("Tidak ada yang menunggu persetujuan")
    for thread_id, item in antrean.items():
        print(f"Menunggu {thread_id}: {item['tool']}({item['args']})")


def decide(db_path: str, antrean_path: str, thread_id: str, putusan: str, alasan: str = "") -> None:
    """'Sesi' terpisah memuat thread tersimpan dan melanjutkannya dengan sebuah keputusan."""
    antrean = muat_antrean(antrean_path)
    if thread_id not in antrean:
        print(f"Tidak ada permintaan tertunda dengan id {thread_id}")
        return

    keputusan = (
        {"type": "approve"}
        if putusan == "approve"
        else {"type": "reject", "message": alasan or "Ditolak oleh pemberi persetujuan"}
    )
    agent, connection = buat_agen(db_path)  # agen baru, tidak ada apa pun di RAM
    config = {"configurable": {"thread_id": thread_id}}
    # TODO(B6.8): lanjutkan thread tersimpan dengan Command(resume={"decisions": [keputusan]}) dan config thread itu
    result = None  # TODO: ganti dengan implementasi Anda
    connection.close()

    del antrean[thread_id]
    simpan_antrean(antrean_path, antrean)
    label = "disetujui" if putusan == "approve" else "ditolak"
    print(f"{thread_id} {label} -> {result['messages'][-1].content}")

# %% [markdown]
# ## Langkah 4 - Folder sementara untuk demo
# Database dan antrean demo berada di folder sementara agar tidak meninggalkan file.

# %%
folder_demo = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
db_path = os.path.join(folder_demo.name, "persetujuan.db")
antrean_path = os.path.join(folder_demo.name, "antrean.json")

# %% [markdown]
# ## Langkah 5 - Proses A: operator mengirim dua permintaan, lalu program KELUAR
# Setiap `submit` membuat objek agen baru dan berhenti di interrupt persetujuan. Permintaan pertama wajar.

# %%
print("Proses A: operator mengirim dua permintaan, lalu program KELUAR")
id1 = submit(db_path, antrean_path, "Pesan 2 unit modul VSD FD500 untuk ESP SR-020")

# %% [markdown]
# ## Langkah 6 - Proses A: permintaan kedua (jumlah besar)

# %%
id2 = submit(db_path, antrean_path, "Pesan 40 unit gasket flange untuk K-ML1-201")

# %% [markdown]
# ## Langkah 7 - Proses B: manajer melihat antrean

# %%
print("Proses B (nanti): manajer melihat antrean")
pending(antrean_path)

# %% [markdown]
# ## Langkah 8 - Proses B: manajer memutuskan
# Keputusan dijalankan dengan objek agen yang benar-benar baru. Permintaan pertama disetujui, kedua ditolak dengan alasan.

# %%
print("Proses B: manajer memutuskan, memakai objek agen yang benar-benar baru")
decide(db_path, antrean_path, id1, "approve")
decide(db_path, antrean_path, id2, "reject", "Stok gasket di gudang Kenanga masih cukup untuk 3 bulan.")

# %% [markdown]
# ## Langkah 9 - Antrean sesudahnya

# %%
print("Antrean sesudahnya")
pending(antrean_path)
folder_demo.cleanup()

# %% [markdown]
# ## Langkah 10 - Memakai file tetap (opsional)
# Untuk mencoba pemisahan proses yang sebenarnya, panggil fungsi di atas dengan file yang bertahan di disk.
# Hapus tanda `#` pada tiga baris di bawah, jalankan `submit`, ulangi sel di sesi lain (atau mulai ulang kernel),
# lalu jalankan `pending` dan `decide`.

# %%
DB_BAWAAN = str(ROOT / "hari3" / "06-persetujuan-manusia" / "persetujuan.db")
ANTREAN_BAWAAN = str(ROOT / "hari3" / "06-persetujuan-manusia" / "antrean_persetujuan.json")

# submit(DB_BAWAAN, ANTREAN_BAWAAN, "Pesan 2 unit modul VSD FD500 untuk ESP SR-020")
# pending(ANTREAN_BAWAAN)
# decide(DB_BAWAAN, ANTREAN_BAWAAN, "<thread_id>", "approve")
