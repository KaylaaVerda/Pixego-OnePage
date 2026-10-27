"""Entry point dashboard single-page Pixego untuk presentasi desktop satu layar."""

import sys
from pathlib import Path

import numpy as np
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import stego_core as core
from app.services import (
    capacity_bytes,
    embed_message,
    extract_message,
    image_to_png_bytes,
    load_cover_upload,
    load_stego_upload,
)

def load_css() -> None:
    css_path = ROOT / "styles.css"
    if not css_path.exists():
        return
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


st.set_page_config(
    page_title="Pixego",
    page_icon=":material/encrypted:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()

for key in [
    "pixego_cover_image",
    "pixego_stego_image",
    "pixego_stego_png",
    "pixego_extracted_text",
    "pixego_extract_password",
    "pixego_message",
    "pixego_embed_password",
]:
    if key not in st.session_state:
        st.session_state[key] = None if "image" in key or "png" in key else ""


def render_wrong_key_panel() -> None:
    cover = st.session_state.get("pixego_cover_image")
    stego = st.session_state.get("pixego_stego_image")

    with st.container(key="card_wrong_key", border=True):
        st.markdown("<div class='panel-title'>Uji Kunci Salah</div>", unsafe_allow_html=True)
        if cover is None or stego is None:
            st.markdown(
                "<div class='placeholder-box'>Password salah akan ditolak oleh autentikasi AES-GCM.</div>",
                unsafe_allow_html=True,
            )
            return

        cover_array = np.asarray(cover.convert("RGB"), dtype=np.float64)
        stego_array = np.asarray(stego.convert("RGB"), dtype=np.float64)
        mse_value = core.mse(cover, stego)
        psnr_value = core.psnr(cover, stego)
        uaci_value = float(np.mean(np.abs(cover_array - stego_array)) / 255.0 * 100.0)

        cover_flat = cover_array.reshape(-1)
        hist = np.bincount(np.clip(cover_flat.astype(np.int64), 0, 255), minlength=256)
        probs = hist[hist > 0] / hist.sum()
        entropy_value = float(-np.sum(probs * np.log2(probs)))

        ssim_value = "N/A"
        try:
            from skimage.metrics import structural_similarity

            grayscale_cover = np.asarray(cover.convert("L"), dtype=np.float64)
            grayscale_stego = np.asarray(stego.convert("L"), dtype=np.float64)
            ssim_value = structural_similarity(grayscale_cover, grayscale_stego, data_range=255.0)
            ssim_value = f"{ssim_value:.4f}"
        except Exception:
            ssim_value = "N/A"

        st.markdown(
            f"""
            <div class='metric-box'><span>MSE</span><strong>{mse_value:.6f}</strong></div>
            <div class='metric-box'><span>PSNR</span><strong>{psnr_value:.2f} dB</strong></div>
            <div class='metric-box'><span>SSIM</span><strong>{ssim_value}</strong></div>
            <div class='metric-box'><span>Entropy</span><strong>{entropy_value:.4f}</strong></div>
            <div class='metric-box'><span>UACI</span><strong>{uaci_value:.2f}%</strong></div>
            """,
            unsafe_allow_html=True,
        )


def render_lapisan_panel() -> None:
    with st.container(key="card_lapisan", border=True):
        st.markdown("<div class='panel-title'>Perbandingan Lapisan</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='placeholder-box'>Belum ada data perbandingan. Unggah cover dan stego untuk melihat selisih lapisan.</div>",
            unsafe_allow_html=True,
        )


def render_metric_panel() -> None:
    with st.container(key="card_metric", border=True):
        st.markdown("<div class='panel-title'>Evaluasi Metrik</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='placeholder-box'>Belum ada data untuk dianalisis.</div>",
            unsafe_allow_html=True,
        )


def render_method_panel() -> None:
    with st.container(key="card_method", border=True):
        st.markdown("<div class='panel-title'>Metode Pengujian</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <ul class='method-list'>
                <li>1. Enkripsi pesan memakai AES-256-GCM dengan kunci Argon2id.</li>
                <li>2. Penyisipan memakai mode acak atau sekuensial sesuai preferensi.</li>
                <li>3. Cover dan stego dibandingkan dengan MSE, PSNR, dan entropi.</li>
                <li>4. Nilai autentikasi ditolak bila kunci salah, sesuai tag AES-GCM.</li>
                <li>5. Evaluasi visual dan numerik memperlihatkan perubahan pada lapisan citra.</li>
            </ul>
            """,
            unsafe_allow_html=True,
        )


# --- Layout utama ---
st.markdown('<div class="pixego-page">', unsafe_allow_html=True)

header_cols = st.columns([2.2, 1, 1, 1], gap="small")
with header_cols[0]:
    st.markdown(
        """
        <div class='pixego-logo'>
            <div class='logo-badge'>P</div>
            <div>
                <div class='brand-title'>Pixego</div>
                <div class='brand-sub'>Steganografi &amp; Kriptografi Citra</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_cols[1]:
    st.markdown("<div class='info-box'><div><strong>Algoritma</strong>AES-256-GCM</div></div>", unsafe_allow_html=True)
with header_cols[2]:
    st.markdown("<div class='info-box'><div><strong>Kunci</strong>Argon2id</div></div>", unsafe_allow_html=True)
with header_cols[3]:
    st.markdown("<div class='info-box'><div><strong>Metode</strong>LSB + Analisis</div></div>", unsafe_allow_html=True)

toolbar_cols = st.columns([1.1, 1.1, 1.1, 1.2, 1.1, 1.0, 1.2], gap="small")
with toolbar_cols[0]:
    st.button("Buka Gambar", key="btn_buka_gambar", use_container_width=True)
with toolbar_cols[1]:
    st.button("Enkripsi", key="btn_enkripsi", use_container_width=True)
with toolbar_cols[2]:
    st.button("Dekripsi", key="btn_dekripsi", use_container_width=True)
with toolbar_cols[3]:
    st.button("Uji Kunci", key="btn_uji_kunci", use_container_width=True)
with toolbar_cols[4]:
    st.button("Analisis", key="btn_analisis", use_container_width=True)
with toolbar_cols[5]:
    st.button("Reset", key="btn_reset", use_container_width=True)
with toolbar_cols[6]:
    if st.session_state.get("pixego_stego_png"):
        st.download_button("Simpan Citra", data=st.session_state["pixego_stego_png"], file_name="stego.png", mime="image/png", key="btn_simpan_citra", use_container_width=True)
    else:
        st.button("Simpan Citra", key="btn_simpan_citra", use_container_width=True, disabled=True)

main_cols = st.columns([1, 1, 1, 1.35], gap="small")

with main_cols[0]:
    with st.container(key="card_cover", border=True):
        st.markdown("<div class='panel-title'>Citra Asli</div>", unsafe_allow_html=True)
        cover_file = st.file_uploader("Pilih gambar cover", type=["png", "jpg", "jpeg", "bmp", "webp"], key="pixego_cover_upload")
        if cover_file is not None:
            try:
                cover, resized = load_cover_upload(cover_file)
                st.session_state["pixego_cover_image"] = cover
                if resized:
                    st.caption("Gambar diperkecil otomatis sampai sisi terpanjang 1024 piksel.")
            except Exception as exc:
                st.error(f"Gambar tidak dapat diproses: {exc}")
        if st.session_state["pixego_cover_image"] is not None:
            st.image(st.session_state["pixego_cover_image"], use_container_width=True)
        else:
            st.markdown("<div class='placeholder-box'>Preview Cover</div>", unsafe_allow_html=True)
        if st.session_state["pixego_cover_image"] is not None:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(2.5, 1.2), dpi=100)
            arr = np.asarray(st.session_state["pixego_cover_image"].convert("RGB"))[:, :, 0].ravel()
            ax.hist(arr, bins=32, range=(0, 256), color="#5e6ef7", alpha=0.8)
            ax.set_xlim(0, 255)
            ax.set_xticks([0, 64, 128, 192, 255])
            ax.set_yticks([])
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

with main_cols[1]:
    with st.container(key="card_stego", border=True):
        st.markdown("<div class='panel-title'>Citra Terenkripsi</div>", unsafe_allow_html=True)
        if st.session_state["pixego_stego_image"] is not None:
            st.image(st.session_state["pixego_stego_image"], use_container_width=True)
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(2.5, 1.2), dpi=100)
            arr = np.asarray(st.session_state["pixego_stego_image"].convert("RGB"))[:, :, 0].ravel()
            ax.hist(arr, bins=32, range=(0, 256), color="#6b7ef0", alpha=0.8)
            ax.set_xlim(0, 255)
            ax.set_xticks([0, 64, 128, 192, 255])
            ax.set_yticks([])
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.markdown("<div class='placeholder-box'>Preview Stego</div>", unsafe_allow_html=True)

with main_cols[2]:
    with st.container(key="card_decrypted", border=True):
        st.markdown("<div class='panel-title'>Citra Terdekripsi</div>", unsafe_allow_html=True)
        if st.session_state.get("pixego_extracted_text"):
            st.text_area("Hasil ekstraksi", value=st.session_state["pixego_extracted_text"], height=120, disabled=True, label_visibility="collapsed")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(2.5, 1.2), dpi=100)
            arr = np.asarray(st.session_state["pixego_stego_image"].convert("RGB"))[:, :, 0].ravel() if st.session_state.get("pixego_stego_image") is not None else np.zeros((1, 1))
            ax.hist(arr, bins=32, range=(0, 256), color="#8a7af0", alpha=0.8)
            ax.set_xlim(0, 255)
            ax.set_xticks([0, 64, 128, 192, 255])
            ax.set_yticks([])
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        elif st.session_state["pixego_stego_image"] is not None:
            st.image(st.session_state["pixego_stego_image"], use_container_width=True)
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(2.5, 1.2), dpi=100)
            arr = np.asarray(st.session_state["pixego_stego_image"].convert("RGB"))[:, :, 0].ravel()
            ax.hist(arr, bins=32, range=(0, 256), color="#8a7af0", alpha=0.8)
            ax.set_xlim(0, 255)
            ax.set_xticks([0, 64, 128, 192, 255])
            ax.set_yticks([])
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.markdown("<div class='placeholder-box'>Preview Hasil</div>", unsafe_allow_html=True)

with main_cols[3]:
    with st.container(key="card_settings", border=True):
        st.markdown("<div class='panel-title'>Pengaturan</div>", unsafe_allow_html=True)
        stego_uploader = st.file_uploader("Pilih stego PNG/BMP", type=["png", "bmp", "jpg", "jpeg", "webp"], key="stego_uploader_single")
        if stego_uploader is not None:
            try:
                st.session_state["pixego_stego_image"] = load_stego_upload(stego_uploader, stego_uploader.name)
            except Exception as exc:
                st.error(f"Gagal membuka stego: {exc}")

        message = st.text_area("Pesan rahasia", placeholder="Tulis pesan rahasia", key="pixego_message", height=90)
        password = st.text_input("Password", type="password", key="pixego_embed_password", placeholder="Password")
        mode_label = st.radio("Mode penyisipan", ["Acak berbasis kunci", "Sekuensial"], horizontal=True, key="pixego_mode")
        mode = "random" if mode_label == "Acak berbasis kunci" else "sequential"

        extract_password = st.text_input("Password ekstraksi", type="password", key="pixego_extract_password", placeholder="Password")

        if st.session_state["pixego_cover_image"] is not None:
            cap = capacity_bytes(st.session_state["pixego_cover_image"].size, 1)
            usage = len(message.encode("utf-8")) / max(cap, 1)
            st.progress(min(max(usage, 0.0), 1.0), text=f"{len(message.encode('utf-8'))}/{cap} byte")

        if st.button("Enkripsi & Simpan", key="embed_action", use_container_width=True, disabled=st.session_state["pixego_cover_image"] is None or not password or not message):
            try:
                with st.spinner("Mengenkripsi dan menyisipkan pesan..."):
                    stego, info = embed_message(st.session_state["pixego_cover_image"], message, password, mode, 1)
                    st.session_state["pixego_stego_image"] = stego
                    st.session_state["pixego_stego_png"] = image_to_png_bytes(stego)
                    st.session_state["pixego_last_info"] = info
                st.success("Pesan berhasil disisipkan.")
            except Exception as exc:
                st.error(f"Proses gagal: {exc}")

        if st.button("Dekripsi Pesan", key="extract_action", use_container_width=True, disabled=not extract_password or st.session_state["pixego_stego_image"] is None):
            try:
                hidden = extract_message(st.session_state["pixego_stego_image"], extract_password)
                try:
                    text = hidden.decode("utf-8")
                except UnicodeDecodeError:
                    text = "<data biner>"
                st.session_state["pixego_extracted_text"] = text
                st.success("Pesan berhasil diekstrak.")
            except Exception as exc:
                st.error(f"Gagal mengekstrak: {exc}")

bottom_cols = st.columns(4, gap="small")
with bottom_cols[0]:
    render_wrong_key_panel()
with bottom_cols[1]:
    render_lapisan_panel()
with bottom_cols[2]:
    render_metric_panel()
with bottom_cols[3]:
    render_method_panel()

st.markdown('</div>', unsafe_allow_html=True)
