# %% [markdown]
# # Bab 5 - Latihan 1: Asisten Serah Terima Shift dengan Memori Persisten
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Asisten yang mengingat setiap operator, bahkan setelah program dimulai ulang.
# - Memori disimpan di file SQLite (SqliteSaver)
# - Setiap nama operator memiliki thread sendiri
# - Perintah pada mode interaktif: /riwayat, /baru, /keluar
#
# Bagian utama berupa demo berskrip yang menirukan: pakai aplikasi, tutup, lalu buka lagi.
# Sel terakhir membuka mode interaktif (ketik pesan sendiri) setelah `INTERAKTIF` diubah menjadi `True`.

# %%
# Langkah 1 - Impor dan fungsi bantu
import os
import sqlite3
import tempfile
import uuid

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver

from migas_shared.config import ROOT

load_dotenv()

DB_BAWAAN = str(ROOT / "hari3" / "05-memori-agen" / "memori_chat.db")


def buat_agen(db_path: str):
    model = ChatOpenAI(
        model=os.getenv("ONLINE_MODEL"),
        base_url=os.getenv("ONLINE_BASE_URL"),
        api_key=os.getenv("ONLINE_API_KEY"),
        reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    )
    # TODO(B5.1): buka koneksi SQLite (check_same_thread=False), buat agen tanpa tool dengan checkpointer=SqliteSaver(connection), lalu kembalikan (agent, connection)
    raise NotImplementedError("TODO(B5.1)")


def chat(agent, user: str, sesi: str, teks: str) -> str:
    """Satu giliran percakapan. user dan sesi bersama-sama menentukan thread."""
    # TODO(B5.2): buat config dengan thread_id '<user>:<sesi>', panggil agent.invoke, dan kembalikan teks jawaban terakhir
    raise NotImplementedError("TODO(B5.2)")


def jumlah_pesan(agent, user: str, sesi: str) -> int:
    # TODO(B5.3): kembalikan jumlah pesan pada state thread itu lewat agent.get_state(config)
    raise NotImplementedError("TODO(B5.3)")


# Folder sementara untuk file database demo; dibersihkan di sel terakhir demo
folder = tempfile.TemporaryDirectory()
db_path = os.path.join(folder.name, "demo.db")

# %% [markdown]
# ## Langkah 2 - Jalan 1: pakai aplikasi
# Rina memperkenalkan diri dan menyebut jam tersibuknya. Percakapan disimpan di file SQLite.

# %%
print("Jalan 1")
agent, connection = buat_agen(db_path)
for teks in ["Saya Rina, supervisor shift malam di GS-SR1.", "Jam tersibuk kami adalah pukul 07.00."]:
    print(f"rina: {teks}")
    print(f"Agen: {chat(agent, 'rina', 'utama', teks)}")
print(f"Pesan tersimpan untuk rina: {jumlah_pesan(agent, 'rina', 'utama')}")
connection.close()

# %% [markdown]
# ## Langkah 3 - Jalan 2: program dimulai ulang
# Agen dan koneksi baru membaca file yang sama. Riwayat Rina dimuat, sedangkan Agus belum punya riwayat.

# %%
print("Jalan 2 (program dimulai ulang)")
agent, connection = buat_agen(db_path)
print(f"Pesan dimuat untuk rina: {jumlah_pesan(agent, 'rina', 'utama')}")
print(f"Pesan dimuat untuk agus: {jumlah_pesan(agent, 'agus', 'utama')}")
pertanyaan = "Di gathering station mana saya bertugas dan kapan jam tersibuk saya?"
print(f"rina: {pertanyaan}")
print(f"Agen: {chat(agent, 'rina', 'utama', pertanyaan)}")

# %% [markdown]
# ## Langkah 4 - Sesi baru untuk Rina
# Sesi baru berarti thread baru, jadi agen tidak mengingat percakapan sebelumnya.

# %%
print("Sesi baru untuk rina (thread baru)")
print(f"rina: {pertanyaan}")
print(f"Agen: {chat(agent, 'rina', 'sesi2', pertanyaan)}")
connection.close()
folder.cleanup()

# %% [markdown]
# ## Langkah 5 - Mode interaktif (opsional)
# Ubah `INTERAKTIF` menjadi `True`, jalankan sel, lalu ketik nama dan pesan Anda. Memori disimpan di
# `hari3/05-memori-agen/memori_chat.db`, jadi percakapan berlanjut saat sel dijalankan lagi.
# Perintah: `/riwayat` (jumlah pesan), `/baru` (sesi baru), `/keluar` (berhenti).

# %%
INTERAKTIF = False  # ubah ke True untuk mencoba sendiri

if INTERAKTIF:
    user = input("Nama Anda: ").strip().lower() or "tamu"
    sesi = "utama"
    agent, connection = buat_agen(DB_BAWAAN)

    ada = jumlah_pesan(agent, user, sesi)
    if ada:
        print(f"Selamat datang kembali, {user}! {ada} pesan tersimpan dimuat.")
    print("Perintah: /riwayat  /baru  /keluar\n")

    while True:
        teks = input("Anda: ").strip()
        if teks == "/keluar":
            break
        if teks == "/riwayat":
            print(f"   {jumlah_pesan(agent, user, sesi)} pesan dalam sesi ini")
        elif teks == "/baru":
            sesi = uuid.uuid4().hex[:6]
            print(f"   Sesi baru dimulai ({sesi}). Sesi lama tetap tersimpan.")
        elif teks:
            print(f"Agen: {chat(agent, user, sesi, teks)}\n")
    connection.close()
