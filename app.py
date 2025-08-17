import os
import re
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader

# OCR (optional fallback)
try:
    from pdf2image import convert_from_path
    import pytesseract
    from pytesseract import TesseractNotFoundError
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# =========================
# CONFIG
# =========================
load_dotenv()
FORCE_OUTPUT_LANG = os.getenv("OUTPUT_LANGUAGE")
ENVIRONMENT = os.getenv("ENVIRONMENT")

if ENVIRONMENT == "dev":
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    os.environ["TESSDATA_PREFIX"] = os.path.join(os.getcwd(), "tessdata")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

prompt = PromptTemplate(
    input_variables=["question", "output_language"],
    template="""
You are a Maths problem solver. 
Write ALL answers in {output_language} ONLY.

Question:
{question}

Rules:
- Provide EXACTLY 5 steps labeled Step 1 ... Step 5.
- Translate the question.
- Format:

Qn:
Step 1: ...
Step 2: ...
Step 3: ...
Step 4: ...
Step 5: ...
Final Answer: ...
"""
)
chain = prompt | llm | StrOutputParser()

# =========================
# OCR fallback
# =========================
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

# =========================
# Language detection
# =========================
def detect_output_language(text: str) -> str:
    tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', text))
    latin_chars = len(re.findall(r'[A-Za-z]', text))

    if FORCE_OUTPUT_LANG in {"ta", "en"}:
        return FORCE_OUTPUT_LANG
    return "ta" if tamil_chars > latin_chars else "en"

def lang_code_to_name(code: str) -> str:
    return {"ta": "Tamil", "en": "English"}.get(code, "English")

# =========================
# Tools
# =========================
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

def split_questions(text: str):
    """Split text into questions based on Q1:, Q2:, 1), 2), etc."""
    parts = re.split(r"(?:\n?\d+\.)", text)
    return [q.strip() for q in parts if q.strip()]

def solve_one_question(question: str, lang_name: str) -> str:
    return chain.invoke({"question": question, "output_language": lang_name})

def save_to_txt_tool(answers: list, filename="answers.txt") -> str:
    with open(filename, "w", encoding="utf-8") as f:
        for ans in answers:
            f.write(ans.strip() + "\n\n")
    return filename

# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="Maths Exam Solver", layout="wide")
st.title("📘 Maths Exam Solver (Live Question-by-Question)")

uploaded_file = st.file_uploader("Upload your Maths exam PDF", type=["pdf"])

if uploaded_file is not None:
    temp_path = "temp.pdf"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    st.info("📄 Extracting text...")
    pdf_text = load_pdf_text_tool(temp_path)

    if "⚠️" in pdf_text:
        st.error(pdf_text)
    else:
        st.text_area("Extracted Text", pdf_text[:3000] + "...", height=200)

        if st.button("🔍 Solve One by One"):
            questions = split_questions(pdf_text)
            if not questions:
                st.error("❌ No questions detected.")
            else:
                st.success(f"✅ Detected {len(questions)} questions.")
                code = detect_output_language(pdf_text)
                lang_name = lang_code_to_name(code)

                answers = []
                container = st.container()

                for idx, q in enumerate(questions, start=1):
                    with st.spinner(f"Solving Q{idx}..."):
                        ans = solve_one_question(q, lang_name)
                        formatted = f"### Q{idx}:\n{ans}"
                        answers.append(formatted)
                        container.markdown(formatted)  # ✅ update UI immediately

                # Save & download
                txt_path = save_to_txt_tool(answers)
                with open(txt_path, "rb") as f:
                    st.download_button("📥 Download Answers (.txt)", f, file_name="answers.txt", mime="text/plain")
