"""Pencarian dokumen workshop dibungkus sebagai tool LangChain.

Aturan penting: peran pengguna (role) TIDAK pernah menjadi argumen yang diisi model. Role dibaca dari
`runtime.context` (KonteksPengguna) yang dikirim program Anda lewat `agent.invoke(..., context=...)`.
Model tidak melihat dan tidak dapat mengubahnya.

Setiap tool memiliki fungsi biasa di belakangnya (`_cari`, `_daftar`, `_jawab`, `_ingest`) sehingga logika
dapat diuji tanpa model. Docstring tool ditulis dalam Bahasa Indonesia karena model membacanya untuk
memutuskan kapan dan bagaimana tool dipakai.

Catatan: file ini sengaja TIDAK memakai `from __future__ import annotations` agar anotasi
`ToolRuntime[KonteksPengguna]` terbaca benar oleh LangChain.
"""
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from langchain.tools import ToolRuntime, tool

from migas_shared import rag_pipeline as rp

Peran = Literal["operator", "engineer", "hse", "management"]

PESAN_KOSONG = "Tidak ada dokumen yang relevan untuk peran Anda."


@dataclass
class KonteksPengguna:
    """Fakta tepercaya tentang pengguna. Dikirim program, bukan oleh model."""

    role: Peran = "engineer"
    area: str = "Seruni"
    user_id: str = "anon"


# ---------------------------------------------------------------------------
# Retriever tunggal (index tidak dibangun ulang pada setiap panggilan)
# ---------------------------------------------------------------------------

_retriever: rp.HybridRetriever | None = None
_lock = threading.Lock()


def build_retriever(rebuild: bool = False) -> rp.HybridRetriever:
    """Kembalikan HybridRetriever bersama. Index Chroma dibangun pada panggilan pertama (disimpan di chroma_db/)."""
    global _retriever
    with _lock:
        if _retriever is None or rebuild:
            _retriever = rp.load_retriever(rebuild=rebuild)
        return _retriever


@contextmanager
def sandbox_knowledge():
    """Basis pengetahuan sementara untuk latihan tindakan TULIS (misalnya mengunggah revisi SOP).

    Selama blok `with`, index Chroma, folder unggahan, dan file override status berada di folder sementara,
    sehingga data/ dan chroma_db/ yang asli tidak berubah. Setelah blok selesai, semuanya dikembalikan.
    Dokumen dasar tetap dibaca dari data/docs. Menghasilkan retriever sandbox.
    """
    global _retriever
    nama = ("ROOT", "DOCS_DIR", "UPLOAD_DIR", "STATUS_OVERRIDES", "CHROMA_DIR")
    asli = {n: getattr(rp, n) for n in nama}
    retriever_asli = _retriever
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        folder = Path(tmp)
        rp.ROOT = folder
        rp.DOCS_DIR = folder / "docs"
        rp.UPLOAD_DIR = rp.DOCS_DIR / "uploads"
        rp.STATUS_OVERRIDES = rp.UPLOAD_DIR / "_status_overrides.json"
        rp.CHROMA_DIR = folder / "chroma_db"
        with _lock:
            _retriever = None
        try:
            yield build_retriever()
        finally:
            for n, nilai in asli.items():
                setattr(rp, n, nilai)
            with _lock:
                _retriever = retriever_asli


# ---------------------------------------------------------------------------
# Logika (tanpa LangChain, bisa diuji langsung)
# ---------------------------------------------------------------------------


def _cari(query: str, k: int, role: str) -> str:
    docs = build_retriever().search(query, k=k, mode="hybrid", role=role, active_only=True)
    return rp.format_context(docs) if docs else PESAN_KOSONG


def _daftar(jenis: str | None, role: str) -> str:
    izin = rp.ROLE_GROUPS[role]
    baris: dict[tuple[str, str], str] = {}
    for c in build_retriever().chunks:
        m = c.metadata
        if m.get("status") != "active" or m.get("access_group") not in izin:
            continue
        if jenis and str(m.get("doc_type", "")).lower() != jenis.lower():
            continue
        baris[(m["doc_id"], str(m.get("revision")))] = (
            f"- {m['doc_id']} (Rev {m.get('revision')}, {m.get('doc_type')}): {m.get('title')}")
    if not baris:
        return PESAN_KOSONG
    return "\n".join(baris[key] for key in sorted(baris))


def _jawab(pertanyaan: str, role: str) -> str:
    hasil = rp.answer(pertanyaan, build_retriever(), role=role, log=True)
    sitasi = ", ".join(hasil["cited_doc_ids"]) or "-"
    peringatan = f"\nSitasi tidak valid: {hasil['invalid_citations']}" if hasil["invalid_citations"] else ""
    return f"{hasil['answer']}\n\nDokumen yang dikutip: {sitasi}{peringatan}"


def _ingest(nama_file: str, isi: str, metadata: dict, role: str) -> str:
    laporan = rp.ingest_document(build_retriever(), nama_file, isi.encode("utf-8"), metadata, uploader_role=role)
    status = "BERHASIL" if laporan["ok"] else "DITOLAK"
    return f"{status}: {laporan['pesan']}"


# ---------------------------------------------------------------------------
# Tool untuk agen
# ---------------------------------------------------------------------------


@tool(parse_docstring=True)
def cari_dokumen(query: str, runtime: ToolRuntime[KonteksPengguna], k: int = 5) -> str:
    """Cari chunk dokumen SOP, manual, laporan dan investigasi yang berstatus aktif.

    Hasil berupa blok <dokumen id=... revisi=... status=... bagian=...> yang dapat dikutip sebagai
    [DOC_ID bagian]. Hanya dokumen yang boleh dilihat peran pengguna yang dikembalikan. Pakai tool ini untuk
    pertanyaan tentang prosedur, batas alarm, langkah kerja, kode alarm perangkat, atau isi laporan.

    Args:
        query: Kalimat pencarian dengan istilah teknis, misalnya "alarm H2S 10 ppm tindakan".
        k: Jumlah chunk dokumen yang dikembalikan (1 sampai 10).
    """
    return _cari(query, max(1, min(k, 10)), runtime.context.role)


@tool(parse_docstring=True)
def jawab_dari_dokumen(pertanyaan: str, runtime: ToolRuntime[KonteksPengguna]) -> str:
    """Jawab pertanyaan langsung dari dokumen dengan sitasi, memakai pipeline RAG siap pakai.

    Jika dokumen tidak memuat jawabannya, hasilnya adalah penolakan baku. Jawaban disertai daftar
    dokumen yang dikutip.

    Args:
        pertanyaan: Pertanyaan lengkap dalam Bahasa Indonesia.
    """
    return _jawab(pertanyaan, runtime.context.role)


@tool(parse_docstring=True)
def daftar_dokumen_aktif(runtime: ToolRuntime[KonteksPengguna], jenis: str | None = None) -> str:
    """Tampilkan daftar dokumen aktif yang boleh dilihat pengguna (ID, revisi, jenis dan judul).

    Berguna untuk memilih dokumen sebelum mencari isinya.

    Args:
        jenis: Filter jenis dokumen, misalnya "sop", "manual", "laporan" atau "investigasi". Kosongkan untuk semua.
    """
    return _daftar(jenis, runtime.context.role)


@tool(parse_docstring=True)
def ingest_dokumen(nama_file: str, isi: str, metadata: dict[str, str], runtime: ToolRuntime[KonteksPengguna]) -> str:
    """Tambahkan dokumen baru ke basis pengetahuan bersama. TINDAKAN TULIS: wajib disetujui manusia.

    Dokumen melewati quality gate: peran pengunggah, metadata wajib, format, panjang teks, duplikat dan
    nomor revisi. Revisi lama dengan doc_id yang sama otomatis menjadi superseded.

    Args:
        nama_file: Nama file dengan ekstensi .md atau .txt, misalnya "SOP-OPS-030_rev1.md".
        isi: Teks lengkap dokumen.
        metadata: Kunci wajib: doc_id, title, doc_type, revision, status, owner, access_group (all, hse atau management).
    """
    return _ingest(nama_file, isi, metadata, runtime.context.role)


SEMUA_TOOL = [cari_dokumen, jawab_dari_dokumen, daftar_dokumen_aktif, ingest_dokumen]
