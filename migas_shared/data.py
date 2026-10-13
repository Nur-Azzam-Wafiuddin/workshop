"""Model data dan basis data SQLite untuk bab 1, 4, 6, bonus Agen SQL.

- WOExtract            : skema ekstraksi work order (diadaptasi dari workshop hari 1)
- KlasifikasiInsiden   : skema klasifikasi laporan insiden HSE
- buat_database_migas  : membangun migas.db dari file CSV (deterministik)
- read_only_connection : koneksi SQLite yang menolak penulisan
"""
from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Iterator, Literal

import pandas as pd
from pydantic import BaseModel, Field, field_validator

from migas_shared.config import DATA, OUTPUTS

# ---------------------------------------------------------------------------
# Skema Pydantic
# ---------------------------------------------------------------------------

EquipmentType = Literal["ESP", "SRP", "PCP", "Steam Generator", "Flowline", "Separator",
                        "Gas Compressor", "Water Injection Pump"]
FailureCategory = Literal["Electrical", "Mechanical", "Leak/Corrosion", "Flow Assurance",
                          "Instrumentation/Control", "Process/Trip", "Preventive Maintenance"]
ActionCategory = Literal["Replace", "Repair", "Clean/Flush", "Adjust/Reset", "Workover"]

IncidentType = Literal["Near Miss", "First Aid Case", "Medical Treatment Case", "Lost Time Injury",
                       "Property Damage", "Environmental Spill"]
Hazard = Literal["Steam/Hot Surface", "Dropped Object", "Working at Height", "Vehicle/Driving", "Hot Work/Fire",
                 "Electrical", "H2S/Gas", "Spill/Release", "Pinch Point", "Manual Handling"]
Severity = Literal["Rendah", "Sedang", "Tinggi"]


class WOExtract(BaseModel):
    """Data terstruktur dari satu catatan work order lapangan (teks bebas)."""

    asset_id: str = Field(description="Kode aset yang disebut pada catatan, huruf kapital, contoh SR-020")
    equipment_type: EquipmentType = Field(description="Jenis peralatan")
    failure_category: FailureCategory = Field(description="Kategori kegagalan")
    component: str = Field(description="Komponen utama yang rusak atau dikerjakan, 1 sampai 3 kata Bahasa Inggris")
    action_category: ActionCategory = Field(description="Tindakan perbaikan")
    downtime_hours: float = Field(ge=0, le=24 * 30, description="Lama unit berhenti dalam jam")
    safety_flag: bool = Field(description="True jika ada kebocoran fluida/gas/uap atau risiko keselamatan lain")

    @field_validator("asset_id")
    @classmethod
    def kapital(cls, v: str) -> str:
        return v.strip().upper()


class KlasifikasiInsiden(BaseModel):
    """Klasifikasi satu laporan insiden HSE dari narasi bebas."""

    incident_type: IncidentType = Field(description="Jenis insiden berdasarkan dampak yang terjadi")
    hazard: Hazard = Field(description="Bahaya utama yang menyebabkan insiden")
    severity: Severity = Field(description="Tingkat keparahan: Rendah, Sedang atau Tinggi")
    ringkasan: str = Field(description="Ringkasan satu kalimat, maksimal 25 kata, Bahasa Indonesia")


# ---------------------------------------------------------------------------
# Database migas.db
# ---------------------------------------------------------------------------

DB_DEFAULT = OUTPUTS / "migas.db"

_SKEMA = """
CREATE TABLE work_order (
    wo_id            TEXT PRIMARY KEY,
    tanggal          TEXT NOT NULL,     -- format YYYY-MM-DD
    area             TEXT NOT NULL,     -- Seruni, Kenanga atau Melati
    dilaporkan_oleh  TEXT,
    deskripsi        TEXT,              -- catatan asli teks bebas
    asset_id         TEXT NOT NULL,
    equipment_type   TEXT NOT NULL,
    failure_category TEXT NOT NULL,
    component        TEXT,
    action_category  TEXT NOT NULL,
    downtime_hours   REAL NOT NULL,
    safety_flag      INTEGER NOT NULL   -- 1 = ada risiko keselamatan
);
CREATE TABLE insiden_hse (
    incident_id   TEXT PRIMARY KEY,
    tanggal       TEXT NOT NULL,        -- format YYYY-MM-DD
    lokasi        TEXT NOT NULL,
    narasi        TEXT,                 -- laporan asli teks bebas
    incident_type TEXT NOT NULL,
    hazard        TEXT NOT NULL,
    severity      TEXT NOT NULL
);
"""


def buat_database_migas(path: str | Path | None = None) -> Path:
    """Bangun basis data SQLite `migas.db` dari CSV mentah dan CSV acuan di folder data/.

    Isi tabel selalu sama (baris diurutkan, file lama ditimpa), sehingga hasil query bab bonus Agen SQL dapat diulang.
    Tabel: work_order (400 baris), insiden_hse (120 baris).
    """
    path = Path(path) if path else DB_DEFAULT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)

    wo = pd.read_csv(DATA / "raw" / "work_orders.csv").merge(
        pd.read_csv(DATA / "eval" / "work_orders_truth.csv"), on="wo_id", validate="one_to_one")
    wo["safety_flag"] = wo["safety_flag"].astype(bool).astype(int)
    wo = wo.sort_values("wo_id")[["wo_id", "tanggal", "area", "dilaporkan_oleh", "deskripsi", "asset_id",
                                  "equipment_type", "failure_category", "component", "action_category",
                                  "downtime_hours", "safety_flag"]]

    ins = pd.read_csv(DATA / "raw" / "hse_incidents.csv").merge(
        pd.read_csv(DATA / "eval" / "hse_incidents_truth.csv"), on="incident_id", validate="one_to_one")
    ins = ins.sort_values("incident_id")[["incident_id", "tanggal", "lokasi", "narasi", "incident_type",
                                          "hazard", "severity"]]

    with closing(sqlite3.connect(path)) as conn:
        conn.executescript(_SKEMA)
        wo.to_sql("work_order", conn, if_exists="append", index=False)
        ins.to_sql("insiden_hse", conn, if_exists="append", index=False)
        conn.commit()
    return path


@contextmanager
def read_only_connection(path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Buka koneksi SQLite hanya-baca. Perintah INSERT/UPDATE/DELETE/DROP ditolak oleh SQLite sendiri.

    Koneksi ditutup otomatis di akhir blok `with` (penting di Windows agar file tidak terkunci).
    """
    path = Path(path) if path else DB_DEFAULT
    conn = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        yield conn
    finally:
        conn.close()
