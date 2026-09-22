from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "data" / "knowledge"
TOKEN_RE = re.compile(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def load_chunks() -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        sections = [part.strip() for part in re.split(r"\n(?=##?\s)", content) if part.strip()]
        for index, section in enumerate(sections):
            chunks.append({"chunk_id": f"{path.stem}-{index + 1}", "source": path.name, "text": section})
    return chunks


def retrieve(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    chunks = load_chunks()
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    documents = [tokenize(chunk["text"]) for chunk in chunks]
    document_frequency = Counter(token for tokens in documents for token in set(tokens))
    query_counts = Counter(query_tokens)

    def weight(token: str, count: int, length: int) -> float:
        idf = math.log((1 + len(documents)) / (1 + document_frequency[token])) + 1
        return (count / max(length, 1)) * idf

    query_vector = {token: weight(token, count, len(query_tokens)) for token, count in query_counts.items()}
    query_norm = math.sqrt(sum(value * value for value in query_vector.values())) or 1.0
    results = []
    for chunk, tokens in zip(chunks, documents):
        counts = Counter(tokens)
        vector = {token: weight(token, count, len(tokens)) for token, count in counts.items()}
        score = sum(query_vector.get(token, 0.0) * value for token, value in vector.items())
        score /= query_norm * (math.sqrt(sum(value * value for value in vector.values())) or 1.0)
        if score > 0:
            results.append({**chunk, "score": round(score, 4)})
    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]


def assemble_context(results: list[dict[str, Any]]) -> str:
    return "\n\n".join(f"[{item['source']} / {item['chunk_id']}]\n{item['text']}" for item in results)

