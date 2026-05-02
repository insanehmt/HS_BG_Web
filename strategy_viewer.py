"""
策略文件查閱 / 更新工具

用法：
    python strategy_viewer.py                        # 列出所有牌型
    python strategy_viewer.py "Aggro Paladin"        # 顯示某牌型策略
    python strategy_viewer.py --class PALADIN        # 顯示某職業所有牌型
    python strategy_viewer.py --refresh              # 強制重新產生所有策略文件
    python strategy_viewer.py --edit 171             # 用系統編輯器開啟策略 JSON
"""
import sys
import os
import json
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "hs_advisor"))

import hs_card_db as db
import hsreplay_meta as meta_module
import strategy_manager as sm

# 顏色
try:
    import colorama; colorama.init(); _C = True
except ImportError:
    _C = False
def _c(code, t): return f"\033[{code}m{t}\033[0m" if _C else t
BOLD    = lambda t: _c("1",  t)
YELLOW  = lambda t: _c("93", t)
CYAN    = lambda t: _c("96", t)
RED     = lambda t: _c("91", t)
DIM     = lambda t: _c("2",  t)
GREEN   = lambda t: _c("92", t)
MAGENTA = lambda t: _c("95", t)


def print_strategy(strat: dict):
    name   = strat.get("name", "")
    nmzh   = strat.get("name_zh", "")
    cls_zh = strat.get("class_zh", strat.get("class", ""))
    style  = strat.get("style", "")
    wr     = strat.get("win_rate", 0)
    pct    = strat.get("pct_of_total", 0)
    rank   = strat.get("rank", 0)
    wr_color = RED if wr >= 60 else (YELLOW if wr >= 55 else str)

    display_name = f"{name}" + (f"（{nmzh}）" if nmzh else "")
    print()
    print(CYAN("═" * 56))
    print(f"  {BOLD(display_name)}  [{cls_zh}]  {DIM('(' + style + ')')}")
    print(f"  勝率：{wr_color(str(wr) + '%')}  使用率：{pct:.1f}%  全榜第 {rank} 名")
    print(CYAN("─" * 56))

    play_style = strat.get("play_style", "")
    if play_style:
        print(f"  {YELLOW('風格說明：')}{play_style}")
    print()

    win_cond = strat.get("win_condition", "")
    if win_cond:
        print(f"  {YELLOW('獲勝條件：')}{win_cond}")
    print()

    key_turns = strat.get("key_turns", "")
    if key_turns:
        print(f"  {YELLOW('關鍵回合：')}{key_turns}")
    print()

    tips = strat.get("against_tips", [])
    if tips:
        print(f"  {YELLOW('對戰重點：')}")
        for t in tips:
            print(f"    {GREEN('•')} {t}")
    print()

    notes = strat.get("notes", "")
    if notes:
        print(f"  {YELLOW('個人筆記：')}{notes}")
    elif not notes:
        aid_str = str(strat.get('archetype_id'))
        hint = 'data/strategies/' + aid_str + '.json'
        print(f"  {DIM('個人筆記：（空白，可編輯 ' + hint + ' 補充）')}")

    cores = strat.get("core_cards", [])
    if cores:
        print()
        print(f"  {YELLOW('核心牌（特徵牌）：')}")
        for c in cores:
            cost  = c.get("cost", 0)
            nm    = c.get("name", "")
            ctype = {"MINION": "隨從", "SPELL": "法術", "WEAPON": "武器"}.get(c.get("type", ""), c.get("type", ""))
            txt   = c.get("text", "")[:45]
            print(f"    ({cost}費) {BOLD(nm)} [{ctype}]  {DIM(txt)}")
    print(CYAN("═" * 56))


def list_all(meta: dict):
    decks = meta.get("decks", [])
    print(CYAN(f"\n{'排名':>4}  {'勝率':>6}  {'使用':>5}  {'牌型名稱':<30}  {'職業'}"))
    print("─" * 60)
    for d in decks:
        wr   = d["win_rate"]
        pct  = d["pct_of_total"]
        nm   = d["name"]
        cls  = d.get("class_zh", d["class"])
        rank = d["rank"]
        wr_s = (RED if wr >= 60 else (YELLOW if wr >= 55 else DIM))(f"{wr:.1f}%")
        print(f"  {rank:>3}.  {wr_s}  {pct:>4.1f}%  {nm:<30}  {cls}")


def list_by_class(cls: str, meta: dict):
    decks = meta_module.decks_by_class(cls, meta)
    if not decks:
        print(f"找不到職業：{cls}")
        return
    print(CYAN(f"\n── {cls} 職業牌型 ──"))
    for d in decks:
        wr   = d["win_rate"]
        nm   = d["name"]
        rank = d["rank"]
        pct  = d["pct_of_total"]
        wr_s = (RED if wr >= 60 else (YELLOW if wr >= 55 else DIM))(f"{wr:.1f}%")
        print(f"  {rank:>3}. {wr_s}  {pct:.1f}%  {nm}")


def main():
    print("載入牌庫…")
    db.load()
    meta = meta_module.fetch_meta()
    sm.generate_all(meta, db, overwrite=False)

    args = sys.argv[1:]

    if not args:
        list_all(meta)
        print(f"\n用法：strategy_viewer.py \"Aggro Paladin\"  或  --class PALADIN  或  --edit 171")
        return

    if args[0] == "--refresh":
        n = sm.generate_all(meta, db, overwrite=True)
        print(f"已重新產生 {n} 個策略文件")
        return

    if args[0] == "--class" and len(args) >= 2:
        list_by_class(args[1].upper(), meta)
        return

    if args[0] == "--edit" and len(args) >= 2:
        try:
            aid = int(args[1])
        except ValueError:
            print("請提供數字牌型 ID")
            return
        path = sm._strat_path(aid)
        if not os.path.exists(path):
            print(f"找不到策略文件：{path}")
            return
        print(f"開啟：{path}")
        os.startfile(path)  # Windows 預設程式開啟
        return

    # 搜尋牌型名稱
    query = " ".join(args).lower()
    matches = [d for d in meta.get("decks", []) if query in d["name"].lower()]

    if not matches:
        print(f"找不到牌型：{query}")
        list_all(meta)
        return

    for d in matches[:3]:
        strat = sm.load_strategy(d["archetype_id"])
        if strat:
            print_strategy(strat)
        else:
            print(f"找不到 {d['name']} 的策略文件")


if __name__ == "__main__":
    main()
