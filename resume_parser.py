import fitz  # PyMuPDF

def extract_text(path):
    text = ""
    doc = fitz.open(path)
    for page in doc:
        text += page.get_text()
    return text.strip()
