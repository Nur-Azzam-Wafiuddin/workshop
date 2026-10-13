"""Fungsi bantu kecil untuk menampilkan hasil agen di terminal.

- jejak_tool(messages)   : daftar tool yang dipanggil agen, dalam urutan, beserta argumennya
- jawaban_akhir(response): teks pesan terakhir dari hasil agent.invoke()
"""
from __future__ import annotations

import asyncio
import sys
import threading
from typing import Any

_loop_latar: asyncio.AbstractEventLoop | None = None

# Kernel Jupyter mengganti sys.stderr dengan objek tanpa fileno(), padahal klien MCP stdio memerlukannya
# untuk menjalankan server sebagai subproses. Kembalikan ke stderr asli proses.
try:
    sys.stderr.fileno()
except Exception:  # noqa: BLE001
    sys.stderr.fileno = sys.__stderr__.fileno


def jalankan(coro):
    """Jalankan coroutine dan kembalikan hasilnya, baik dari skrip biasa maupun dari Jupyter/Interactive Window.

    Jupyter/VS Code sudah punya event loop berjalan, sehingga asyncio.run() gagal di sana. Karena itu semua
    coroutine dijalankan pada SATU event loop di thread latar yang dipakai ulang oleh semua sel (dan oleh skrip
    biasa). Satu loop yang sama penting: klien async seperti ChatOpenAI terikat ke loop pertama yang
    memakainya, dan gagal ("Event loop is closed") bila loop berganti pada panggilan berikutnya.
    """
    global _loop_latar
    if _loop_latar is None:
        _loop_latar = asyncio.new_event_loop()
        threading.Thread(target=_loop_latar.run_forever, daemon=True).start()
    return asyncio.run_coroutine_threadsafe(coro, _loop_latar).result()


def jejak_tool(messages: list[Any]) -> list[str]:
    """Ambil urutan pemanggilan tool dari daftar pesan hasil agen, mis. ["hitung_water_cut({'oil_bopd': 120, ...})"]."""
    jejak = []
    for pesan in messages:
        for pemanggilan in getattr(pesan, "tool_calls", None) or []:
            jejak.append(f"{pemanggilan['name']}({pemanggilan['args']})")
    return jejak


def jawaban_akhir(response: dict) -> str:
    """Teks dari pesan terakhir pada hasil agent.invoke()."""
    isi = response["messages"][-1].content
    return isi if isinstance(isi, str) else "".join(b.get("text", "") for b in isi if isinstance(b, dict))
