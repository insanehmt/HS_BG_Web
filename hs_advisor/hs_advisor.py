"""
爐石傳說標準對戰輔助工具（含 HSReplay Meta 整合）

顯示內容：
  - 對手可能打的牌型（根據職業 + 本週 meta 勝率）
  - 板面狀況（我方 / 對手隨從、攻/血、嘲諷/聖盾）
  - 手牌列表（費用、名稱、卡文）
  - 本回合應優先打哪張牌（含清場/致命分析）

執行：
    python run_advisor.py
    python run_advisor.py "C:/path/to/Power.log"
"""

import os
import sys
import time

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_DIR))

import hs_card_db as db
import hsreplay_meta as meta_module
import strategy_manager as sm
import mulligan as mulligan_module
from hs_game_state import HSGameParser, ZONE_PLAY, ZONE_HAND, ZONE_SECRET

def _find_log_path(hint: str = "") -> str:
    """自動偵測最新的 Power.log 路徑（支援 session 子資料夾）"""
    if hint and os.path.isfile(hint):
        return hint

    candidates = [
        # D槽 BZGame 安裝路徑
        r"D:\BZGame\Hearthstone\Logs",
        # C槽預設路徑
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Blizzard", "Hearthstone", "Logs"),
        # Program Files
        r"C:\Program Files (x86)\Hearthstone\Logs",
        r"C:\Program Files\Hearthstone\Logs",
    ]
    # 若 hint 是目錄也加進去
    if hint and os.path.isdir(hint):
        candidates.insert(0, hint)

    for logs_dir in candidates:
        if not os.path.isdir(logs_dir):
            continue
        # 直接在 Logs/ 底下
        direct = os.path.join(logs_dir, "Power.log")
        if os.path.isfile(direct):
            return direct
        # Logs/ 底下有 session 子資料夾
        subdirs = sorted(
            [d for d in os.scandir(logs_dir) if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        for sd in subdirs:
            p = os.path.join(sd.path, "Power.log")
            if os.path.isfile(p):
                return p

    # 找不到就回傳預設（讓 monitor 等待）
    return os.path.join(
        os.environ.get("LOCALAPPDATA", ""), "Blizzard", "Hearthstone", "Logs", "Power.log"
    )


DEFAULT_LOG = r"D:\BZGame\Hearthstone\Logs"


# ── 顏色 ──────────────────────────────────────────────────────────────────────
try:
    import colorama; colorama.init(); _COLOR = True
except ImportError:
    _COLOR = False

def _c(code, t):   return f"\033[{code}m{t}\033[0m" if _COLOR else t
GREEN   = lambda t: _c("92", t)
YELLOW  = lambda t: _c("93", t)
CYAN    = lambda t: _c("96", t)
RED     = lambda t: _c("91", t)
BOLD    = lambda t: _c("1",  t)
DIM     = lambda t: _c("2",  t)
MAGENTA = lambda t: _c("95", t)
WHITE   = lambda t: _c("97", t)

# 職業中文名
CLASS_ZH = {
    "DEATHKNIGHT": "死亡騎士", "DEMONHUNTER": "惡魔獵人", "DRUID": "德魯伊",
    "HUNTER": "獵人", "MAGE": "法師", "PALADIN": "聖騎士", "PRIEST": "牧師",
    "ROGUE": "盜賊", "SHAMAN": "薩滿", "WARLOCK": "術士", "WARRIOR": "戰士",
}

# ── 全域 meta 快取 ──────────────────────────────────────────────────────────
_meta: dict = {}


def _load_meta_bg():
    """在背景載入 meta + 確保所有策略文件都存在"""
    global _meta
    try:
        print("  正在從 HSReplay 抓取本週 Meta…")
        _meta = meta_module.fetch_meta()
        n = len(_meta.get("decks", []))
        print(f"  Meta 載入完成（{n} 個牌型）")
        # 自動生成尚未存在的策略文件
        created = sm.generate_all(_meta, db, overwrite=False)
        if created:
            print(f"  已建立 {created} 個新策略文件（data/strategies/）")
    except Exception as e:
        print(f"  Meta 載入失敗：{e}")
        _meta = {}


# ── 手牌行 ────────────────────────────────────────────────────────────────────
def _card_line(entity, mana_avail: int, priority_tuple=None) -> str:
    cid   = entity.card_id
    info  = db.get(cid) if cid else {}
    cname = info.get("name", cid) if info else cid
    ctype = info.get("type", "") if info else ""
    ctext = db.text(cid) if cid else ""
    ccost = entity.cost_tag if entity.cost_tag is not None else (info.get("cost", 0) if info else 0)
    atk_v = entity.atk
    hp_v  = entity.health

    type_label = {"MINION": "隨從", "SPELL": "法術", "WEAPON": "武器",
                  "HERO_POWER": "英雄技能"}.get(ctype, ctype)
    stats = f" [{atk_v}/{hp_v}]" if ctype in ("MINION", "WEAPON") else ""
    text_short = (ctext[:38] + "…") if len(ctext) > 38 else ctext
    text_part  = f"  {DIM(text_short)}" if text_short else ""

    can_play = (ccost <= mana_avail)
    label = priority_tuple[1] if priority_tuple else ""
    pri_label = f" {YELLOW(label)}" if label else ""
    line = f"({ccost}費) {BOLD(cname)}{stats} [{type_label}]{pri_label}{text_part}"
    if can_play:
        return GREEN(f"  ▶ {line}")
    return DIM(f"    {line}")


# ── 隨從行 ────────────────────────────────────────────────────────────────────
def _minion_line(entity, prefix="") -> str:
    cid   = entity.card_id
    cname = db.name(cid) if cid else "（隱藏）"
    flags = []
    if entity.taunt:         flags.append("嘲諷")
    if entity.divine_shield: flags.append("聖盾")
    if entity.exhausted:     flags.append("已攻")
    flag_str = f" [{'/'.join(flags)}]" if flags else ""
    return f"  {prefix}{BOLD(cname)} {entity.atk}/{entity.health}{flag_str}"


# ── META 對手分析 ─────────────────────────────────────────────────────────────
def _show_meta_opp(opp_class: str, turn: int):
    """根據對手職業顯示最可能在用的牌型 + 策略"""
    if not _meta or not opp_class:
        return
    decks = meta_module.decks_by_class(opp_class, _meta)
    if not decks:
        return

    cls_zh = CLASS_ZH.get(opp_class, opp_class)
    print(MAGENTA(f"── 對手職業：{cls_zh}  可能的牌型 ──"))

    for i, d in enumerate(decks[:3]):
        wr      = d["win_rate"]
        pct     = d["pct_of_total"]
        nm      = d["name"]
        rank    = d["rank"]
        wr_str  = (RED if wr >= 60 else (YELLOW if wr >= 55 else WHITE))(f"{wr:.1f}%")
        pct_str = DIM(f"使用率{pct:.1f}%")
        rank_str= DIM(f"全榜第{rank}")
        print(f"  {i+1}. {BOLD(nm)}  WR={wr_str}  {pct_str}  {rank_str}")

    # 快攻警示（只計算一次）
    aggro_keywords = ("Aggro", "Face", "Zoo", "Pirate", "Rush", "Token", "Murloc")
    is_aggro = any(kw in d["name"] for d in decks[:2] for kw in aggro_keywords)
    if is_aggro and turn <= 6:
        print(f"  {RED('⚠')} 對手可能是快攻！優先清場、留存生命值")

    # 策略文件
    top   = decks[0]
    strat = sm.load_strategy(top["archetype_id"])
    if strat:
        play_style = strat.get("play_style", "")
        if play_style:
            print(f"  {DIM('風格：')}{play_style}")
        tips = strat.get("against_tips", [])
        if tips:
            print(f"  {YELLOW('對戰重點：')}")
            for tip in tips:
                print(f"    • {tip}")
        key_turns = strat.get("key_turns", "")
        if key_turns:
            print(f"  {DIM('關鍵回合：')}{key_turns}")
        notes = strat.get("notes", "")
        if notes:
            print(f"  {YELLOW('備注：')}{notes}")
    else:
        cores = top.get("core_cards", [])
        core_names = [db.name(cid) for cid in cores[:5] if db.name(cid) != cid]
        if core_names:
            print(f"  核心牌：{DIM(', '.join(core_names))}")
    print()


# ── 本回合出牌建議 ─────────────────────────────────────────────────────────────
def _print_suggestions(hand, my_board, opp_board, mana: int, turn: int, opp_class: str):
    playable = [e for e in hand
                if e.card_id and
                (e.cost_tag if e.cost_tag is not None else db.cost(e.card_id)) <= mana]
    if not playable and not my_board:
        return

    print(YELLOW("── 本回合建議 ──"))

    # ── 致命傷害計算 ──
    opp_hp_from_board = _lethal_check(playable, my_board, mana)
    if opp_hp_from_board is not None:
        print(f"  {RED('★★ 可能致命！')} 嘗試直攻對手英雄（預估傷害 ≥ 對手血量）")

    # ── 嘲諷提醒 ──
    taunt_targets = [e for e in opp_board if e.taunt]
    if taunt_targets:
        for t in taunt_targets:
            nm = db.name(t.card_id)
            print(f"  {RED('!')} 對手嘲諷：{BOLD(nm)} {t.atk}/{t.health}，必須先處理")

    # ── 清場計算 ──
    clears = _find_trades(my_board, opp_board)
    if clears:
        print(f"  {CYAN('>')} 有利交換：")
        for (my_m, opp_m, desc) in clears[:3]:
            print(f"    用 {BOLD(db.name(my_m.card_id))} {my_m.atk}/{my_m.health} "
                  f"換掉 {BOLD(db.name(opp_m.card_id))} {opp_m.atk}/{opp_m.health}"
                  f"{DIM(' ('+desc+')')}")

    # ── 費用最高推薦 ──
    by_cost = sorted(playable,
                     key=lambda e: e.cost_tag if e.cost_tag is not None else db.cost(e.card_id),
                     reverse=True)
    if by_cost:
        best = by_cost[0]
        cost_v = best.cost_tag if best.cost_tag is not None else db.cost(best.card_id)
        remaining = mana - cost_v
        print(f"  {GREEN('>')} 費用最高：{BOLD(db.name(best.card_id))} ({cost_v}費)，剩 {remaining} 費")

    # ── 恰好花完法力 ──
    combos = _mana_exact(playable, mana)
    for combo in combos[:2]:
        total_cost = sum(e.cost_tag if e.cost_tag is not None else db.cost(e.card_id) for e in combo)
        if total_cost == mana and len(combo) > 1:
            names = " + ".join(BOLD(db.name(e.card_id)) for e in combo)
            print(f"  {GREEN('>')} 恰好花完 {mana} 費：{names}")
            break

    # ── 快攻對手：建議打隨從/清場 ──
    if opp_class and _meta:
        decks = meta_module.decks_by_class(opp_class, _meta)
        aggro_kws = ("Aggro", "Face", "Zoo", "Pirate", "Rush", "Token", "Murloc")
        if decks and any(kw in decks[0]["name"] for kw in aggro_kws) and turn <= 6:
            board_spells = [e for e in playable
                            if db.card_type(e.card_id) == "SPELL"
                            and ("傷害" in db.text(e.card_id) or "消滅" in db.text(e.card_id)
                                 or "摧毀" in db.text(e.card_id))]
            if board_spells:
                nm = db.name(board_spells[0].card_id)
                print(f"  {YELLOW('>')} 對手快攻，優先用 {BOLD(nm)} 清場控場")


def _lethal_check(hand, my_board, mana: int):
    """簡易致命檢查：我方未攻隨從攻擊力 + 可直攻法術是否可能致命"""
    dmg = sum(e.atk for e in my_board if not e.exhausted and not e.tags.get("CHARGE", "") == "0")
    for e in hand:
        cid = e.card_id
        ctext = db.text(cid)
        ccost = e.cost_tag if e.cost_tag is not None else db.cost(cid)
        if ccost <= mana and ("傷害" in ctext) and db.card_type(cid) == "SPELL":
            info = db.get(cid)
            # 嘗試解析「造成$X點傷害」
            import re
            m = re.search(r'\$(\d+)', ctext)
            if m:
                dmg += int(m.group(1))
    return dmg if dmg >= 15 else None  # 只在高傷害時提示


def _find_trades(my_board, opp_board):
    """找有利交換（我攻擊力 >= 對手血量，且我不死）"""
    trades = []
    for my in my_board:
        if my.exhausted:
            continue
        for opp in opp_board:
            can_kill = my.atk >= opp.health
            i_survive = opp.atk < my.health
            if can_kill and i_survive:
                trades.append((my, opp, "有利換"))
            elif can_kill and opp.atk >= my.health and not my.divine_shield:
                trades.append((my, opp, "換換"))
    return trades


# ── 換牌階段顯示 ──────────────────────────────────────────────────────────────
def _show_mulligan(hand: list, going_first: bool, opp_class: str):
    side_str = "先手" if going_first else "後手"
    cls_zh   = CLASS_ZH.get(opp_class, opp_class or "未知")
    print(YELLOW(f"══ 換牌建議（{side_str}  對手：{cls_zh}）══"))
    print()

    if not hand:
        print(DIM("  （尚未抽到起始手牌）"))
        return

    advice_list = mulligan_module.mulligan_advice(
        hand, going_first, opp_class, _meta, db, meta_module
    )

    keep_cards    = [a for a in advice_list if a["keep"]]
    discard_cards = [a for a in advice_list if not a["keep"]]

    # ── 建議留牌 ──
    print(GREEN(f"  ✔ 建議留（{len(keep_cards)} 張）"))
    if keep_cards:
        for a in keep_cards:
            e    = a["entity"]
            cost = a["cost"]
            nm   = a["name"]
            ctype = db.card_type(e.card_id)
            type_zh = {"MINION":"隨從","SPELL":"法術","WEAPON":"武器"}.get(ctype, ctype)
            ctext = db.text(e.card_id)
            short = (ctext[:35] + "…") if len(ctext) > 35 else ctext
            stars = "★" * min(a["priority"], 5)
            print(GREEN(f"    {stars} ({cost}費) {BOLD(nm)} [{type_zh}]  {DIM(short)}"))
            print(f"       {DIM('原因：' + a['reason'])}")
    else:
        print(DIM("  （沒有特別值得留的牌）"))

    print()

    # ── 建議換掉 ──
    print(RED(f"  ✘ 建議換掉（{len(discard_cards)} 張）"))
    if discard_cards:
        for a in discard_cards:
            e    = a["entity"]
            cost = a["cost"]
            nm   = a["name"]
            print(RED(f"    ({cost}費) {nm}") + f"  {DIM(a['reason'])}")
    else:
        print(DIM("  （全部都值得留）"))

    print()
    # ── 對手牌型提醒 ──
    if opp_class and _meta:
        decks = meta_module.decks_by_class(opp_class, _meta)
        if decks:
            top = decks[0]
            wr  = top["win_rate"]
            nm  = top["name"]
            wr_str = (RED if wr >= 60 else YELLOW)(f"{wr:.1f}%")
            print(f"  {DIM('對手最可能：')}{BOLD(nm)}  WR={wr_str}")
            strat = sm.load_strategy(top["archetype_id"])
            if strat:
                kt = strat.get("key_turns", "")
                if kt:
                    print(f"  {DIM('關鍵回合：')}{kt}")


def _mana_exact(cards, mana: int, max_results=3):
    """找恰好花完法力的出牌組合"""
    results = []
    def _bt(idx, rem, chosen):
        if rem == 0:
            results.append(list(chosen))
            return
        if len(results) >= max_results or idx >= len(cards):
            return
        for i in range(idx, len(cards)):
            cv = cards[i].cost_tag if cards[i].cost_tag is not None else db.cost(cards[i].card_id)
            if cv <= rem:
                chosen.append(cards[i])
                _bt(i + 1, rem - cv, chosen)
                chosen.pop()
    _bt(0, mana, [])
    return results


# ── 計算手牌優先順序 ──────────────────────────────────────────────────────────
def _card_priorities(hand, my_board, opp_board, mana: int, opp_class: str) -> dict:
    """回傳 {entity_eid: (priority_score, label)}，所有可打的牌都給標籤"""
    pri = {}
    taunt_targets = [e for e in opp_board if e.taunt]
    has_taunt = bool(taunt_targets)

    is_aggro_opp = False
    if opp_class and _meta:
        decks = meta_module.decks_by_class(opp_class, _meta)
        aggro_kws = ("Aggro", "Face", "Zoo", "Pirate", "Rush", "Token", "Murloc")
        is_aggro_opp = bool(decks) and any(kw in decks[0]["name"] for kw in aggro_kws)

    for e in hand:
        cid   = e.card_id
        ctype = db.card_type(cid)
        ctext = db.text(cid)
        ccost = e.cost_tag if e.cost_tag is not None else db.cost(cid)
        if ccost > mana:
            continue

        score = 1
        label = ""

        if ctype == "SPELL":
            has_dmg  = "傷害" in ctext
            has_kill = any(k in ctext for k in ("消滅", "摧毀"))
            has_draw  = "抽" in ctext
            has_heal  = "回復" in ctext
            if (has_dmg or has_kill) and has_taunt:
                label, score = "★清場", 5
            elif has_dmg or has_kill:
                if opp_board:
                    label, score = "★攻擊", 4
                else:
                    label, score = "直攻英雄", 3
            elif has_draw:
                label, score = "★抽牌", 3
            elif has_heal:
                label, score = "回復", 2
            else:
                label, score = "法術", 2

        elif ctype == "MINION":
            has_taunt_self   = "嘲諷" in ctext
            has_battle_cry   = "戰吼" in ctext
            has_divine       = "聖盾" in ctext
            board_empty      = not my_board

            if board_empty and is_aggro_opp:
                label, score = "★急補板面", 5
            elif has_taunt_self and is_aggro_opp:
                label, score = "★嘲諷擋傷", 5
            elif has_battle_cry and has_taunt:
                label, score = "★戰吼清場", 4
            elif has_battle_cry:
                label, score = "★戰吼", 4
            elif has_divine:
                label, score = "★聖盾", 3
            elif board_empty:
                label, score = "★補板面", 4
            elif len(my_board) < 4:
                label, score = "補板面", 3
            else:
                label, score = "隨從", 2

        elif ctype == "WEAPON":
            label, score = "★武器", 4

        else:
            label, score = "出牌", 2

        pri[e.eid] = (score, label)

    return pri


# ── 主顯示函式 ────────────────────────────────────────────────────────────────
def display_state(parser: HSGameParser):
    s    = parser.state
    ents = parser.entities
    if not s.is_active:
        return

    mana_avail = s.my_mana
    my_max     = s.my_max_mana
    opp_class  = s.opp_class

    os.system("cls" if os.name == "nt" else "clear")

    # ── 標頭 ──
    phase_label = "【換牌階段】" if s.phase == "MULLIGAN" else ""
    turn_label  = f"第 {s.turn} 回合"
    whose       = "【我的回合】" if s.whose_turn == "mine" else ("【對手回合】" if s.whose_turn == "opp" else "")
    hand_label  = "先手" if s.going_first else "後手"
    cls_zh_my   = CLASS_ZH.get(s.my_class,  s.my_class)
    cls_zh_opp  = CLASS_ZH.get(opp_class, opp_class)
    print(CYAN(f"═══════════ 爐石輔助  {turn_label}  {whose}{phase_label} ═══════════"))
    print(f"  我方：{cls_zh_my or '未知'}  血量={GREEN(str(s.my_hero_hp))}  "
          f"法力={YELLOW(str(mana_avail))}/{YELLOW(str(my_max))}  {DIM(hand_label)}")
    print(f"  對手：{cls_zh_opp or '未知'}  血量={RED(str(s.opp_hero_hp))}")
    print()

    hand = s.hand(ents)

    # ════ 換牌階段：顯示留牌建議 ════
    if s.phase == "MULLIGAN":
        _show_mulligan(hand, s.going_first, opp_class)
        print()
        print(DIM("  [即時更新中… Ctrl+C 離開]"))
        return

    # ── META 對手分析 ──
    _show_meta_opp(opp_class, s.turn)

    # ── 對手板面 ──
    opp_board = s.opp_board(ents)
    print(MAGENTA(f"── 對手板面（{len(opp_board)} 個隨從）──"))
    if opp_board:
        for e in opp_board:
            print(_minion_line(e))
    else:
        print(DIM("  （無隨從）"))
    print()

    # ── 我方板面 ──
    my_board = s.my_board(ents)
    print(CYAN(f"── 我方板面（{len(my_board)} 個隨從）──"))
    if my_board:
        for e in my_board:
            print(_minion_line(e))
    else:
        print(DIM("  （無隨從）"))
    print()

    # ── 秘密 ──
    my_sec  = s.my_secrets(ents)
    opp_sec = s.opp_secrets(ents)
    if my_sec or opp_sec:
        if my_sec:
            print(f"  我方秘密：{YELLOW(', '.join(db.name(e.card_id) for e in my_sec))}")
        if opp_sec:
            print(f"  對手秘密：{RED(str(len(opp_sec)) + ' 個（未知）')}")
        print()

    # ── 手牌（含優先標示）──
    priorities = _card_priorities(hand, my_board, opp_board, mana_avail, opp_class)
    print(CYAN(f"── 手牌（{len(hand)} 張） — 綠色可打，標籤=建議 ──"))
    if hand:
        # 可打的按優先分數排序，不可打的放後面
        def sort_key(e):
            ccost = e.cost_tag if e.cost_tag is not None else db.cost(e.card_id)
            can = ccost <= mana_avail
            score = priorities.get(e.eid, (0, ""))[0] if e.eid in priorities else 0
            return (0 if can else 1, -score, ccost)
        for e in sorted(hand, key=sort_key):
            print(_card_line(e, mana_avail, priorities.get(e.eid)))
    else:
        print(DIM("  （手牌為空）"))

    # ── 本回合建議：顯示所有可打牌的出牌順序 ──
    playable = sorted(
        [e for e in hand if (e.cost_tag if e.cost_tag is not None else db.cost(e.card_id)) <= mana_avail],
        key=lambda e: -(priorities.get(e.eid, (0,""))[0])
    )
    if playable:
        print()
        print(YELLOW("── 本回合建議出牌順序 ──"))
        for i, e in enumerate(playable, 1):
            ccost = e.cost_tag if e.cost_tag is not None else db.cost(e.card_id)
            nm    = db.name(e.card_id)
            label = priorities.get(e.eid, (0, "出牌"))[1]
            print(GREEN(f"  {i}. ({ccost}費) {BOLD(nm)}") + f"  {YELLOW(label)}")
        total = sum(e.cost_tag if e.cost_tag is not None else db.cost(e.card_id) for e in playable)
        remaining = mana_avail - total
        if remaining >= 0:
            print(f"  {DIM(f'全部出完共花 {total} 費，剩 {remaining} 費')}")
        # 嘲諷警示
        taunt_targets = [e for e in opp_board if e.taunt]
        if taunt_targets:
            for t in taunt_targets:
                print(RED(f"  ⚠ 對手嘲諷：{db.name(t.card_id)} {t.atk}/{t.health}，必須先處理！"))
        # 清場交換
        clears = _find_trades(my_board, opp_board)
        if clears:
            print(CYAN(f"  ↔ 有利交換："), end="")
            parts = [f"{db.name(m.card_id)} 換 {db.name(o.card_id)}" for m, o, _ in clears[:2]]
            print(", ".join(parts))
    elif s.whose_turn == "mine":
        print()
        print(DIM("  （本回合無牌可出）"))
        clears = _find_trades(my_board, opp_board)
        if clears:
            print(CYAN("  ↔ 有利交換："), end="")
            parts = [f"{db.name(m.card_id)} 換 {db.name(o.card_id)}" for m, o, _ in clears[:2]]
            print(", ".join(parts))

    print()
    print(DIM("  [即時更新中… Ctrl+C 離開]"))


# ── 主迴圈 ────────────────────────────────────────────────────────────────────
def monitor(log_hint: str):
    print("載入牌庫…")
    db.load()
    _load_meta_bg()

    parser             = HSGameParser()
    file_pos           = 0
    last_display_turn  = -1
    last_display_mana  = -1
    last_phase         = ""
    last_hand_count    = -1
    last_opp_board_cnt = -1
    current_log        = ""

    while True:
        try:
            # 每次迴圈都重新解析最新的 log 路徑（session 可能換）
            log_path = _find_log_path(log_hint)

            if not os.path.isfile(log_path):
                if log_path != current_log:
                    print(f"  等待爐石啟動… ({log_path})")
                    current_log = log_path
                time.sleep(2)
                continue

            # log 路徑換了（新 session）→ 重置解析器
            if log_path != current_log:
                print(f"  讀取 log：{log_path}")
                current_log = log_path
                parser.reset()
                file_pos = 0
                last_display_turn  = -1
                last_display_mana  = -1
                last_phase         = ""
                last_hand_count    = -1
                last_opp_board_cnt = -1

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(file_pos)
                new_lines = f.readlines()
                file_pos  = f.tell()

            if new_lines:
                parser.process_lines(new_lines)
                s = parser.state

                cur_hand_cnt    = len(s.hand(parser.entities))
                cur_opp_brd_cnt = len(s.opp_board(parser.entities))

                changed = (
                    s.turn          != last_display_turn  or
                    s.my_mana       != last_display_mana  or
                    s.phase         != last_phase         or
                    cur_hand_cnt    != last_hand_count    or
                    cur_opp_brd_cnt != last_opp_board_cnt
                )

                if s.is_active and changed:
                    display_state(parser)
                    last_display_turn  = s.turn
                    last_display_mana  = s.my_mana
                    last_phase         = s.phase
                    last_hand_count    = cur_hand_cnt
                    last_opp_board_cnt = cur_opp_brd_cnt

            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n[離開]")
            break
        except Exception as e:
            print(f"[錯誤] {e}")
            time.sleep(1)


if __name__ == "__main__":
    log_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG
    monitor(log_path)
