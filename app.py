import streamlit as st
import subprocess
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

# -------------------------------------------------
# One-time Chromium install (cached by Streamlit)
# -------------------------------------------------
@st.cache_resource
def install_chromium():
    subprocess.run(
        ["playwright", "install", "chromium"],
        check=True
    )

install_chromium()

# -------------------------------------------------
# Streamlit UI
# -------------------------------------------------
st.set_page_config(page_title="HTML → PDF Engine", layout="centered")

st.title("HTML → Multi-Format PDF Generator")
st.caption("Text-selectable PDFs • Canva compatible • CSS accurate")

html_input = st.text_area(
    "Paste clean HTML (BODY content only)",
    height=260
)

renderer = st.selectbox(
    "Choose output format",
    ["A4", "Poster (1200×1500)", "PPT (16:9)"]
)

# -------------------------------------------------
# Helper: renderer → CSS + page size
# -------------------------------------------------
def renderer_config(choice):
    if choice == "A4":
        return {
            "css": "a4.css",
            "pdf": {"format": "A4"}
        }
    if choice == "Poster (1200×1500)":
        return {
            "css": "poster.css",
            "pdf": {"width": "1200px", "height": "1500px"}
        }
    return {
        "css": "slides.css",
        "pdf": {"width": "1280px", "height": "720px"}
    }

# -------------------------------------------------
# Preview (HTML)
# -------------------------------------------------
if html_input:
    cfg = renderer_config(renderer)

    preview_html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="styles/base.css">
<link rel="stylesheet" href="styles/{cfg['css']}">
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

# -------------------------------------------------
# PDF Generation (THE IMPORTANT PART)
# -------------------------------------------------
if st.button("Generate PDF"):
    if not html_input.strip():
        st.error("Please paste HTML first.")
        st.stop()

    cfg = renderer_config(renderer)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        html_file = td / "doc.html"
        pdf_file = td / "output.pdf"

        html_file.write_text(preview_html, encoding="utf-8")

        with sync_playwright() as p:
            browser = p.chromium.launch()
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
            "Download PDF",
            data=pdf_file.read_bytes(),
            file_name="nirnay_output.pdf",
            mime="application/pdf"
        )
