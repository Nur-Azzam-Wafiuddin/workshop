# %% [markdown]
# # Pembantu latihan bab bonus Agen SQL: database produksi harian
# Database kecil dan deterministik. File ini pustaka bantu: ia diimpor oleh `production_analyst.py` dan
# `conversational_analyst.py`. Menjalankannya langsung hanya mendefinisikan data dan fungsi `buat_database_produksi`.
#
# Tabel:
#
# - `Sumur` (SumurId, Kode, Area, JenisPompa)
# - `Produk` (ProdukId, Nama, HargaUSDPerBarel)
# - `ProduksiHarian` (ProduksiId, Tanggal, SumurId, ProdukId, Barel)
#
# Datanya dibuat dengan rumus tetap (tanpa angka acak), jadi setiap eksekusi menghasilkan angka yang sama.
# Itu memungkinkan kita memeriksa jawaban agen terhadap kebenaran yang dihitung sendiri.
# (Data fiktif untuk pelatihan.)

# %%
import sqlite3
from contextlib import closing
from pathlib import Path

SUMUR = [
    ("SR-020", "Seruni", "ESP"),
    ("SR-027", "Seruni", "ESP"),
    ("KN-033", "Kenanga", "SRP"),
    ("KN-041", "Kenanga", "SRP"),
    ("ML-012", "Melati", "ESP"),
    ("ML-015", "Melati", "PCP"),
]
PRODUK = [("Minyak", 70), ("Kondensat", 78), ("Air", 0)]
HARI = 14  # 2026-06-01 .. 2026-06-14


def buat_database_produksi(path: Path | str) -> Path:
    """Buat (atau timpa) file basis data dan kembalikan path-nya."""
    path = Path(path)
    path.unlink(missing_ok=True)

    with closing(sqlite3.connect(path)) as sambungan:
        sambungan.executescript(
            """
            CREATE TABLE Sumur         (SumurId INTEGER PRIMARY KEY, Kode TEXT, Area TEXT, JenisPompa TEXT);
            CREATE TABLE Produk        (ProdukId INTEGER PRIMARY KEY, Nama TEXT, HargaUSDPerBarel INTEGER);
            CREATE TABLE ProduksiHarian(ProduksiId INTEGER PRIMARY KEY, Tanggal TEXT,
                                        SumurId INTEGER, ProdukId INTEGER, Barel INTEGER);
            """
        )
        for sumur_id, (kode, area, pompa) in enumerate(SUMUR, start=1):
            sambungan.execute("INSERT INTO Sumur VALUES (?, ?, ?, ?)", (sumur_id, kode, area, pompa))
        for produk_id, (nama, harga) in enumerate(PRODUK, start=1):
            sambungan.execute("INSERT INTO Produk VALUES (?, ?, ?)", (produk_id, nama, harga))

        produksi_id = 1
        for hari in range(1, HARI + 1):
            for sumur_id in range(1, len(SUMUR) + 1):
                for produk_id in range(1, len(PRODUK) + 1):
                    barel = 100 + (sumur_id * 37 + produk_id * 61 + hari * 23) % 400
                    sambungan.execute(
                        "INSERT INTO ProduksiHarian VALUES (?, ?, ?, ?, ?)",
                        (produksi_id, f"2026-06-{hari:02d}", sumur_id, produk_id, barel),
                    )
                    produksi_id += 1
        sambungan.commit()
    return path
