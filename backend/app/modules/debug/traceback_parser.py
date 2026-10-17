import re

PYTHON_EXCEPTION = re.compile(
    r"(?P<exc>[\w.]+(?:Error|Exception|Warning)):\s*(?P<msg>.+?)(?:\n|$)",
    re.MULTILINE,
)
PYTHON_LINE = re.compile(r'File ".*?", line (\d+)', re.MULTILINE)

JS_ERROR = re.compile(
    r"(?P<exc>SyntaxError|ReferenceError|TypeError|RangeError|Error):\s*(?P<msg>.+?)(?:\n|$)",
    re.MULTILINE,
)
JS_LINE = re.compile(r":(\d+)(?::\d+)?(?:\n|$)")


def parse_error(text: str, language: str) -> dict[str, str | int | None]:
    """Extract exception type, message, and line hint from a traceback."""
    if not text or not text.strip():
        return {"exception": None, "message": None, "line": None}

    if language == "python":
        exc_match = PYTHON_EXCEPTION.search(text)
        line_match = PYTHON_LINE.search(text)
        if exc_match:
            return {
                "exception": exc_match.group("exc"),
                "message": exc_match.group("msg").strip(),
                "line": int(line_match.group(1)) if line_match else None,
            }

    if language in ("javascript", "typescript", "react"):
        exc_match = JS_ERROR.search(text)
        line_match = JS_LINE.search(text)
        if exc_match:
            return {
                "exception": exc_match.group("exc"),
                "message": exc_match.group("msg").strip(),
                "line": int(line_match.group(1)) if line_match else None,
            }

    first_line = text.strip().split("\n")[0]
    return {"exception": None, "message": first_line[:500], "line": None}
