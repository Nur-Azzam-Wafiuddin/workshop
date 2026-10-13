# %% [markdown]
# # Bab 1 - Latihan 1: Chatbot Serah Terima Shift
# Isi bagian bertanda `TODO(...)` dengan kode dari bagian **Kode Jawaban Latihan** pada PDF bab ini, lalu jalankan sel satu per satu
# dengan Shift+Enter. Baris `... = None  # TODO` atau `raise NotImplementedError` berarti kode itu harus Anda ganti.
#
# Chatbot dengan riwayat percakapan: setiap giliran ditambahkan ke daftar pesan lalu seluruhnya dikirim ke model.
#
# Bagian utama memakai dua giliran contoh. Sel terakhir membuka mode interaktif (ketik catatan sendiri)
# setelah `INTERAKTIF` diubah menjadi `True`.

# %%
# Langkah 1 - Menyiapkan model dan riwayat percakapan
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("ONLINE_MODEL"),
    base_url=os.getenv("ONLINE_BASE_URL"),
    api_key=os.getenv("ONLINE_API_KEY"),
    reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
)

# TODO(B1.1): buat daftar messages berisi satu SystemMessage yang meminta asisten mencatat laporan operator, mengingatnya, dan menjawab ringkas dalam Bahasa Indonesia
messages = []  # TODO: ganti dengan implementasi Anda

print("Asisten: Halo, saya asisten serah terima shift. Sampaikan catatan Anda.")

# %% [markdown]
# ## Langkah 2 - Fungsi satu giliran
# Pesan pengguna ditambahkan ke riwayat, model dipanggil dengan seluruh riwayat, lalu jawabannya ikut disimpan.

# %%
def kirim_giliran(masukan: str):
    """Satu giliran chat dengan riwayat percakapan."""
    # TODO(B1.2): tambahkan pesan pengguna (HumanMessage) ke riwayat messages
    pass  # TODO: ganti dengan implementasi Anda

    try:
        # TODO(B1.3): panggil model dengan seluruh riwayat messages
        response = None  # TODO: ganti dengan implementasi Anda
        print(f"\nAsisten: {response.content}")

        # TODO(B1.4): simpan jawaban model ke riwayat sebagai AIMessage agar giliran berikutnya bisa mengingatnya
        pass  # TODO: ganti dengan implementasi Anda
        print(f"Panjang percakapan: {len(messages)} pesan")

    except Exception as error:
        print(f"\nError: {error}")
        messages.pop()  # buang pesan pengguna yang gagal diproses agar riwayat tetap rapi


# %% [markdown]
# ## Langkah 3 - Giliran pertama: melaporkan catatan

# %%
masukan = "Shift pagi: separator V-SR1-101 level controller hunting, ESP SR-020 stabil."
print(f"\nAnda: {masukan}")
kirim_giliran(masukan)

# %% [markdown]
# ## Langkah 4 - Giliran kedua: menanyakan ingatan
# Asisten bisa menjawab karena seluruh riwayat dikirim ulang.

# %%
masukan = "Apa saja yang tadi saya laporkan?"
print(f"\nAnda: {masukan}")
kirim_giliran(masukan)

print(f"\nSampai jumpa! Percakapan kita berisi {len(messages)} pesan.")

# %% [markdown]
# ## Langkah 5 - Mencoba sendiri (opsional)
# Ubah `INTERAKTIF` menjadi `True`, jalankan sel, lalu ketik catatan atau pertanyaan. Ketik `keluar` untuk berhenti.
# Pertanyaan kosong dilewati.

# %%
INTERAKTIF = False  # ubah ke True untuk mencoba sendiri

if INTERAKTIF:
    while True:
        try:
            masukan = input("\nAnda: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n\nSampai jumpa! Percakapan kita berisi {len(messages)} pesan.")
            break

        if masukan.lower() in ("keluar", "exit", "quit"):
            print(f"\nSampai jumpa! Percakapan kita berisi {len(messages)} pesan.")
            break

        if not masukan:
            continue

        kirim_giliran(masukan)
