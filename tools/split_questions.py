import re

import re

def split_questions(text: str):
    """Split text into candidate questions and keep only math-related ones (any language)."""
    # Remove exam headers -> cut everything before first "1." or "1)"
    match = re.search(r"(?:\n?1[\.\)])", text)
    if match:
        text = text[match.start():]

    # Split by 1., 2., 3) etc.
    parts = re.split(r"(?:\n?\d+[\.\)])", text)
    questions = [q.strip() for q in parts if q.strip()]

    valid = []
    math_pattern = r"[0-9]|[\+\-\*/=\^√∑π%<>≤≥]"

    for q in questions:
        if re.search(math_pattern, q) and len(q.split()) > 2:
            valid.append(q)

    return questions, valid 


def save_to_txt_tool(answers: list, filename="answers.txt") -> str:
    with open(filename, "w", encoding="utf-8") as f:
        for ans in answers:
            f.write(ans.strip() + "\n\n")
    return filename

