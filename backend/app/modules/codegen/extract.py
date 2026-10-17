import re

FENCE_RE = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    blocks = FENCE_RE.findall(text)
    return blocks[0].strip() if blocks else text.strip()


def extract_explanation(text: str, code: str) -> str | None:
    without_code = text.replace(f"```{code}```", "").strip()
    without_code = FENCE_RE.sub("", without_code).strip()
    return without_code or None
