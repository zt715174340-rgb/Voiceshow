from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import db, rag

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_FILE = ROOT / "data" / "products.json"


def search_products(category: str | None = None, query: str = "") -> list[dict[str, Any]]:
    products = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    if category:
        products = [item for item in products if item["category"] == category]
    if query:
        terms = [term.lower() for term in query.split() if term.strip()]
        products = [item for item in products if any(term in json.dumps(item, ensure_ascii=False).lower() for term in terms)] or products
    return products


def list_order_history(user_id: int = 1) -> list[dict[str, Any]]:
    products = {item["id"]: item["name"] for item in search_products()}
    return [{**order, "product_name": products.get(order["product_id"], "商品")} for order in db.list_orders(user_id)]


def retrieve_knowledge(query: str, top_k: int = 3) -> dict[str, Any]:
    chunks = rag.retrieve(query, top_k=top_k)
    return {"chunks": chunks, "context": rag.assemble_context(chunks), "sources": [item["source"] for item in chunks]}
