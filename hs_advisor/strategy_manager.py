"""
牌型策略文件管理
- 每個 meta 牌型都有一個 JSON 策略檔
- 首次執行自動建立模板（可手動編輯補充）
- 顯示時讀取策略供玩家參考
"""
import json
import os
import re

_STRAT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "strategies")
)

# 依牌型名稱關鍵字推斷風格
_ARCHETYPE_STYLE = {
    "aggro":    "快攻",
    "face":     "快攻",
    "zoo":      "快攻",
    "pirate":   "快攻",
    "rush":     "快攻",
    "token":    "快攻",
    "murloc":   "快攻",
    "tempo":    "節奏",
    "midrange": "中速",
    "dragon":   "中速",
    "egg":      "中速",
    "herald":   "中速",
    "imbue":    "中速",
    "spell":    "法術",
    "burn":     "爆發傷害",
    "otk":      "一回合斃命",
    "combo":    "組合技",
    "control":  "控制",
    "quest":    "任務",
    "bubble":   "防護盾",
    "aura":     "光環",
    "unholy":   "亡語鏈",
    "merithra": "大型威脅",
}

# 每個風格的對戰建議模板
_STYLE_ADVICE = {
    "快攻": {
        "play_style": "快攻型，前期快速鋪場並強攻英雄血量，通常在 6-8 回合結束遊戲",
        "against": [
            "前期必須積極清場，不讓對手建立雪球優勢",
            "優先保留 AoE（全體傷害）法術，開板後使用",
            "維持自己的血量在 15 以上，不要讓 burst 一次帶走",
            "對手血量剩餘少時，當心手牌 burn（燃燒傷害）combo",
        ],
        "key_turns": "1-6 回合最關鍵，超過 8 回合通常你佔優",
        "win_condition": "清場穩住板面後，對手牌力下降即可反攻",
    },
    "節奏": {
        "play_style": "節奏型，高效使用每回合法力，在板面上保持領先換取優勢",
        "against": [
            "不要讓對手的節奏牌白賺價值，積極交換",
            "注意對手的強力 4-5 費隨從（節奏關鍵轉換點）",
            "盡量使板面維持 2:1 以上的優勢",
        ],
        "key_turns": "4-7 回合是關鍵，板面優勢決定勝負",
        "win_condition": "維持板面控制，逐步消耗對手資源",
    },
    "中速": {
        "play_style": "中速型，平衡前後期，有多樣化的應對手段",
        "against": [
            "觀察對手打出的關鍵牌，判斷其 win condition",
            "小心中期威脅，注意是否有 buff 型隨從雪球",
            "保留高費法術應對關鍵隨從",
        ],
        "key_turns": "5-8 回合決定走向",
        "win_condition": "耗盡對手資源或建立不可解的板面",
    },
    "法術": {
        "play_style": "法術型，依靠施放法術觸發效果，多有 synergy 鏈",
        "against": [
            "施壓對手英雄或板面，讓對手無法純打法術",
            "注意對手手牌增厚時可能有大量法術 combo",
            "快攻型對其有一定優勢（打臉比清場快）",
        ],
        "key_turns": "法術累積到 5-8 回合爆發",
        "win_condition": "法術 synergy 連發清場或直傷斃命",
    },
    "爆發傷害": {
        "play_style": "爆發型，靠直接傷害法術快速帶走英雄血量",
        "against": [
            "保持血量在 15 以上，避免一波 combo 帶走",
            "不要讓對手安心抽牌組合，保持施壓",
            "可以適當無視板面，優先確保自己血線安全",
        ],
        "key_turns": "積累到 7-10 費時為 OTK 窗口期",
        "win_condition": "combo 連打直傷斃命英雄",
    },
    "一回合斃命": {
        "play_style": "OTK 型，積累特定組合牌後一回合斃命",
        "against": [
            "快速降低對手血量，不給其湊齊 OTK 的時間",
            "使用干擾/沉默/反制（如有）阻斷組合技",
            "記錄對手已打出的 combo 牌，評估剩餘威脅",
        ],
        "key_turns": "8 回合後隨時可能 OTK，需在 6-7 回合完成致命壓力",
        "win_condition": "在對手湊齊 OTK 前打死或封鎖",
    },
    "組合技": {
        "play_style": "Combo 型，搭配特定牌組產生大量價值或直接斃命",
        "against": [
            "積極施壓，縮短遊戲長度",
            "注意對手屯牌，手牌大於 5 張時需警惕",
            "若有干擾牌（沉默、反制），留到關鍵 combo 牌出現時使用",
        ],
        "key_turns": "Combo 通常在 7-10 回合形成",
        "win_condition": "在 combo 形成前以血量壓力取勝",
    },
    "控制": {
        "play_style": "控制型，大量去除和回血，拖到後期以大牌取勝",
        "against": [
            "節奏快攻，讓對手的去除疲於奔命",
            "盡量逼對手在次優時機使用全體清場",
            "小心後期大威脅（通常在 7-10 費），提前算好致命",
        ],
        "key_turns": "前中期是你的機會，後期會越來越難",
        "win_condition": "在對手穩定下來前造成足夠傷害，或資源戰佔優",
    },
    "任務": {
        "play_style": "任務型，完成特定任務後解鎖強力能力或獎勵",
        "against": [
            "積極施壓，不要給對手安穩完成任務的時間",
            "注意對手完成任務的時間節點，判斷威脅等級",
            "任務完成後遊戲通常進入對方優勢，需在此之前分出勝負",
        ],
        "key_turns": "任務完成前（通常 5-8 回合）是最佳攻勢視窗",
        "win_condition": "任務完成前決出勝負，或之後快速答問",
    },
    "防護盾": {
        "play_style": "聖盾型，使用護盾保護關鍵隨從，難以用交換清除",
        "against": [
            "保留能無視護盾的技能（沉默、消滅、變形）",
            "AoE 可先戳破護盾再掃場",
            "優先解決帶護盾的大型威脅",
        ],
        "key_turns": "中後期護盾隨從上場時需即時應對",
        "win_condition": "克制護盾的去除 + 板面優勢",
    },
    "光環": {
        "play_style": "光環型，依靠持續光環效果增強所有隨從",
        "against": [
            "立即消滅光環來源（通常是特定隨從或法術），否則會雪球",
            "保留點殺給光環隨從，不要等它累積太多效果",
        ],
        "key_turns": "光環隨從一出場就需立刻處理",
        "win_condition": "殺掉光環來源，維持板面對等",
    },
    "亡語鏈": {
        "play_style": "亡語型，依靠亡語效果獲取額外資源或傷害",
        "against": [
            "若有沉默，優先用在高價值亡語隨從",
            "盡量讓亡語在你準備好後才觸發（控制交換時間）",
            "不要用點殺浪費亡語，考慮 AoE 或變形",
        ],
        "key_turns": "中期亡語鏈是關鍵，3-7 回合需保持清醒",
        "win_condition": "克制亡語後板面穩定推進",
    },
    "大型威脅": {
        "play_style": "大隨從型，後期投放大型威脅取勝",
        "against": [
            "快攻或組合技在大牌出來前結束遊戲",
            "若拖入後期，保留點殺/變形應對大型隨從",
            "早期對手牌力較弱，需積極利用",
        ],
        "key_turns": "7-9 回合大牌上場是轉折點",
        "win_condition": "在大牌出場前造成足夠傷害，或準備好應對方案",
    },
}

_DEFAULT_ADVICE = {
    "play_style": "此牌型目前尚無詳細資料，請根據對手打出的牌判斷風格",
    "against": ["觀察對手的出牌節奏判斷是快攻/中速/控制", "記錄對手核心牌型"],
    "key_turns": "依對手行動判斷",
    "win_condition": "根據你的牌組優勢施展",
}


def _strat_path(archetype_id: int) -> str:
    return os.path.join(_STRAT_DIR, f"{archetype_id}.json")


def _detect_style(name: str) -> str:
    lower = name.lower()
    for kw, style in _ARCHETYPE_STYLE.items():
        if kw in lower:
            return style
    return ""


def _make_template(deck: dict, db_module) -> dict:
    """為牌型自動產生策略模板"""
    name       = deck["name"]
    cls        = deck["class"]
    cls_zh     = deck.get("class_zh", cls)
    wr         = deck["win_rate"]
    pct        = deck["pct_of_total"]
    rank       = deck["rank"]
    core_ids   = deck.get("core_cards", [])
    style      = _detect_style(name)

    advice = _STYLE_ADVICE.get(style, _DEFAULT_ADVICE)

    # 核心牌中文名
    core_names = []
    for cid in core_ids:
        n = db_module.name(cid)
        ctype = db_module.card_type(cid)
        cost  = db_module.cost(cid)
        ctext = db_module.text(cid)
        short_text = re.sub(r"<[^>]+>", "", ctext).replace("\n", " ")[:50]
        core_names.append({
            "card_id":   cid,
            "name":      n,
            "type":      ctype,
            "cost":      cost,
            "text":      short_text,
        })

    return {
        "archetype_id": deck["archetype_id"],
        "name":         name,
        "name_zh":      "",          # 可手動填寫中文名稱
        "class":        cls,
        "class_zh":     cls_zh,
        "style":        style,
        "win_rate":     wr,
        "pct_of_total": pct,
        "rank":         rank,
        "core_cards":   core_names,
        "play_style":   advice["play_style"],
        "win_condition":advice["win_condition"],
        "key_turns":    advice["key_turns"],
        "against_tips": advice["against"],
        "notes":        "",          # 可手動填寫補充筆記
    }


def ensure_strategy(deck: dict, db_module, overwrite: bool = False) -> dict:
    """確保策略文件存在，若不存在則自動建立模板"""
    path = _strat_path(deck["archetype_id"])
    if not overwrite and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    os.makedirs(_STRAT_DIR, exist_ok=True)
    data = _make_template(deck, db_module)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def load_strategy(archetype_id: int) -> dict:
    path = _strat_path(archetype_id)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def generate_all(meta: dict, db_module, overwrite: bool = False) -> int:
    """為所有 meta 牌型生成策略文件，回傳建立數量"""
    created = 0
    for deck in meta.get("decks", []):
        path = _strat_path(deck["archetype_id"])
        if overwrite or not os.path.exists(path):
            ensure_strategy(deck, db_module, overwrite=overwrite)
            created += 1
    return created
