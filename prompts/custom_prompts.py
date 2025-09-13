from langchain.prompts import PromptTemplate

maths_prompt = PromptTemplate(
    input_variables=["question", "output_language"],
    template="""
You are a Maths problem resolver.
Write ALL answers in {output_language} ONLY.

Question:
{question}

Rules:
- Check the question in related to maths or not.
- If yes, then answer the question.
- If no, then say "This question is not related to maths." don't solve that problem
 and move to next question.
- Provide EXACTLY 5 steps labeled Step 1 ... Step 5.
- Translate the question.
- Format:

Qn:
Step 1: ...
Step 2: ...
Step 3: ...
Step 4: ...
Step 5: ...
Final Answer: ...
"""
)

prompt = PromptTemplate(
    input_variables=["question", "output_language"],
    template="""
You are a history exam resolver.
Write ALL answers in {output_language}.
There are 40 muliple choice questions.
Format will be 
1. {question}
(1) option1 (2) option2 (3) option3 (4) option4
upto 40.

skip the question from part I
Answer the questions from part II

Question:
{question}

Rules:
- read the question.
- if it is mcq select one answer
- if it is a essay question contains brief or describe please describe
- sometimes it might related to picture.
- please answer to the question
Final Answer: ...
"""
)