"""Alat data migas untuk agen contoh mini project.

Data berasal dari folder data/ (fiktif), sama dengan yang dipakai di hari 1 dan 2:

  work order  : data/raw/work_orders.csv + data/eval/work_orders_truth.csv  (kolom terstruktur hasil ekstraksi)
  insiden HSE : data/raw/hse_incidents.csv + data/eval/hse_incidents_truth.csv
  produksi    : data/eval/daily_gs_sr1_2026-07.csv  (laporan harian GS-SR1, Juli 2026)

Ini KATALOG keping puzzle: tool untuk empat use case (Operasi, Perawatan, HSE, Engineering). Lihat KATALOG di
bagian bawah file, atau jalankan code/01_katalog_tool.py.

Tool BACA mengembalikan teks ringkas. Tool TULIS (nama-namanya di TULIS) hanya mencatat ke daftar CATATAN_TINDAKAN
di memori. Tidak ada sistem nyata yang diubah, sehingga aman dicoba. Agen yang memakai tool tulis sebaiknya dipasangi
persetujuan manusia (lihat solusi/agen_contoh/perawatan.py).
"""
from functools import lru_cache

import pandas as pd
from langchain.tools import tool

from migas_shared.config import DATA
from migas_shared.field_tools import DATA_SUMUR, cek_status_sumur, hitung_water_cut, konversi_satuan
from migas_shared.rag_tools import cari_dokumen

CATATAN_TINDAKAN: list[dict] = []


@lru_cache(maxsize=1)
def _work_order() -> pd.DataFrame:
    mentah = pd.read_csv(DATA / "raw" / "work_orders.csv")
    terstruktur = pd.read_csv(DATA / "eval" / "work_orders_truth.csv")
    return mentah.merge(terstruktur, on="wo_id").sort_values("tanggal", ascending=False)


@lru_cache(maxsize=1)
def _insiden() -> pd.DataFrame:
    mentah = pd.read_csv(DATA / "raw" / "hse_incidents.csv")
    terstruktur = pd.read_csv(DATA / "eval" / "hse_incidents_truth.csv")
    return mentah.merge(terstruktur, on="incident_id").sort_values("tanggal", ascending=False)


@lru_cache(maxsize=1)
def _harian() -> pd.DataFrame:
    return pd.read_csv(DATA / "eval" / "daily_gs_sr1_2026-07.csv")


# ---------------------------------------------------------------------------
# Pemeliharaan
# ---------------------------------------------------------------------------


@tool(parse_docstring=True)
def riwayat_work_order(asset_id: str, maks: int = 5) -> str:
    """Tampilkan riwayat work order sebuah aset: tanggal, kategori kegagalan, komponen, tindakan, dan downtime.

    Args:
        asset_id: Kode aset, contoh "SR-020" atau "V-SR1-101".
        maks: Jumlah work order terbaru yang ditampilkan (1 sampai 10).
    """
    baris = _work_order()
    baris = baris[baris["asset_id"].str.upper() == asset_id.strip().upper()]
    if baris.empty:
        return f"Tidak ada work order untuk aset {asset_id}."
    tampil = baris.head(max(1, min(maks, 10)))
    teks = [f"{asset_id.upper()}: {len(baris)} work order, total downtime {baris['downtime_hours'].sum():.1f} jam. Terbaru:"]
    for _, r in tampil.iterrows():
        teks.append(f"- {r['wo_id']} ({r['tanggal']}): {r['failure_category']}, komponen {r['component']}, "
                    f"tindakan {r['action_category']}, downtime {r['downtime_hours']} jam")
    return "\n".join(teks)


@tool(parse_docstring=True)
def statistik_kegagalan(tipe_peralatan: str | None = None) -> str:
    """Hitung jumlah work order dan total downtime per kategori kegagalan, untuk satu tipe peralatan atau semuanya.

    Args:
        tipe_peralatan: Salah satu dari ESP, SRP, PCP, Flowline, Separator, Steam Generator, Gas Compressor, Water Injection Pump. Kosongkan untuk semua.
    """
    baris = _work_order()
    if tipe_peralatan:
        baris = baris[baris["equipment_type"].str.lower() == tipe_peralatan.strip().lower()]
        if baris.empty:
            return f"Tipe peralatan {tipe_peralatan} tidak ditemukan."
    ringkas = (baris.groupby("failure_category")["downtime_hours"].agg(["count", "sum"])
               .sort_values("sum", ascending=False))
    judul = tipe_peralatan or "semua peralatan"
    teks = [f"Kegagalan {judul}: {len(baris)} work order, total downtime {baris['downtime_hours'].sum():.0f} jam."]
    for kategori, r in ringkas.iterrows():
        teks.append(f"- {kategori}: {int(r['count'])} work order, {r['sum']:.0f} jam")
    return "\n".join(teks)


@tool(parse_docstring=True)
def buat_work_order(asset_id: str, uraian: str, prioritas: str) -> str:
    """Buat work order pemeliharaan baru. TINDAKAN TULIS: perlu persetujuan manusia.

    Args:
        asset_id: Kode aset, contoh "V-SR1-101".
        uraian: Uraian pekerjaan yang diminta.
        prioritas: rendah, sedang, atau tinggi.
    """
    nomor = f"WO-UJI-{len(CATATAN_TINDAKAN) + 1:03d}"
    CATATAN_TINDAKAN.append({"nomor": nomor, "jenis": "work order", "asset_id": asset_id, "uraian": uraian, "prioritas": prioritas})
    return f"Work order {nomor} dibuat untuk {asset_id} (prioritas {prioritas})."


@tool(parse_docstring=True)
def aset_downtime_tertinggi(maks: int = 5) -> str:
    """Tampilkan aset dengan total downtime tertinggi dari seluruh work order, beserta jumlah work order dan tipe peralatannya.

    Args:
        maks: Jumlah aset teratas yang ditampilkan (1 sampai 10).
    """
    baris = _work_order()
    per_aset = (baris.groupby("asset_id").agg(jumlah=("wo_id", "count"), jam=("downtime_hours", "sum"),
                                              tipe=("equipment_type", "first"))
                .sort_values("jam", ascending=False).head(max(1, min(maks, 10))))
    teks = [f"{len(per_aset)} aset dengan downtime tertinggi:"]
    for aset, r in per_aset.iterrows():
        teks.append(f"- {aset} ({r['tipe']}): {r['jam']:.0f} jam dari {int(r['jumlah'])} work order")
    return "\n".join(teks)


@tool(parse_docstring=True)
def tutup_work_order(wo_id: str, catatan: str) -> str:
    """Tutup sebuah work order yang pekerjaannya selesai. TINDAKAN TULIS: perlu persetujuan manusia.

    Args:
        wo_id: Nomor work order yang ada di riwayat, contoh "WO-26-12115".
        catatan: Catatan penutupan, singkat dan faktual.
    """
    if _work_order()["wo_id"].str.upper().ne(wo_id.strip().upper()).all():
        return f"Work order {wo_id} tidak ditemukan, penutupan tidak dicatat."
    nomor = f"TUTUP-UJI-{len(CATATAN_TINDAKAN) + 1:03d}"
    CATATAN_TINDAKAN.append({"nomor": nomor, "jenis": "penutupan work order", "wo_id": wo_id.strip().upper(), "catatan": catatan})
    return f"Penutupan {wo_id.strip().upper()} dicatat sebagai {nomor}."


# ---------------------------------------------------------------------------
# HSE
# ---------------------------------------------------------------------------


@tool(parse_docstring=True)
def cari_insiden(lokasi: str | None = None, bahaya: str | None = None, tingkat: str | None = None, maks: int = 5) -> str:
    """Cari insiden HSE menurut lokasi, jenis bahaya, dan tingkat keparahan. Semua filter bersifat opsional.

    Args:
        lokasi: Sebagian nama lokasi, contoh "GS-SR1" atau "Workshop".
        bahaya: Jenis bahaya, contoh "H2S/Gas", "Hot Work/Fire", "Working at Height", "Dropped Object".
        tingkat: Tingkat keparahan: Rendah, Sedang, atau Tinggi.
        maks: Jumlah insiden terbaru yang ditampilkan (1 sampai 10).
    """
    baris = _insiden()
    if lokasi:
        baris = baris[baris["lokasi"].str.contains(lokasi.strip(), case=False, regex=False)]
    if bahaya:
        baris = baris[baris["hazard"].str.contains(bahaya.strip(), case=False, regex=False)]
    if tingkat:
        baris = baris[baris["severity"].str.lower() == tingkat.strip().lower()]
    if baris.empty:
        return "Tidak ada insiden yang cocok dengan filter tersebut."
    teks = [f"{len(baris)} insiden cocok. Terbaru:"]
    for _, r in baris.head(max(1, min(maks, 10))).iterrows():
        teks.append(f"- {r['incident_id']} ({r['tanggal']}, {r['lokasi']}): {r['incident_type']}, bahaya {r['hazard']}, "
                    f"tingkat {r['severity']}. {r['narasi'][:150]}")
    return "\n".join(teks)


@tool(parse_docstring=True)
def ringkasan_insiden() -> str:
    """Ringkas seluruh insiden HSE: jumlah per jenis bahaya, per tingkat keparahan, dan lokasi paling sering."""
    baris = _insiden()
    per_bahaya = baris["hazard"].value_counts()
    per_tingkat = baris["severity"].value_counts()
    lokasi = baris["lokasi"].value_counts().head(3)
    return (f"Total {len(baris)} insiden.\n"
            f"Per bahaya: " + ", ".join(f"{k} {v}" for k, v in per_bahaya.items()) + "\n"
            f"Per tingkat: " + ", ".join(f"{k} {v}" for k, v in per_tingkat.items()) + "\n"
            f"Lokasi terbanyak: " + ", ".join(f"{k} {v}" for k, v in lokasi.items()))


@tool(parse_docstring=True)
def usulkan_tindakan_korektif(incident_id: str, tindakan: str, penanggung_jawab: str) -> str:
    """Catat usulan tindakan korektif untuk sebuah insiden. TINDAKAN TULIS: perlu persetujuan manusia.

    Args:
        incident_id: Nomor insiden, contoh "HSE-26-0004".
        tindakan: Tindakan korektif yang diusulkan.
        penanggung_jawab: Jabatan penanggung jawab, contoh "Supervisor HSE".
    """
    nomor = f"CAPA-UJI-{len(CATATAN_TINDAKAN) + 1:03d}"
    CATATAN_TINDAKAN.append({"nomor": nomor, "jenis": "tindakan korektif", "incident_id": incident_id,
                             "tindakan": tindakan, "penanggung_jawab": penanggung_jawab})
    return f"Tindakan korektif {nomor} dicatat untuk {incident_id}, penanggung jawab {penanggung_jawab}."


@tool(parse_docstring=True)
def kirim_notifikasi_hse(penerima: str, pesan: str) -> str:
    """Kirim notifikasi HSE kepada seorang penerima atau satu kelompok. TINDAKAN TULIS: perlu persetujuan manusia, karena pesan yang terkirim tidak bisa ditarik.

    Args:
        penerima: Jabatan atau kelompok penerima, contoh "Supervisor HSE" atau "Seluruh crew GS-SR1".
        pesan: Isi notifikasi, singkat dan faktual.
    """
    nomor = f"NOTIF-UJI-{len(CATATAN_TINDAKAN) + 1:03d}"
    CATATAN_TINDAKAN.append({"nomor": nomor, "jenis": "notifikasi HSE", "penerima": penerima, "pesan": pesan})
    return f"Notifikasi {nomor} dikirim ke {penerima}."


# ---------------------------------------------------------------------------
# Operasi
# ---------------------------------------------------------------------------


@tool(parse_docstring=True)
def laporan_harian(tanggal: str) -> str:
    """Tampilkan laporan produksi harian GS-SR1: minyak, air, gas, jumlah sumur aktif, deferred, dan kejadian.

    Args:
        tanggal: Tanggal format YYYY-MM-DD pada Juli 2026, contoh "2026-07-14".
    """
    baris = _harian()
    baris = baris[baris["tanggal"] == tanggal.strip()]
    if baris.empty:
        return f"Tidak ada laporan untuk tanggal {tanggal}. Data tersedia 2026-07-01 sampai 2026-07-31."
    r = baris.iloc[0]
    kejadian = r["event"] if isinstance(r["event"], str) else "tidak ada kejadian khusus"
    return (f"GS-SR1 {r['tanggal']}: minyak {r['oil_bopd']} bopd, air {r['water_bwpd']} bwpd, gas {r['gas_mmscfd']} MMscfd, "
            f"{r['wells_on']} sumur aktif, deferred {r['deferred_bbl']} bbl. Kejadian: {kejadian}.")


@tool(parse_docstring=True)
def ringkasan_produksi_bulanan() -> str:
    """Ringkas produksi GS-SR1 selama Juli 2026: rata-rata minyak dan air, water cut, total deferred, dan hari berkejadian."""
    d = _harian()
    minyak, air = d["oil_bopd"].mean(), d["water_bwpd"].mean()
    kejadian = d[d["event"].notna()]
    terendah = d.loc[d["oil_bopd"].idxmin()]
    return (f"GS-SR1 Juli 2026 ({len(d)} hari): rata-rata minyak {minyak:.0f} bopd, air {air:.0f} bwpd, "
            f"water cut {air / (minyak + air) * 100:.1f}%. Total deferred {d['deferred_bbl'].sum()} bbl. "
            f"{len(kejadian)} hari memiliki kejadian. Minyak terendah {terendah['oil_bopd']} bopd pada {terendah['tanggal']}.")


@tool(parse_docstring=True)
def catat_serah_terima(catatan: str) -> str:
    """Simpan catatan serah terima shift. TINDAKAN TULIS: perlu persetujuan manusia.

    Args:
        catatan: Isi catatan serah terima, singkat dan faktual.
    """
    nomor = f"SHIFT-UJI-{len(CATATAN_TINDAKAN) + 1:03d}"
    CATATAN_TINDAKAN.append({"nomor": nomor, "jenis": "serah terima", "catatan": catatan})
    return f"Catatan serah terima {nomor} disimpan."


@tool(parse_docstring=True)
def bandingkan_produksi(tanggal_a: str, tanggal_b: str) -> str:
    """Bandingkan laporan produksi harian GS-SR1 pada dua tanggal: selisih minyak, air, gas, dan deferred (tanggal_b dikurangi tanggal_a).

    Args:
        tanggal_a: Tanggal pembanding format YYYY-MM-DD pada Juli 2026, contoh "2026-07-10".
        tanggal_b: Tanggal yang dibandingkan format YYYY-MM-DD pada Juli 2026, contoh "2026-07-14".
    """
    d = _harian().set_index("tanggal")
    hilang = [t for t in (tanggal_a.strip(), tanggal_b.strip()) if t not in d.index]
    if hilang:
        return f"Tidak ada laporan untuk tanggal {', '.join(hilang)}. Data tersedia 2026-07-01 sampai 2026-07-31."
    a, b = d.loc[tanggal_a.strip()], d.loc[tanggal_b.strip()]
    return (f"{tanggal_b.strip()} dibanding {tanggal_a.strip()}: minyak {b['oil_bopd'] - a['oil_bopd']:+.0f} bopd "
            f"({a['oil_bopd']} -> {b['oil_bopd']}), air {b['water_bwpd'] - a['water_bwpd']:+.0f} bwpd, "
            f"gas {b['gas_mmscfd'] - a['gas_mmscfd']:+.2f} MMscfd, deferred {b['deferred_bbl'] - a['deferred_bbl']:+.0f} bbl.")


@tool(parse_docstring=True)
def hari_berkejadian(maks: int = 10) -> str:
    """Daftar hari pada Juli 2026 yang punya kejadian khusus di laporan harian GS-SR1, beserta deferred produksinya.

    Args:
        maks: Jumlah hari yang ditampilkan (1 sampai 15).
    """
    baris = _harian().dropna(subset=["event"])
    if baris.empty:
        return "Tidak ada hari berkejadian pada Juli 2026."
    teks = [f"{len(baris)} hari berkejadian. Ditampilkan {min(len(baris), max(1, min(maks, 15)))} pertama:"]
    for _, r in baris.head(max(1, min(maks, 15))).iterrows():
        teks.append(f"- {r['tanggal']}: {r['event'][:110]} (deferred {r['deferred_bbl']} bbl)")
    return "\n".join(teks)


# ---------------------------------------------------------------------------
# Engineering
# ---------------------------------------------------------------------------


@tool(parse_docstring=True)
def ubah_setpoint_vsd(kode_sumur: str, frekuensi_hz: int) -> str:
    """Ubah frekuensi VSD (setpoint) pompa ESP sebuah sumur. TINDAKAN TULIS: perlu persetujuan manusia, karena salah setpoint dapat merusak pompa atau mengganggu produksi.

    Args:
        kode_sumur: Kode sumur ESP, contoh "SR-020".
        frekuensi_hz: Frekuensi baru dalam Hz, contoh 48.
    """
    kode = kode_sumur.strip().upper()
    if kode not in DATA_SUMUR:
        return f"Sumur {kode_sumur} tidak ditemukan. Sumur yang terdaftar: {', '.join(DATA_SUMUR)}"
    nomor = f"VSD-UJI-{len(CATATAN_TINDAKAN) + 1:03d}"
    CATATAN_TINDAKAN.append({"nomor": nomor, "jenis": "setpoint VSD", "kode_sumur": kode, "frekuensi_hz": frekuensi_hz})
    peringatan = " PERINGATAN: di atas 55 Hz memerlukan persetujuan Production Engineer." if frekuensi_hz > 55 else ""
    return f"Setpoint VSD {kode} dicatat {frekuensi_hz} Hz ({nomor}).{peringatan}"


# ---------------------------------------------------------------------------
# Katalog keping puzzle
# ---------------------------------------------------------------------------

# Nama tool yang mengubah sesuatu. Semuanya hanya mencatat ke CATATAN_TINDAKAN, tetapi di sistem nyata
# tool seperti ini harus lewat persetujuan manusia (interrupt).
TULIS = {"buat_work_order", "tutup_work_order", "usulkan_tindakan_korektif", "kirim_notifikasi_hse",
         "catat_serah_terima", "ubah_setpoint_vsd"}

KATALOG: dict[str, list] = {
    "Operasi": [laporan_harian, ringkasan_produksi_bulanan, bandingkan_produksi, hari_berkejadian,
                cek_status_sumur, hitung_water_cut, catat_serah_terima],
    "Perawatan": [riwayat_work_order, statistik_kegagalan, aset_downtime_tertinggi, cari_dokumen,
                  buat_work_order, tutup_work_order],
    "HSE": [cari_insiden, ringkasan_insiden, cari_dokumen, usulkan_tindakan_korektif, kirim_notifikasi_hse],
    "Engineering": [cari_dokumen, konversi_satuan, hitung_water_cut, cek_status_sumur, ubah_setpoint_vsd],
}


def jenis_tool(t) -> str:
    """'tulis' untuk tool yang mengubah sesuatu (perlu interrupt), 'baca' untuk lainnya."""
    return "tulis" if t.name in TULIS else "baca"
