import re

from app.modules.codegen.extract import extract_code

DIAGNOSIS_RE = re.compile(
    r"\*\*Diagnosis\*\*[:\s—-]*(.+?)(?=\*\*Explanation\*\*|\*\*Fixed code\*\*|```|$)",
    re.DOTALL | re.IGNORECASE,
)
EXPLANATION_RE = re.compile(
    r"\*\*Explanation\*\*[:\s—-]*(.+?)(?=\*\*Fixed code\*\*|```|$)",
    re.DOTALL | re.IGNORECASE,
)


def extract_diagnosis(text: str) -> str:
    match = DIAGNOSIS_RE.search(text)
    if match:
        return match.group(1).strip()
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    return lines[0] if lines else "Unable to determine diagnosis."


def extract_explanation(text: str) -> str:
    match = EXPLANATION_RE.search(text)
    if match:
        return match.group(1).strip()
    without_code = re.sub(r"```[\s\S]*?```", "", text).strip()
    parts = without_code.split("\n\n")
    return parts[1].strip() if len(parts) > 1 else without_code


def extract_debug_response(text: str) -> tuple[str, str, str]:
    diagnosis = extract_diagnosis(text)
    explanation = extract_explanation(text)
    fixed_code = extract_code(text)
    return diagnosis, explanation, fixed_code
