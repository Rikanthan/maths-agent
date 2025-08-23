import os
import re
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from prompts.custom_prompts import prompt
from langchain.schema import StrOutputParser
from tools.convert_image_to_pdf import load_pdf_text_tool, detect_output_language, lang_code_to_name
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

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, disable_streaming=False)
chain = prompt | llm | StrOutputParser()

# =========================
# Solve question with streaming
# =========================
def solve_one_question_stream(question: str, lang_name: str) -> str:
    partial_answer = ""
    for chunk in chain.stream({"question": question, "output_language": lang_name}):
        if st.session_state.get("stop", False):
            print("[TRACE] Stop triggered during streaming!")
            break
        if isinstance(chunk, str):
            partial_answer += chunk
            print(f"[TRACE] Streaming chunk: {chunk[:40]}...")
    return partial_answer.strip()

# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="English Exam Solver", layout="wide")
st.title("📘 English Exam Solver (Live Question-by-Question)")

if "stop" not in st.session_state:
    st.session_state["stop"] = False

# Step 1: User selects language
selected_lang = st.selectbox(
    "Select output language:",
    options=["auto", "en", "ta", "si"],
    format_func=lambda x: lang_code_to_name(x) if x != "auto" else "Auto Detect"
)

# Step 2: Upload PDF
uploaded_file = st.file_uploader("Upload your English exam PDF", type=["pdf"])

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

        # Language selection
        if selected_lang == "auto":
            code = detect_output_language(pdf_text)
            st.caption(f"📌 Auto-detected language: **{lang_code_to_name(code)}**")
        else:
            code = selected_lang

        lang_name = lang_code_to_name(code)

        if st.button("⏹ Stop Solving"):
            st.session_state["stop"] = True

        if st.button("🔍 Solve One by One"):
            st.session_state["stop"] = False

            # Split and filter
            all_questions, valid_questions = split_questions(pdf_text)
            total_count = len(all_questions)
            valid_count = len(valid_questions)
            invalid_count = total_count - valid_count
            answered_count = 0

            if not valid_questions:
                st.error("❌ No valid math questions detected.")
            else:
                st.success(f"✅ Detected {valid_count} valid math questions out of {total_count} total.")
                answers = []
                container = st.container()

                for idx, q in enumerate(valid_questions, start=1):
                    if st.session_state["stop"]:
                        st.warning("⏹ Solving stopped by user.")
                        break

                    with st.spinner(f"Solving Q{idx}..."):
                        ans = solve_one_question_stream(q, lang_name)
                        if ans and "not related to maths" not in ans.lower():
                            answered_count += 1
                            formatted = f"### Q{idx}:\n{ans}"
                            answers.append(formatted)
                            container.markdown(formatted)

                # Summary
                st.subheader("📊 Summary")
                st.write(f"- Total questions detected: **{total_count}**")
                st.write(f"- Valid questions: **{valid_count}**")
                st.write(f"- Invalid / ignored questions: **{invalid_count}**")
                st.write(f"- Answered questions: **{answered_count}**")

                # Save & download answers
                if answers:
                    txt_path = save_to_txt_tool(answers)
                    with open(txt_path, "rb") as f:
                        st.download_button(
                            "📥 Download Answers (.txt)",
                            f,
                            file_name="answers.txt",
                            mime="text/plain",
                        )