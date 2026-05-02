"""
Power.log 解析器：重建實體狀態，提取英雄戰場完整對局資料。

記錄內容：
- 英雄 + 兩個技能（HERO_POWER / HERO_POWER_ENTITY）
- 兩個飾品（BATTLEGROUND_TRINKET，選中後 card_id 更新）
- 最終板面（隨從名稱、攻擊/血量/護甲，黃金標記）
- 最終名次、回合數、最高金幣、對局時長
- 全場對手英雄列表
- 遊戲模式（單打/雙打）
"""
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ── 正規表達式 ─────────────────────────────────────────────────────────────
RE_TIMESTAMP     = re.compile(r"^[DWI] (\d{2}:\d{2}:\d{2})\.\d+")
RE_CREATE_GAME   = re.compile(r"CREATE_GAME")
RE_FULL_ENTITY   = re.compile(r"(?:FULL_ENTITY|SHOW_ENTITY).*?(?:Creating|Updating).*?(?:\[.*?id=(\d+).*?cardId=(\S+?)\s|ID=(\d+)\s+CardID=(\S*))")
RE_SHOW_ENTITY   = re.compile(r"SHOW_ENTITY.*?(?:Entity=)?(?:\[.*?id=(\d+).*?\]|(\d+))\s+CardID=(\S+)")
RE_TAG_CHANGE    = re.compile(r"TAG_CHANGE Entity=(.+?) tag=(\S+) value=(\S+)")
RE_GAME_ENTITY   = re.compile(r"GameEntity EntityID=(\d+)")
RE_PLAYER_ENTITY = re.compile(r"Player EntityID=(\d+) PlayerID=(\d+) GameAccountId=\[hi=(\d+) lo=(\d+)\]")
RE_TAG_LINE      = re.compile(r"(?:^|\s+)tag=(\S+) value=(\S+)")
RE_ENTITY_REF    = re.compile(r"\[.*?id=(\d+).*?\]")
RE_CHOSEN_ENTITY = re.compile(r"Entities\[\d+\]=\[.*?id=(\d+).*?cardId=(\S+?)\s+player=(\d+)")
RE_PLAYER_NAME   = re.compile(r"PlayerID=(\d+),\s*PlayerName=(.+)")

# 戰場模式 GAME_TYPE 值
BG_GAME_TYPES = {"17", "49", "50"}   # solo / friendly / duo
DUO_GAME_TYPES = {"50"}

CARD_TYPE_HERO       = "HERO"
CARD_TYPE_HERO_POWER = "HERO_POWER"
CARD_TYPE_MINION     = "MINION"
CARD_TYPE_TRINKET    = "BATTLEGROUND_TRINKET"
ZONE_PLAY            = "PLAY"
HERO_PLACEHOLDER     = "TB_BaconShop_HERO_PH"


@dataclass
class MinionStats:
    card_id: str
    name: str = ""
    atk: int = 0
    health: int = 0
    max_health: int = 0
    armor: int = 0
    divine_shield: bool = False
    windfury: bool = False
    reborn: bool = False
    poisonous: bool = False
    golden: bool = False
    taunt: bool = False
    cleave: bool = False

    def stat_str(self) -> str:
        """格式化為 ★名稱[攻/血 +護甲｜關鍵字]"""
        prefix = "★" if self.golden else ""
        hp = self.max_health if self.max_health > 0 else self.health
        base = f"{prefix}{self.name}[{self.atk}/{hp}"
        if self.armor > 0:
            base += f"+{self.armor}護"
        base += "]"
        keywords = []
        if self.divine_shield: keywords.append("聖")
        if self.taunt:         keywords.append("嘲")
        if self.windfury:      keywords.append("風")
        if self.reborn:        keywords.append("復")
        if self.poisonous:     keywords.append("毒")
        if self.cleave:        keywords.append("劈")
        if keywords:
            base += "(" + "".join(keywords) + ")"
        return base


@dataclass
class Entity:
    entity_id: str
    card_id: str = ""
    tags: dict = field(default_factory=dict)

    def tag(self, key: str, default: str = "") -> str:
        return self.tags.get(key, default)

    @property
    def zone(self) -> str:        return self.tags.get("ZONE", "")
    @property
    def controller(self) -> str:  return self.tags.get("CONTROLLER", "")
    @property
    def card_type(self) -> str:   return self.tags.get("CARDTYPE", "")
    @property
    def zone_pos(self) -> int:
        try: return int(self.tags.get("ZONE_POSITION", "0"))
        except ValueError: return 0

    def to_minion_stats(self) -> MinionStats:
        try:   atk = int(self.tags.get("ATK", "0"))
        except: atk = 0
        try:   health = int(self.tags.get("HEALTH", "0"))
        except: health = 0
        try:   damage = int(self.tags.get("DAMAGE", "0"))
        except: damage = 0
        try:   armor = int(self.tags.get("ARMOR", "0"))
        except: armor = 0
        cur_hp = max(0, health - damage)
        return MinionStats(
            card_id=self.card_id,
            atk=atk,
            health=cur_hp,
            max_health=health,
            armor=armor,
            divine_shield=self.tags.get("DIVINE_SHIELD", "0") == "1",
            windfury=self.tags.get("WINDFURY", "0") not in ("0", ""),
            reborn=self.tags.get("REBORN", "0") == "1",
            poisonous=self.tags.get("POISONOUS", "0") == "1",
            golden=self.tags.get("PREMIUM", "") in ("GOLDEN", "1"),
            taunt=self.tags.get("TAUNT", "0") == "1",
            cleave=self.tags.get("CLEAVE", "0") == "1",
        )


@dataclass
class GameRecord:
    game_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    build_version: str = ""
    game_mode: str = "solo"           # "solo" | "duo"
    hero_card_id: str = ""
    _hero_entity_id: str = ""         # 內部用：DebugPrintEntitiesChosen 捕捉到的英雄 entity id
    hero_power_ids: list[str] = field(default_factory=list)   # 最多2個技能 card_id
    trinket_ids: list[str] = field(default_factory=list)      # 最多2個飾品 card_id
    placement: int = 0
    final_board: list[MinionStats] = field(default_factory=list)
    penultimate_board: list[MinionStats] = field(default_factory=list)  # 倒數第二場陣容
    turn_count: int = 0
    max_gold: int = 0
    duration_seconds: int = 0
    opponent_heroes: list[str] = field(default_factory=list)        # card_id list
    # {hero_card_id: [MinionStats]}，只含遊戲結束時還在場的對手板面
    opponent_boards: dict[str, list] = field(default_factory=dict)
    teammate_hero_card_id: str = ""   # 雙打隊友英雄 card_id
    is_bg: bool = False
    local_player_id: str = ""
    is_complete: bool = False


class PowerLogParser:
    def __init__(self, log_path: str, build_version: str = "", name_resolver=None):
        self.log_path = log_path
        self.build_version = build_version
        # 可選：card_id → 顯示名稱的查詢函式，由 main.py 傳入
        self._name_resolver = name_resolver or (lambda cid: cid)
        self.log_path = log_path
        self.build_version = build_version
        # 從 log 目錄名稱提取日期（Hearthstone_2026_04_30_...），確保 game_id 跨執行穩定
        self._log_date: Optional[datetime] = None
        dir_name = os.path.basename(os.path.dirname(log_path))
        date_m = re.search(r"Hearthstone_(\d{4})_(\d{2})_(\d{2})_", dir_name)
        if date_m:
            try:
                self._log_date = datetime(int(date_m.group(1)),
                                          int(date_m.group(2)),
                                          int(date_m.group(3)))
            except ValueError:
                pass
        self._reset()

    def _reset(self):
        self._entities: dict[str, Entity] = {}
        self._current_game: Optional[GameRecord] = None
        self._local_player_id: str = ""
        self._completed_games: list[GameRecord] = []
        self._parsing_entity_id: str = ""
        self._trinket_entity_ids: dict[str, int] = {}
        # 最後一次購物階段結束時的板面快照（戰鬥開始前）
        self._last_board_snapshot: list = []
        # 倒數第二次的板面快照
        self._prev_board_snapshot: list = []
        # entityName（含 BattleTag）→ entity_id 對應表，供 _resolve_entity_id 使用
        self._name_to_eid: dict[str, str] = {}
        # PlayerID → PlayerName（從 DebugPrintGame 行取得）
        self._player_id_to_name: dict[str, str] = {}
        # 本地玩家的 BACON_DUO_TEAM_ID（雙打隊友偵測用）
        self._local_team_id: str = ""
        # 最後一行 log 的時間戳（HH:MM:SS），用於計算正確的對局時長
        self._last_log_time_str: Optional[str] = None
        # 戰鬥開始時（MAIN_READY）最高的 entity ID 數字（用於隔離本輪戰鬥副本）
        self._combat_start_eid: int = 0
        # 最後一輪戰鬥中對手的板面（CTRL=15 非 passable 的隨從副本）
        self._last_opponent_combat_board: list = []
        # 最後一輪戰鬥中隊友傳送過來的隨從（CTRL=local, passable=1）
        self._last_teammate_combat_board: list = []
        # 開局模式是否已公告（避免重複印）
        self._mode_announced: bool = False

    # ── 公開 API ──────────────────────────────────────────────────────────

    def parse_file(self, content: str) -> list[GameRecord]:
        self._reset()
        for line in content.splitlines():
            self._process_line(line)
        return list(self._completed_games)

    def parse_lines(self, lines: list[str]) -> list[GameRecord]:
        before = len(self._completed_games)
        for line in lines:
            self._process_line(line)
        return self._completed_games[before:]

    # ── 私有方法 ──────────────────────────────────────────────────────────

    def _process_line(self, line: str):
        # 飾品選擇：解析 DebugPrintEntitiesChosen（伺服器確認玩家的選擇）
        if "GameState.DebugPrintEntitiesChosen()" in line:
            self._handle_entities_chosen_line(line)
            return

        # DebugPrintGame：取得玩家名稱 + ScenarioID（開局模式偵測）
        if "GameState.DebugPrintGame()" in line:
            if "PlayerName" in line:
                m = RE_PLAYER_NAME.search(line)
                if m:
                    self._player_id_to_name[m.group(1)] = m.group(2).strip()
            if "ScenarioID=" in line and self._current_game:
                sm = re.search(r"ScenarioID=(\d+)", line)
                if sm:
                    self._announce_mode_from_scenario(sm.group(1))
            return

        # 只處理 GameState 的輸出（PowerTaskList 是動畫用的重複資料）
        if "GameState.DebugPrintPower()" not in line:
            return

        # 提取 log 行的時間戳（HH:MM:SS）
        ts_m = RE_TIMESTAMP.match(line)
        log_time_str = ts_m.group(1) if ts_m else None
        prev_log_time_str = self._last_log_time_str  # 儲存前一個時間，跨午夜偵測用
        if log_time_str:
            self._last_log_time_str = log_time_str

        # 去掉 log prefix
        marker = "GameState.DebugPrintPower() - "
        idx = line.find(marker)
        if idx < 0:
            return
        content = line[idx + len(marker):].strip()

        if not content:
            return

        # 新遊戲
        if RE_CREATE_GAME.search(content):
            self._start_new_game(log_time_str, prev_log_time_str)
            return

        if self._current_game is None:
            return

        # GameEntity 區塊
        m = RE_GAME_ENTITY.search(content)
        if m:
            self._parsing_entity_id = m.group(1)
            eid = self._parsing_entity_id
            if eid not in self._entities:
                self._entities[eid] = Entity(entity_id=eid)
            return

        # Player 區塊
        m = RE_PLAYER_ENTITY.search(content)
        if m:
            self._handle_player_entity(m.group(1), m.group(2), m.group(3), m.group(4))
            return

        # FULL_ENTITY / SHOW_ENTITY / CHANGE_ENTITY（含 [entityName=...] 格式）
        if "FULL_ENTITY" in content or "SHOW_ENTITY" in content or "CHANGE_ENTITY" in content:
            self._handle_entity_line(content)
            return

        # 縮排 tag= 子行
        if "tag=" in content and "TAG_CHANGE" not in content:
            mt = RE_TAG_LINE.search(content)
            if mt and self._parsing_entity_id:
                self._set_entity_tag(self._parsing_entity_id, mt.group(1), mt.group(2))
            return

        # TAG_CHANGE
        m = RE_TAG_CHANGE.search(content)
        if m:
            self._handle_tag_change(m.group(1).strip(), m.group(2), m.group(3))
            return

    # ScenarioID → 確認遊戲模式並即時顯示
    # 已知：5173 = 雙打，3459 = 單打（其他 BG 模式未來可補充）
    _SCENARIO_DUO  = {"5173"}
    _SCENARIO_SOLO = {"3459"}

    def _announce_mode_from_scenario(self, scenario_id: str):
        game = self._current_game
        if not game or self._mode_announced:
            return
        if scenario_id in self._SCENARIO_DUO:
            game.game_mode = "duo"
            self._mode_announced = True
            print(f"\n{'─'*40}")
            print(f"  開局偵測：【雙打模式】（ScenarioID={scenario_id}）")
            print(f"{'─'*40}\n")
        elif scenario_id in self._SCENARIO_SOLO:
            game.game_mode = "solo"
            self._mode_announced = True
            print(f"\n{'─'*40}")
            print(f"  開局偵測：【單打模式】（ScenarioID={scenario_id}）")
            print(f"{'─'*40}\n")
        else:
            # 未知 ScenarioID，依 BACON_DUO_TEAM_ID 判斷，這裡先記下
            print(f"[parser] 未知 ScenarioID={scenario_id}，等待 BACON_DUO_TEAM_ID 確認模式")

    def _start_new_game(self, log_time_str: Optional[str] = None, prev_log_time_str: Optional[str] = None):
        if self._current_game and not self._current_game.is_complete:
            self._finalize_game(force=True)

        # 用 log 行的 HH:MM:SS 作為 start_time；日期優先用目錄名稱，確保跨執行穩定
        now = datetime.now()
        if log_time_str:
            try:
                t = datetime.strptime(log_time_str, "%H:%M:%S")
                if self._log_date:
                    # 目錄名已含日期，直接用，不受執行時間點影響
                    start_time = self._log_date.replace(
                        hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
                    # 跨午夜偵測：若前一行 log 時間是深夜（>=18:00）
                    # 而本局開始時間是凌晨（<6:00），表示跨過午夜，日期 +1
                    check_prev = prev_log_time_str or self._last_log_time_str
                    if check_prev:
                        try:
                            from datetime import timedelta
                            prev_t = datetime.strptime(check_prev, "%H:%M:%S")
                            if t.hour < 6 and prev_t.hour >= 18:
                                start_time += timedelta(days=1)
                                print(f"[parser] 跨午夜偵測：{check_prev} → {log_time_str}，日期 +1")
                        except ValueError:
                            pass
                else:
                    start_time = now.replace(
                        hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
                    # log 時間若在現在時刻之後，表示 log 是昨天（或更早）的
                    if start_time > now:
                        from datetime import timedelta
                        start_time -= timedelta(days=1)
            except ValueError:
                start_time = now.replace(microsecond=0)
        else:
            start_time = now.replace(microsecond=0)

        self._current_game = GameRecord(
            game_id="",          # 在 _finalize_game 確定英雄後才設定
            start_time=start_time,
            build_version=self.build_version,
        )
        self._entities = {}
        self._local_player_id = ""
        self._parsing_entity_id = ""
        self._trinket_entity_ids = {}
        self._last_board_snapshot = []
        self._name_to_eid = {}
        self._player_id_to_name = {}
        self._combat_start_eid = 0
        self._last_opponent_combat_board = []
        self._last_teammate_combat_board = []
        self._mode_announced = False
        print(f"[parser] 新對局")

    def _handle_entity_line(self, content: str):
        """解析 FULL_ENTITY / SHOW_ENTITY，支援兩種格式：
        1. FULL_ENTITY - Creating ID=X CardID=Y
        2. FULL_ENTITY - Updating [entityName=... id=X ... cardId=Y player=Z] CardID=Y
        """
        # 格式2：[...id=X...cardId=Y...]
        bracket_m = RE_ENTITY_REF.search(content)
        card_id_m = re.search(r"CardID=(\S+)", content)

        if bracket_m:
            eid = bracket_m.group(1)
            card_id = card_id_m.group(1) if card_id_m else ""
            # 也從括號內取 player
            player_m = re.search(r"player=(\d+)", content)
            if player_m:
                self._set_entity_tag(eid, "CONTROLLER", player_m.group(1))
            # 記錄 entityName → eid（BattleTag 等名稱之後在 TAG_CHANGE 裡會用到）
            name_m = re.search(r"\[entityName=([^\] ]+)", content)
            if name_m:
                self._name_to_eid[name_m.group(1)] = eid
        else:
            # 格式1：ID=X CardID=Y
            id_m = re.search(r"(?:ID|id)=(\d+)", content)
            if not id_m:
                return
            eid = id_m.group(1)
            card_id = card_id_m.group(1) if card_id_m else ""

        if not eid:
            return
        self._parsing_entity_id = eid
        if eid not in self._entities:
            self._entities[eid] = Entity(entity_id=eid)
        if card_id and card_id not in ("0", ""):
            self._entities[eid].card_id = card_id

        # 識別飾品槽位
        if card_id in ("BG30_Trinket_1st", "BG30_Trinket_2nd"):
            slot = 1 if card_id == "BG30_Trinket_1st" else 2
            self._trinket_entity_ids[eid] = slot

    def _handle_player_entity(self, entity_id: str, player_id: str,
                               hi: str, lo: str):
        self._parsing_entity_id = entity_id
        if entity_id not in self._entities:
            self._entities[entity_id] = Entity(entity_id=entity_id)
        self._entities[entity_id].tags["PLAYER_ID"] = player_id

        if lo != "0" and not self._local_player_id:
            self._local_player_id = player_id
            if self._current_game:
                self._current_game.local_player_id = player_id

    def _handle_entities_chosen_line(self, line: str):
        """解析 GameState.DebugPrintEntitiesChosen() 行，捕捉英雄選擇與飾品選擇。"""
        if not self._current_game:
            return
        m = RE_CHOSEN_ENTITY.search(line)
        if not m:
            return
        entity_id = m.group(1)
        card_id   = m.group(2)
        player_id = m.group(3)
        game = self._current_game

        # 只處理本地玩家的選擇
        if self._local_player_id and player_id != self._local_player_id:
            return

        # 英雄選擇：DebugPrintEntitiesChosen 是最可靠的來源（覆蓋初始的佔位英雄）
        # 真實英雄 card_id 格式：BG23_HERO_304、BG22_HERO_000 等（非 TB_BaconShop_HERO_*）
        ent = self._entities.get(entity_id)
        is_hero = (ent and ent.tags.get("CARDTYPE") == "HERO") or ("_HERO_" in card_id)
        if is_hero and card_id != HERO_PLACEHOLDER:
            game.hero_card_id = card_id
            game._hero_entity_id = entity_id
            hero_name = self._name_resolver(card_id)
            print(f"[parser] 英雄選擇（確認）：{hero_name}（{card_id}，entity={entity_id}）")
            return

        # 飾品選擇（BG__MagicItem__）
        if "MagicItem" in card_id:
            if card_id not in game.trinket_ids:
                game.trinket_ids.append(card_id)
                print(f"[parser] 飾品選擇：{card_id}")

    def _set_entity_tag(self, eid: str, tag: str, value: str):
        if eid not in self._entities:
            self._entities[eid] = Entity(entity_id=eid)
        self._entities[eid].tags[tag] = value

        game = self._current_game
        if not game:
            return

        # BG 模式偵測
        if tag in ("BACON_BARTENDER_CARD_ID", "BACON_TRINKETS_ACTIVE"):
            game.is_bg = True

        # 雙打偵測
        # 只有 BACON_DUO_TEAM_ID 才代表雙打；BACON_DUOS_PUNISH_LEAVERS 單打也有
        if tag == "BACON_DUO_TEAM_ID" and value not in ("0", ""):
            game.game_mode = "duo"
            # 若 ScenarioID 未知（未公告），由此補上
            if not self._mode_announced:
                self._mode_announced = True
                print(f"\n{'─'*40}")
                print(f"  開局偵測：【雙打模式】（BACON_DUO_TEAM_ID={value}）")
                print(f"{'─'*40}\n")

        # 雙打隊伍 ID：本地玩家 Player entity 的 BACON_DUO_TEAM_ID
        if tag == "BACON_DUO_TEAM_ID" and value not in ("0", "") and self._local_player_id:
            ent = self._entities.get(eid)
            if ent and ent.tags.get("PLAYER_ID") == self._local_player_id:
                self._local_team_id = value

        # 飾品槽位追蹤
        if tag == "CARDTYPE" and value == CARD_TYPE_TRINKET:
            if eid not in self._trinket_entity_ids:
                self._trinket_entity_ids[eid] = len(self._trinket_entity_ids) + 1

    def _handle_tag_change(self, entity: str, tag: str, value: str):
        game = self._current_game
        if not game:
            return

        entity_id = self._resolve_entity_id(entity)

        if entity_id:
            # 從 entity ref 的 player=X 補充 CONTROLLER（TAG_CHANGE 不另外設 CONTROLLER）
            player_m = re.search(r"player=(\d+)", entity)
            if player_m:
                self._set_entity_tag(entity_id, "CONTROLLER", player_m.group(1))
            self._set_entity_tag(entity_id, tag, value)

        # ── 關鍵標籤 ──

        # BG 模式：靠 BACON_BARTENDER_CARD_ID 或 BACON_TRINKETS_ACTIVE 偵測（log 裡沒有 GAME_TYPE）
        if tag in ("BACON_BARTENDER_CARD_ID", "BACON_TRINKETS_ACTIVE"):
            game.is_bg = True

        if tag == "GAME_TYPE" and value in BG_GAME_TYPES:
            game.is_bg = True
            if value in DUO_GAME_TYPES:
                game.game_mode = "duo"

        # 本地玩家的英雄
        local_eid = self._get_local_player_entity_id()
        if tag == "HERO_ENTITY" and entity_id == local_eid:
            hero_eid = value
            hero_ent = self._entities.get(hero_eid)
            if hero_ent and hero_ent.card_id and hero_ent.card_id != HERO_PLACEHOLDER:
                game.hero_card_id = hero_ent.card_id

        # 英雄技能（HERO_POWER 和 HERO_POWER_ENTITY 都算）
        if tag in ("HERO_POWER", "HERO_POWER_ENTITY"):
            # 找到這個 tag 屬於本地玩家的英雄 entity
            owner_eid = entity_id or self._find_local_hero_entity_id()
            if owner_eid and self._is_local_hero_entity(owner_eid):
                hp_eid = value
                hp_ent = self._entities.get(hp_eid)
                if hp_ent and hp_ent.card_id:
                    cid = hp_ent.card_id
                    if cid not in game.hero_power_ids:
                        game.hero_power_ids.append(cid)

        # 英雄技能：追蹤 BACON_HERO_POWER_ACTIVATED=1（只在 TAG_CHANGE 有 entity ref 才可靠）
        if tag == "BACON_HERO_POWER_ACTIVATED" and value == "1" and entity_id:
            ent = self._entities.get(entity_id)
            if ent and ent.card_id and ent.controller == self._local_player_id:
                if ent.card_id not in game.hero_power_ids:
                    game.hero_power_ids.append(ent.card_id)

        # 最終名次
        if tag == "PLAYER_LEADERBOARD_PLACE":
            pid = self._get_player_id_from_entity(entity_id or entity)
            if pid == self._local_player_id:
                try:
                    game.placement = int(value)
                    print(f"[parser] 名次={value}")
                except ValueError:
                    pass

        # 回合數
        if tag == "TURN":
            try:
                v = int(value)
                if v > game.turn_count:
                    game.turn_count = v
            except ValueError:
                pass

        # 最高金幣（RESOURCES = 當回合可用金幣）
        if tag == "RESOURCES":
            pid = self._get_player_id_from_entity(entity_id or entity)
            if pid == self._local_player_id:
                try:
                    v = int(value)
                    if v > game.max_gold:
                        game.max_gold = v
                except ValueError:
                    pass

        # 戰鬥開始前（MAIN_READY）：快照本地板面 + 記錄 entity ID 基準
        if tag == "STEP" and value == "MAIN_READY":
            self._snapshot_board()
            # 記錄目前最高 entity ID，讓後續只看本輪新建的戰鬥副本
            if self._entities:
                try:
                    self._combat_start_eid = max(int(e) for e in self._entities if e.isdigit())
                except ValueError:
                    pass

        # 戰鬥結束後（MAIN_END）：收集對手 / 隊友板面副本
        if tag == "STEP" and value == "MAIN_END":
            self._capture_combat_boards()

        # 戰鬥開始前，拍板面快照（此時隨從還在 PLAY zone）
        if tag == "STEP" and value == "MAIN_COMBAT":
            self._snapshot_board()

        # 遊戲結束
        if tag == "STATE" and value == "COMPLETE":
            self._capture_game_end()
            self._finalize_game()

    def _resolve_entity_id(self, entity_str: str) -> Optional[str]:
        if not entity_str:
            return None
        # 可能是純數字 ID
        if entity_str.isdigit():
            return entity_str
        # 可能是 [entityName=... id=X ...] 格式
        m = RE_ENTITY_REF.search(entity_str)
        if m:
            return m.group(1)
        # BattleTag / entityName 查表（TAG_CHANGE Entity=Insane#3202 這類格式）
        if entity_str in self._name_to_eid:
            return self._name_to_eid[entity_str]
        # 玩家名稱反查（PLAYER_ID 欄位）
        for eid, ent in self._entities.items():
            if ent.tags.get("PLAYER_ID") == entity_str:
                return eid
        return None

    def _get_local_player_entity_id(self) -> Optional[str]:
        for eid, ent in self._entities.items():
            if ent.tags.get("PLAYER_ID") == self._local_player_id:
                return eid
        return None

    def _snapshot_board(self):
        """在戰鬥開始前（STEP=MAIN_COMBAT）拍下本地玩家板面快照。"""
        local_pid = self._local_player_id
        if not local_pid:
            return
        board: list[tuple[int, MinionStats]] = []
        for ent in self._entities.values():
            if (ent.card_type == CARD_TYPE_MINION
                    and ent.zone == ZONE_PLAY
                    and ent.controller == local_pid
                    and ent.card_id):
                ms = ent.to_minion_stats()
                board.append((ent.zone_pos, ms))
        board.sort(key=lambda x: x[0])
        if board:
            self._prev_board_snapshot = self._last_board_snapshot  # 舊的變倒數第二
            self._last_board_snapshot = [ms for _, ms in board]

    def _find_local_hero_entity_id(self) -> Optional[str]:
        """找本地玩家的英雄 entity（優先 PLAY zone，game end 時 fallback 不限 zone）。"""
        # 先找 PLAY zone
        for eid, ent in self._entities.items():
            if (ent.card_type == CARD_TYPE_HERO
                    and ent.controller == self._local_player_id
                    and ent.zone == ZONE_PLAY
                    and ent.card_id != HERO_PLACEHOLDER):
                return eid
        # fallback：不限 zone（遊戲結束後英雄可能已離開 PLAY）
        for eid, ent in self._entities.items():
            if (ent.card_type == CARD_TYPE_HERO
                    and ent.controller == self._local_player_id
                    and ent.card_id
                    and ent.card_id != HERO_PLACEHOLDER):
                return eid
        return None

    def _is_local_hero_entity(self, eid: str) -> bool:
        ent = self._entities.get(eid)
        if not ent:
            return False
        return (ent.card_type == CARD_TYPE_HERO
                and ent.controller == self._local_player_id)

    def _get_player_id_from_entity(self, entity_id_or_name: str) -> str:
        eid = self._resolve_entity_id(entity_id_or_name)
        if eid:
            ent = self._entities.get(eid)
            if ent:
                pid = ent.tags.get("PLAYER_ID")
                if pid:
                    return pid
                return ent.controller
        return entity_id_or_name  # 可能本身就是 player name

    def _capture_combat_boards(self):
        """在 MAIN_END（戰鬥結束後）收集本輪戰鬥中對手和隊友板面副本。
        
        戰場副本結構（DUO 模式）：
          - CTRL=local_pid, PASSABLE=0: 本地玩家自身的戰鬥副本
          - CTRL=local_pid, PASSABLE=1: 隊友傳送過來協助的隨從
          - CTRL=15,        PASSABLE=0: 對手自身的板面副本
          - CTRL=15,        PASSABLE=1: 對手隊友傳送過來的隨從
        """
        if self._combat_start_eid == 0:
            return
        game = self._current_game
        if not game:
            return

        local_pid = self._local_player_id
        opponent_minions: list[tuple[int, MinionStats]] = []
        teammate_minions: list[tuple[int, MinionStats]] = []

        for eid, ent in self._entities.items():
            # 只看本輪戰鬥新建的 entity
            try:
                if int(eid) <= self._combat_start_eid:
                    continue
            except ValueError:
                continue

            if ent.card_type != CARD_TYPE_MINION or not ent.card_id:
                continue
            # 排除 UI / 佔位 卡牌
            if ent.card_id.startswith("TB_") or ent.card_id == HERO_PLACEHOLDER:
                continue

            passable = ent.tags.get("BACON_DUO_PASSABLE", "0") == "1"
            ctrl = ent.controller
            pos = ent.zone_pos

            if ctrl == "15" and not passable:
                # 對手主力板面副本
                opponent_minions.append((pos, ent.to_minion_stats()))
            elif ctrl == local_pid and passable:
                # 隊友傳送過來的隨從（PASSABLE=1 + 本地玩家 CTRL）
                teammate_minions.append((pos, ent.to_minion_stats()))

        if opponent_minions:
            opponent_minions.sort(key=lambda x: x[0])
            self._last_opponent_combat_board = [ms for _, ms in opponent_minions]
        if teammate_minions:
            teammate_minions.sort(key=lambda x: x[0])
            self._last_teammate_combat_board = [ms for _, ms in teammate_minions]

    def _capture_game_end(self):
        game = self._current_game
        if not game:
            return

        # ── 最終板面（優先用快照，game end 時隨從已離開 PLAY zone）──
        local_pid = self._local_player_id
        if self._last_board_snapshot:
            game.final_board = self._last_board_snapshot
        else:
            # fallback：直接讀目前 PLAY zone
            board: list[tuple[int, MinionStats]] = []
            for ent in self._entities.values():
                if (ent.card_type == CARD_TYPE_MINION
                        and ent.zone == ZONE_PLAY
                        and ent.controller == local_pid
                        and ent.card_id):
                    ms = ent.to_minion_stats()
                    board.append((ent.zone_pos, ms))
            board.sort(key=lambda x: x[0])
            game.final_board = [ms for _, ms in board]
        print(f"[parser] 板面 {len(game.final_board)} 隻：{[m.card_id for m in game.final_board]}")
        # 倒數第二場陣容
        if self._prev_board_snapshot:
            game.penultimate_board = self._prev_board_snapshot
            print(f"[parser] 倒數第二場 {len(game.penultimate_board)} 隻：{[m.card_id for m in game.penultimate_board]}")

        # ── 英雄（再確認一次）──
        hero_eid = self._find_local_hero_entity_id()
        if hero_eid and not game.hero_card_id:
            game.hero_card_id = self._entities[hero_eid].card_id

        # ── 英雄技能：掃描 CARDTYPE=HERO_POWER + CONTROLLER=local_pid + ZONE=PLAY ──
        # 強制重掃：Duos 模式下對手英雄技能會被標記 BACON_HERO_POWER_ACTIVATED，
        # 且 controller 也可能是 local_pid（幽靈戰），所以用 zone=PLAY 過濾才可靠。
        game.hero_power_ids = []
        seen_hp: set[str] = set()
        for ent in self._entities.values():
            if (ent.card_type == CARD_TYPE_HERO_POWER
                    and ent.controller == local_pid
                    and ent.zone == ZONE_PLAY
                    and ent.card_id
                    and ent.card_id not in seen_hp):
                seen_hp.add(ent.card_id)
                game.hero_power_ids.append(ent.card_id)

        # ── 飾品：優先用 live-tracking（BACON_TRINKET=1），不再掃描所有 entity ──
        # live-tracking 已在 _handle_tag_change 中填入 game.trinket_ids

        # ── 對手英雄 + 對手板面 ──
        # 雙打：先找隊友（同隊伍 ID、非本地玩家的英雄），從對手列表排除
        teammate_card_ids: set[str] = set()
        if game.game_mode == "duo" and self._local_team_id:
            local_hero_eid = game._hero_entity_id
            for eid, ent in self._entities.items():
                if (ent.card_type == CARD_TYPE_HERO
                        and ent.controller != local_pid
                        and ent.controller != ""
                        and ent.card_id
                        and ent.card_id != HERO_PLACEHOLDER
                        and ent.tags.get("BACON_DUO_TEAM_ID") == self._local_team_id
                        and eid != local_hero_eid):
                    game.teammate_hero_card_id = ent.card_id
                    teammate_card_ids.add(ent.card_id)
                    print(f"[parser] 隊友英雄：{ent.card_id}")
                    break

        # 收集所有非本地玩家的英雄（排除隊友）
        opponent_hero_map: dict[str, str] = {}  # player_id → hero card_id

        for ent in self._entities.values():
            if (ent.card_type == CARD_TYPE_HERO
                    and ent.controller != local_pid
                    and ent.controller != ""
                    and ent.card_id
                    and ent.card_id != HERO_PLACEHOLDER
                    and ent.card_id not in teammate_card_ids):
                if ent.card_id not in game.opponent_heroes:
                    game.opponent_heroes.append(ent.card_id)
                opponent_hero_map[ent.controller] = ent.card_id

        # 收集對手隨從（優先用最後一輪戰鬥的副本，fallback 讀遊戲結束時的 PLAY zone）
        opp_boards: dict[str, list[tuple[int, MinionStats]]] = {}
        if self._last_opponent_combat_board:
            # 用最後一輪捕捉的對手戰鬥副本
            game.opponent_boards = {"last_combat": self._last_opponent_combat_board}
            print(f"[parser] 對手板面 {len(self._last_opponent_combat_board)} 隻（戰鬥副本）")
        else:
            # fallback：讀遊戲結束時仍在 PLAY zone 的對手隨從
            for ent in self._entities.values():
                if (ent.card_type == CARD_TYPE_MINION
                        and ent.zone == ZONE_PLAY
                        and ent.controller != local_pid
                        and ent.controller != ""
                        and ent.card_id):
                    hero_cid = opponent_hero_map.get(ent.controller, f"player_{ent.controller}")
                    opp_boards.setdefault(hero_cid, [])
                    opp_boards[hero_cid].append((ent.zone_pos, ent.to_minion_stats()))

            game.opponent_boards = {
                hero_cid: [ms for _, ms in sorted(minions, key=lambda x: x[0])]
                for hero_cid, minions in opp_boards.items()
            }

        # ── 對局時長（用 log 時間戳，避免重新解析時用到現在時間）──
        if game.start_time and self._last_log_time_str:
            try:
                t = datetime.strptime(self._last_log_time_str, "%H:%M:%S")
                log_date = self._log_date or game.start_time.date()
                end_time = datetime(log_date.year, log_date.month, log_date.day,
                                    t.hour, t.minute, t.second)
                # 若結束時間早於開始時間，表示跨日
                if end_time < game.start_time:
                    from datetime import timedelta
                    end_time += timedelta(days=1)
                game.duration_seconds = int((end_time - game.start_time).total_seconds())
            except Exception:
                game.duration_seconds = int((datetime.now() - game.start_time).total_seconds())
        hero_name = self._name_resolver(game.hero_card_id) if game.hero_card_id else "未知"
        mate_name = self._name_resolver(game.teammate_hero_card_id) if game.teammate_hero_card_id else ""
        print(f"[parser] 英雄={hero_name}, 隊友={mate_name}, 技能={game.hero_power_ids}, 飾品={game.trinket_ids}")

    def _finalize_game(self, force: bool = False):
        game = self._current_game
        if not game:
            return

        # 用 log 時間戳設定 end_time（避免重新解析時時間偏移）
        if self._last_log_time_str:
            try:
                t = datetime.strptime(self._last_log_time_str, "%H:%M:%S")
                log_date = self._log_date or game.start_time.date() if game.start_time else datetime.now().date()
                end_dt = datetime(log_date.year, log_date.month, log_date.day,
                                  t.hour, t.minute, t.second)
                if game.start_time and end_dt < game.start_time:
                    from datetime import timedelta
                    end_dt += timedelta(days=1)
                game.end_time = end_dt
            except Exception:
                game.end_time = datetime.now()
        else:
            game.end_time = datetime.now()
        game.is_complete = True
        game.turn_count = game.turn_count // 2  # 每2個TURN = 1完整回合

        # 用 start_time + hero_card_id 產生穩定的 game_id
        # 重新解析同一份 log 時，相同對局會得到相同 id → 去重生效
        ts  = game.start_time.strftime("%Y%m%d%H%M%S")
        hero = game.hero_card_id or "unknown"
        game.game_id = f"game_{ts}_{hero}"

        if game.is_bg and (game.placement > 0 or force):
            self._completed_games.append(game)
            print(f"[parser] 對局記錄：{game.game_id}  名次={game.placement}, 模式={game.game_mode}")
        else:
            reason = []
            if not game.is_bg: reason.append("非BG")
            if game.placement == 0: reason.append("無名次")
            print(f"[parser] 略過（{', '.join(reason)}）")

        self._current_game = None
