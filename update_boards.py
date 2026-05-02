"""更新現有 DB 記錄的對手板面資料（重新解析 log）"""
import json, sys
sys.path.insert(0, ".")
from log_parser import PowerLogParser
from db import init_db, save_game
import glob as glob_mod
import os

LOG_BASE = r"D:\BZGame\Hearthstone\Logs"
CARDS_CACHE = os.path.join(os.path.dirname(__file__), "data", "cards_cache.json")

with open(CARDS_CACHE, encoding="utf-8") as f:
    card_db = json.load(f)  # {card_id: name}

# 掃描所有 log 資料夾
log_dirs = sorted(glob_mod.glob(os.path.join(LOG_BASE, "Hearthstone_*")))
for log_dir in log_dirs:
    log_path = os.path.join(log_dir, "Power.log")
    if not os.path.exists(log_path):
        continue

    print(f"\n=== 解析 {log_dir} ===")
    with open(log_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    parser = PowerLogParser(log_path)
    games = parser.parse_file(content)

    init_db()
    for g in games:
        # 設定卡片名稱（stat_str() 需要 name 欄位）
        for m in g.final_board:
            m.name = card_db.get(m.card_id, m.card_id)
        for minions in g.opponent_boards.values():
            for m in minions:
                m.name = card_db.get(m.card_id, m.card_id)

        boards_data = {}
        for key, minions in g.opponent_boards.items():
            boards_data[key] = [
                {
                    "card_id": m.card_id,
                    "name": card_db.get(m.card_id, m.card_id),
                    "stats": m.stat_str(),
                    "atk": m.atk,
                    "health": m.health,
                    "golden": m.golden,
                    "divine_shield": m.divine_shield,
                    "taunt": m.taunt,
                    "windfury": m.windfury,
                    "reborn": m.reborn,
                    "poisonous": m.poisonous,
                }
                for m in minions
            ]

        final_board_data = [
            {
                "card_id": m.card_id,
                "name": card_db.get(m.card_id, m.card_id),
                "stats": m.stat_str(),
                "golden": m.golden,
                "divine_shield": m.divine_shield,
                "taunt": m.taunt,
                "windfury": m.windfury,
                "reborn": m.reborn,
                "poisonous": m.poisonous,
            }
            for m in g.final_board
        ]

        result = save_game(
            game_id=g.game_id,
            start_time=g.start_time,
            end_time=g.end_time,
            build_version=g.build_version,
            game_mode=g.game_mode,
            hero_card_id=g.hero_card_id,
            hero_name=card_db.get(g.hero_card_id, g.hero_card_id),
            hero_power_ids=g.hero_power_ids,
            hero_power_names=[card_db.get(hp, hp) for hp in g.hero_power_ids],
            trinket_ids=g.trinket_ids,
            trinket_names=[card_db.get(t, t) for t in g.trinket_ids],
            placement=g.placement,
            final_board=final_board_data,
            turn_count=g.turn_count,
            max_gold=g.max_gold,
            duration_seconds=g.duration_seconds,
            opponent_heroes=g.opponent_heroes,
            opponent_boards=boards_data,
            teammate_hero_card_id=g.teammate_hero_card_id,
            teammate_hero_name=card_db.get(g.teammate_hero_card_id, g.teammate_hero_card_id),
        )
        print(f"  game: {g.game_id}  saved={result}")
        if boards_data.get("last_combat"):
            lc = boards_data["last_combat"]
            print(f"  對手板面 {len(lc)} 隻：{[m['name'] for m in lc[:5]]}")
        else:
            print(f"  對手板面 keys: {list(boards_data.keys())}")

print("\n完成！")
