import re

def split_questions(text: str):
    """
    Split text into questions based on patterns like:
    Q1:, Q2:, 1., 2., 1), 2), 01), 02), etc.
    """
    parts = re.split(r"(?:\n?(?:Q?\d{1,2}[\.:)]))", text)
    return [q.strip() for q in parts if q.strip()]

def save_to_txt_tool(answers: list, filename="answers.txt") -> str:
    with open(filename, "w", encoding="utf-8") as f:
        for ans in answers:
            f.write(ans.strip() + "\n\n")
    return filename

