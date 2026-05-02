"""從 SQLite DB 重新產生 Excel（不改動 DB）。"""
import sqlite3
import json
import os
from datetime import datetime
from excel_writer import append_record, EXCEL_PATH

conn = sqlite3.connect("data/records.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM games ORDER BY start_time").fetchall()
conn.close()

# 刪舊 Excel，從頭重建
target_path = EXCEL_PATH
if os.path.exists(EXCEL_PATH):
    try:
        os.remove(EXCEL_PATH)
        print(f"已刪除舊 Excel: {EXCEL_PATH}")
    except PermissionError:
        # 檔案被 Excel 開著，改寫到備份路徑
        target_path = EXCEL_PATH.replace(".xlsx", "_new.xlsx")
        if os.path.exists(target_path):
            os.remove(target_path)
        print(f"⚠️  Excel 已開啟，將寫入備份：{target_path}")
        print("   請關閉 Excel 後，手動將 _new.xlsx 改名取代原檔。")

# 暫時改寫目標路徑
import excel_writer as _ew
_orig_path = _ew.EXCEL_PATH
_ew.EXCEL_PATH = target_path

for row in rows:
    start_time = datetime.fromisoformat(row["start_time"])
    board_data = json.loads(row["final_board"])
    board_strs = [d["stats"] for d in board_data] if board_data else []

    opp_boards_data = json.loads(row["opponent_boards"])
    opp_board_strs = []
    for hero_label, minions in opp_boards_data.items():
        minion_strs = [m["stats"] for m in minions if "stats" in m]
        if minion_strs:
            opp_board_strs.append(hero_label + "：" + "、".join(minion_strs))

    success = append_record(
        start_time=start_time,
        build_version=row["build_version"],
        game_mode=row["game_mode"],
        hero_name=row["hero_name"],
        teammate_hero_name=row["teammate_hero_name"] or "",
        power_names=json.loads(row["hero_power_names"]),
        trinket_names=json.loads(row["trinket_names"]),
        placement=row["placement"],
        board_strs=board_strs,
        turn_count=row["turn_count"],
        max_gold=row["max_gold"],
        duration_seconds=row["duration_seconds"],
        opponent_names=json.loads(row["opponent_heroes"]),
        opponent_board_strs=opp_board_strs,
    )
    status = "OK" if success else "FAIL"
    print(f"{status} [{row['game_id']}]")
    print(f"   英雄={row['hero_name']}  技能={row['hero_power_names']}  飾品={row['trinket_names']}  名次={row['placement']}")

print("\nExcel 重建完成！")
