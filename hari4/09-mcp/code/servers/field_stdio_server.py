"""
Server MCP Sederhana untuk Transport stdio: Perhitungan Lapangan

Server ini berjalan sebagai subproses dan berkomunikasi lewat stdio. Ia membuka tiga alat lapangan
(water cut, konversi satuan, status sumur) kepada klien MCP mana pun, bukan hanya program LangChain Anda.

Dipakai oleh code/02_mcp_local_stdio.py dan code/04_mcp_multi_server.py.

Jalankan (jarang perlu; klien MCP menjalankannya sendiri): python hari4/09-mcp/code/servers/field_stdio_server.py
"""

import sys

from mcp.server.fastmcp import FastMCP

from migas_shared.field_tools import DATA_SUMUR

# Buat server MCP
mcp = FastMCP("lapangan-stdio")


@mcp.tool()
def hitung_water_cut(oil_bopd: float, water_bwpd: float) -> str:
    """
    Hitung water cut (persentase air dalam total cairan produksi) sebuah sumur.

    Args:
        oil_bopd: Produksi minyak dalam barel per hari (bopd)
        water_bwpd: Produksi air dalam barel per hari (bwpd)

    Returns:
        Water cut dalam persen beserta total cairan.
    """
    total = oil_bopd + water_bwpd
    if total <= 0:
        raise ValueError("Total produksi cairan harus lebih dari 0")
    return f"Water cut = {water_bwpd / total * 100:.1f}% (total cairan {total:.0f} bpd)"


@mcp.tool()
def konversi_satuan(nilai: float, dari: str, ke: str) -> str:
    """
    Konversi satuan volume (bbl dan m3) atau tekanan (psi dan bar).

    Args:
        nilai: Angka yang dikonversi
        dari: Satuan asal: 'bbl', 'm3', 'psi', atau 'bar'
        ke: Satuan tujuan: 'bbl', 'm3', 'psi', atau 'bar'

    Returns:
        Hasil konversi sebagai teks.
    """
    faktor = {("bbl", "m3"): 0.158987, ("m3", "bbl"): 1 / 0.158987, ("psi", "bar"): 0.0689476, ("bar", "psi"): 14.5038}
    dari, ke = dari.lower(), ke.lower()
    if dari == ke:
        return f"{nilai} {ke}"
    if (dari, ke) not in faktor:
        raise ValueError(f"Konversi {dari} ke {ke} tidak didukung (volume dan tekanan tidak dapat saling dikonversi)")
    return f"{nilai} {dari} = {nilai * faktor[(dari, ke)]:.3f} {ke}"


@mcp.tool()
def cek_status_sumur(kode_sumur: str) -> str:
    """
    Cek status operasi sebuah sumur: area, pompa, status, produksi, dan catatan terakhir.

    Args:
        kode_sumur: Kode sumur, contoh 'SR-020' atau 'KN-033'

    Returns:
        Ringkasan status sumur.
    """
    data = DATA_SUMUR.get(kode_sumur.strip().upper())
    if not data:
        return f"Sumur {kode_sumur} tidak ditemukan. Sumur yang terdaftar: {', '.join(DATA_SUMUR)}"
    return (f"Sumur {kode_sumur} ({data['area']}, {data['pompa']}): status {data['status']}, "
            f"minyak {data['minyak_bopd']} bopd, air {data['air_bwpd']} bwpd. Catatan: {data['catatan']}")


if __name__ == "__main__":
    # Log ke stderr (stdout dipakai untuk komunikasi MCP)
    print("Server MCP lapangan (stdio) berjalan...", file=sys.stderr)
    print("Tool: hitung_water_cut, konversi_satuan, cek_status_sumur", file=sys.stderr)

    # Jalankan dengan transport stdio
    mcp.run(transport="stdio")
