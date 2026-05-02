"""
卡牌 ID → 名稱對照表（優先繁中，fallback 英文）。
使用 HearthstoneJSON API 取得，結果快取至 data/cards_cache.json。
"""
import json
import os
import requests

CACHE_PATH = os.path.join(os.path.dirname(__file__), "data", "cards_cache.json")
API_ZH_TW = "https://api.hearthstonejson.com/v1/latest/zhTW/cards.json"
API_EN_US = "https://api.hearthstonejson.com/v1/latest/enUS/cards.json"

_card_map: dict[str, str] = {}


def _fetch_cards(url: str) -> list[dict]:
    print(f"[card_db] 下載卡牌資料：{url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _build_map(zh_cards: list[dict], en_cards: list[dict]) -> dict[str, str]:
    """建立 cardId → 繁中名稱（無則英文）的對照表。"""
    en_map = {c["id"]: c.get("name", c["id"]) for c in en_cards if "id" in c}
    result = {}
    for c in zh_cards:
        cid = c.get("id")
        if not cid:
            continue
        name = c.get("name") or en_map.get(cid, cid)
        result[cid] = name
    # 補上只有英文的卡牌
    for cid, name in en_map.items():
        if cid not in result:
            result[cid] = name
    return result


def load_card_db(force_refresh: bool = False) -> dict[str, str]:
    """載入卡牌對照表，優先使用快取。"""
    global _card_map

    if _card_map and not force_refresh:
        return _card_map

    if os.path.exists(CACHE_PATH) and not force_refresh:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            _card_map = json.load(f)
        print(f"[card_db] 從快取載入 {len(_card_map)} 張卡牌")
        return _card_map

    try:
        zh_cards = _fetch_cards(API_ZH_TW)
        en_cards = _fetch_cards(API_EN_US)
        _card_map = _build_map(zh_cards, en_cards)
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_card_map, f, ensure_ascii=False)
        print(f"[card_db] 已快取 {len(_card_map)} 張卡牌")
    except Exception as e:
        print(f"[card_db] 無法下載卡牌資料：{e}，使用空對照表")
        _card_map = {}

    return _card_map


def get_card_name(card_id: str) -> str:
    """取得卡牌名稱，找不到則回傳 card_id。"""
    return _card_map.get(card_id, card_id)


if __name__ == "__main__":
    db = load_card_db(force_refresh=True)
    print(f"總共 {len(db)} 張卡牌")
