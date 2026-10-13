"""Tool lapangan sederhana dari bab 2, tersedia di paket bersama agar bab 3 dan seterusnya dapat memakainya.

- hitung_water_cut : menghitung water cut dari produksi minyak (bopd) dan air (bwpd)
- konversi_satuan  : konversi bbl <-> m3 dan psi <-> bar
- cek_status_sumur : status sumur dari dictionary DATA_SUMUR (fiktif)

Definisinya sama dengan yang Anda tulis sendiri di bab 2. DATA_SUMUR menggantikan database atau SCADA.
"""
from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field

DATA_SUMUR = {
    "SR-020": {"area": "Seruni", "pompa": "ESP", "status": "Produksi", "minyak_bopd": 120, "air_bwpd": 480,
               "catatan": "ESP trip overload kemarin sore, stabil sejak pukul 18.00"},
    "SR-027": {"area": "Seruni", "pompa": "ESP", "status": "Produksi", "minyak_bopd": 95, "air_bwpd": 380,
               "catatan": "Pembacaan H2S 12 ppm pada 22 Juli 2026, dalam investigasi HSE"},
    "KN-033": {"area": "Kenanga", "pompa": "SRP", "status": "Menunggu pulling", "minyak_bopd": 0, "air_bwpd": 0,
               "catatan": "Sucker rod patah, menunggu jadwal rig"},
    "ML-012": {"area": "Melati", "pompa": "ESP", "status": "Produksi", "minyak_bopd": 85, "air_bwpd": 340,
               "catatan": "Normal"},
}


class WaterCutInput(BaseModel):
    """Skema masukan tool water cut."""
    oil_bopd: float = Field(ge=0, description="Produksi minyak dalam barel per hari (bopd), contoh 120")
    water_bwpd: float = Field(ge=0, description="Produksi air dalam barel per hari (bwpd), contoh 480")


class KonversiInput(BaseModel):
    """Skema masukan tool konversi satuan."""
    nilai: float = Field(description="Angka yang dikonversi")
    dari: Literal["bbl", "m3", "psi", "bar"] = Field(description="Satuan asal")
    ke: Literal["bbl", "m3", "psi", "bar"] = Field(description="Satuan tujuan")


class StatusSumurInput(BaseModel):
    """Skema masukan tool status sumur."""
    kode_sumur: str = Field(description="Kode sumur, contoh SR-020 atau KN-033")


@tool(args_schema=WaterCutInput)
def hitung_water_cut(oil_bopd: float, water_bwpd: float) -> str:
    """Hitung water cut (persentase air dalam total cairan produksi) sebuah sumur.
    Pakai tool ini bila perlu mengetahui water cut dari angka produksi minyak dan air."""
    total = oil_bopd + water_bwpd
    if total == 0:
        return "Tidak dapat dihitung: total produksi cairan adalah 0."
    return f"Water cut = {water_bwpd / total * 100:.1f}% (total cairan {total:.0f} bpd)"


@tool(args_schema=KonversiInput)
def konversi_satuan(nilai: float, dari: str, ke: str) -> str:
    """Konversi satuan volume (bbl dan m3) atau tekanan (psi dan bar)."""
    faktor = {("bbl", "m3"): 0.158987, ("m3", "bbl"): 1 / 0.158987, ("psi", "bar"): 0.0689476, ("bar", "psi"): 14.5038}
    if dari == ke:
        return f"{nilai} {ke}"
    if (dari, ke) not in faktor:
        return f"Konversi {dari} ke {ke} tidak didukung (volume dan tekanan tidak dapat saling dikonversi)."
    return f"{nilai} {dari} = {nilai * faktor[(dari, ke)]:.3f} {ke}"


@tool(args_schema=StatusSumurInput)
def cek_status_sumur(kode_sumur: str) -> str:
    """Cek status operasi sebuah sumur: area, jenis pompa, status, produksi minyak dan air, serta catatan terakhir."""
    data = DATA_SUMUR.get(kode_sumur.strip().upper())
    if not data:
        return f"Sumur {kode_sumur} tidak ditemukan. Sumur yang terdaftar: {', '.join(DATA_SUMUR)}"
    return (f"Sumur {kode_sumur} ({data['area']}, {data['pompa']}): status {data['status']}, "
            f"minyak {data['minyak_bopd']} bopd, air {data['air_bwpd']} bwpd. Catatan: {data['catatan']}")


TOOL_LAPANGAN = [hitung_water_cut, konversi_satuan, cek_status_sumur]
