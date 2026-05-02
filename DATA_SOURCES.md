# HS BG Tracker — 資料來源說明

## 第一參考資料：HearthstoneJSON

**官網：** https://hearthstonejson.com  
**API：** https://api.hearthstonejson.com/v1/latest/zhTW/cards.json  
**圖片 CDN：** https://art.hearthstonejson.com/v1/256x/{CARD_ID}.jpg

### 說明
HearthstoneJSON 是由社群維護的專案，資料直接從遊戲客戶端解析，每次遊戲版本更新後會自動同步。

### 使用方式
- 提供繁體中文（zhTW）卡牌名稱、說明文字、屬性
- 涵蓋所有卡牌類型：英雄、英雄技能、手下、法術、飾品、夥伴
- 本地快取檔案：
  - `data/hs_cards_full.json` — 完整卡牌資料（以 card_id 為 key 的 dict）
  - `data/bg_minions_cache.json` — BG 手下快取
  - `data/bg_spells_cache.json` — BG 法術快取
  - `data/bg_trinkets_cache.json` — BG 飾品快取

### 卡牌 ID 規則
| 類型 | 格式 | 範例 |
|------|------|------|
| 英雄 | `BG{XX}_HERO_{NNN}` | `BG20_HERO_100` |
| 英雄技能 | `{HERO_ID}p` | `BG20_HERO_100p` |
| 英雄夥伴 | `{HERO_ID}_Buddy` | `BG20_HERO_100_Buddy` |
| 閃光夥伴 | `{HERO_ID}_Buddy_G` | `BG20_HERO_100_Buddy_G` |
| 手下 | `BG{XX}_{NNN}` | `BG26_805` |
| 閃光手下 | `{CARD_ID}_G` | `BG26_805_G` |

### 更新腳本
- `scripts/fetch_bg_spells.py` — 更新法術快取
- `update_boards.py` — 更新看板資料

---

## 第二參考資料：Hearthstone Wiki (hearthstone.wiki.gg)

**網址：** https://hearthstone.wiki.gg  
**BG 英雄頁：** https://hearthstone.wiki.gg/wiki/Battlegrounds/Heroes  
**BG 卡圖分類：** https://hearthstone.wiki.gg/wiki/Category:Battlegrounds_card_images  
**參考工具：** https://www.firestoneapp.com/battlegrounds/heroes

### 說明
Hearthstone Wiki 是社群維護的 wiki，提供更豐富的背景說明、策略資訊、官方卡圖。作為第二參考資料，用於補充 HearthstoneJSON 沒有的資訊（如英雄夥伴適合種族、組合策略建議等）。

### 使用場景
- 當 HearthstoneJSON 缺少某張卡牌或資料不完整時，以 wiki 內容補充
- 英雄適合種族（`data/hero_meta.json`）由 wiki 資料推導而來
- 組合策略文字參考自社群資料（Firestone / HSReplay 匯入）

### 圖片備援
若 HearthstoneJSON CDN 圖片載入失敗，可改用 wiki 圖片：
```
https://hearthstone.wiki.gg/wiki/Special:FilePath/{Card_Name}.png
```
> 注意：wiki 圖片以卡名命名，非 card_id，需額外對應。

---

## 資料流程

```
HearthstoneJSON API
        │
        ▼
  下載 cards.json (zh-TW)
        │
        ├──► data/hs_cards_full.json   (完整資料，供 /api/hero-guide 等使用)
        ├──► data/bg_minions_cache.json (手下圖鑑)
        ├──► data/bg_spells_cache.json  (法術圖鑑)
        └──► data/bg_trinkets_cache.json (飾品圖鑑)

hearthstone.wiki.gg (手動參考)
        │
        └──► data/hero_meta.json        (英雄適合種族，人工整理)
```
