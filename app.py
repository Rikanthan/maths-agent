import os
import re
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from prompts.custom_prompts import prompt
from langchain.schema import StrOutputParser
from tools.convert_image_to_pdf import load_pdf_text_tool,detect_output_language, lang_code_to_name
from tools.split_questions import save_to_txt_tool, split_questions

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

chain = prompt | llm | StrOutputParser()

def solve_one_question(question: str, lang_name: str) -> str:
    return chain.invoke({"question": question, "output_language": lang_name})

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
