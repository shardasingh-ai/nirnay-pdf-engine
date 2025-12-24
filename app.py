import streamlit as st
import subprocess
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

# ============================================================
# Streamlit config
# ============================================================
st.set_page_config(
    page_title="HTML → PDF Engine (Nirnay)",
    layout="centered"
)

# ============================================================
# Ensure Chromium is installed (Streamlit-safe)
# ============================================================
@st.cache_resource
def install_chromium():
    subprocess.run(
        ["playwright", "install", "chromium"],
        check=True
    )

install_chromium()

# ============================================================
# UI
# ============================================================
st.title("HTML → Multi-Format PDF Generator")
st.caption("Selectable text • Accurate CSS • Canva-compatible PDFs")

html_input = st.text_area(
    "Paste clean HTML (BODY content only)",
    height=260,
    placeholder="<h1>Title</h1><h3>Why in News?</h3><p>Content…</p>"
)

renderer = st.selectbox(
    "Choose output format",
    [
        "A4",
        "Poster (1200 × 1500)",
        "PPT (16:9)"
    ]
)

# ============================================================
# Renderer configuration
# ============================================================
def renderer_config(choice):
    if choice == "A4":
        return {
            "css": "a4.css",
            "pdf": {"format": "A4"}
        }

    if choice == "Poster (1200 × 1500)":
        return {
            "css": "poster.css",
            "pdf": {
                "width": "1200px",
                "height": "1500px"
            }
        }

    # PPT (16:9)
    return {
        "css": "slides.css",
        "pdf": {
            "width": "1280px",
            "height": "720px"
        }
    }

cfg = renderer_config(renderer)

# ============================================================
# HTML Preview (browser only)
# ============================================================
if html_input.strip():
    preview_html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="styles/base.css">
<link rel="stylesheet" href="styles/{cfg['css']}">
<style>
html, body {{
  margin: 0;
  padding: 0;
}}
</style>
</head>
<body>
{html_input}
</body>
</html>
"""

    st.subheader("Preview")
    st.components.v1.html(
        preview_html,
        height=600,
        scrolling=True
    )

# ============================================================
# PDF Generation (Playwright → Chromium)
# ============================================================
if st.button("Generate PDF"):
    if not html_input.strip():
        st.error("Please paste HTML first.")
        st.stop()

    with st.spinner("Rendering PDF…"):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            html_file = td / "doc.html"
            pdf_file = td / "output.pdf"

            html_file.write_text(preview_html, encoding="utf-8")

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--no-zygote",
                        "--single-process"
                    ]
                )

                page = browser.new_page()
                page.goto(html_file.as_uri(), wait_until="networkidle")

                page.pdf(
                    path=str(pdf_file),
                    print_background=True,
                    prefer_css_page_size=True,
                    **cfg["pdf"]
                )

                browser.close()

            st.success("PDF generated successfully.")

            st.download_button(
                label="Download PDF",
                data=pdf_file.read_bytes(),
                file_name="nirnay_output.pdf",
                mime="application/pdf"
            )
