import pymupdf as fitz


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract and combine text from all pages of a PDF document using PyMuPDF (fitz).
    """
    text_content = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text = page.get_text()
            if text:
                text_content.append(text)
    return "\n".join(text_content).strip()
