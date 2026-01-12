from __future__ import annotations

from pathlib import Path
from typing import List

import requests


def read_file(file_path: str) -> str:
    p = Path(file_path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(str(p))
    if p.is_dir():
        raise IsADirectoryError(str(p))
    if p.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("File too large (>2MB) for review via this endpoint")
    return p.read_text(encoding="utf-8", errors="replace")


def list_directory(dir_path: str) -> List[dict]:
    p = Path(dir_path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(str(p))
    if not p.is_dir():
        raise NotADirectoryError(str(p))
    items = []
    for entry in sorted(p.iterdir()):
        try:
            stat = entry.stat()
            items.append(
                {
                    "name": entry.name,
                    "path": str(entry),
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size,
                }
            )
        except PermissionError:
            items.append(
                {
                    "name": entry.name,
                    "path": str(entry),
                    "is_dir": entry.is_dir(),
                    "size": None,
                }
            )
    return items


def _build_review_prompt(code: str, language: str) -> str:
    return (
        "You are an expert code reviewer. Analyze this {language} code and provide:\n\n"
        "1. Code Quality (1-10): Rate overall quality\n"
        "2. Issues Found: List bugs, anti-patterns, security issues\n"
        "3. Suggestions: Specific improvements with code examples\n"
        "4. Best Practices: What's done well\n\n"
        "Code to review (start):\n"
        "```{language}\n{code}\n```\n"
        "Code to review (end).\n\n"
        "Format your response in clear sections with markdown headings."
    ).format(language=language, code=code)


def review_code(*, code: str, language: str, model: str, ollama_url: str) -> str:
    prompt = _build_review_prompt(code, language)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    url = f"{ollama_url.rstrip('/')}/api/generate"
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "")
