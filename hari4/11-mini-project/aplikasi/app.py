"""Template aplikasi chat untuk mini project. Anda tidak perlu mengubah file ini.

Yang Anda ubah adalah file di folder agen/ (mulai dari agen/saya.py): susun tool, prompt, dan aturan persetujuan
(interrupt) menjadi satu agen. Aplikasi ini menyediakan:

  - chat dengan jawaban yang tampil saat ditulis (streaming) dan panel tool yang dipanggil agen
  - persetujuan manusia: bila agen berhenti di sebuah tool, formulir approve, edit, atau reject muncul
  - sidebar riwayat percakapan seperti ChatGPT, didukung InMemorySaver (checkpointer dari bab 5)

Jalankan dari root repositori:   streamlit run hari4/11-mini-project/aplikasi/app.py
"""
import json
import uuid
from pathlib import Path

import streamlit as st
from langchain_core.messages import HumanMessage

import kerangka as k

LABEL = {"approve": "Setujui", "edit": "Ubah", "reject": "Tolak"}
FOLDER = Path(__file__).resolve().parent

st.set_page_config(page_title="Mini Project Agen", layout="wide")


# ---------------------------------------------------------------------------
# Sumber daya yang bertahan antar rerun Streamlit
# ---------------------------------------------------------------------------


@st.cache_resource
def penyimpanan() -> k.Penyimpanan:
    """Satu checkpointer dan satu daftar percakapan untuk seluruh proses. Hilang bila aplikasi dihentikan."""
    return k.Penyimpanan()


@st.cache_resource(show_spinner="Menyiapkan agen...")
def agen_untuk(nama: str, versi: float):
    """Bangun agen sekali per file agen. `versi` (waktu ubah file) membuat agen dibangun ulang setelah Anda menyimpan perubahan."""
    return k.bangun_agen(nama, penyimpanan().saver)


def versi_agen(nama: str) -> float:
    files = [FOLDER / "agen" / f"{nama}.py", k.FOLDER_SOLUSI / f"{nama}.py", FOLDER / "alat_data.py"]
    return max(f.stat().st_mtime for f in files if f.exists())


# ---------------------------------------------------------------------------
# Aksi sidebar
# ---------------------------------------------------------------------------


def percakapan_baru():
    st.session_state.thread_id = None


def buka_percakapan(thread_id: str):
    st.session_state.thread_id = thread_id
    st.session_state.agen = penyimpanan().percakapan[thread_id]["agen"]


def pakai_contoh(teks: str):
    st.session_state.antrean = teks


# ---------------------------------------------------------------------------
# Menggambar
# ---------------------------------------------------------------------------


def gambar_tool(nama: str, args: dict, hasil: str | None):
    with st.expander(f"Tool: {nama}"):
        st.caption("Argumen")
        st.code(json.dumps(args, indent=2, ensure_ascii=False), language="json")
        st.caption("Hasil")
        st.text(hasil if hasil is not None else "(belum ada hasil: menunggu persetujuan atau belum dijalankan)")


def gambar_riwayat(agen, thread_id: str):
    for giliran in k.pesan_untuk_tampilan(agen, thread_id):
        with st.chat_message(giliran["peran"]):
            if giliran["peran"] == "user":
                st.markdown(giliran["teks"])
                continue
            for bagian in giliran["bagian"]:
                if bagian[0] == "teks":
                    st.markdown(bagian[1])
                else:
                    gambar_tool(*bagian[1:])


def jalankan_dan_tampilkan(agen, masukan, thread_id: str, konteks) -> bool:
    """Jalankan agen sambil menggambar langsung. Kembalikan False bila terjadi error."""
    with st.chat_message("assistant"):
        wadah = st.container()
        tempat, buffer = wadah.empty(), ""
        try:
            for p in k.jalankan(agen, masukan, thread_id, konteks):
                if p.jenis == "teks":
                    buffer += p.teks
                    tempat.markdown(buffer)
                elif p.jenis == "tool":
                    if buffer:
                        tempat.markdown(buffer)
                    wadah.caption(f"Memanggil tool {p.nama}({json.dumps(p.args, ensure_ascii=False)})")
                    tempat, buffer = wadah.empty(), ""
        except Exception as e:  # noqa: BLE001 - tampilkan error model atau tool apa adanya
            st.error(f"Agen gagal: {type(e).__name__}: {e}")
            return False
    return True


def formulir_persetujuan(menunggu: dict, thread_id: str) -> list[dict] | None:
    """Tampilkan permintaan persetujuan. Kembalikan daftar keputusan setelah dikirim, atau None."""
    with st.chat_message("assistant"):
        st.warning("Agen menunggu keputusan Anda sebelum menjalankan tindakan berikut.")
        with st.form(f"setuju-{thread_id}-{menunggu['id']}"):
            isian = []
            for i, (permintaan, tinjau) in enumerate(zip(menunggu["action_requests"], menunggu["review_configs"])):
                boleh = tinjau["allowed_decisions"]
                st.markdown(f"**{permintaan['name']}**")
                teks_args = json.dumps(permintaan["args"], indent=2, ensure_ascii=False)
                st.code(teks_args, language="json")
                pilihan = st.radio("Keputusan", boleh, format_func=LABEL.get, horizontal=True, key=f"k{i}-{menunggu['id']}")
                args_baru = st.text_area("Argumen baru (JSON), dipakai bila memilih Ubah", teks_args, key=f"a{i}-{menunggu['id']}") \
                    if "edit" in boleh else None
                alasan = st.text_input("Alasan bila ditolak (opsional)", key=f"r{i}-{menunggu['id']}")
                isian.append((permintaan, pilihan, args_baru, alasan))
            kirim = st.form_submit_button("Kirim keputusan", type="primary")
    if not kirim:
        return None
    keputusan = []
    for permintaan, pilihan, args_baru, alasan in isian:
        if pilihan == "approve":
            keputusan.append({"type": "approve"})
        elif pilihan == "reject":
            keputusan.append({"type": "reject", "message": alasan or "Ditolak oleh reviewer"})
        else:
            try:
                keputusan.append({"type": "edit", "edited_action": {"name": permintaan["name"], "args": json.loads(args_baru)}})
            except json.JSONDecodeError as e:
                st.error(f"Argumen baru untuk {permintaan['name']} bukan JSON yang valid: {e}")
                return None
    return keputusan


# ---------------------------------------------------------------------------
# Halaman
# ---------------------------------------------------------------------------

simpan = penyimpanan()
st.session_state.setdefault("thread_id", None)
nama_agen_semua = k.daftar_agen()

with st.sidebar:
    st.header("Mini Project Agen")
    st.selectbox("Agen", nama_agen_semua, key="agen", on_change=percakapan_baru,
                 help="Satu file di folder agen/. Memilih agen lain memulai percakapan baru.")
    st.selectbox("Peran pengguna", k.PERAN, index=k.PERAN.index("engineer"), key="peran",
                 help="Menentukan dokumen yang boleh dibaca tool pencarian dokumen. Di penggunaan nyata, peran berasal dari sistem login.")
    st.button("Percakapan baru", on_click=percakapan_baru, use_container_width=True)
    st.subheader("Riwayat percakapan")
    if not simpan.percakapan:
        st.caption("Belum ada percakapan.")
    for tid, info in reversed(list(simpan.percakapan.items())):
        st.button(f"{info['judul']}", key=f"buka-{tid}", on_click=buka_percakapan, args=(tid,), use_container_width=True,
                  type="primary" if tid == st.session_state.thread_id else "secondary", help=f"Agen: {info['agen']}")
    st.caption("Riwayat disimpan di memori (InMemorySaver) dan hilang saat aplikasi dihentikan.")

nama_agen = st.session_state.agen
try:
    modul, agen = agen_untuk(nama_agen, versi_agen(nama_agen))
except k.ErrorAgen as e:
    st.error(str(e))
    st.stop()

konteks = k.konteks_untuk(st.session_state.peran)
thread_id = st.session_state.thread_id

st.title(modul.JUDUL)
st.caption(modul.PENGANTAR)
st.caption(f"Peran pengguna: {st.session_state.peran}. Dokumen terbatas (misalnya laporan investigasi HSE) hanya terbaca oleh peran hse.")

menunggu = k.persetujuan_menunggu(agen, thread_id) if thread_id else None
if thread_id:
    gambar_riwayat(agen, thread_id)
else:
    st.write("Coba salah satu pertanyaan ini, atau tulis sendiri di kotak bawah:")
    for i, contoh in enumerate(modul.CONTOH_PERTANYAAN):
        st.button(contoh, key=f"contoh-{i}", on_click=pakai_contoh, args=(contoh,))

if menunggu:
    keputusan = formulir_persetujuan(menunggu, thread_id)
    if keputusan is not None:
        jalankan_dan_tampilkan(agen, k.lanjutkan(keputusan), thread_id, konteks)
        st.rerun()

prompt = st.session_state.pop("antrean", None) or st.chat_input("Tulis pertanyaan...", disabled=menunggu is not None)
if prompt:
    if thread_id is None:
        thread_id = uuid.uuid4().hex[:8]
        st.session_state.thread_id = thread_id
        simpan.percakapan[thread_id] = {"judul": k.judul_dari(prompt), "agen": nama_agen}
    with st.chat_message("user"):
        st.markdown(prompt)
    if jalankan_dan_tampilkan(agen, {"messages": [HumanMessage(content=prompt)]}, thread_id, konteks):
        st.rerun()
