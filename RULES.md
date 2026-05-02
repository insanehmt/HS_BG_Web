# 爐石傳說：酒館戰棋 紀錄規則

## 遊戲模式

### 單打模式（Solo）
- **人數**：8 人
- **組隊**：每人單獨參賽（1人1隊）
- **排名**：第 1 名 ～ 第 8 名
- **特殊**：無飾品系統（部分賽季有）

### 雙打模式（Duo）
- **人數**：8 人，分 4 隊
- **組隊**：2 人為一組（共 4 隊）
- **排名**：第 1 名 ～ 第 4 名（以隊伍為單位）
- **隊友識別**：與本地玩家擁有相同 `BACON_DUO_TEAM_ID` 的玩家

---

## 紀錄欄位規則

### 本地玩家（自己）
| 欄位 | 說明 |
|------|------|
| 英雄 | 從 `DebugPrintEntitiesChosen` MULLIGAN 選擇偵測 |
| 技能 | `CARDTYPE=HERO_POWER` + `ZONE=PLAY` + `CONTROLLER=local` |
| 飾品1 / 飾品2 | 從 `DebugPrintEntitiesChosen` `MagicItem` 選擇偵測（最多 2 個）|
| 名次 | `PLAYER_LEADERBOARD_PLACE` tag |
| 最終排組 | `STEP=MAIN_COMBAT` 時拍板面快照（戰鬥前） |
| 回合數 | 最大 `TURN` 值 |
| 最高金幣 | 最大 `RESOURCES` 值 |
| 對局時長 | 遊戲結束時間 − 開始時間 |

### 雙打模式 額外欄位
| 欄位 | 說明 |
|------|------|
| 隊友英雄 | 與本地玩家同 `BACON_DUO_TEAM_ID`、且 `CONTROLLER != local` 的英雄 |

### 對手
| 欄位 | 說明 |
|------|------|
| 對手英雄 | 所有非本地玩家、非隊友的英雄 card_id |
| 對手排組 | 遊戲結束時仍在 `ZONE=PLAY` 的對手隨從 |

---

## 強力排組紀錄規則

- **單打第 1 名** → 寫入「強力排組（單打）」分頁
- **雙打第 1 名** → 寫入「強力排組（雙打）」分頁

---

## Log 解析規則

### BG 模式偵測
- `BACON_BARTENDER_CARD_ID` 或 `BACON_TRINKETS_ACTIVE` tag 出現 → 為酒館戰棋對局

### 雙打模式偵測
- `BACON_DUO_TEAM_ID` 或 `BACON_DUOS_PUNISH_LEAVERS` tag 出現且值非 0 → 為雙打模式

### 本地玩家偵測
- `Player EntityID=X PlayerID=Y GameAccountId=[hi=... lo=N]`，其中 `lo != 0` 為本地玩家

### 隊友偵測（雙打）
- 本地 Player 實體的 `BACON_DUO_TEAM_ID` 值 = 本地隊伍編號
- 找到 `CARDTYPE=HERO`、`BACON_DUO_TEAM_ID` == 本地隊伍編號、`CONTROLLER != local_player_id` 的英雄 = 隊友英雄

---

## Excel 輸出格式

### 分頁結構
| 分頁名稱 | 內容 |
|----------|------|
| 單打紀錄 | 所有單打對局 |
| 雙打紀錄 | 所有雙打對局 |
| 強力排組（單打）| 單打第 1 名排組 |
| 強力排組（雙打）| 雙打第 1 名排組 |

### 欄位順序（雙打含隊友欄）
`日期時間` / `版本` / `模式` / `英雄` / `隊友英雄` / `技能1` / `技能2` / `飾品1` / `飾品2` / `名次` / `最終排組` / `回合數` / `最高金幣` / `對局時長` / `對手英雄` / `對手排組` / `備註`

> 單打無「隊友英雄」欄（或該欄留空）

---

## 資料儲存

- **SQLite**：`data/records.db`（來源資料，防重複寫入）
- **Excel**：`output/hs_bg_records.xlsx`
- **重建 Excel**：執行 `python regen_excel.py`
