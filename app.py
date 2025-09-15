import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client
from google.api_core.exceptions import ResourceExhausted

# LangChain imports
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain.vectorstores import SupabaseVectorStore

# Custom tools
from tools.convert_image_to_pdf import load_pdf_text_tool, detect_output_language, lang_code_to_name
from tools.split_questions import save_to_txt_tool, split_questions
from tools.superbase_db_functions import compute_file_hash

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
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

groq_api_key = os.getenv("GROQ_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
ENVIRONMENT = os.getenv("ENVIRONMENT")

if ENVIRONMENT == "dev":
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    os.environ["TESSDATA_PREFIX"] = os.path.join(os.getcwd(), "tessdata")

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
gemini_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
groq_llm = ChatGroq(model_name="groq/compound-mini", api_key=groq_api_key)


# =========================
# Prompt Template (query version for .run)
# =========================
exam_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are an English exam assistant. Use the context from the syllabus to answer.

Context:
{context}

Question:
{question}

Answer in tamil:
"""
)


# =========================
# Supabase Helpers
# =========================

def save_questions_to_supabase(file_hash: str, filename: str, questions: list[str]):
    for q in questions:
        emb = embeddings.embed_query(q)
        supabase.table("documents").insert({
            "content": q,
            "metadata": {"file": filename, "hash": file_hash},
            "embedding": emb
        }).execute()


def load_questions_from_supabase(file_hash: str):
    result = supabase.table("documents").select("content").filter("metadata->>hash", "eq", file_hash).execute()
    if result.data:
        return [row["content"] for row in result.data]
    return None


# =========================
# Retrieval Function (.run with query)
# =========================

def get_relevant_answer(query, embeddings, primary_llm, fallback_llm, output_lang):
    vectorstore = SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name="documents",
        query_name="match_documents"
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    rag_chain = RetrievalQA.from_chain_type(
        llm=primary_llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": exam_prompt}
    )

    try:
        # ✅ Use .run() with key 'query'
        result = rag_chain.run({
            "query": query
        })
    except ResourceExhausted:
        st.warning("⚠️ Quota exceeded for Gemini. Switching to Groq...")
        rag_chain = RetrievalQA.from_chain_type(
            llm=fallback_llm,
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": exam_prompt}
        )
        result = rag_chain.run({
            "query": query
        })

    if "Sorry" not in result:
        return f"📂 (Matched in Supabase): {result}"

    return "❌ Sorry, question is out of the syllabus."


# =========================
# Streamlit UI
# =========================

st.set_page_config(page_title="English Exam Solver", layout="wide")
st.title("📘 English Exam Solver (Live Question-by-Question)")

if "stop" not in st.session_state:
    st.session_state["stop"] = False

# Step 1: Language selection
selected_lang = st.selectbox(
    "Select output language:",
    options=["auto", "en", "ta", "si"],
    format_func=lambda x: lang_code_to_name(x) if x != "auto" else "Auto Detect"
)

# Step 2: Upload PDF
uploaded_file = st.file_uploader("Upload your English exam PDF", type=["pdf"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    file_hash = compute_file_hash(file_bytes)

    # Load questions from Supabase
    existing_questions = load_questions_from_supabase(file_hash)

    if existing_questions:
        st.success("✅ Loaded questions from Supabase (already processed).")
        all_questions, valid_questions = existing_questions, existing_questions
    else:
        temp_path = "temp.pdf"
        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        st.info("📄 Extracting text...")
        pdf_text = load_pdf_text_tool(temp_path)

        if "⚠️" in pdf_text:
            st.error(pdf_text)
        else:
            all_questions, valid_questions = split_questions(pdf_text)
            save_questions_to_supabase(file_hash, uploaded_file.name, valid_questions)
            st.success("✅ Questions extracted and stored in Supabase.")

    # Auto language detection
    if selected_lang == "auto":
        code = detect_output_language(" ".join(valid_questions))
        st.caption(f"📌 Auto-detected language: **{lang_code_to_name(code)}**")
    else:
        code = selected_lang

    lang_name = lang_code_to_name(code)

    if st.button("⏹ Stop Solving"):
        st.session_state["stop"] = True

    if st.button("🔍 Solve One by One"):
        st.session_state["stop"] = False

        total_count = len(all_questions)
        valid_count = len(valid_questions)
        invalid_count = total_count - valid_count
        answered_count = 0

        if not valid_questions:
            st.error("❌ No valid questions detected.")
        else:
            st.success(f"✅ Detected {valid_count} valid questions out of {total_count} total.")
            answers = []
            container = st.container()

            for idx, q in enumerate(valid_questions, start=1):
                if st.session_state["stop"]:
                    st.warning("⏹ Solving stopped by user.")
                    break

                with st.spinner(f"Solving Q{idx}..."):
                    answer = get_relevant_answer(q, embeddings, gemini_llm, groq_llm, lang_name)
                    st.write("### 📌 Result:", answer)
                    if answer and "not related" not in answer.lower():
                        answered_count += 1
                        formatted = f"### Q{idx}:\n{answer}"
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
