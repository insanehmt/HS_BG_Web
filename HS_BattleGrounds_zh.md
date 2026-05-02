# HS_BattleGrounds 專案說明文件

> **爐石傳說：戰場**個人紀錄追蹤 + 圖鑑網站  
> 本地完整版 + 雲端公開版（Render.com）

---

## 目錄

1. [專案架構](#專案架構)
2. [快速啟動](#快速啟動)
3. [主程式（對局追蹤）](#主程式對局追蹤)
4. [Web 伺服器（網頁介面）](#web-伺服器網頁介面)
5. [網頁功能頁面](#網頁功能頁面)
6. [API 端點](#api-端點)
7. [爬蟲工具](#爬蟲工具)
8. [維護腳本](#維護腳本)
9. [打牌顧問（標準模式）](#打牌顧問標準模式)
10. [雲端部署](#雲端部署)
11. [資料檔案](#資料檔案)
12. [環境設定](#環境設定)

---

## 專案架構

```
HS_BattleGrounds/
├── main.py                  # 主程式：監控 Power.log，追蹤戰場對局
├── log_parser.py            # Power.log 解析器
├── log_config.py            # 爐石路徑設定
├── db.py                    # SQLite 資料庫操作
├── card_db.py               # 卡牌資料庫
├── excel_writer.py          # Excel 匯出
├── strategy_viewer.py       # 牌型策略查詢（命令列）
├── update_boards.py         # 板面數據更新工具
├── run_advisor.py           # 打牌顧問啟動器
├── regen_excel.py           # 重新產生 Excel 報表
│
├── web/
│   ├── app.py               # Flask 後端（所有 API + 頁面）
│   ├── templates/           # Jinja2 HTML 頁面
│   └── uploads/             # 上傳的 Excel 檔案暫存
│
├── scripts/                 # 維護/爬蟲腳本
├── hs_advisor/              # 標準對戰打牌顧問模組
├── data/                    # 所有資料檔案（JSON + SQLite）
│
├── Dockerfile               # 雲端部署用映像檔
├── docker-compose.yml       # 本地公開模式測試
├── render.yaml              # Render.com 部署設定
├── .push_config             # 本地推送設定（私人，不進 Git）
│
├── start_web.bat            # 啟動本地完整版
├── start_public.bat         # 啟動本地公開模式（Docker）
└── 打牌顧問.bat              # 啟動標準對戰顧問
```

---

## 快速啟動

| 需求 | 指令 / 方式 |
|------|------------|
| 啟動本地網站 | 雙擊 `start_web.bat` 或 `python web/app.py` |
| 啟動對局追蹤 | `python main.py` |
| 啟動打牌顧問 | 雙擊 `打牌顧問.bat` 或 `python run_advisor.py` |
| 推送資料到雲端 | `python scripts/push_to_web.py` |
| 永久更新雲端 | `python scripts/push_to_web.py --commit` |

---

## 主程式（對局追蹤）

### `main.py` — 戰場對局監控主程式

**功能：** 在背景持續監控 Hearthstone 的 `Power.log`，自動解析並儲存每場戰場對局。

**監控內容：**
- 使用英雄 + 英雄技能
- 選取的兩個飾品
- 最終板面（隨從名稱、攻擊力、血量、護甲、黃金標記）
- 最終名次、回合數、最高金幣、對局時長
- 所有對手英雄列表
- 遊戲模式（單打 Solo / 雙打 Duo）

**啟動：**
```bash
python main.py
# 或
start_web.bat（同時啟動網站）
```

**輸出：**
- 儲存到 `data/records.db`（SQLite）
- 匯出到 `output/hs_bg_records.xlsx`（Excel）

---

### `log_parser.py` — Power.log 解析器

解析 Hearthstone 原始日誌，重建遊戲實體狀態，提取完整對局資料。

**解析的遊戲事件：**
- `CREATE_GAME` / `FULL_ENTITY` / `SHOW_ENTITY`：建立實體
- `TAG_CHANGE`：追蹤血量、攻擊力、名次、遊戲狀態
- `PlayerID`：識別英雄與玩家
- 飾品（`BATTLEGROUND_TRINKET`）：追蹤選取事件

---

### `log_config.py` — 爐石路徑設定

自動偵測 Hearthstone 安裝路徑：
- `D:\BZGame\Hearthstone`（BZGame 版）
- `C:\Program Files (x86)\Hearthstone`（Battle.net 版）
- `%LOCALAPPDATA%\Blizzard\Hearthstone`

---

### `db.py` — SQLite 資料庫

**資料表：** `games`  
**欄位：** 英雄、名次、回合數、金幣、模式、板面、飾品、對手、時間戳...

**主要函式：**
- `init_db()` — 建立資料表
- `save_game(record)` — 儲存對局
- `get_stats()` — 統計總覽
- `start_time_exists(ts)` — 防止重複記錄

---

### `excel_writer.py` — Excel 報表匯出

將 SQLite 資料以結構化表格匯出為 `.xlsx`。每場對局一行，包含英雄、板面組成、名次等欄位。

---

## Web 伺服器（網頁介面）

### `web/app.py` — Flask 後端主程式

**技術：** Flask + SQLite + Alpine.js + Tailwind CSS

**模式：**
- **本地完整版**（`PUBLIC_MODE=0`，預設）：含上傳、紀錄、爬蟲所有功能
- **雲端公開版**（`PUBLIC_MODE=1`）：只顯示 5 個圖鑑頁面，隱藏私人資料

---

## 網頁功能頁面

### 🏠 紀錄總覽 `/`（本地限定）
個人戰場對局統計：
- 勝率、平均名次、前4率
- 英雄使用分布
- 對局列表（可篩選模式/名次）
- 上傳 Excel 匯入紀錄

### 📊 當季最強 `/tier-list`
- 40+ 個組合（Tier S/A/B/C）
- 核心卡牌 + 附加卡牌圖示
- 難度、策略說明
- 可編輯（新增/修改組合）
- 爬蟲按鈕：自動抓取 Firestone + HSReplay 資料

### 🐾 手下圖鑑 `/minions`
- 所有戰場手下按族群/費用/攻血篩選
- 顯示技能描述、黃金版本效果
- 搜尋功能

### ✨ 法術圖鑑 `/spells`
- 所有戰場法術
- 費用、效果、族群標籤篩選

### 💎 飾品圖鑑 `/trinkets`
- 所有戰場飾品
- 品質（普通/稀有/史詩）篩選

### 🦸 英雄圖鑑 `/hero-guide`
- 英雄技能說明
- 適合族群/流派標記

### 📈 英雄排名 `/heroes`（本地限定）
- 個人英雄勝率統計（從本地 records.db 讀取）
- 按平均名次/勝率/場數排序

---

## API 端點

### 對局紀錄
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/games` | GET | 取得對局列表，支援篩選/分頁 |
| `/api/games/stats` | GET | 統計總覽（場數/勝率/均名） |
| `/api/upload` | POST | 上傳 Excel 匯入對局紀錄 |

### 圖鑑資料
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/minions` | GET | 取得所有戰場手下 |
| `/api/spells` | GET | 取得所有戰場法術 |
| `/api/trinkets` | GET | 取得所有戰場飾品 |
| `/api/heroes` | GET | 取得英雄排名統計 |
| `/api/hero-guide` | GET | 取得英雄圖鑑資料 |
| `/api/cards` | GET | 搜尋卡牌（支援關鍵字/類型篩選） |

### 組合管理
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/tier-list` | GET | 取得所有組合（含標記已輪調） |
| `/api/tier-list` | POST | 新增組合 |
| `/api/tier-list/<id>` | PUT | 修改組合 |
| `/api/tier-list/<id>` | DELETE | 刪除組合 |

### 爬蟲
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/scrape-comps` | POST | Playwright 爬取 Firestone 組合數據 |
| `/api/scrape-hsreplay` | POST | Playwright 爬取 HSReplay 組合評級 |

### 雲端同步
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/push-data` | POST | 接收本地資料推送（需 SYNC_TOKEN 認證） |

---

## 爬蟲工具

### Firestone 爬蟲（`/api/scrape-comps`）

**來源：** https://www.firestoneapp.com/battlegrounds/comps

**技術：** Playwright（無頭 Chromium）+ 網路攔截

**抓取內容：**
- compId、powerLevel（S/A/B/C）、difficulty
- 核心卡牌（CORE）、附加選擇（ADDON/CYCLE）
- 平均名次、數據量、版本號
- 英文策略 tips

**合併規則（絕不刪除現有組合）：**
1. 直接 ID 符合 → 原地更新（名稱、策略保留使用者自訂）
2. Alias 符合（新舊 ID 對應）→ 原地更新舊 ID 的資料
3. 新 ID → 新增
4. 核心卡牌：合併（保留現有 + 追加新增），不覆蓋

**獨立腳本：** `scripts/scrape_firestone_comps.py`

---

### HSReplay 爬蟲（`/api/scrape-hsreplay`）

**來源：** https://hsreplay.net/battlegrounds/comps/

**技術：** Playwright + DOM 擷取 + 捲動觸發延遲載入

**抓取內容：**
- 組合名稱、Tier 評級（S/A/B）、難度
- 核心卡牌（從 img src 提取 Card ID）

**規則：**
- 不覆蓋 Firestone 的 Tier（Firestone 優先）
- 卡牌只合併，不取代
- 透過 `HSREPLAY_NAME_TO_ID` 名稱對應表匹配現有組合

**測試腳本：** `scripts/test_hsreplay_final.py`

---

### `scripts/push_to_web.py` — 資料推送工具

將本地 JSON 資料檔案推送到雲端網站。

```bash
# 推送常用資料（組合、英雄 meta）
python scripts/push_to_web.py

# 推送所有資料（含手下/法術/飾品快取）
python scripts/push_to_web.py --all

# 推送 + git commit（永久保存，觸發 Render 重新部署）
python scripts/push_to_web.py --commit
```

**設定：** 建立 `.push_config` 填入：
```
WEB_URL=https://hs-bg-web.onrender.com
SYNC_TOKEN=你的密碼
```

---

### `scripts/update_and_push.py` — 一鍵更新腳本

爬蟲 + 推送一步完成（需先啟動本地 Flask）：

```bash
python scripts/update_and_push.py             # 爬蟲 + 推送
python scripts/update_and_push.py --push-only # 只推送
python scripts/update_and_push.py --all       # 推送所有資料
```

---

## 維護腳本

| 腳本 | 用途 |
|------|------|
| `scripts/cleanup_comps.py` | 清理重複組合（合併舊→新 ID） |
| `scripts/check_comps.py` | 快速列出所有組合 ID 和 Tier |
| `scripts/add_comps.py` | 批次新增組合資料 |
| `scripts/merge_old_comps.py` | 合併舊版組合資料 |
| `scripts/rebuild_comps_firestone.py` | 從 Firestone 格式重建組合 |
| `scripts/fetch_bg_spells.py` | 抓取戰場法術資料 |
| `scripts/search_cards.py` | 搜尋卡牌 ID |
| `regen_excel.py` | 從 SQLite 重新產生 Excel 報表 |
| `update_boards.py` | 更新板面數據 |

---

## 打牌顧問（標準模式）

> ⚠️ 此模組為**標準模式**對戰輔助，非戰場模式

### 啟動方式
- 雙擊 `打牌顧問.bat`
- 或 `python run_advisor.py`

### `hs_advisor/hs_advisor.py` — 主顯示模組
即時從 Power.log 讀取遊戲狀態，顯示：
- 對手可能打的牌型（職業 + 本週 meta）
- 板面狀況（我方/對手隨從，攻/血/嘲諷/聖盾）
- 手牌列表（費用、名稱、卡文）
- 本回合建議（清場/致命優先分析）

### `hs_advisor/hs_game_state.py` — 遊戲狀態解析
即時解析 Power.log，追蹤：
- 板面隨從（PLAY 區域）
- 手牌（HAND 區域）
- 祕密（SECRET 區域）

### `hs_advisor/mulligan.py` — 換牌建議
根據起始手牌費用分布、對手職業和 meta 風格，給出「留牌」或「換牌」建議：
- 永遠留：嘲諷、戰吼、抽牌引擎
- 永遠換：組合技、高費牌（先手時）

### `hs_advisor/hsreplay_meta.py` — HSReplay Meta 整合
從 HSReplay API 取得本週各職業最強牌型，預測對手可能使用的策略。

### `hs_advisor/strategy_manager.py` — 牌型策略管理
- 讀取 `data/strategies/` 下的 JSON 策略檔
- 自動辨識牌型風格（快攻/控制/中速/法術）
- 首次執行自動建立策略模板

---

## 雲端部署

### 架構

```
本地端（你）               ←→               雲端（朋友）
──────────────────────           ──────────────────────
完整功能                           公開圖鑑
• 對局追蹤                         • 當季最強
• 上傳紀錄                         • 手下圖鑑
• 爬蟲更新                         • 法術圖鑑
• 英雄排名                         • 飾品圖鑑
                                   • 英雄圖鑑
         ↓
python scripts/push_to_web.py
```

### 相關檔案

| 檔案 | 說明 |
|------|------|
| `Dockerfile` | 輕量映像檔（Python + Flask + gunicorn，無 Playwright） |
| `docker-compose.yml` | 本地公開模式測試（port 5001） |
| `render.yaml` | Render.com 免費方案設定 |
| `requirements_web.txt` | 雲端精簡依賴（flask/gunicorn/requests/openpyxl） |
| `.push_config` | 本地推送設定（網址 + token，不進 Git） |
| `.push_config.example` | 設定範本 |
| `DEPLOY.md` | 完整部署步驟說明 |

### 環境變數（Render 設定）

| 變數 | 說明 |
|------|------|
| `PUBLIC_MODE=1` | 啟用公開模式，隱藏私人頁面 |
| `SYNC_TOKEN=xxx` | 資料推送認證 token |

---

## 資料檔案

| 檔案 | 大小 | 說明 |
|------|------|------|
| `data/bg_comps.json` | 58KB | 戰場組合資料（40+ 組合，Tier/策略/卡牌） |
| `data/bg_minions_cache.json` | 666KB | 所有戰場手下（ID/名稱/費用/攻血/效果） |
| `data/bg_spells_cache.json` | 76KB | 所有戰場法術 |
| `data/bg_trinkets_cache.json` | 68KB | 所有戰場飾品 |
| `data/bg_heroes_cache.json` | — | 英雄圖鑑資料 |
| `data/hero_meta.json` | 4KB | 英雄 meta 統計（勝率/名次/熱門程度） |
| `data/hsreplay_meta_cache.json` | 42KB | HSReplay meta 快取 |
| `data/bg_config.json` | 1KB | 版本設定（當前賽季/版本號） |
| `data/records.db` | 私人 | 個人對局紀錄 SQLite（不上傳雲端） |
| `data/hs_cards_full.json` | 5.3MB | 完整卡牌資料庫（英雄技能搜尋用） |
| `data/cards_cache.json` | 1.1MB | 卡牌快取 |
| `data/strategies/` | — | 牌型策略 JSON（各 meta 牌型一個檔） |

---

## 環境設定

### 本地安裝
```bash
pip install -r requirements.txt
playwright install chromium   # 爬蟲用
```

### requirements.txt（本地完整版）
```
flask>=3.0.0
openpyxl>=3.1.0
watchdog>=4.0.0
requests>=2.31.0
playwright>=1.44.0
```

### requirements_web.txt（雲端精簡版）
```
flask>=3.0.0
gunicorn>=21.0.0
requests>=2.31.0
openpyxl>=3.1.0
```

### Git 操作
```bash
# 提交資料更新並觸發 Render 重新部署
git add data/bg_comps.json
git commit -m "data: 更新組合資料"
git push
```
