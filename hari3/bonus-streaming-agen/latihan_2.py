"""
Bab bonus Streaming Agen - Latihan Bonus: Endpoint HTTP Streaming (SSE)

Server web kecil, hanya dengan library standar Python, yang mengalirkan jawaban agen ke klien sebagai
Server-Sent Events (SSE):

    GET /chat?q=<pertanyaan>   ->   data: {"type": "token", "text": "..."}\\n\\n   (berulang)
                                    data: {"type": "done"}\\n\\n

Browser dapat membacanya dengan API EventSource bawaan; di sini klien Python yang melakukannya.
(Di proyek nyata Anda memakai framework seperti FastAPI, tetapi gagasannya identik.)

Jalankan demo mandiri:  python hari3/bonus-streaming-agen/latihan_2.py --demo
Jalankan server saja:   python hari3/bonus-streaming-agen/latihan_2.py
                        lalu buka http://localhost:8000/chat?q=Apa%20itu%20water%20cut
"""

import json
import os
import sys
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv()


def buat_agen():
    model = ChatOpenAI(
        model=os.getenv("ONLINE_MODEL"),
        base_url=os.getenv("ONLINE_BASE_URL"),
        api_key=os.getenv("ONLINE_API_KEY"),
        reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    )
    return create_agent(
        model, tools=[], system_prompt="Anda asisten operasi produksi migas. Jawab dalam 2-3 kalimat pendek Bahasa Indonesia."
    )


AGEN = buat_agen()


def event_sse(payload: dict) -> bytes:
    """Format satu Server-Sent Event."""
    # TODO(BS.4): kembalikan satu Server-Sent Event: teks 'data: <JSON>' diakhiri dua baris baru, dalam bytes UTF-8
    raise NotImplementedError("TODO(BS.4)")


class PenanganChat(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path != "/chat":
            self.send_error(404, "Pakai /chat?q=pertanyaan+anda")
            return
        pertanyaan = urllib.parse.parse_qs(url.query).get("q", [""])[0].strip()
        if not pertanyaan:
            self.send_error(400, "Parameter ?q= belum diisi")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")  # memberi tahu klien bahwa ini aliran SSE
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        try:
            # TODO(BS.5): alirkan AGEN.stream(..., stream_mode="messages"); untuk setiap chunk teks dari node model tulis event token ke self.wfile lalu flush; setelah selesai tulis event done
            pass  # TODO: ganti dengan implementasi Anda
        except (BrokenPipeError, ConnectionResetError):
            pass  # klien menutup koneksi; hentikan streaming

    def log_message(self, format, *args):
        pass  # jaga konsol tetap tenang


def jalankan_klien(port: int, pertanyaan: str) -> None:
    """Klien SSE minimal: baca respons baris demi baris saat tiba."""
    url = f"http://127.0.0.1:{port}/chat?q={urllib.parse.quote(pertanyaan)}"
    print(f"Permintaan klien: GET {url}\n")
    print("Agen: ", end="", flush=True)
    jumlah = 0
    with urllib.request.urlopen(url) as response:
        for baris_mentah in response:
            baris = baris_mentah.decode("utf-8").strip()
            if not baris.startswith("data:"):
                continue  # baris pemisah kosong
            event = json.loads(baris[len("data:"):])
            jumlah += 1
            if event["type"] == "token":
                print(event["text"], end="", flush=True)
            elif event["type"] == "done":
                print(f"\n\nAliran selesai setelah {jumlah} event")


def main():
    if "--demo" in sys.argv:
        server = ThreadingHTTPServer(("127.0.0.1", 0), PenanganChat)  # port 0 = pilih port kosong
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        print(f"Server berjalan di http://127.0.0.1:{port}\n")
        jalankan_klien(port, "Apa bedanya alarm H2S tingkat 1 dan tingkat 2?")
        server.shutdown()
        return

    server = ThreadingHTTPServer(("127.0.0.1", 8000), PenanganChat)
    print("Mendengarkan di http://localhost:8000/chat?q=... (Ctrl+C untuk berhenti)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDihentikan")


if __name__ == "__main__":
    main()
