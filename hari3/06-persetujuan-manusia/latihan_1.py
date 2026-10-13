# %% [markdown]
# # Bab 6 - Latihan 1: Asisten Operasi yang Aman
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Agen operasi dengan empat tool dan aturan persetujuan berbeda untuk masing-masing:
# - `baca_status_peralatan`: tidak pernah bertanya (hanya baca)
# - `jadwalkan_perawatan`: approve / edit / reject
# - `pesan_suku_cadang`: approve / edit / reject (aturan reviewer membatasi jumlah)
# - `shutdown_darurat`: approve / reject saja (tidak pernah boleh diubah)
#
# Setiap keputusan ditulis ke audit log yang dicetak di akhir.
#
# Reviewer-nya adalah fungsi berskrip (`reviewer`) agar demo berjalan tanpa pengawasan. Ganti `reviewer` dengan `input()`,
# seperti `tanya_manusia` di `code/04_approval_loop.py`, untuk membuatnya interaktif.

# %%
# Langkah 1 - Menyiapkan model
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# %% [markdown]
# ## Langkah 2 - Empat tool operasi

# %%
MAKS_JUMLAH_PESANAN = 4
JEJAK_AUDIT: list[dict] = []


@tool
def baca_status_peralatan(lokasi: str) -> str:
    """Baca status peralatan utama di sebuah lokasi (hanya baca).

    Args:
        lokasi: Kode lokasi, contoh "GS-SR1"
    """
    return f"{lokasi}: separator V-SR1-101 OK, kompresor K-ML1-201 OK, pompa injeksi P-SR1-302 tekanan hisap rendah, flare OK"


@tool
def jadwalkan_perawatan(asset_id: str, tanggal: str, uraian: str) -> str:
    """Jadwalkan pekerjaan perawatan pada sebuah aset.

    Args:
        asset_id: Kode aset
        tanggal: Tanggal format YYYY-MM-DD
        uraian: Uraian pekerjaan
    """
    return f"Perawatan {asset_id} dijadwalkan pada {tanggal}: {uraian}"


@tool
def pesan_suku_cadang(asset_id: str, nama_barang: str, jumlah: int) -> str:
    """Buat permintaan pengadaan suku cadang untuk sebuah aset.

    Args:
        asset_id: Kode aset
        nama_barang: Nama suku cadang
        jumlah: Jumlah unit
    """
    return f"Dipesan {jumlah} unit {nama_barang} untuk {asset_id}"


@tool
def shutdown_darurat(lokasi: str, alasan: str) -> str:
    """Hentikan SELURUH fasilitas di sebuah lokasi segera (emergency shutdown).

    Args:
        lokasi: Kode lokasi
        alasan: Mengapa shutdown diperlukan
    """
    return f"EMERGENCY SHUTDOWN {lokasi}: {alasan}"

# %% [markdown]
# ## Langkah 3 - Kebijakan, reviewer, dan pencatat audit
# `reviewer` adalah pengganti otomatis untuk reviewer manusia. `catat_keputusan` menulis setiap keputusan ke `JEJAK_AUDIT`.

# %%
# TODO(B6.1): isi KEBIJAKAN per tool: baca_status_peralatan False; jadwalkan_perawatan dan pesan_suku_cadang approve/edit/reject; shutdown_darurat hanya approve/reject
KEBIJAKAN = {}  # TODO: ganti dengan implementasi Anda


def reviewer(permintaan: dict) -> dict:
    """Pengganti otomatis untuk reviewer manusia."""
    nama, argumen = permintaan["name"], permintaan["args"]

    # TODO(B6.2): kembalikan keputusan reviewer: edit jumlah pesanan menjadi MAKS_JUMLAH_PESANAN bila lebih besar, reject shutdown_darurat dengan pesan agar dikonfirmasi manajer jaga, selain itu approve
    raise NotImplementedError("TODO(B6.2)")


def catat_keputusan(permintaan: dict, keputusan: dict) -> None:
    JEJAK_AUDIT.append(
        {
            "waktu": datetime.now().strftime("%H:%M:%S"),
            "tool": permintaan["name"],
            "argumen": permintaan["args"],
            "keputusan": keputusan["type"],
            "catatan": keputusan.get("message") or keputusan.get("edited_action", {}).get("args"),
        }
    )

# %% [markdown]
# ## Langkah 4 - Membuat agen dengan persetujuan

# %%
agent = create_agent(
    model,
    tools=[baca_status_peralatan, jadwalkan_perawatan, pesan_suku_cadang, shutdown_darurat],
    system_prompt=(
        "Anda asisten operasi untuk gathering station. Pakai tool untuk melakukan yang diminta pengguna. "
        "Jika sebuah pemanggilan ditolak, jelaskan alasannya dan jangan coba lagi. Jawab singkat dalam Bahasa Indonesia."
    ),
    # TODO(B6.3): pasang HumanInTheLoopMiddleware(interrupt_on=KEBIJAKAN) pada agen
    middleware=[],  # TODO: ganti dengan implementasi Anda
    checkpointer=InMemorySaver(),
)
config = {"configurable": {"thread_id": "ops-1"}}

# %% [markdown]
# ## Langkah 5 - Satu permintaan, beberapa tindakan, banyak keputusan
# Selama masih ada interrupt, setiap tindakan yang diusulkan ditinjau dan dicatat, lalu agen dilanjutkan.

# %%
teks_permintaan = (
    "Periksa peralatan di GS-SR1. Lalu jadwalkan perawatan untuk peralatan yang bermasalah pada 2026-08-10, "
    "pesan 10 unit seal pompa untuk P-SR1-302, dan jika ada yang tampak berbahaya, lakukan shutdown darurat."
)
print(f"Pengguna: {teks_permintaan}\n")

result = agent.invoke({"messages": [HumanMessage(content=teks_permintaan)]}, config)

while "__interrupt__" in result:
    payload = result["__interrupt__"][0].value
    keputusan_daftar = []
    for permintaan in payload["action_requests"]:
        keputusan = reviewer(permintaan)
        catat_keputusan(permintaan, keputusan)
        print(f"Usulan {permintaan['name']}({permintaan['args']}) -> {keputusan['type'].upper()}")
        keputusan_daftar.append(keputusan)
    # TODO(B6.4): lanjutkan agen dengan Command(resume={"decisions": keputusan_daftar}) dan config yang sama
    result = {}  # TODO: ganti dengan implementasi Anda

print(f"\nAgen: {result['messages'][-1].content}\n")

# %% [markdown]
# ## Langkah 6 - Audit log

# %%
print("Audit log")
print("-" * 60)
for entri in JEJAK_AUDIT:
    print(json.dumps(entri, ensure_ascii=False))
