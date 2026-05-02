"""
標準對戰遊戲狀態解析器 — 解析 Power.log 即時追蹤手牌、板面、法力水晶
"""
import re
from dataclasses import dataclass, field
from typing import Optional

RE_TIMESTAMP    = re.compile(r"^[DWI] (\d{2}:\d{2}:\d{2})")
RE_CREATE_GAME  = re.compile(r"CREATE_GAME")
RE_PLAYER_ENT   = re.compile(r"Player EntityID=(\d+) PlayerID=(\d+) GameAccountId=\[hi=(\d+) lo=(\d+)\]")
RE_FULL_ENTITY  = re.compile(r"(?:FULL_ENTITY|SHOW_ENTITY|CHANGE_ENTITY).*?(?:Creating|Updating).*?(?:\[.*?id=(\d+).*?cardId=(\S+?)\s|ID=(\d+)\s+CardID=(\S*))")
RE_TAG_LINE     = re.compile(r"(?:^|\s+)tag=(\S+) value=(\S+)")
RE_TAG_CHANGE   = re.compile(r"TAG_CHANGE Entity=(.+?) tag=(\S+) value=(\S+)")
RE_ENTITY_REF   = re.compile(r"\[.*?id=(\d+).*?\]")
RE_CARD_ID      = re.compile(r"CardID=(\S+)")
RE_PLAYER_ID    = re.compile(r"player=(\d+)")

ZONE_HAND      = "HAND"
ZONE_PLAY      = "PLAY"
ZONE_DECK      = "DECK"
ZONE_GRAVEYARD = "GRAVEYARD"
ZONE_SECRET    = "SECRET"
ZONE_SETASIDE  = "SETASIDE"


@dataclass
class CardEntity:
    eid: str
    card_id: str = ""
    tags: dict = field(default_factory=dict)

    @property
    def zone(self) -> str:       return self.tags.get("ZONE", "")
    @property
    def controller(self) -> str: return self.tags.get("CONTROLLER", "")
    @property
    def zone_pos(self) -> int:
        try: return int(self.tags.get("ZONE_POSITION", "0"))
        except: return 0
    @property
    def cost_tag(self) -> Optional[int]:
        v = self.tags.get("COST")
        try: return int(v) if v else None
        except: return None
    @property
    def atk(self) -> int:
        try: return int(self.tags.get("ATK", "0"))
        except: return 0
    @property
    def health(self) -> int:
        try:
            h = int(self.tags.get("HEALTH", "0"))
            d = int(self.tags.get("DAMAGE", "0"))
            return h - d
        except: return 0
    @property
    def exhausted(self) -> bool:
        return self.tags.get("EXHAUSTED", "0") == "1"
    @property
    def divine_shield(self) -> bool:
        return self.tags.get("DIVINE_SHIELD", "0") == "1"
    @property
    def taunt(self) -> bool:
        return self.tags.get("TAUNT", "0") == "1"


@dataclass
class GameState:
    """目前對局的即時狀態"""
    is_active: bool = False
    local_player_id: str = ""
    opponent_player_id: str = ""
    turn: int = 0
    my_mana: int = 0
    my_max_mana: int = 0
    opp_mana: int = 0
    opp_max_mana: int = 0
    my_hero_card_id: str = ""
    opp_hero_card_id: str = ""
    my_hero_hp: int = 30
    opp_hero_hp: int = 30
    whose_turn: str = ""   # "mine" | "opp" | ""
    phase: str = ""       # "MULLIGAN" | "MAIN" | ""
    going_first: bool = False  # 先手？
    _local_player_confirmed: bool = False  # 本地玩家已確認
    _class_by_pid: dict = field(default_factory=dict)  # {pid: class}

    @property
    def my_class(self) -> str:
        return self._class_by_pid.get(self.local_player_id, "")

    @property
    def opp_class(self) -> str:
        return self._class_by_pid.get(self.opponent_player_id, "")

    def mana_remaining(self) -> int:
        return max(0, self.my_mana - 0)   # RESOURCES_USED subtracted separately

    def hand(self, entities: dict) -> list:
        return sorted(
            [e for e in entities.values()
             if e.controller == self.local_player_id and e.zone == ZONE_HAND and e.card_id],
            key=lambda e: e.zone_pos
        )

    def my_board(self, entities: dict) -> list:
        return sorted(
            [e for e in entities.values()
             if e.controller == self.local_player_id and e.zone == ZONE_PLAY
             and e.tags.get("CARDTYPE") == "MINION"],
            key=lambda e: e.zone_pos
        )

    def opp_board(self, entities: dict) -> list:
        return sorted(
            [e for e in entities.values()
             if e.controller == self.opponent_player_id and e.zone == ZONE_PLAY
             and e.tags.get("CARDTYPE") == "MINION"],
            key=lambda e: e.zone_pos
        )

    def my_secrets(self, entities: dict) -> list:
        return [e for e in entities.values()
                if e.controller == self.local_player_id and e.zone == ZONE_SECRET and e.card_id]

    def opp_secrets(self, entities: dict) -> list:
        return [e for e in entities.values()
                if e.controller == self.opponent_player_id and e.zone == ZONE_SECRET and e.card_id]


class HSGameParser:
    def __init__(self):
        self.state = GameState()
        self.entities: dict[str, CardEntity] = {}
        self._parsing_eid = ""
        self._name_to_eid: dict[str, str] = {}
        self._player_ids: list[str] = []
        self._pending_local_choice_id: str = ""

    def reset(self):
        self.state = GameState(is_active=True)
        self.entities = {}
        self._parsing_eid = ""
        self._name_to_eid = {}
        self._player_ids: list[str] = []
        self._pending_local_choice_id: str = ""

    def process_lines(self, lines: list[str]):
        for line in lines:
            self._process_line(line)

    def _process_line(self, line: str):
        # ── EntityChoices：必須在 marker filter 前處理（不含 DebugPrintPower） ──
        if "DebugPrintEntityChoices" in line:
            if "ChoiceType=MULLIGAN" in line:
                if "Player=UNKNOWN HUMAN PLAYER" not in line:
                    # 找 id=X 記下來，等後面 Entities 行給出 player=X
                    cid_m = re.search(r"\bid=(\d+)\b", line)
                    if cid_m:
                        self._pending_local_choice_id = cid_m.group(1)
            elif self._pending_local_choice_id and "player=" in line:
                pid_m = re.search(r"\bplayer=(\d+)\b", line)
                if pid_m:
                    pid = pid_m.group(1)
                    if pid and pid != "0" and not self.state._local_player_confirmed:
                        self.state.local_player_id = pid
                        for other in self._player_ids:
                            if other != pid:
                                self.state.opponent_player_id = other
                                break
                        self.state._local_player_confirmed = True
                        self._pending_local_choice_id = ""
            return

        # 接受 GameState 或 PowerTaskList 兩種格式
        for marker_key in ("GameState.DebugPrintPower() - ",
                           "PowerTaskList.DebugPrintPower() - "):
            idx = line.find(marker_key)
            if idx >= 0:
                content = line[idx + len(marker_key):].strip()
                break
        else:
            return
        if not content:
            return

        # 新對局
        if RE_CREATE_GAME.search(content):
            self.reset()
            return

        if not self.state.is_active:
            return

        # Player entity
        m = RE_PLAYER_ENT.search(content)
        if m:
            eid, pid, hi, lo = m.group(1), m.group(2), m.group(3), m.group(4)
            self._parsing_eid = eid
            if eid not in self.entities:
                self.entities[eid] = CardEntity(eid=eid)
            self.entities[eid].tags["PLAYER_ID"] = pid
            # 記錄 player id 出現順序
            if pid not in self._player_ids:
                self._player_ids.append(pid)
            # 初始偵測：lo 非 0 的先當本地玩家，之後 _fix_local_player 會修正
            if lo != "0" and not self.state.local_player_id:
                self.state.local_player_id = pid
            return

        # FULL/SHOW/CHANGE ENTITY
        if any(k in content for k in ("FULL_ENTITY", "SHOW_ENTITY", "CHANGE_ENTITY")):
            self._handle_entity(content)
            return

        # 縮排 tag=
        if "tag=" in content and "TAG_CHANGE" not in content:
            mt = RE_TAG_LINE.search(content)
            if mt and self._parsing_eid:
                self._set_tag(self._parsing_eid, mt.group(1), mt.group(2))
            return

        # TAG_CHANGE
        m = RE_TAG_CHANGE.search(content)
        if m:
            self._handle_tag_change(m.group(1).strip(), m.group(2), m.group(3))

    def _handle_entity(self, content: str):
        bracket_m = RE_ENTITY_REF.search(content)
        card_m    = RE_CARD_ID.search(content)
        if bracket_m:
            eid     = bracket_m.group(1)
            card_id = card_m.group(1) if card_m else ""
            p_m = RE_PLAYER_ID.search(content)
            if p_m:
                self._set_tag(eid, "CONTROLLER", p_m.group(1))
            name_m = re.search(r"\[entityName=([^\] ]+)", content)
            if name_m:
                self._name_to_eid[name_m.group(1)] = eid
        else:
            id_m    = re.search(r"(?:ID|id)=(\d+)", content)
            card_m2 = RE_CARD_ID.search(content)
            if not id_m:
                return
            eid     = id_m.group(1)
            card_id = card_m2.group(1) if card_m2 else ""

        if not eid:
            return
        self._parsing_eid = eid
        if eid not in self.entities:
            self.entities[eid] = CardEntity(eid=eid)
        if card_id and card_id not in ("0", ""):
            self.entities[eid].card_id = card_id

        # ── 早期本地玩家偵測：第一張在 HAND zone 有 card_id 的牌，其 controller 就是本地玩家 ──
        # 只在還沒確定本地玩家時做這個判斷
        if (not self.state._local_player_confirmed
                and card_id and card_id not in ("0", "")):
            zone_m = re.search(r"\bzone=(\w+)\b", content)
            ctrl_m = re.search(r"\bplayer=(\d+)\b", content)
            if zone_m and zone_m.group(1) == ZONE_HAND and ctrl_m:
                pid = ctrl_m.group(1)
                if pid and pid != "0":
                    self.state.local_player_id = pid
                    # 對手是另一個 pid
                    for other in self._player_ids:
                        if other != pid:
                            self.state.opponent_player_id = other
                    self.state._local_player_confirmed = True

    def _set_tag(self, eid: str, tag: str, value: str):
        if eid not in self.entities:
            self.entities[eid] = CardEntity(eid=eid)
        self.entities[eid].tags[tag] = value

        # 偵測對手 player（第2個 player）
        if tag == "PLAYER_ID" and value and value != self.state.local_player_id:
            if not self.state.opponent_player_id and value != "0":
                self.state.opponent_player_id = value

        # 回合
        if tag == "TURN":
            try: self.state.turn = int(value)
            except: pass

        # 法力水晶（本地玩家）
        if tag == "RESOURCES":
            ent = self.entities.get(eid)
            if ent and ent.tags.get("PLAYER_ID") == self.state.local_player_id:
                try: self.state.my_max_mana = int(value)
                except: pass
        if tag == "RESOURCES_USED":
            ent = self.entities.get(eid)
            if ent and ent.tags.get("PLAYER_ID") == self.state.local_player_id:
                try:
                    used = int(value)
                    self.state.my_mana = max(0, self.state.my_max_mana - used)
                except: pass
        if tag == "TEMP_RESOURCES":
            ent = self.entities.get(eid)
            if ent and ent.tags.get("PLAYER_ID") == self.state.local_player_id:
                try: self.state.my_mana = self.state.my_max_mana + int(value)
                except: pass

        # 對手法力水晶
        if tag == "RESOURCES":
            ent = self.entities.get(eid)
            if ent and ent.tags.get("PLAYER_ID") == self.state.opponent_player_id:
                try: self.state.opp_max_mana = int(value)
                except: pass

        # 英雄血量 & 職業偵測
        if tag in ("HEALTH", "CARDTYPE", "CLASS"):
            ent = self.entities.get(eid)
            if ent:
                if tag == "HEALTH" and ent.tags.get("CARDTYPE") == "HERO":
                    pid = ent.tags.get("PLAYER_ID") or ent.controller
                    dmg = int(ent.tags.get("DAMAGE", "0")) if ent.tags.get("DAMAGE") else 0
                    try: hp_val = int(value) - dmg
                    except: hp_val = 0
                    if pid == self.state.local_player_id:
                        self.state.my_hero_hp = hp_val
                    elif pid == self.state.opponent_player_id:
                        self.state.opp_hero_hp = hp_val
                if tag == "CLASS" and value not in ("", "INVALID"):
                    # 只從 HERO 實體取職業，避免手牌職業牌覆蓋
                    if ent.tags.get("CARDTYPE") == "HERO":
                        pid = ent.tags.get("PLAYER_ID") or ent.controller
                        if pid:
                            self.state._class_by_pid[pid] = value

        # 輪到誰（方法1：CURRENT_PLAYER tag 改為 1 的玩家在行動）
        if tag == "CURRENT_PLAYER" and value == "1":
            ent = self.entities.get(eid)
            if ent:
                acting_pid = ent.tags.get("PLAYER_ID") or ent.controller
                if acting_pid == self.state.local_player_id:
                    self.state.whose_turn = "mine"
                elif acting_pid and acting_pid != "0":
                    self.state.whose_turn = "opp"

        # 輪到誰（方法2：STEP MAIN_ACTION 也可偵測）
        if tag == "STEP" and value == "MAIN_ACTION":
            ent = self.entities.get(eid)
            if ent:
                acting_pid = ent.tags.get("PLAYER_ID") or ent.controller
                if acting_pid == self.state.local_player_id:
                    self.state.whose_turn = "mine"
                elif acting_pid and acting_pid != "0":
                    self.state.whose_turn = "opp"

        # 換牌/遊戲階段偵測
        if tag == "STEP":
            if value == "BEGIN_MULLIGAN":
                self.state.phase = "MULLIGAN"
            elif value in ("MAIN_READY", "MAIN_ACTION", "MAIN_START_TRIGGERS"):
                if self.state.phase == "MULLIGAN":
                    self.state.phase = "MAIN"

        # 先手偵測（回合1時我方的 FIRST_PLAYER 為1）
        if tag == "FIRST_PLAYER" and value == "1":
            ent = self.entities.get(eid)
            if ent:
                pid = ent.tags.get("PLAYER_ID") or ent.controller
                self.state.going_first = (pid == self.state.local_player_id)

    def _handle_tag_change(self, entity: str, tag: str, value: str):
        eid = self._resolve_eid(entity)
        if eid:
            self._set_tag(eid, tag, value)

    def _resolve_eid(self, entity: str) -> Optional[str]:
        if entity.isdigit():
            return entity
        m = RE_ENTITY_REF.search(entity)
        if m:
            return m.group(1)
        # 固定名稱映射
        if entity in ("GameEntity",):
            return self._name_to_eid.get("GameEntity", "1")
        return self._name_to_eid.get(entity)
