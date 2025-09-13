import re

# def split_questions(text: str):
#     """Split text into candidate questions and keep only math-related ones (any language)."""
#     # Remove exam headers -> cut everything before first "1." or "1)"
#     match = re.search(r"(?:\n?1[\.\)])", text)
#     if match:
#         text = text[match.start():]

#     # Split by 1., 2., 3) etc.
#     parts = re.split(r"(?:\n?\d+[\.\)])", text)
#     questions = [q.strip() for q in parts if q.strip()]

#     valid = questions
#     math_pattern = r"[0-9]|[\+\-\*/=\^√∑π%<>≤≥]"
#     print(f'split questions count: {len(questions)} ')
#     for q in questions:
#         if re.search(math_pattern, q) and len(q.split()) > 2:
#             valid.append(q)
#     return questions, valid 

import re

import re

def split_questions(text: str, max_q: int = 40):
    """Extract up to max_q multiple-choice questions from text and format them."""

    # Find question blocks (e.g., 1. ... until next number)
    pattern = r"(\d+\..*?)(?=\d+\.|$)"
    questions = re.findall(pattern, text, flags=re.S)

    formatted = []
    for idx, q in enumerate(questions[:max_q], start=1):
        lines = q.strip().split("\n")
        if not lines:
            continue

        # First line = question text
        q_text = lines[0].strip()
        # Remove original numbering
        q_text_clean = re.sub(r"^\d+\.\s*", "", q_text)

        # Remaining lines = options
        opts = [line.strip() for line in lines[1:] if line.strip()]
        options_str = " ".join([f"({i+1}) {opt}" for i, opt in enumerate(opts[:4])])

        formatted.append(f"{idx}. {q_text_clean}\n{options_str}\n")

    print(f"extracted questions: {len(formatted)}")
    return formatted, formatted



def save_to_txt_tool(answers: list, filename="answers.txt") -> str:
    with open(filename, "w", encoding="utf-8") as f:
        for ans in answers:
            f.write(ans.strip() + "\n\n")
    return filename

