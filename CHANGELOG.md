# Changelog

## 2026-06-09 — Admin page + auto GitHub push

### 新功能
- **`/admin?token=xxx` 管理後台頁面**（`web/templates/admin.html`）
  - 🔄 更新排庫：呼叫 `/api/update-cards`，顯示手下/法術/英雄/飾品數量及 git push 結果
  - 🕷️ 抓取 Firestone：呼叫 `/api/scrape-comps`
  - 在 Render 設定 `ADMIN_TOKEN` 環境變數可自訂 token
  - 公開網站 `PUBLIC_MODE=1` 下不顯示管理按鈕，改用此頁面操作

- **`/api/update-cards` 執行後自動 commit + push 到 GitHub**
  - 使用 GitHub Contents REST API（`urllib`），不依賴 Render 上沒有的 `git` CLI
  - 若 `GITHUB_PAT` 已設定且資料有變動，會逐一比對並 PUT 更新
  - 結果回傳在 JSON 的 `git` 欄位（`pushed`, `files`, `skipped`）

### 修正
- **`[Errno 2] No such file or directory: 'curl'`**：`api_update_cards` 改用 `urllib.request.urlopen` 下載卡牌 JSON，不再呼叫系統 `curl`
- **`[Errno 2] No such file or directory: 'git'`**：`_git_push_data()` 完全改用 GitHub REST API，不再呼叫系統 `git`
- `_git_push_data()` 呼叫包在 `try/except`，git 錯誤不會造成 `/api/update-cards` 回傳 500

### 環境變數（需在 Render 設定）

| 變數 | 說明 |
|------|------|
| `GITHUB_PAT` | GitHub Personal Access Token（`repo` 權限），更新排庫後自動 push |
| `ADMIN_TOKEN` | `/admin?token=xxx` 頁面的存取 token，未設定則 403 |

### 待辦（手動）
- [ ] 撤銷舊 PAT（已洩漏）：https://github.com/settings/tokens
- [ ] 在 Render 設定 `ADMIN_TOKEN` 環境變數

---

## 更早的更新

詳見 git log。
