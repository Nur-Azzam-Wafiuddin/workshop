"""
Server MCP Pencarian Dokumen (stdio)

Membuka pencarian dokumen SOP dan laporan perusahaan (indeks hybrid yang sama dengan bab 10)
sebagai tool MCP. Klien MCP mana pun dapat memakainya: agen LangChain, editor kode, atau aplikasi lain.

PERHATIKAN soal keamanan: server MCP tidak punya `ToolRuntime` dan tidak melihat konteks LangChain Anda.
Siapa penggunanya dan perannya harus ditentukan oleh KONFIGURASI SERVER, bukan oleh argumen yang diisi model.
Di sini peran dibaca dari variabel lingkungan PERAN_PENGGUNA yang diatur klien ketika menjalankan server.
Model tidak dapat mengubahnya, dan tidak ada tool yang menerima `role` sebagai argumen.

Dipakai oleh code/03_mcp_local_documents.py dan code/04_mcp_multi_server.py.

Jalankan (jarang perlu; klien MCP menjalankannya sendiri):
  PERAN_PENGGUNA=hse python hari4/09-mcp/code/servers/documents_stdio_server.py
"""

import os
import sys

from mcp.server.fastmcp import FastMCP

from migas_shared import rag_tools
from migas_shared.rag_pipeline import ROLE_GROUPS

PERAN = os.getenv("PERAN_PENGGUNA", "operator")
if PERAN not in ROLE_GROUPS:
    raise SystemExit(f"PERAN_PENGGUNA '{PERAN}' tidak valid. Pilihan: {', '.join(ROLE_GROUPS)}")

mcp = FastMCP("dokumen-migas")


@mcp.tool()
def cari_dokumen(pertanyaan: str, k: int = 4) -> str:
    """
    Cari chunk dokumen SOP, laporan, atau manual yang relevan dengan pertanyaan.
    Hasil hanya memuat dokumen berstatus aktif yang boleh dilihat oleh peran pengguna ini.

    Args:
        pertanyaan: Pertanyaan atau kata kunci pencarian, contoh 'alarm H2S 10 ppm'
        k: Jumlah chunk dokumen yang dikembalikan

    Returns:
        Chunk dokumen dengan id dokumen, revisi, dan bagian.
    """
    return rag_tools._cari(pertanyaan, max(1, min(k, 8)), PERAN)


@mcp.tool()
def daftar_dokumen_aktif(jenis: str | None = None) -> str:
    """
    Daftar dokumen aktif yang boleh dilihat oleh peran pengguna ini.

    Args:
        jenis: Filter jenis dokumen, contoh 'SOP' atau 'Laporan' (kosong = semua)

    Returns:
        Satu baris per dokumen: id, revisi, jenis, dan judul.
    """
    return rag_tools._daftar(jenis, PERAN)


if __name__ == "__main__":
    # Log ke stderr (stdout dipakai untuk komunikasi MCP)
    print(f"Server MCP dokumen (stdio) berjalan untuk peran: {PERAN}", file=sys.stderr)
    mcp.run(transport="stdio")
