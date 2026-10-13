# %% [markdown]
# # Contoh 4: Loop Persetujuan yang Nyata
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari3/06-persetujuan-manusia/code/04_approval_loop.py`
#
# Agen nyata bisa mengusulkan BEBERAPA tindakan berisiko sekaligus, dan tool berbeda pantas diberi aturan
# berbeda. Contoh ini membangun loop persetujuan yang bisa dipakai ulang:
#
# 1. Kebijakan per tool: tool hanya-baca berjalan bebas; tool berisiko berhenti; sebagian tool hanya boleh
#    disetujui atau ditolak (tidak boleh diubah)
# 2. Beberapa permintaan: satu interrupt bisa memuat banyak tindakan yang diusulkan, dan Anda menjawab satu per satu
#    sesuai urutan
# 3. Sebuah loop: terus lanjutkan sampai agen tidak punya pertanyaan lagi
#
# Bagian utama memakai fungsi `auto_reviewer` (reviewer berskrip) sebagai pengganti manusia. Sel terakhir
# membuka mode interaktif, tempat Anda sendiri yang memutuskan, setelah `INTERAKTIF` diubah menjadi `True`.

# %%
# Langkah 1 - Menyiapkan model
import json
import os

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
# ## Langkah 2 - Empat tool dengan data uji
# Dua tool mengubah data (`FREKUENSI_VSD`, `WORK_ORDER`), satu menghentikan produksi (`SUMUR_SHUT_IN`),
# dan satu hanya membaca.

# %%
FREKUENSI_VSD = {"SR-020": 50, "SR-033": 48, "SR-027": 50}
WORK_ORDER: list[dict] = []
SUMUR_SHUT_IN: list[str] = []


@tool
def baca_frekuensi_vsd(kode_sumur: str) -> str:
    """Baca frekuensi VSD saat ini pada sebuah sumur ESP (hanya baca).

    Args:
        kode_sumur: Kode sumur, contoh "SR-033"
    """
    frekuensi = FREKUENSI_VSD.get(kode_sumur.upper())
    return f"{kode_sumur}: {frekuensi} Hz" if frekuensi else f"Sumur tidak dikenal: {kode_sumur}"


@tool
def ubah_frekuensi_vsd(kode_sumur: str, frekuensi_hz: int) -> str:
    """Ubah setpoint frekuensi VSD sebuah sumur ESP. Berlaku langsung pada motor.

    Args:
        kode_sumur: Kode sumur, contoh "SR-033"
        frekuensi_hz: Frekuensi baru dalam Hz
    """
    FREKUENSI_VSD[kode_sumur.upper()] = frekuensi_hz
    return f"Frekuensi VSD {kode_sumur} sekarang {frekuensi_hz} Hz"


@tool
def buat_work_order(asset_id: str, uraian: str, prioritas: str) -> str:
    """Buat work order pemeliharaan baru.

    Args:
        asset_id: Kode aset, contoh "V-SR1-101"
        uraian: Uraian pekerjaan
        prioritas: Prioritas: rendah, sedang, atau tinggi
    """
    nomor = f"WO-UJI-{len(WORK_ORDER) + 1:03d}"
    WORK_ORDER.append({"nomor": nomor, "asset_id": asset_id, "uraian": uraian, "prioritas": prioritas})
    return f"Work order {nomor} dibuat untuk {asset_id} (prioritas {prioritas})"


@tool
def shut_in_sumur(kode_sumur: str, alasan: str) -> str:
    """Hentikan produksi sebuah sumur (shut-in). Produksi sumur hilang sampai dibuka kembali.

    Args:
        kode_sumur: Kode sumur
        alasan: Alasan shut-in
    """
    SUMUR_SHUT_IN.append(kode_sumur)
    return f"Sumur {kode_sumur} di-shut-in: {alasan}"

# %% [markdown]
# ## Langkah 3 - Kebijakan persetujuan dan agen
# Satu entri per tool. `allowed_decisions` membatasi pilihan reviewer; `shut_in_sumur` tidak boleh diubah.

# %%
# Kebijakan persetujuan: satu entri per tool
KEBIJAKAN_PERSETUJUAN = {
    "baca_frekuensi_vsd": False,  # hanya baca -> tidak pernah bertanya
    "ubah_frekuensi_vsd": {
        "allowed_decisions": ["approve", "edit", "reject"],
        "description": "PERUBAHAN SETPOINT memerlukan persetujuan",
    },
    "buat_work_order": {
        "allowed_decisions": ["approve", "edit", "reject"],
        "description": "WORK ORDER baru memerlukan persetujuan",
    },
    "shut_in_sumur": {
        "allowed_decisions": ["approve", "reject"],  # tidak boleh diubah!
        "description": "SHUT-IN SUMUR memerlukan persetujuan",
    },
}

agent = create_agent(
    model,
    tools=[baca_frekuensi_vsd, ubah_frekuensi_vsd, buat_work_order, shut_in_sumur],
    system_prompt=(
        "Anda asisten operasi produksi. Pakai tool untuk melakukan yang diminta pengguna. "
        "Jika sebuah pemanggilan tool ditolak, jelaskan alasannya dan jangan coba lagi. Jawab singkat dalam Bahasa Indonesia."
    ),
    middleware=[HumanInTheLoopMiddleware(interrupt_on=KEBIJAKAN_PERSETUJUAN)],
    checkpointer=InMemorySaver(),
)
config = {"configurable": {"thread_id": "sesi-operasi"}}

# %% [markdown]
# ## Langkah 4 - Auto reviewer dan loop persetujuan
# `auto_reviewer` adalah "reviewer" berskrip, pengganti manusia sungguhan. `jalankan_dengan_persetujuan`
# menjalankan agen dan terus melanjutkan selama masih ada interrupt, dengan satu keputusan per permintaan secara berurutan.

# %%
def auto_reviewer(permintaan: dict, boleh: list[str]) -> dict:
    """'Reviewer' berskrip: pengganti manusia sungguhan."""
    nama, argumen = permintaan["name"], permintaan["args"]
    print(f"\n   Usulan: {nama}({json.dumps(argumen, ensure_ascii=False)})")
    if nama == "ubah_frekuensi_vsd":
        lama = FREKUENSI_VSD[argumen["kode_sumur"].upper()]
        perubahan = abs(argumen["frekuensi_hz"] - lama) / lama
        if perubahan <= 0.10:
            print(f"      auto reviewer: perubahan {perubahan:.1%} (<= 10%) -> approve")
            return {"type": "approve"}
        print(f"      auto reviewer: perubahan {perubahan:.1%} (> 10%) -> reject")
        return {"type": "reject", "message": "Perubahan di atas 10% memerlukan persetujuan Production Engineer."}
    if nama == "shut_in_sumur":
        print("      auto reviewer: shut-in harus dikonfirmasi supervisor -> reject")
        return {"type": "reject", "message": "Supervisor harus mengonfirmasi shut-in langsung."}
    print("      auto reviewer: tidak berisiko -> approve")
    return {"type": "approve"}


def jalankan_dengan_persetujuan(agent, teks: str, config: dict, reviewer) -> str:
    """Jalankan agen dan terus lanjutkan sampai tidak ada lagi permintaan persetujuan."""
    result = agent.invoke({"messages": [HumanMessage(content=teks)]}, config)

    putaran = 0
    while "__interrupt__" in result:
        putaran += 1
        payload = result["__interrupt__"][0].value
        permintaan = payload["action_requests"]
        konfigurasi = payload["review_configs"]
        print(f"\nPutaran {putaran}: agen menunggu {len(permintaan)} tindakan")

        # Satu keputusan per permintaan, dengan URUTAN YANG SAMA
        keputusan = [
            reviewer(p, tinjau["allowed_decisions"])
            for p, tinjau in zip(permintaan, konfigurasi)
        ]
        result = agent.invoke(Command(resume={"decisions": keputusan}), config)

    return result["messages"][-1].content

# %% [markdown]
# ## Langkah 5 - Satu permintaan dengan tiga tindakan berisiko
# Agen mengusulkan ubah frekuensi, buat work order, dan shut-in sekaligus. Auto reviewer memutuskan satu per satu.

# %%
permintaan = (
    "Naikkan frekuensi VSD SR-033 ke 52 Hz, buat work order prioritas sedang untuk memeriksa "
    "level controller V-SR1-101, dan shut-in sumur SR-027 karena pembacaan H2S."
)
print(f"Pengguna: {permintaan}")
jawaban = jalankan_dengan_persetujuan(agent, permintaan, config, auto_reviewer)
print(f"\nAgen: {jawaban}\n")

# %% [markdown]
# ## Langkah 6 - Keadaan akhir
# Periksa apa yang benar-benar terjadi pada data setelah semua keputusan diterapkan.

# %%
def cetak_ringkasan():
    print(f"Frekuensi SR-033    : {FREKUENSI_VSD['SR-033']} Hz")
    print(f"Work order dibuat   : {WORK_ORDER or 'tidak ada'}")
    print(f"Sumur di-shut-in    : {SUMUR_SHUT_IN or 'tidak ada'}")


cetak_ringkasan()

# %% [markdown]
# ## Ide Utama
# - `interrupt_on` bisa memuat aturan berbeda untuk setiap tool
# - `allowed_decisions` membatasi apa yang boleh dilakukan reviewer (`shut_in_sumur`: tidak boleh diubah)
# - Satu interrupt bisa membawa beberapa `action_requests`: kembalikan satu keputusan per permintaan, berurutan
# - Bungkus siklus interrupt dan lanjut dalam sebuah loop; agen mungkin bertanya lagi nanti

# %% [markdown]
# ## Langkah 7 - Mencoba sendiri sebagai reviewer (opsional)
# Ubah `INTERAKTIF` menjadi `True`, jalankan sel, lalu ketik permintaan, misalnya
# "Naikkan frekuensi SR-033 ke 52 Hz dan shut-in SR-027". Anda yang memutuskan `a` (approve), `e` (edit), atau `r` (reject)
# untuk setiap tindakan. Ketik `keluar` atau kosongkan untuk berhenti. Percakapan melanjutkan thread yang sama.

# %%
INTERAKTIF = False  # ubah ke True untuk mencoba sendiri

if INTERAKTIF:
    def tanya_manusia(permintaan: dict, boleh: list[str]) -> dict:
        """Tampilkan satu tindakan yang diusulkan di terminal dan kembalikan keputusan manusia."""
        print(f"\n   Usulan: {permintaan['name']}({json.dumps(permintaan['args'], ensure_ascii=False)})")
        print(f"      Boleh: {', '.join(boleh)}")
        while True:
            pilihan = input("      Keputusan Anda [a=approve, e=edit, r=reject]: ").strip().lower()
            if pilihan == "a" and "approve" in boleh:
                return {"type": "approve"}
            if pilihan == "r" and "reject" in boleh:
                return {"type": "reject", "message": input("      Alasan: ").strip() or "Ditolak oleh reviewer"}
            if pilihan == "e" and "edit" in boleh:
                argumen_baru = input("      Argumen baru sebagai JSON: ").strip()
                return {
                    "type": "edit",
                    "edited_action": {"name": permintaan["name"], "args": json.loads(argumen_baru)},
                }
            print("      Pilihan tidak valid untuk tindakan ini")

    print("Ketik permintaan (atau 'keluar'). Contoh: 'Naikkan frekuensi SR-033 ke 52 Hz dan shut-in SR-027'\n")
    while True:
        teks = input("Anda: ").strip()
        if teks.lower() in {"keluar", "exit", ""}:
            break
        jawaban = jalankan_dengan_persetujuan(agent, teks, config, tanya_manusia)
        print(f"\nAgen: {jawaban}\n")
    cetak_ringkasan()
