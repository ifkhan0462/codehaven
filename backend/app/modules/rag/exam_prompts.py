from __future__ import annotations

from app.modules.rag.schemas import ExamGenerateRequest, SourceChunk


def build_rag_qa_messages(
    question: str,
    sources: list[SourceChunk],
) -> list[dict[str, str]]:
    context_blocks = []
    for s in sources:
        context_blocks.append(
            f"=== Source Document: {s.filename} (Section {s.chunk_index}) ===\n{s.text}"
        )
    context_str = "\n\n".join(context_blocks)

    system_prompt = (
        "You are CodeHaven's Offline Academic Assistant for students.\n"
        "Your task is to answer the student's question using the provided lecture notes and documentation excerpts.\n"
        "Guidelines:\n"
        "1. Base your answer primarily on the provided source excerpts.\n"
        "2. Cite your sources clearly using the format [Source: <filename>, Section <number>].\n"
        "3. Provide clean code snippets or formulas if relevant.\n"
        "4. If the provided excerpts do not contain the complete answer, state clearly: "
        "'Based on your uploaded notes, ...' and provide the best available answer without hallucinating facts."
    )

    user_prompt = (
        f"CONTEXT FROM UPLOADED NOTES:\n"
        f"{context_str}\n\n"
        f"STUDENT QUESTION:\n{question}\n\n"
        f"Please provide a clear, comprehensive, and grounded answer with citations."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_exam_paper_messages(
    request: ExamGenerateRequest,
    notes_content: str,
) -> list[dict[str, str]]:
    system_prompt = (
        "You are an experienced University Professor and Examination Board Setter.\n"
        "Your duty is to generate a comprehensive, authentic, high-quality College Reference Examination Paper "
        "grounded strictly in the student's uploaded subject notes and syllabus.\n"
        "The exam must follow standard university academic evaluation standards."
    )

    difficulty_desc = {
        "easy": "Fundamental concepts, core definitions, basic code traces, and straightforward application.",
        "medium": "Balanced mix of theoretical comprehension, problem-solving, algorithms, edge-cases, and coding.",
        "hard": "Advanced design questions, deep analysis, optimization, multi-concept synthesis, and rigorous coding.",
    }.get(request.difficulty, "Standard University Level")

    user_prompt = f"""Generate an official Reference Examination Paper based on the provided notes.

EXAMINATION DETAILS:
- Subject / Course: {request.subject}
- Paper Title: {request.title}
- Target Difficulty: {request.difficulty.upper()} ({difficulty_desc})
- Maximum Marks: {request.total_marks} Marks
- Duration: {request.duration_minutes} Minutes

UPLOADED NOTES CONTENT:
\"\"\"
{notes_content}
\"\"\"

FORMATTING REQUIREMENTS:
Format the output in clean, professional Markdown with this exact structure:

# {request.title}
**Subject:** {request.subject} | **Time Allowed:** {request.duration_minutes} Minutes | **Max. Marks:** {request.total_marks}

---

### INSTRUCTIONS TO CANDIDATES:
1. Answer all sections as per given instructions.
2. Figures to the right indicate full marks.
3. Assume suitable data wherever necessary and state it clearly.
4. Neat diagrams and clean code snippets must be provided wherever relevant.

---

### SECTION A: MULTIPLE CHOICE QUESTIONS (MCQs)
- Provide multiple choice questions covering key terms and concepts from the notes.
- Each MCQ must have 4 options: (A), (B), (C), (D) and mark allocation e.g., `[1 Mark]` or `[2 Marks]`.

---

### SECTION B: SHORT ANSWER & CONCEPTUAL QUESTIONS
- 3 to 5 conceptual questions (definitions, differences, complexity analysis, code output prediction).
- Indicate marks for each e.g., `[5 Marks]`.

---

### SECTION C: LONG ANSWER & PRACTICAL IMPLEMENTATION QUESTIONS
- 2 to 4 in-depth problem-solving or coding questions (algorithm design, step-by-step implementation, case study).
- Indicate marks for each e.g., `[10 Marks]`.

---

{"### SECTION D: COMPLETE MARKING SCHEME & MODEL ANSWERS" if request.include_solutions else ""}
{"- Provide the exact Answer Key for Section A (MCQs) with explanation." if request.include_solutions else ""}
{"- Provide model answers and step-by-step marking rubrics for Sections B and C." if request.include_solutions else ""}

Generate the complete, thorough examination paper now.
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
