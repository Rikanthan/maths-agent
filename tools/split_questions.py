import re

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

def split_questions(text: str):
    """Split text by Test sections only, ignore everything before Test 1."""

    # Normalize spacing (handles Test1 / Test 1)
    text = re.sub(r"(Test\s*\d+)", r"\n\1", text, flags=re.IGNORECASE)

    # Cut everything before Test 1
    match = re.search(r"(?:Test\s*1)", text, flags=re.IGNORECASE)
    if match:
        text = text[match.start():]

    # Split by Test labels only
    parts = re.split(r"(?:Test\s*\d+)", text, flags=re.IGNORECASE)

    # Clean
    sections = [p.strip() for p in parts if p.strip()]

    print(f'split test sections count: {len(sections)} ')
    return sections, sections


def save_to_txt_tool(answers: list, filename="answers.txt") -> str:
    with open(filename, "w", encoding="utf-8") as f:
        for ans in answers:
            f.write(ans.strip() + "\n\n")
    return filename

