from supabase import create_client
import hashlib
import json
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()
url = os.getenv("PROJECT_URL")
key = os.getenv("SUPERBASE_API_KEY")

def get_supabase_client():
    return create_client(url, key)

def compute_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def save_questions_to_db(file_hash: str, filename: str, questions: list):
    supabase = get_supabase_client()
    data = {
        "file_hash": file_hash,
        "filename": filename,
        "questions": questions
    }
    supabase.table("exam_files").upsert(data).execute()

def load_questions_from_db(file_hash: str):
    supabase = get_supabase_client()
    res = supabase.table("exam_files").select("questions").eq("file_hash", file_hash).execute()
    if res.data:
        return res.data[0]["questions"]
    return None

def list_all_files():
    supabase = get_supabase_client()
    res = supabase.table("exam_files").select("id, filename, file_hash, questions").execute()
    return res.data
