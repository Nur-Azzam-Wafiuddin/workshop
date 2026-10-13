"""Mengekspor agen mini project sebagai graf untuk LangGraph Studio (perintah `langgraph dev`).

Studio memasang checkpointer sendiri untuk menyimpan percakapan, jadi agen di sini dibuat TANPA checkpointer.
Untuk menambahkan agen kelompok Anda:

  1. tambahkan satu baris di bawah, mis. `kelompok_a = graf("kelompok_a")`
  2. daftarkan di langgraph.json (root repositori): "kelompok_a": "./hari4/11-mini-project/aplikasi/studio.py:kelompok_a"

Menjalankannya (dari root repositori):   langgraph dev
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # agar `import kerangka` berhasil

import kerangka as k  # noqa: E402
from migas_shared.llm import get_chat_model  # noqa: E402


def graf(nama: str):
    """Muat file agen/<nama>.py dan kembalikan agennya tanpa checkpointer."""
    return k.muat_definisi(nama).buat_agen(get_chat_model(), None)


saya = graf("saya")
