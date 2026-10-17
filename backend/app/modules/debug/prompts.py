def build_debug_messages(
    code: str,
    language: str,
    error_message: str | None,
    parsed: dict[str, str | int | None],
) -> list[dict[str, str]]:
    system = (
        "You are CodeHaven, an offline debugging assistant for students. "
        f"Language: {language}. "
        "Analyze the code and any error carefully. "
        "Respond in this exact structure:\n\n"
        "**Diagnosis** — one sentence stating what is wrong\n\n"
        "**Explanation** — 2-4 sentences explaining why it happens (teach the concept)\n\n"
        "**Fixed code** — one fenced code block with the corrected, runnable code\n\n"
        "If the code looks correct and no error was given, say so and suggest improvements. "
        "Do not invent errors that are not present."
    )

    user_parts = [f"Code to debug:\n```{language}\n{code}\n```"]
    if error_message:
        user_parts.append(f"Error / traceback:\n```\n{error_message}\n```")
    if parsed.get("exception"):
        line = parsed.get("line")
        line_hint = f" at line {line}" if line else ""
        user_parts.append(f"Detected: {parsed['exception']}{line_hint}")

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]
