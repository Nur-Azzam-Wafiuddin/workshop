"""
Server MCP buatan sendiri untuk Latihan 3 (Bonus): informasi work order.

Server stdio ini membuka dua tool hanya-baca:
- daftar_wo_terbuka(area)           : work order terbuka di sebuah area
- hitung_kerugian_downtime(...)     : perkiraan biaya downtime

Dipakai oleh latihan_4.py (klien yang menjalankannya sebagai subproses).
"""

import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("work-order")

WORK_ORDER = {
    "Seruni": [
        ("WO-26-12501", "Kebocoran seal ESP SR-020", "tinggi"),
        ("WO-26-12502", "Lampu penerangan manifold berkedip", "rendah"),
    ],
    "Kenanga": [("WO-26-12611", "Sucker rod KN-033 patah, menunggu rig", "tinggi")],
    "Melati": [],
}


# TODO(B9.9): tulis tool daftar_wo_terbuka(area) dengan @mcp.tool(): cari WORK_ORDER menurut area (huruf besar di awal), raise ValueError yang menyebut area yang ada bila tidak dikenal, dan kembalikan satu baris per work order (id | deskripsi | prioritas)
pass  # TODO: ganti dengan implementasi Anda


# TODO(B9.10): tulis tool hitung_kerugian_downtime(downtime_jam, laju_bopd, harga_usd_per_bbl=70.0): raise ValueError bila negatif, hitung barel = laju_bopd * downtime_jam / 24, dan kembalikan teks 'Kehilangan X barel, perkiraan kerugian USD Y'
pass  # TODO: ganti dengan implementasi Anda


if __name__ == "__main__":
    print("Server MCP work order (stdio) berjalan...", file=sys.stderr)
    mcp.run(transport="stdio")
