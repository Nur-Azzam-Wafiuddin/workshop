"""
Modul bantu bab bonus Agen SQL: tool SQL yang aman untuk agen.

Dipakai oleh Contoh 2-5 dan solusi latihan. Contoh 1 mendefinisikan tool-nya langsung di file contoh
agar Anda melihat rancangannya berkembang; file inilah tempat rancangan itu berakhir.

Modul ini menyediakan tiga tool dan lapisan perlindungan di sekelilingnya:

  daftar_tabel     : tabel apa saja yang ada
  deskripsikan_tabel : kolom + beberapa baris contoh dari satu tabel
  jalankan_query   : jalankan SATU SELECT hanya-baca, dengan batas baris

  Lapis 1  validasi_query()       : pemeriksaan teks (hanya SELECT, satu pernyataan, tanpa kata kunci tulis)
  Lapis 2  koneksi hanya-baca     : SQLite sendiri menolak penulisan (perlindungan yang sebenarnya)
  Lapis 3  batas baris            : tidak pernah mengirim lebih dari MAKS_BARIS baris ke model
  Lapis 4  timeout query      : query yang lepas kendali dihentikan setelah beberapa detik

`bangun_alat_sql(db_path)` membuat ketiga tool untuk SEMBARANG file SQLite. Tool tingkat modul
`daftar_tabel`, `deskripsikan_tabel`, dan `jalankan_query` adalah tool yang sama untuk basis data `migas.db`
(work order dan insiden HSE), yang dibangun dari data pelatihan oleh `buat_database_migas()`.
"""

import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from langchain_core.tools import tool

from migas_shared.data import DB_DEFAULT, buat_database_migas

DB_PATH = DB_DEFAULT
MAKS_BARIS = 50
BATAS_WAKTU_QUERY_DETIK = 5

KATA_KUNCI_TERLARANG = {
    "insert", "update", "delete", "drop", "alter", "create", "attach",
    "detach", "pragma", "vacuum", "reindex", "truncate", "grant", "revoke",
}


def pastikan_database(db_path: Path | str = DB_PATH) -> Path:
    """Bangun migas.db bila belum ada (isinya selalu sama karena dibangun deterministik dari CSV)."""
    db_path = Path(db_path)
    if not db_path.exists():
        buat_database_migas(db_path)
    return db_path


def koneksi_hanya_baca_dengan_batas(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Buka basis data dalam mode hanya-baca (penulisan menimbulkan error) dengan batas waktu query."""
    sambungan = sqlite3.connect(f"file:{Path(db_path).resolve().as_posix()}?mode=ro", uri=True)
    mulai = time.time()

    def lewat_batas_waktu() -> bool:
        return time.time() - mulai > BATAS_WAKTU_QUERY_DETIK

    # SQLite memanggil ini setiap 100.000 langkah; mengembalikan True menghentikan query yang sedang berjalan
    sambungan.set_progress_handler(lewat_batas_waktu, 100_000)
    return sambungan


@contextmanager
def koneksi_hanya_baca(db_path: Path | str = DB_PATH):
    """Buka koneksi hanya-baca dan SELALU menutupnya setelah selesai.

    (`with sqlite3.connect(...)` biasa hanya melakukan commit, tidak menutup koneksi; file bisa tetap
    terkunci, misalnya saat Anda menghapusnya di Windows.)
    """
    sambungan = koneksi_hanya_baca_dengan_batas(db_path)
    try:
        yield sambungan
    finally:
        sambungan.close()


def validasi_query(sql: str) -> str | None:
    """Lapis 1: pemeriksaan teks murah. Mengembalikan pesan error, atau None bila query tampak aman."""
    bersih = sql.strip().rstrip(";").strip()
    if not bersih:
        return "Query kosong."
    if ";" in bersih:
        return "Hanya satu pernyataan SQL yang diizinkan."
    huruf_kecil = bersih.lower()
    if not (huruf_kecil.startswith("select") or huruf_kecil.startswith("with")):
        return "Hanya query SELECT yang diizinkan."
    terlarang = KATA_KUNCI_TERLARANG & set(re.findall(r"[a-z_]+", huruf_kecil))
    if terlarang:
        return f"Kata kunci terlarang: {', '.join(sorted(terlarang))}."
    return None


def nama_tabel(db_path: Path | str = DB_PATH) -> list[str]:
    with koneksi_hanya_baca(db_path) as sambungan:
        baris = sambungan.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return [b[0] for b in baris]


def format_baris(kolom: list[str], baris: list[tuple]) -> str:
    """Format baris sebagai tabel sederhana berpemisah | yang mudah dibaca model."""
    teks = [" | ".join(kolom)]
    teks += [" | ".join("NULL" if nilai is None else str(nilai) for nilai in b) for b in baris]
    return "\n".join(teks)


def bangun_alat_sql(db_path: Path | str):
    """Buat tool (daftar_tabel, deskripsikan_tabel, jalankan_query) untuk satu file basis data SQLite."""

    @tool
    def daftar_tabel() -> str:
        """Daftar semua tabel di basis data. Panggil ini lebih dulu untuk melihat data apa yang tersedia."""
        return "Tabel: " + ", ".join(nama_tabel(db_path))

    @tool
    def deskripsikan_tabel(tabel: str) -> str:
        """Tampilkan kolom sebuah tabel dan 3 baris contoh. Pakai sebelum menulis query.

        Args:
            tabel: Nama tabel persis seperti yang dikembalikan daftar_tabel
        """
        nama = nama_tabel(db_path)
        cocok = next((n for n in nama if n.lower() == tabel.lower()), None)
        if cocok is None:
            return f"Tabel '{tabel}' tidak dikenal. Tabel yang tersedia: {', '.join(nama)}"

        with koneksi_hanya_baca(db_path) as sambungan:
            kolom = sambungan.execute(f'PRAGMA table_info("{cocok}")').fetchall()
            contoh = sambungan.execute(f'SELECT * FROM "{cocok}" LIMIT 3').fetchall()
        baris_kolom = "\n".join(f"  - {k[1]} ({k[2]})" for k in kolom)
        teks_contoh = format_baris([k[1] for k in kolom], contoh)
        return f"Tabel {cocok}\nKolom:\n{baris_kolom}\n\nBaris contoh:\n{teks_contoh}"

    @tool
    def jalankan_query(sql: str) -> str:
        """Jalankan SATU query SQL SELECT hanya-baca dan kembalikan barisnya. Dialek SQLite.
        Jika query gagal, baca error-nya, periksa skema dengan deskripsikan_tabel, lalu perbaiki.

        Args:
            sql: Satu pernyataan SELECT
        """
        masalah = validasi_query(sql)
        if masalah:
            return f"Query ditolak: {masalah}"

        try:
            with koneksi_hanya_baca(db_path) as sambungan:
                kursor = sambungan.execute(sql)
                kolom = [d[0] for d in kursor.description or []]
                baris = kursor.fetchmany(MAKS_BARIS + 1)
        except sqlite3.Error as error:
            return f"Error SQL: {error}. Periksa nama tabel dan kolom dengan deskripsikan_tabel."

        terpotong = len(baris) > MAKS_BARIS
        baris = baris[:MAKS_BARIS]
        if not baris:
            return "Query berhasil dijalankan tetapi tidak mengembalikan baris."
        hasil = format_baris(kolom, baris)
        if terpotong:
            hasil += f"\n(Hanya {MAKS_BARIS} baris pertama yang ditampilkan. Tambahkan LIMIT atau agregasi.)"
        return hasil

    return daftar_tabel, deskripsikan_tabel, jalankan_query


# Tool yang sama, siap dipakai dengan database migas.db
daftar_tabel, deskripsikan_tabel, jalankan_query = bangun_alat_sql(pastikan_database(DB_PATH))


PROMPT_SISTEM_SQL = (
    "Anda analis data yang cermat untuk basis data SQLite operasi migas. "
    "SELALU mulai dengan daftar_tabel, lalu deskripsikan_tabel untuk tabel yang Anda perlukan, dan baru "
    "setelah itu tulis query. Tulis satu SELECT setiap kali. Jika query gagal, baca error-nya dan perbaiki. "
    "Jangan pernah mengarang data: jawab hanya dari hasil query. Jawab singkat dalam Bahasa Indonesia."
)
