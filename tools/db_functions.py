import sqlite3
import hashlib
import json

# ======================
# DB Setup
# ======================
DB_PATH = "questions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_hash TEXT UNIQUE,
            filename TEXT,
            questions TEXT
        )
    """)
    conn.commit()
    conn.close()

def compute_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def save_questions_to_db(file_hash: str, filename: str, questions: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO exam_files (file_hash, filename, questions)
        VALUES (?, ?, ?)
    """, (file_hash, filename, json.dumps(questions)))
    conn.commit()
    conn.close()

def load_questions_from_db(file_hash: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT questions FROM exam_files WHERE file_hash = ?", (file_hash,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None
