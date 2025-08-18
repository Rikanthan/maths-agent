from pdf2image import convert_from_path
import pytesseract
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
import os
import re

# def extract_text_with_ocr(pdf_path):
#     pages = convert_from_path(pdf_path)
#     text = ""
#     for i, page in enumerate(pages):
#         text += pytesseract.image_to_string(page, lang="eng+tam")  
#         text += "\n\n"
#     return text

load_dotenv()
FORCE_OUTPUT_LANG = os.getenv("OUTPUT_LANGUAGE")

try:
    from pdf2image import convert_from_path
    import pytesseract
    from pytesseract import TesseractNotFoundError
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def extract_text_with_ocr(pdf_path: str) -> str:
    if not OCR_AVAILABLE:
        return "⚠️ OCR not available (Poppler or Tesseract not installed)."
    try:
        pages = convert_from_path(pdf_path)
        text = ""
        for page in pages:
            try:
                text += pytesseract.image_to_string(page, lang="eng+tam")
            except TesseractNotFoundError:
                return "⚠️ Tesseract not installed. Install it for OCR support."
            text += "\n\n"
        return text.strip()
    except Exception as e:
        return f"⚠️ OCR failed: {e}"
    

def detect_output_language(text: str) -> str:
    tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', text))
    latin_chars = len(re.findall(r'[A-Za-z]', text))

    if FORCE_OUTPUT_LANG in {"ta", "en"}:
        return FORCE_OUTPUT_LANG
    return "ta" if tamil_chars > latin_chars else "en"

def lang_code_to_name(code: str) -> str:
    return {"ta": "Tamil", "en": "English"}.get(code, "English")

def load_pdf_text_tool(pdf_path: str) -> str:
    try:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        text = "\n".join(d.page_content for d in docs)
    except Exception:
        text = ""

    if not text.strip():
        text = extract_text_with_ocr(pdf_path)

    return text if text.strip() else "⚠️ No text could be extracted from this PDF."
