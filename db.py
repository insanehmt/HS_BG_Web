"""
SQLite 資料庫：對局紀錄的 source of truth，防止重複寫入。
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "records.db")


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_id           TEXT PRIMARY KEY,
                start_time        TEXT NOT NULL,
                end_time          TEXT,
                build_version     TEXT DEFAULT '',
                game_mode         TEXT DEFAULT 'solo',
                hero_card_id      TEXT DEFAULT '',
                hero_name         TEXT DEFAULT '',
                hero_power_ids    TEXT DEFAULT '[]',
                hero_power_names  TEXT DEFAULT '[]',
                trinket_ids       TEXT DEFAULT '[]',
                trinket_names     TEXT DEFAULT '[]',
                placement         INTEGER DEFAULT 0,
                final_board       TEXT DEFAULT '[]',
                penultimate_board TEXT DEFAULT '[]',
                turn_count        INTEGER DEFAULT 0,
                max_gold          INTEGER DEFAULT 0,
                duration_seconds  INTEGER DEFAULT 0,
                opponent_heroes   TEXT DEFAULT '[]',
                opponent_boards   TEXT DEFAULT '{}',
                teammate_hero_card_id TEXT DEFAULT '',
                teammate_hero_name    TEXT DEFAULT '',
                exported          INTEGER DEFAULT 0
            )
        """)
        # 升級現有資料庫：補上新欄位（若已存在則略過）
        for col, default in [
            ("teammate_hero_card_id", "''"),
            ("teammate_hero_name",    "''"),
            ("penultimate_board",     "'[]'"),
        ]:
            try:
                conn.execute(f"ALTER TABLE games ADD COLUMN {col} TEXT DEFAULT {default}")
            except Exception:
                pass
        conn.commit()


def game_exists(game_id: str) -> bool:
    with _get_conn() as conn:
        return conn.execute(
            "SELECT 1 FROM games WHERE game_id=?", (game_id,)
        ).fetchone() is not None


def start_time_exists(start_time: datetime) -> bool:
    """在相同 start_time 已有紀錄，表示這是隊友英雄的重複紀錄。"""
    with _get_conn() as conn:
        return conn.execute(
            "SELECT 1 FROM games WHERE start_time=?",
            (start_time.isoformat(),)
        ).fetchone() is not None


def save_game(
    game_id: str,
    start_time: datetime,
    end_time: Optional[datetime],
    build_version: str,
    game_mode: str,
    hero_card_id: str,
    hero_name: str,
    hero_power_ids: list[str],
    hero_power_names: list[str],
    trinket_ids: list[str],
    trinket_names: list[str],
    placement: int,
    final_board: list[dict],
    penultimate_board: list[dict],
    turn_count: int,
    max_gold: int,
    duration_seconds: int,
    opponent_heroes: list[str],
    opponent_boards: dict,
    teammate_hero_card_id: str = "",
    teammate_hero_name: str = "",
) -> bool:
    """儲存一筆紀錄。若已存在且 opponent_boards 為空則更新板面資料；否則略過。回傳是否有寫入。"""
    with _get_conn() as conn:
        existing = conn.execute(
            "SELECT opponent_boards FROM games WHERE game_id=?", (game_id,)
        ).fetchone()

        if existing is not None:
            # 若已有對手板面資料，直接略過
            existing_ob = json.loads(existing[0]) if existing[0] else {}
            if existing_ob:
                print(f"[db] 已存在 {game_id}，略過")
                return False
            # 否則只更新板面相關欄位
            conn.execute(
                "UPDATE games SET opponent_boards=?, final_board=?, penultimate_board=? WHERE game_id=?",
                (
                    json.dumps(opponent_boards, ensure_ascii=False),
                    json.dumps(final_board, ensure_ascii=False),
                    json.dumps(penultimate_board, ensure_ascii=False),
                    game_id,
                ),
            )
            conn.commit()
            print(f"[db] 更新板面 {game_id}")
            return True

    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO games (
                game_id, start_time, end_time, build_version, game_mode,
                hero_card_id, hero_name, hero_power_ids, hero_power_names,
                trinket_ids, trinket_names, placement, final_board, penultimate_board,
                turn_count, max_gold, duration_seconds, opponent_heroes,
                opponent_boards, teammate_hero_card_id, teammate_hero_name
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                game_id,
                start_time.isoformat(),
                end_time.isoformat() if end_time else None,
                build_version,
                game_mode,
                hero_card_id,
                hero_name,
                json.dumps(hero_power_ids, ensure_ascii=False),
                json.dumps(hero_power_names, ensure_ascii=False),
                json.dumps(trinket_ids, ensure_ascii=False),
                json.dumps(trinket_names, ensure_ascii=False),
                placement,
                json.dumps(final_board, ensure_ascii=False),
                json.dumps(penultimate_board, ensure_ascii=False),
                turn_count,
                max_gold,
                duration_seconds,
                json.dumps(opponent_heroes, ensure_ascii=False),
                json.dumps(opponent_boards, ensure_ascii=False),
                teammate_hero_card_id,
                teammate_hero_name,
            ),
        )
        conn.commit()
    return True


def mark_exported(game_id: str):
    with _get_conn() as conn:
        conn.execute("UPDATE games SET exported=1 WHERE game_id=?", (game_id,))
        conn.commit()


def get_stats() -> dict:
    with _get_conn() as conn:
        total   = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
        first   = conn.execute("SELECT COUNT(*) FROM games WHERE placement=1").fetchone()[0]
        solo    = conn.execute("SELECT COUNT(*) FROM games WHERE game_mode='solo'").fetchone()[0]
        duo     = conn.execute("SELECT COUNT(*) FROM games WHERE game_mode='duo'").fetchone()[0]
    return {"total": total, "first": first, "solo": solo, "duo": duo}
