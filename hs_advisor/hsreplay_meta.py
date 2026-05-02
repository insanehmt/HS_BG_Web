"""
HSReplay Meta 資料抓取模組
- 每次啟動時從 HSReplay API 抓取本週標準天梯 meta
- 提供 top decks 列表（勝率、使用率、排名）
- 提供依職業查詢最強牌型
- 結果快取到本地，避免重複請求
"""
import urllib.request
import json
import os
import time
from typing import Optional

_CACHE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "hsreplay_meta_cache.json")
)
_CACHE_TTL = 3600  # 1小時更新一次

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

_ARCH_URL  = "https://hsreplay.net/api/v1/archetypes/"
_STATS_URL = (
    "https://hsreplay.net/analytics/query/archetype_popularity_distribution_stats_v2/"
    "?GameType=RANKED_STANDARD&RankRange=LEGEND_THROUGH_DIAMOND_4&TimeRange=LAST_7_DAYS"
)
_HSCARD_URL = "https://api.hearthstonejson.com/v1/latest/zhTW/cards.json"

# 職業名稱對照（英文 -> 中文）
CLASS_ZH = {
    "DEATHKNIGHT": "死亡騎士",
    "DEMONHUNTER": "惡魔獵人",
    "DRUID":       "德魯伊",
    "HUNTER":      "獵人",
    "MAGE":        "法師",
    "PALADIN":     "聖騎士",
    "PRIEST":      "牧師",
    "ROGUE":       "盜賊",
    "SHAMAN":      "薩滿",
    "WARLOCK":     "術士",
    "WARRIOR":     "戰士",
}


def _fetch_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def _load_cache() -> Optional[dict]:
    if not os.path.exists(_CACHE_PATH):
        return None
    try:
        with open(_CACHE_PATH, encoding="utf-8") as f:
            cache = json.load(f)
        if time.time() - cache.get("fetched_at", 0) < _CACHE_TTL:
            return cache
    except Exception:
        pass
    return None


def _save_cache(data: dict):
    data["fetched_at"] = time.time()
    os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
    with open(_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def fetch_meta(force: bool = False) -> dict:
    """
    回傳 meta 資料字典：
    {
      "fetched_at": <timestamp>,
      "as_of": <ISO date str>,
      "decks": [
        {
          "rank": 1,
          "archetype_id": 851,
          "name": "Aggro Paladin",
          "class": "PALADIN",
          "class_zh": "聖騎士",
          "win_rate": 64.5,
          "pct_of_total": 3.7,
          "total_games": 19000,
          "core_cards": ["CS3_032", ...]   # 特徵牌 card_id
        },
        ...
      ],
      "by_class": {
        "PALADIN": [<deck>, ...],
        ...
      }
    }
    """
    if not force:
        cached = _load_cache()
        if cached:
            return cached

    try:
        # 1. Archetypes id -> name
        archetypes_raw = _fetch_json(_ARCH_URL)
        arch_map = {a["id"]: a for a in archetypes_raw}

        # 2. dbfId -> card_id map
        hs_cards = _fetch_json(_HSCARD_URL)
        dbfid_map = {}
        for c in hs_cards:
            dbf = c.get("dbfId")
            cid = c.get("id")
            if dbf and cid:
                dbfid_map[dbf] = cid

        # 3. Meta stats
        stats_raw = _fetch_json(_STATS_URL)
        meta_data = stats_raw["series"]["data"]
        as_of = stats_raw.get("as_of", "")

        all_decks = []
        for cls, items in meta_data.items():
            for item in items:
                aid = item["archetype_id"]
                arch = arch_map.get(aid, {})
                sig = arch.get("standard_ccp_signature_core") or {}
                comp_dbf = sig.get("components", [])
                core_cards = [dbfid_map[d] for d in comp_dbf if d in dbfid_map]
                all_decks.append({
                    "archetype_id": aid,
                    "name": arch.get("name", str(aid)),
                    "class": cls,
                    "class_zh": CLASS_ZH.get(cls, cls),
                    "win_rate": round(item["win_rate"], 1),
                    "pct_of_total": round(item["pct_of_total"], 1),
                    "total_games": item["total_games"],
                    "core_cards": core_cards,
                })

        all_decks.sort(key=lambda x: x["win_rate"], reverse=True)
        for i, d in enumerate(all_decks):
            d["rank"] = i + 1

        by_class: dict[str, list] = {}
        for d in all_decks:
            by_class.setdefault(d["class"], []).append(d)

        result = {
            "as_of": as_of,
            "decks": all_decks,
            "by_class": by_class,
        }
        _save_cache(result)
        return result

    except Exception as e:
        # 若網路失敗，回傳空白 meta
        return {"as_of": "", "decks": [], "by_class": {}, "error": str(e)}


def top_decks(n: int = 10, meta: dict = None) -> list:
    if meta is None:
        meta = fetch_meta()
    return meta.get("decks", [])[:n]


def decks_by_class(cls: str, meta: dict = None) -> list:
    """依職業（英文大寫）回傳此職業的牌型排行（勝率排序）"""
    if meta is None:
        meta = fetch_meta()
    return meta.get("by_class", {}).get(cls.upper(), [])
