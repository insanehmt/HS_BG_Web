# 雲端部署指南（Render.com）

## 整體步驟概覽
```
Step 1: 安裝 Git → Step 2: 建立 GitHub repo → Step 3: 上傳程式碼
→ Step 4: 設定 Render → Step 5: 設定本地推送設定
```

---

## Step 1：安裝 Git for Windows

1. 前往 https://git-scm.com/download/win
2. 下載並安裝（全部按 Next，預設即可）
3. 安裝完後開新的 PowerShell/命令提示字元確認：
   ```
   git --version
   ```

---

## Step 2：建立 GitHub 帳號與 Repo

1. 前往 https://github.com → 用 Google 帳號登入或註冊
2. 點右上角 **+** → **New repository**
3. Repository name: `hs-battlegrounds`（或任意名稱）
4. 選 **Private**（私人，朋友看不到原始碼）
5. 點 **Create repository**

---

## Step 3：上傳程式碼到 GitHub

在 `F:\GitHub_Copilot\HS_BattleGrounds` 資料夾開 PowerShell，執行：

```powershell
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/你的帳號/hs-battlegrounds.git
git push -u origin main
```

> 第一次 push 會彈出 GitHub 登入視窗，用瀏覽器授權即可。

---

## Step 4：部署到 Render.com（免費）

1. 前往 https://render.com → **Sign in with Google**
2. 點 **New +** → **Web Service**
3. 選 **Connect a repository** → 授權 GitHub → 選 `hs-battlegrounds`
4. 設定：
   | 欄位 | 值 |
   |------|----|
   | Name | hs-battlegrounds |
   | Runtime | **Docker** |
   | Branch | main |
   | Instance Type | **Free** |

5. 展開 **Environment Variables**，新增：
   | Key | Value |
   |-----|-------|
   | `PUBLIC_MODE` | `1` |
   | `SYNC_TOKEN` | 自訂一個密碼，例如 `MySecret2025` |

6. 點 **Create Web Service**
7. 等待約 5-10 分鐘部署完成（首次會下載 Docker 映像）
8. 完成後取得網址，例如：`https://hs-battlegrounds.onrender.com`

> ⚠️ **免費方案限制**：15 分鐘無人使用會休眠，有人開網頁時約等 30 秒喚醒，完全夠用。

---

## Step 5：設定本地推送

複製設定範本：
```powershell
Copy-Item .push_config.example .push_config
```

用記事本打開 `.push_config`，填入：
```
WEB_URL=https://hs-battlegrounds.onrender.com
SYNC_TOKEN=MySecret2025
```

測試推送：
```powershell
python scripts/push_to_web.py
```

---

## 日常使用流程

### 更新組合資料（最常用）
```powershell
# 方法 A：快速推送（當次有效，Render 15 分鐘休眠重啟後資料重置）
python scripts/push_to_web.py

# 方法 B：推送 + 永久保存（推薦，觸發 Render 自動重新部署）
python scripts/push_to_web.py --commit
```

### 換版本後更新所有資料（手下/法術/飾品/英雄）
```powershell
python scripts/push_to_web.py --all --commit
```

### 爬蟲 + 推送一步完成
```powershell
# 需先啟動本地 Flask（python web/app.py）
python scripts/update_and_push.py
```

---

## 更新程式碼（修了 Bug 後重新部署）

```powershell
git add .
git commit -m "更新說明"
git push
```

Render 偵測到 push 後會自動重新部署（約 3-5 分鐘）。

---

## 常見問題

**Q: Render 需要信用卡嗎？**
A: 免費方案不需要，直接用 Google 登入即可。

**Q: 朋友怎麼開？**
A: 把 `https://hs-battlegrounds.onrender.com` 網址給他們，用瀏覽器直接開，不用安裝任何東西。

**Q: 推送後資料會消失嗎？**
A: Render 免費方案 **無持久磁碟**，15 分鐘休眠後重啟資料會重置。解決方法：
- 用 `push_to_web.py --commit` → git push → Render 重新部署，資料永久包進映像檔
- 或升級 Render 付費方案（$7/月）加持久磁碟

**Q: SYNC_TOKEN 忘記了？**
A: 去 Render Dashboard → 你的服務 → Environment → 查看或修改 SYNC_TOKEN，`.push_config` 同步更新即可。
