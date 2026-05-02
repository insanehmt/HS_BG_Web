# 爐石傳說 英雄戰場 對局紀錄器

自動從 Hearthstone 的 `Power.log` 擷取英雄戰場對局資料，記錄到本地 Excel 檔案。
**第一名的排組**會另外存入「強力排組」工作表。

## 安裝

```bash
pip install -r requirements.txt
```

## 使用

1. 確認遊戲路徑在 `log_config.py` 中正確設定（預設 `D:\BZGame\Hearthstone`）
2. 啟動紀錄器：
   ```bash
   python main.py
   ```
3. 正常遊玩英雄戰場，每局結束後自動記錄

## 輸出

| 檔案 | 說明 |
|------|------|
| `output/hs_bg_records.xlsx` | Excel 紀錄檔 |
| `data/records.db` | SQLite 資料庫（防重複） |
| `data/cards_cache.json` | 卡牌名稱快取 |

## Excel 工作表

- **對局紀錄**：所有對局（含名次顏色：金/銀/銅）
- **強力排組**：僅第一名的排組

## 欄位說明

| 欄位 | 說明 |
|------|------|
| 日期時間 | 對局開始時間 |
| 英雄 | 使用的英雄名稱（繁中） |
| 名次 | 最終名次（1–8） |
| 最終排組（隨從） | 遊戲結束時在場的隨從（繁中名稱） |
| 回合數 | 遊戲回合數 |
| 備註 | 手動填寫用 |

## 更新卡牌資料庫

```bash
python card_db.py
```
