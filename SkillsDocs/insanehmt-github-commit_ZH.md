# 🚀 insanehmt-github-commit — 使用者指南（繁體中文）

> **Skill 版本：** 1.0  |  **最後更新：** 2026-06-04

---

## 目錄

1. [這個 Skill 是什麼？](#1-這個-skill-是什麼)
2. [觸發關鍵詞](#2-觸發關鍵詞)
3. [如何使用](#3-如何使用)
4. [Skill 檔案位置](#4-skill-檔案位置)
5. [常見問題](#5-常見問題)

---

## 1. 這個 Skill 是什麼？

**insanehmt-github-commit** 是安裝在此環境中的 GitHub Copilot CLI skill。

Push code to GitHub account insanehmt via API token. Triggered when user says 'push to github', 'git push', 'commit and push', 'push code', or 'upload to github'.

---

## 2. 觸發關鍵詞

| 觸發詞 | 動作 |
|--------|------|
| `push to github` | 啟動此 Skill |
| `git push` | 啟動此 Skill |
| `commit and push` | 啟動此 Skill |
| `push code` | 啟動此 Skill |
| `upload to github` | 啟動此 Skill |
| `create repo` | 啟動此 Skill |
| `new github repo` | 啟動此 Skill |
| `set token` | 啟動此 Skill |
| `update token` | 啟動此 Skill |
| `configure token` | 啟動此 Skill |

---

## 3. 如何使用

在對話中輸入上方任一觸發詞，Agent 就會自動執行對應的工作流程。

所有輸出檔案會儲存到設定的輸出目錄，不需要特別的安裝設定。

---

## 4. Skill 檔案位置

```
C:\Users\User\.copilot\skills\insanehmt-github-commit\
├── config.json          ← 輔助腳本
├── github_commit.py     ← 輔助腳本
├── SKILL.md             ← Skill 定義與規則
```

---

## 5. 常見問題

**Q：如何安裝這個 Skill？**
A：將 `SKILL.md` 放到 `C:\Users\User\.copilot\skills\insanehmt-github-commit\` 即可。下次啟動 Agent session 時會自動載入。

**Q：如何更新 Skill？**
A：直接編輯 `SKILL.md`，下次 Agent session 啟動時生效。

---

*GitHub Copilot CLI Skill · insanehmt-github-commit · v1.0*
