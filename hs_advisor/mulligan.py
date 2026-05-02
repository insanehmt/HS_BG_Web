"""
換牌（Mulligan）建議模組
根據：
  - 起始手牌費用分布
  - 對手職業 + meta 牌型風格
  - 先手/後手
  - 牌的類型和效果關鍵字
給出「建議留牌」vs「建議換掉」的判斷
"""
import re

# ── 換牌原則 ──────────────────────────────────────────────────────────────────
# 費用上限：先手 <= 3費可留，後手 <= 4費可留（基礎規則）
# 快攻對手：降低留牌費用上限 1費（需要更快的反應）
# 控制對手：提高留牌費用上限 1費（可以留 4-5費強力牌）

# 永遠建議留的牌（關鍵字匹配）
ALWAYS_KEEP_KEYWORDS = [
    "嘲諷",        # 有嘲諷的低費隨從
    "戰吼",        # 戰吼隨從通常值得留
    "抽一張牌",    # 抽牌引擎
    "抽兩張牌",
    "抽牌",
    "法力水晶",    # 費用加速
]

# 永遠建議換掉的牌（關鍵字匹配）
ALWAYS_DISCARD_KEYWORDS = [
    "組合技",
    "若你手中有 10 張牌",  # 後期組合技
]

# 依牌型風格調整費用上限
STYLE_COST_LIMIT = {
    "快攻":     {"first": 2, "second": 3},  # 先手留 ≤2費，後手留 ≤3費
    "節奏":     {"first": 3, "second": 4},
    "中速":     {"first": 3, "second": 4},
    "法術":     {"first": 3, "second": 4},
    "爆發傷害": {"first": 4, "second": 5},
    "一回合斃命": {"first": 4, "second": 5},
    "組合技":   {"first": 4, "second": 5},
    "控制":     {"first": 4, "second": 5},
    "任務":     {"first": 3, "second": 4},
    "防護盾":   {"first": 3, "second": 4},
    "光環":     {"first": 3, "second": 4},
    "亡語鏈":   {"first": 3, "second": 4},
    "大型威脅": {"first": 4, "second": 5},
}

_DEFAULT_COST_LIMIT = {"first": 3, "second": 4}


def _card_text(card_id: str, db_module) -> str:
    return db_module.text(card_id) if card_id else ""


def _has_keyword(text: str, keywords: list) -> str:
    """回傳匹配到的關鍵字，否則空字串"""
    for kw in keywords:
        if kw in text:
            return kw
    return ""


def mulligan_advice(hand: list, going_first: bool, opp_class: str,
                    meta: dict, db_module, meta_module) -> list:
    """
    回傳每張手牌的換牌建議清單：
    [
      {
        "entity": <CardEntity>,
        "keep":   True/False,
        "reason": "說明文字",
        "priority": 1-5 (5=最應該留)
      },
      ...
    ]
    """
    # 判斷對手牌型風格
    opp_style = ""
    if opp_class and meta:
        decks = meta_module.decks_by_class(opp_class, meta)
        if decks:
            top_deck = decks[0]
            opp_style = top_deck.get("style", "") or _detect_style(top_deck.get("name", ""))

    side = "first" if going_first else "second"
    limit = STYLE_COST_LIMIT.get(opp_style, _DEFAULT_COST_LIMIT).get(side, 3)

    results = []
    for ent in hand:
        cid   = ent.card_id
        cost  = ent.cost_tag if ent.cost_tag is not None else db_module.cost(cid)
        ctype = db_module.card_type(cid)
        cname = db_module.name(cid)
        ctext = _card_text(cid, db_module)

        keep     = False
        reason   = ""
        priority = 3

        # ── 永遠換掉 ──
        discard_kw = _has_keyword(ctext, ALWAYS_DISCARD_KEYWORDS)
        if discard_kw:
            keep   = False
            reason = f"後期組合技，開局不需要（{discard_kw}）"
            priority = 1

        # ── 費用過高 ──
        elif cost > limit:
            keep   = False
            reason = f"{cost}費太貴（{'先手' if going_first else '後手'}建議留 ≤{limit}費）"
            if opp_style:
                reason += f"，對手為{opp_style}型"
            priority = 1

        # ── 低費強力牌 ──
        elif cost <= 2 and ctype == "MINION":
            keep   = True
            reason = f"{cost}費隨從，早期上場建立板面"
            priority = 5

        # ── 關鍵字加分 ──
        elif _has_keyword(ctext, ALWAYS_KEEP_KEYWORDS):
            kw = _has_keyword(ctext, ALWAYS_KEEP_KEYWORDS)
            keep   = True
            reason = f"有「{kw}」效果，開局有價值"
            priority = 4

        # ── 費用合理 ──
        elif cost <= limit:
            keep   = True
            reason = f"{cost}費在合理範圍內（≤{limit}費）"
            priority = 3

        # ── 預設換掉 ──
        else:
            keep   = False
            reason = f"{cost}費偏高，建議換更低費的牌"
            priority = 2

        # 先手特殊加權：1費牌最重要
        if going_first and cost == 1 and keep:
            priority = min(5, priority + 1)
            reason += "（先手1費非常關鍵）"

        # 後手多留一張牌（後手多一張換的機會）
        if not going_first and cost == limit and ctype == "MINION":
            reason += "（後手可留稍貴的隨從）"

        results.append({
            "entity":   ent,
            "keep":     keep,
            "reason":   reason,
            "priority": priority,
            "cost":     cost,
            "name":     cname,
        })

    # 排序：建議留的在前，優先度高的在前
    results.sort(key=lambda x: (-x["keep"], -x["priority"], x["cost"]))
    return results


def _detect_style(name: str) -> str:
    """從牌型名稱猜測風格"""
    lower = name.lower()
    mapping = {
        "aggro": "快攻", "face": "快攻", "zoo": "快攻",
        "token": "快攻", "pirate": "快攻", "rush": "快攻",
        "tempo": "節奏", "midrange": "中速", "dragon": "中速",
        "control": "控制", "combo": "組合技", "otk": "一回合斃命",
        "quest": "任務", "bubble": "防護盾", "burn": "爆發傷害",
        "spell": "法術", "herald": "中速", "imbue": "中速",
    }
    for kw, style in mapping.items():
        if kw in lower:
            return style
    return "中速"
