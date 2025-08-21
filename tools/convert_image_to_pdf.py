from pdf2image import convert_from_path
import pytesseract
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
import os
import re

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
                # Enable OCR for all 3 languages
                text += pytesseract.image_to_string(page, lang="eng+tam+sin")
            except TesseractNotFoundError:
                return "⚠️ Tesseract not installed. Install it for OCR support."
            text += "\n\n"
        return text.strip()
    except Exception as e:
        return f"⚠️ OCR failed: {e}"

    

def detect_output_language(text: str) -> str:
    tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', text))
    sinhala_chars = len(re.findall(r'[\u0D80-\u0DFF]', text))
    english_chars = len(re.findall(r'[A-Za-z]', text))

    if FORCE_OUTPUT_LANG in {"ta", "si", "en"}:
        return FORCE_OUTPUT_LANG
    
    # Pick the language with the most characters
    if sinhala_chars > tamil_chars and sinhala_chars > english_chars:
        return "si"
    elif tamil_chars > english_chars:
        return "ta"
    elif english_chars > 0:
        return "en"
    else:
        return "en"  # fallback default

def lang_code_to_name(code: str) -> str:
    return {"ta": "Tamil", "si": "Sinhala", "en": "English"}.get(code, "English")


def load_pdf_text_tool(pdf_path: str) -> str:
    # try:
    #     loader = PyPDFLoader(pdf_path)
    #     docs = loader.load()
    #     text = "\n".join(d.page_content for d in docs)
    # except Exception:
    #     text = ""

    # if not text.strip():
    text = extract_text_with_ocr(pdf_path)

    return text if text.strip() else "⚠️ No text could be extracted from this PDF."
