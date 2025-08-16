from pdf2image import convert_from_path
import pytesseract

def extract_text_with_ocr(pdf_path):
    pages = convert_from_path(pdf_path)
    text = ""
    for i, page in enumerate(pages):
        text += pytesseract.image_to_string(page, lang="eng+tam")  
        text += "\n\n"
    return text
