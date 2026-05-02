"""
爐石傳說牌庫查詢模組（含費用、攻擊、血量、牌文）
"""
import json
import os
import re

_DB: dict = {}
_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "hs_cards_full.json")


def load() -> dict:
    global _DB
    if _DB:
        return _DB
    path = os.path.normpath(_DB_PATH)
    with open(path, encoding="utf-8") as f:
        _DB = json.load(f)
    return _DB


def get(card_id: str) -> dict:
    db = load()
    return db.get(card_id, {})


def name(card_id: str) -> str:
    return get(card_id).get("name", card_id)


def cost(card_id: str) -> int:
    c = get(card_id).get("cost")
    return c if c is not None else 0


def card_type(card_id: str) -> str:
    return get(card_id).get("type", "")


def atk(card_id: str) -> int:
    return get(card_id).get("atk", 0)


def hp(card_id: str) -> int:
    return get(card_id).get("hp", 0)


def text(card_id: str) -> str:
    raw = get(card_id).get("text", "")
    return re.sub(r"<[^>]+>", "", raw).replace("\n", " ").strip()
