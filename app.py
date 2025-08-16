import os
import re
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# =========================
# CONFIG
# =========================
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
FORCE_OUTPUT_LANG = os.getenv("OUTPUT_LANGUAGE")

# =========================
# PyMuPDF fallback
# =========================
def extract_text_with_pymupdf(pdf_path: str) -> str:
    if not PYMUPDF_AVAILABLE:
        return "⚠️ PyMuPDF not available. Please install it (pip install PyMuPDF)."
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n\n"
        return text.strip()
    except Exception as e:
        return f"⚠️ PDF extraction failed: {e}"

# =========================
# Language detection
# =========================
def detect_output_language(text: str) -> str:
    tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', text))
    latin_chars = len(re.findall(r'[A-Za-z]', text))

    if tamil_chars > 50 and tamil_chars >= latin_chars * 1.2:
        return "ta"
    if latin_chars > 50 and latin_chars >= tamil_chars * 1.2:
        return "en"

    try:
        from langdetect import detect
        code = detect(text)
        if code.startswith("ta"): return "ta"
        if code.startswith("en"): return "en"
    except Exception:
        pass

    return "en"

def lang_code_to_name(code: str) -> str:
    return {"ta": "Tamil", "en": "English"}.get(code, "English")

# =========================
# Tools
# =========================
def load_pdf_text_tool(pdf_path: str) -> str:
    # First try LangChain PyPDFLoader
    try:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        text = "\n".join(d.page_content for d in docs)
    except Exception:
        text = ""

    # If no text extracted, fallback to PyMuPDF
    if not text.strip():
        text = extract_text_with_pymupdf(pdf_path)

    return text if text.strip() else "⚠️ No text could be extracted from this PDF."

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

prompt = PromptTemplate(
    input_variables=["question_paper", "output_language"],
    template="""
You are a Maths problem solver. 
Write ALL answers in {output_language} ONLY.

Exam paper:
{question_paper}

For each question:
- Provide EXACTLY 5 steps labeled: Step 1, Step 2, Step 3, Step 4, Step 5.
- Do NOT translate the question, just answer in {output_language}.
- Output strictly in this format:

Q1:
Step 1: ...
Step 2: ...
Step 3: ...
Step 4: ...
Step 5: ...
Final Answer: ...

Q2:
Step 1: ...
...
Final Answer: ...
"""
)

chain = prompt | llm | StrOutputParser()

def solve_math_tool(question_paper: str) -> str:
    if "No text could be extracted" in question_paper:
        return "⚠️ Cannot solve because no text was extracted."
    code = FORCE_OUTPUT_LANG if FORCE_OUTPUT_LANG in {"ta", "en"} else detect_output_language(question_paper)
    lang_name = lang_code_to_name(code)
    return chain.invoke({"question_paper": question_paper, "output_language": lang_name})

def save_to_txt_tool(answers: str, filename="answers.txt") -> str:
    with open(filename, "w", encoding="utf-8") as f:
        f.write(answers.strip() + "\n")
    return filename

# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="Maths Exam Solver", layout="wide")
st.title("📘 Maths Exam Solver")

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

        if st.button("🔍 Solve Questions"):
            with st.spinner("Solving questions... ⏳"):
                answers = solve_math_tool(pdf_text)

            st.subheader("✅ Answers")
            st.write(answers)

            # Save & download
            txt_path = save_to_txt_tool(answers)
            with open(txt_path, "rb") as f:
                st.download_button("📥 Download Answers (.txt)", f, file_name="answers.txt", mime="text/plain")
