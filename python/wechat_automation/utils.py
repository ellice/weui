from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Sequence

from .models import MessageChunk, SessionType

_KEY_ALIASES = {
    "ctrl": "^",
    "control": "^",
    "alt": "%",
    "shift": "+",
    "win": "{VK_LWIN}",
    "windows": "{VK_LWIN}",
    "enter": "{ENTER}",
    "return": "{ENTER}",
    "esc": "{ESC}",
    "escape": "{ESC}",
    "tab": "{TAB}",
    "backspace": "{BACKSPACE}",
    "space": " ",
    "newline": "{ENTER}",
    "linebreak": "{ENTER}",
    "up": "{UP}",
    "down": "{DOWN}",
    "left": "{LEFT}",
    "right": "{RIGHT}",
    "pageup": "{PGUP}",
    "pagedown": "{PGDN}",
    "delete": "{DELETE}",
}


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def ensure_paths(paths: str | Path | Iterable[str | Path]) -> tuple[Path, ...]:
    if isinstance(paths, (str, Path)):
        raw_paths: Iterable[str | Path] = [paths]
    else:
        raw_paths = paths
    resolved = tuple(Path(item).expanduser() for item in raw_paths)
    if not resolved:
        raise ValueError("at least one path is required")
    return resolved


def split_long_text(text: str, max_chunk_length: int = 500) -> list[MessageChunk]:
    if max_chunk_length <= 0:
        raise ValueError("max_chunk_length must be positive")

    normalized = normalize_newlines(text)
    if normalized == "":
        return [MessageChunk(content="", index=0, is_last=True)]

    chunks: list[str] = []
    paragraphs = normalized.split("\n")
    current = ""

    for paragraph in paragraphs:
        segment = paragraph if not current else f"\n{paragraph}"
        if len(current) + len(segment) <= max_chunk_length:
            current += segment
            continue

        if current:
            chunks.append(current)
            current = ""

        while len(paragraph) > max_chunk_length:
            chunks.append(paragraph[:max_chunk_length])
            paragraph = paragraph[max_chunk_length:]

        current = paragraph

    if current:
        chunks.append(current)

    return [
        MessageChunk(content=chunk, index=index, is_last=index == len(chunks) - 1)
        for index, chunk in enumerate(chunks)
    ]


def infer_session_type(name: str, raw_text: str = "") -> SessionType:
    combined = f"{name} {raw_text}".strip()
    if not combined:
        return "unknown"

    if re.search(r"[\(（]\d+[\)）]\s*$", name):
        return "group"
    if any(keyword in combined for keyword in ("群聊", "群成员", "group chat", "chat members")):
        return "group"
    if any(keyword in combined for keyword in ("订阅号", "公众号", "service account")):
        return "unknown"
    return "private"


def normalize_hotkey(keys: str | Sequence[str]) -> str:
    if isinstance(keys, str):
        return keys

    if not keys:
        raise ValueError("keys must not be empty")

    normalized_tokens = [_KEY_ALIASES.get(token.strip().lower(), token) for token in keys]
    modifier_prefix = "".join(token for token in normalized_tokens[:-1] if token in {"^", "%", "+"})
    final_token = normalized_tokens[-1]

    extra_tokens = [token for token in normalized_tokens[:-1] if token not in {"^", "%", "+"}]
    if extra_tokens:
        raise ValueError(f"unsupported modifier tokens: {extra_tokens}")

    return f"{modifier_prefix}{final_token}"
