"""Konfigurasi terpusat. Semua nilai dibaca dari file .env di root repo."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# migas_shared/config.py -> root repo adalah satu tingkat di atas folder paket
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
CACHE = ROOT / ".cache"

load_dotenv(ROOT / ".env")


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


# Penyedia LLM (endpoint kompatibel OpenAI). Memakai variabel .env yang sama dengan hari 1 dan 2.
# Dibaca saat dipakai agar pesan error jelas.
def ai_settings() -> tuple[str, str, str]:
    """Kembalikan (api_key, endpoint, model). Raise RuntimeError bila belum diisi."""
    api_key, endpoint, model = _env("ONLINE_API_KEY"), _env("ONLINE_BASE_URL"), _env("ONLINE_MODEL")
    kosong = [n for n, v in (("ONLINE_API_KEY", api_key), ("ONLINE_BASE_URL", endpoint), ("ONLINE_MODEL", model)) if not v]
    if kosong:
        raise RuntimeError(
            f"Variabel berikut belum diisi di file .env: {', '.join(kosong)}. "
            "Salin .env.example menjadi .env lalu isi nilainya."
        )
    return api_key, endpoint, model


MAX_CONCURRENCY = int(_env("LLM_MAX_CONCURRENCY", "4"))

# Embedding: fastembed (lokal, default) atau openai (endpoint kompatibel OpenAI)
EMBED_PROVIDER = _env("EMBED_PROVIDER", "fastembed").lower()
EMBED_MODEL = _env("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
EMBED_CACHE_DIR = str((ROOT / _env("EMBED_CACHE_DIR", "./models")).resolve())
EMBED_BASE_URL = _env("EMBED_BASE_URL")
EMBED_API_KEY = _env("EMBED_API_KEY", "local")
