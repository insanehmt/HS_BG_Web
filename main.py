"""
主程式：背景監控 Power.log，自動記錄英雄戰場對局。

啟動：python main.py
停止：Ctrl+C
"""
import os
import sys
import re
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional

from log_config import setup_log_config, HS_PATH
from log_parser import PowerLogParser, GameRecord
from card_db import load_card_db, get_card_name
from excel_writer import append_record, get_record_counts
from db import init_db, save_game, mark_exported, get_stats, start_time_exists

# ── 路徑設定 ────────────────────────────────────────────────────────────────
LOGS_DIR       = os.path.join(HS_PATH, "Logs")
POLL_INTERVAL  = 2.0  # 秒
_running       = True


# ── 工具函式 ────────────────────────────────────────────────────────────────

def find_latest_log_folder() -> Optional[Path]:
    """找最新的 Hearthstone_YYYY_MM_DD_HH_MM_SS 資料夾。"""
    if not os.path.exists(LOGS_DIR):
        return None
    dirs = [d for d in Path(LOGS_DIR).iterdir()
            if d.is_dir() and d.name.startswith("Hearthstone_")]
    return max(dirs, key=lambda d: d.name) if dirs else None


def find_power_log() -> Optional[str]:
    folder = find_latest_log_folder()
    if folder:
        p = folder / "Power.log"
        if p.exists():
            return str(p)
    fallback = os.path.join(LOGS_DIR, "Power.log")
    return fallback if os.path.exists(fallback) else None


def read_build_version() -> str:
    """從最新 session 的 Hearthstone.log 讀取遊戲版本。"""
    folder = find_latest_log_folder()
    if not folder:
        return ""
    hs_log = folder / "Hearthstone.log"
    if not hs_log.exists():
        return ""
    try:
        with open(hs_log, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.search(r"BattleNet version: Product = ([\d.]+)", line)
                if m:
                    return m.group(1)
    except Exception:
        pass
    return ""


def signal_handler(sig, frame):
    global _running
    print("\n[main] 停止監控...")
    _running = False


# ── 對局處理 ────────────────────────────────────────────────────────────────

def process_games(games: list[GameRecord], card_db: dict):
    seen_this_batch: set[str] = set()   # 本批次已處理的 start_time
    for game in games:
        if not game.is_bg or game.placement == 0:
            continue

        # 防止雙打模式記錄隊友英雄（同一場兩個英雄有相同 start_time）
        ts_key = game.start_time.isoformat() if game.start_time else ""
        if ts_key and ts_key in seen_this_batch:
            print(f"[main] 略過重複 start_time（隊友英雄）: {game.hero_card_id}")
            continue
        if ts_key and start_time_exists(game.start_time):
            print(f"[main] 略過重複 start_time（已在DB）: {game.hero_card_id}")
            continue
        if ts_key:
            seen_this_batch.add(ts_key)

        # ── 名稱解析 ──
        hero_name           = card_db.get(game.hero_card_id, game.hero_card_id or "未知英雄")
        power_names         = [card_db.get(c, c) for c in game.hero_power_ids]
        trinket_names       = [card_db.get(c, c) if c else "" for c in game.trinket_ids]
        opponent_names      = [card_db.get(c, c) for c in game.opponent_heroes]
        teammate_hero_name  = card_db.get(game.teammate_hero_card_id, game.teammate_hero_card_id) if game.teammate_hero_card_id else ""

        # 自己的板面
        for ms in game.final_board:
            ms.name = card_db.get(ms.card_id, ms.card_id)
        board_strs = [ms.stat_str() for ms in game.final_board]
        board_dicts = [{"card_id": ms.card_id, "name": ms.name,
                        "stats": ms.stat_str(), "golden": ms.golden}
                       for ms in game.final_board]

        # 倒數第二場陣容
        for ms in game.penultimate_board:
            ms.name = card_db.get(ms.card_id, ms.card_id)
        penultimate_dicts = [{"card_id": ms.card_id, "name": ms.name,
                              "stats": ms.stat_str(), "golden": ms.golden}
                             for ms in game.penultimate_board]

        # 對手板面：格式 "英雄名：★隨從[4/2]、..." 每位對手一行
        opp_board_strs: list[str] = []
        opp_board_dicts: dict[str, list] = {}
        for hero_cid, minions in game.opponent_boards.items():
            hero_label = card_db.get(hero_cid, hero_cid)
            for ms in minions:
                ms.name = card_db.get(ms.card_id, ms.card_id)
            minion_strs = [ms.stat_str() for ms in minions]
            if minion_strs:
                opp_board_strs.append(f"{hero_label}：{'、'.join(minion_strs)}")
            opp_board_dicts[hero_label] = [{"card_id": ms.card_id, "name": ms.name,
                                            "stats": ms.stat_str(), "golden": ms.golden}
                                           for ms in minions]

        # ── 儲存 SQLite ──
        is_new = save_game(
            game_id=game.game_id,
            start_time=game.start_time,
            end_time=game.end_time,
            build_version=game.build_version,
            game_mode=game.game_mode,
            hero_card_id=game.hero_card_id,
            hero_name=hero_name,
            hero_power_ids=game.hero_power_ids,
            hero_power_names=power_names,
            trinket_ids=game.trinket_ids,
            trinket_names=trinket_names,
            placement=game.placement,
            final_board=board_dicts,
            penultimate_board=penultimate_dicts,
            turn_count=game.turn_count,
            max_gold=game.max_gold,
            duration_seconds=game.duration_seconds,
            opponent_heroes=opponent_names,
            opponent_boards=opp_board_dicts,
            teammate_hero_card_id=game.teammate_hero_card_id,
            teammate_hero_name=teammate_hero_name,
        )

        if not is_new:
            continue

        # ── 匯出 Excel ──
        success = append_record(
            start_time=game.start_time,
            build_version=game.build_version,
            game_mode=game.game_mode,
            hero_name=hero_name,
            teammate_hero_name=teammate_hero_name,
            power_names=power_names,
            trinket_names=trinket_names,
            placement=game.placement,
            board_strs=board_strs,
            turn_count=game.turn_count,
            max_gold=game.max_gold,
            duration_seconds=game.duration_seconds,
            opponent_names=opponent_names,
            opponent_board_strs=opp_board_strs,
        )

        if success:
            mark_exported(game.game_id)
            stats = get_stats()
            mode_label = "雙打" if game.game_mode == "duo" else "單打"
            print(f"\n{'='*50}")
            print(f"  ✅ 對局記錄完成！")
            print(f"  模式：{mode_label}  名次：第 {game.placement} 名")
            print(f"  英雄：{hero_name}（{' / '.join(power_names)}）")
            if teammate_hero_name:
                print(f"  隊友：{teammate_hero_name}")
            if any(trinket_names):
                print(f"  飾品：{' / '.join(t for t in trinket_names if t)}")
            print(f"  板面：{'、'.join(board_strs[:3])}{'...' if len(board_strs)>3 else ''}")
            if opp_board_strs:
                print(f"  對手板面：{opp_board_strs[0][:60]}...")
            print(f"  回合：{game.turn_count}  金幣：{game.max_gold}  時長：{game.duration_seconds//60}分{game.duration_seconds%60:02d}秒")
            print(f"  📊 累計：單打 {stats['solo']} 局 / 雙打 {stats['duo']} 局 / 第一名 {stats['first']} 次")
            if game.placement == 1:
                print(f"  🏆 已加入強力排組！")
            print(f"{'='*50}\n")


# ── 主程式 ──────────────────────────────────────────────────────────────────

def main():
    global _running

    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform == "win32":
        signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 55)
    print("  爐石傳說 英雄戰場 對局紀錄器  v2.0")
    print("=" * 55)

    setup_log_config()
    init_db()

    print("[main] 載入卡牌資料庫...")
    card_db = load_card_db()
    print(f"[main] 卡牌資料庫：{len(card_db)} 張")

    build_version = read_build_version()
    if build_version:
        print(f"[main] 遊戲版本：{build_version}")

    # 找 log 路徑
    log_path = find_power_log()
    if not log_path:
        print(f"[main] 尚未找到 Power.log，等待爐石啟動...")
    else:
        print(f"[main] Log：{log_path}")

    parser   = PowerLogParser(log_path or "", build_version, name_resolver=lambda cid: card_db.get(cid, cid))
    offset   = 0
    file_mtime = 0.0
    current_folder: Optional[str] = str(find_latest_log_folder()) if find_latest_log_folder() else None

    # 掃描現有 log（防重複由 DB 處理）
    if log_path and os.path.exists(log_path):
        print("[main] 掃描歷史 log...")
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            offset = f.tell()
        games = parser.parse_file(content)
        process_games(games, card_db)
        print(f"[main] 歷史掃描完成，找到 {len(games)} 局")

    print("[main] 開始即時監控（Ctrl+C 退出）...\n")

    while _running:
        time.sleep(POLL_INTERVAL)

        # 偵測新 session 資料夾（遊戲重啟）
        new_folder = find_latest_log_folder()
        new_folder_str = str(new_folder) if new_folder else None
        if new_folder_str != current_folder:
            current_folder = new_folder_str
            log_path = find_power_log()
            build_version = read_build_version()
            parser = PowerLogParser(log_path or "", build_version, name_resolver=lambda cid: card_db.get(cid, cid))
            offset = 0
            file_mtime = 0.0
            if log_path:
                print(f"[main] 偵測到新 session：{log_path}（版本 {build_version}）")

        if not log_path or not os.path.exists(log_path):
            log_path = find_power_log()
            if log_path:
                parser = PowerLogParser(log_path, build_version, name_resolver=lambda cid: card_db.get(cid, cid))
                offset = 0
            continue

        try:
            mtime = os.path.getmtime(log_path)
            if mtime == file_mtime:
                continue
            file_mtime = mtime

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(0, 2)
                size = f.tell()

            if size < offset:
                print("[main] log 重置，重新解析")
                offset = 0
                parser = PowerLogParser(log_path, build_version)

            if size <= offset:
                continue

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(offset)
                new_content = f.read()
                offset = f.tell()

            if not new_content.strip():
                continue

            new_games = parser.parse_lines(new_content.splitlines())
            if new_games:
                process_games(new_games, card_db)

        except Exception as e:
            print(f"[main] 錯誤：{e}")

    print("[main] 已停止，再見！")


if __name__ == "__main__":
    main()
