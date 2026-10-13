# %% [markdown]
# # Contoh 2: RAG Agentik
# Jalankan sel satu per satu dengan Shift+Enter, atau seluruh file: `python hari4/10-agentic-rag/code/02_agentic_rag.py`
#
# Pada RAG agentik, agen memutuskan SENDIRI apakah perlu mencari di dokumen atau cukup menjawab dari pengetahuan
# umum. Tool pencarian `cari_dokumen` (dari paket bersama) dipakai seperti tool biasa; agen memutuskan kapan
# memanggilnya dari deskripsi tool dan prompt sistem.
#
# Contoh ini mengajukan campuran pertanyaan, lalu MEMERIKSA DI KODE apakah agen mencari atau tidak.

# %%
# Langkah 1 - Membuat agen dengan tool pencarian
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from migas_shared.rag_tools import KonteksPengguna, cari_dokumen
from migas_shared.tampil import jawaban_akhir, jejak_tool

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

PROMPT = """Anda asisten dokumen untuk operasi lapangan migas.
Untuk pertanyaan tentang prosedur, batas alarm, kode alarm perangkat, atau isi laporan perusahaan, pakai tool
cari_dokumen lebih dulu. Untuk pengetahuan umum yang tidak terkait dokumen perusahaan (hitungan sederhana, fakta umum),
jawab langsung tanpa mencari.
Jawab dokumen hanya dari hasil pencarian dan beri sitasi [DOC_ID bagian]. Kalau hasil pencarian tidak memuat
jawabannya, katakan terus terang bahwa informasinya tidak ditemukan.
Jawab dalam Bahasa Indonesia, ringkas."""

agent = create_agent(model, tools=[cari_dokumen], system_prompt=PROMPT, context_schema=KonteksPengguna)
konteks = KonteksPengguna(role="engineer", area="Seruni", user_id="ENG-208")

# %% [markdown]
# ## Langkah 2 - Fungsi untuk satu pertanyaan
# `periksa` menanyakan agen, menampilkan keputusannya (mencari atau tidak) dari daftar tool call, dan membandingkannya
# dengan harapan. Peran penanya dikirim lewat `context`, bukan diisi oleh model.

# %%
def periksa(pertanyaan: str, seharusnya_mencari: bool) -> bool:
    print(f"Pertanyaan: {pertanyaan}")
    response = agent.invoke({"messages": [HumanMessage(content=pertanyaan)]}, context=konteks)
    pencarian = jejak_tool(response["messages"])
    if pencarian:
        print(f"   Keputusan agen: MENCARI di dokumen -> {pencarian}")
    else:
        print("   Keputusan agen: menjawab langsung dari pengetahuan umum (tanpa mencari)")
    print(f"   Jawaban: {jawaban_akhir(response)[:300]}")
    cocok = bool(pencarian) == seharusnya_mencari
    print(f"   Pemeriksaan: {'LOLOS' if cocok else 'GAGAL'} (diharapkan {'mencari' if seharusnya_mencari else 'tidak mencari'})")
    return cocok


hasil_pemeriksaan = []

# %% [markdown]
# ## Langkah 3 - Pertanyaan umum: seharusnya tidak mencari

# %%
hasil_pemeriksaan.append(periksa("Berapa 2 + 2?", seharusnya_mencari=False))

# %%
hasil_pemeriksaan.append(periksa("Apa ibu kota Prancis?", seharusnya_mencari=False))

# %% [markdown]
# ## Langkah 4 - Pertanyaan tentang dokumen perusahaan: seharusnya mencari

# %%
hasil_pemeriksaan.append(periksa("Berapa nilai IDLH untuk gas H2S menurut SOP kita?", seharusnya_mencari=True))

# %%
hasil_pemeriksaan.append(
    periksa("VSD FD-500 menampilkan kode F12. Apa artinya dan apa yang harus dilakukan?", seharusnya_mencari=True)
)

# %% [markdown]
# ## Langkah 5 - Rekap

# %%
print(f"Keputusan agen sesuai harapan pada {sum(hasil_pemeriksaan)} dari {len(hasil_pemeriksaan)} pertanyaan")

# %% [markdown]
# ## Ide Utama
# - Agen menjawab pengetahuan umum langsung tanpa mencari, dan memakai tool pencarian untuk pertanyaan tentang dokumen perusahaan
# - Agen memutuskan SENDIRI kapan mencari, dari deskripsi tool dan prompt; keputusannya diperiksa di kode lewat daftar tool call
# - Panggilan pencarian lebih sedikit dan respons lebih cepat untuk pertanyaan umum dibandingkan RAG tradisional
# - Pola yang sama bisa diperluas dengan beberapa sumber pencarian dan tool lain
