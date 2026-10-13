# Lampiran: Pengaturan Penyedia Model dan Embedding

Lampiran ini menjelaskan dua pengaturan model yang didokumentasikan untuk hari 3 dan 4, serta cara mengganti model embedding. Kode tidak berubah apa pun pilihan Anda; hanya isi file `.env` yang berbeda. Hari 3 dan 4 membaca variabel `ONLINE_*` (profil `online` di hari 1 dan 2), sehingga pengaturan lokal juga diisi di `ONLINE_*`, bukan di `LOCAL_*`.

## Pengaturan A: OpenRouter (online, pengaturan workshop)

OpenRouter adalah gerbang tunggal ke banyak model lewat satu API kompatibel OpenAI.

1. Dapatkan API key dari penyelenggara workshop, atau buat akun di [openrouter.ai](https://openrouter.ai) lalu buat key di halaman Keys.
2. Isi `.env`:

```bash
ONLINE_API_KEY=isi-dengan-api-key-anda
ONLINE_BASE_URL=https://openrouter.ai/api/v1
ONLINE_MODEL=isi-dengan-nama-model-dari-penyelenggara
```

3. Jalankan `python setup_check.py`.

Catatan:

- Beberapa model gratis atau bersama bisa sesekali mengembalikan error `400 ... Model is unavailable` atau `429`. Itu sementara; jalankan ulang skrip.
- Kalau API key dipakai bersama banyak peserta, turunkan `LLM_MAX_CONCURRENCY` di `.env` (misalnya menjadi 2) agar tidak terkena batas laju.
- Pilih model yang mendukung pemanggilan tool (function calling). Bab 2 dan seterusnya bergantung padanya.

## Pengaturan B: Server lokal dengan Ollama

Cocok untuk bekerja offline atau tanpa biaya, dengan syarat laptop Anda cukup kuat (disarankan RAM 16 GB atau lebih untuk model 7B).

1. Pasang Ollama dari [ollama.com](https://ollama.com) dan jalankan aplikasinya.
2. Download sebuah model yang mendukung tool, misalnya:

```bash
ollama pull qwen2.5:7b-instruct
```

3. Isi `.env`:

```bash
ONLINE_API_KEY=local
ONLINE_BASE_URL=http://localhost:11434/v1
ONLINE_MODEL=qwen2.5:7b-instruct
```

4. Jalankan `python setup_check.py`.

Catatan:

- Model lokal berukuran kecil kurang andal dalam memilih tool dan mengikuti structured output dibanding model online besar. Kalau agen terlihat "bingung", coba model yang lebih besar atau pangkas jumlah tool.
- Respons pertama lebih lambat karena model dimuat ke memori.

## Mengganti model embedding

Secara bawaan, embedding dihitung di laptop Anda dengan `fastembed` memakai model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (multibahasa, cocok untuk teks Indonesia). Model ini sama dengan hari 2 dan disimpan di folder `models/`, jadi tidak di-download ulang. Tidak butuh API key.

Untuk memakai server embedding yang kompatibel OpenAI (misalnya Ollama), ubah di `.env`:

```bash
EMBED_PROVIDER=openai
EMBED_MODEL=nomic-embed-text
EMBED_BASE_URL=http://localhost:11434/v1
EMBED_API_KEY=local
```

lalu `ollama pull nomic-embed-text`. Setelah mengganti penyedia embedding, jalankan `python scripts/reset_knowledge.py` agar index Chroma dibangun ulang dengan embedding yang baru (vektor dari model berbeda tidak bisa dicampur).

Kalau Anda sudah memiliki salinan model fastembed di folder lain, arahkan `EMBED_CACHE_DIR` ke folder itu.

## Opsional: Tracking dengan LangSmith

LangSmith menampilkan setiap langkah agen (panggilan model, panggilan tool) sebagai jejak yang bisa ditelusuri. Untuk mengaktifkannya, tambahkan di `.env`:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=isi-dengan-api-key-langsmith
```

Jangan aktifkan kalau data Anda tidak boleh dikirim ke layanan eksternal. Data kursus ini fiktif, tetapi kebiasaan itu penting untuk data operasi nyata.
