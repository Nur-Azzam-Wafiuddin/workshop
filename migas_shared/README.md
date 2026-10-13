# migas_shared: paket bersama kursus

Paket Python yang dipakai semua bab. Dipasang dengan `pip install -e .` dari root repo, sehingga bab cukup menulis `from migas_shared.rag_tools import ...` tanpa `sys.path`.

## Modul dan tanda tangan publik

### `migas_shared.config`
- `ROOT`, `DATA`, `OUTPUTS`, `CACHE`: path (`pathlib.Path`).
- `ai_settings() -> (api_key, endpoint, model)`: membaca `ONLINE_API_KEY`, `ONLINE_BASE_URL`, `ONLINE_MODEL` dari `.env`; `RuntimeError` berbahasa Indonesia bila ada yang kosong.
- `EMBED_PROVIDER`, `EMBED_MODEL`, `EMBED_CACHE_DIR`, `EMBED_BASE_URL`, `EMBED_API_KEY`, `MAX_CONCURRENCY`.

### `migas_shared.llm`
- `get_chat_model(temperature=0.0, **kwargs) -> ChatOpenAI`
- `chat(prompt, system=None, *, json_mode=False, temperature=0.0) -> str`
- `parse_json(text) -> Any` (toleran terhadap blok kode dan teks pengantar; `ValueError` bila gagal)
- `run_parallel(fn, items, max_workers=None, desc="Memproses") -> list` (galat per item dikembalikan sebagai objek Exception)
- `ringkasan_pemakaian() -> str`, `reset_pemakaian()`: jumlah panggilan dan token sejak proses mulai

### `migas_shared.embeddings`
- `get_embeddings() -> Embeddings`: fastembed lokal (default) atau endpoint kompatibel OpenAI, sesuai `EMBED_PROVIDER`.

### `migas_shared.rag_pipeline`
Salinan pipeline RAG workshop hari 2. Fungsi yang paling sering dipakai: `load_documents`, `chunk_documents(docs, strategy, chunk_size, chunk_overlap)`, `load_retriever(...) -> HybridRetriever`, `HybridRetriever.search(query, k, mode, role, active_only)`, `format_context(docs, spotlight=False)`, `answer(question, retriever, role, ...) -> dict`, `ROLE_GROUPS`, `REFUSAL`, `cited_ids`, `ingest_document`, `load_golden`, `retrieval_metrics`. Index Chroma disimpan di `chroma_db/` dan dibangun otomatis pada pemakaian pertama.

### `migas_shared.rag_tools`
```python
from migas_shared.rag_tools import KonteksPengguna, SEMUA_TOOL, build_retriever
from migas_shared.rag_tools import cari_dokumen, jawab_dari_dokumen, daftar_dokumen_aktif, ingest_dokumen
```
- `KonteksPengguna(role="engineer", area="Seruni", user_id="anon")`: `role` salah satu dari `operator`, `engineer`, `hse`, `management`.
- `cari_dokumen(query, k=5)`: pencarian hybrid, hanya dokumen aktif yang boleh dilihat peran; hasil berupa blok `<dokumen id= revisi= status= bagian=>`.
- `jawab_dari_dokumen(pertanyaan)`: pipeline RAG siap pakai dengan sitasi dan penolakan baku.
- `daftar_dokumen_aktif(jenis=None)`: daftar dokumen aktif menurut peran.
- `ingest_dokumen(nama_file, isi, metadata)`: tindakan tulis (quality gate); dipakai di bab 6 di balik persetujuan manusia.
- `build_retriever(rebuild=False)`: retriever tunggal bersama.
- Semua tool memiliki parameter tersembunyi `runtime: ToolRuntime[KonteksPengguna]`. Role selalu diambil dari konteks yang Anda kirim:

```python
agen = create_agent(model=get_chat_model(), tools=[cari_dokumen], context_schema=KonteksPengguna)
agen.invoke({"messages": [("user", "...")]}, context=KonteksPengguna(role="operator"))
```

### `migas_shared.data`
- `WOExtract`: skema ekstraksi work order (asset_id, equipment_type, failure_category, component, action_category, downtime_hours, safety_flag).
- `KlasifikasiInsiden`: `incident_type`, `hazard`, `severity` (Rendah/Sedang/Tinggi), `ringkasan`.
- `buat_database_migas(path=None) -> Path`: membangun `outputs/migas.db` (tabel `work_order` 400 baris dan `insiden_hse` 120 baris).
- `read_only_connection(path=None)`: context manager koneksi SQLite hanya-baca.

## Lingkungan uji

```text
python setup_check.py --embedding       # .env, model, data, embedding
```

Pada Windows jalankan dengan `PYTHONUTF8=1`. Pada pemakaian pertama, model embedding (sekitar 220 MB) diunduh ke `models/`. Jika Anda sudah punya salinannya, arahkan `EMBED_CACHE_DIR` ke folder itu.
