"""Akses LLM yang dipakai bersama oleh semua bab.

- get_chat_model()      : objek ChatOpenAI yang diarahkan ke ONLINE_BASE_URL / ONLINE_MODEL
- chat()                : pemanggilan satu kali yang mengembalikan teks (dipakai pipeline RAG)
- parse_json()          : membaca JSON dari jawaban LLM secara toleran
- run_parallel()        : menjalankan fungsi untuk banyak item secara paralel
- ringkasan_pemakaian() : jumlah token yang sudah terpakai pada proses ini
"""
from __future__ import annotations

import json
import re
import threading
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import openai
from langchain_core.callbacks import BaseCallbackHandler

from migas_shared import config


class _Pemakaian(BaseCallbackHandler):
    """Menghitung token dari setiap panggilan model (aman untuk banyak thread)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        self.panggilan = 0
        self.token_masuk = 0
        self.token_keluar = 0

    def on_llm_end(self, response, **kwargs) -> None:
        pemakaian = (response.llm_output or {}).get("token_usage") or {}
        with self._lock:
            self.panggilan += 1
            self.token_masuk += pemakaian.get("prompt_tokens", 0) or 0
            self.token_keluar += pemakaian.get("completion_tokens", 0) or 0


PEMAKAIAN = _Pemakaian()


def ringkasan_pemakaian() -> str:
    """Satu baris ringkasan pemakaian token sejak proses dimulai (atau sejak reset_pemakaian())."""
    p = PEMAKAIAN
    return f"{p.panggilan} panggilan, {p.token_masuk} token masuk, {p.token_keluar} token keluar"


def reset_pemakaian() -> None:
    PEMAKAIAN.reset()


def get_chat_model(temperature: float = 0.0, **kwargs: Any):
    """ChatOpenAI LangChain yang diarahkan ke ONLINE_BASE_URL dengan model ONLINE_MODEL di file .env."""
    from langchain_openai import ChatOpenAI

    api_key, endpoint, model = config.ai_settings()
    # Mode reasoning mengikuti LLM_REASONING_EFFORT di .env, sama seperti hari 1 dan 2
    kwargs.setdefault("reasoning_effort", config._env("LLM_REASONING_EFFORT", "none"))
    return ChatOpenAI(model=model, base_url=endpoint, api_key=api_key, temperature=temperature,
                      max_retries=5, callbacks=[PEMAKAIAN], **kwargs)


def chat(prompt: str, system: str | None = None, *, json_mode: bool = False, temperature: float = 0.0) -> str:
    """Kirim satu prompt ke LLM dan kembalikan teks jawabannya.

    json_mode : minta keluaran JSON. Jika server atau model tidak mendukung, otomatis diulang tanpa opsi ini.
    """
    pesan: list[tuple[str, str]] = ([("system", system)] if system else []) + [("human", prompt)]
    model = get_chat_model(temperature)
    if json_mode:
        try:
            return model.bind(response_format={"type": "json_object"}).invoke(pesan).content
        except openai.BadRequestError:
            pass
    return model.invoke(pesan).content


_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def parse_json(text: str) -> Any:
    """Baca JSON dari jawaban LLM secara toleran (menangani blok ```json ... ``` dan teks pengantar).

    Raise ValueError jika tidak ada JSON yang valid.
    """
    kandidat = [m.group(1) for m in _FENCE.finditer(text)] + [text]
    for c in kandidat:
        c = c.strip()
        for buka, tutup in (("{", "}"), ("[", "]")):
            awal, akhir = c.find(buka), c.rfind(tutup)
            if awal != -1 and akhir > awal:
                try:
                    return json.loads(c[awal : akhir + 1])
                except json.JSONDecodeError:
                    pass
    raise ValueError(f"Tidak menemukan JSON valid pada jawaban: {text[:200]!r}")


def run_parallel(fn: Callable[[Any], Any], items: Iterable[Any], max_workers: int | None = None,
                 desc: str = "Memproses") -> list[Any]:
    """Jalankan fn(item) untuk setiap item secara paralel (urutan hasil sama dengan urutan input).

    Jika fn raise exception, hasil untuk item tersebut berisi objek Exception (batch tidak berhenti).
    """
    items = list(items)
    pekerja = min(max_workers or config.MAX_CONCURRENCY, config.MAX_CONCURRENCY)
    hasil: list[Any] = [None] * len(items)
    selesai = 0
    with ThreadPoolExecutor(max_workers=pekerja) as kolam:
        futures = {kolam.submit(fn, it): i for i, it in enumerate(items)}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                hasil[i] = fut.result()
            except Exception as e:  # noqa: BLE001
                hasil[i] = e
            selesai += 1
            if selesai % max(1, len(items) // 10) == 0 or selesai == len(items):
                print(f"  {desc}: {selesai}/{len(items)}")
    return hasil
