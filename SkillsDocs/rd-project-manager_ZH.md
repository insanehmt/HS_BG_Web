# 📋 rd-project-manager — 使用者指南（繁體中文）

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

**rd-project-manager** 是安裝在此環境中的 GitHub Copilot CLI skill。

R&D project management skill. Manages SPEC, IssueList, ReleaseNote, and bilingual UserGuides for a software project. Triggered when user says 'fix issue', 'update spec', 'add feature', 'new release', 'update docs', or uses /rdpm command. Automatically updates all related documents after every code or spec change.

---

## 2. 觸發關鍵詞

| 觸發詞 | 動作 |
|--------|------|
| `fix issue ISS-XXX` | 啟動此 Skill |
| `fix it` | 啟動此 Skill |
| `update spec` | 啟動此 Skill |
| `add feature F-XX` | 啟動此 Skill |
| `new release` | 啟動此 Skill |
| `release v1.2.3` | 啟動此 Skill |
| `update docs` | 啟動此 Skill |
| `sync docs` | 啟動此 Skill |
| `export spec` | 啟動此 Skill |
| `generate word` | 啟動此 Skill |
| `/rdpm export-spec` | 啟動此 Skill |
| `/rdpm status` | 啟動此 Skill |
| `/rdpm init <path> <ProjectName>` | 啟動此 Skill |

---

## 3. 如何使用

在對話中輸入上方任一觸發詞，Agent 就會自動執行對應的工作流程。

所有輸出檔案會儲存到設定的輸出目錄，不需要特別的安裝設定。

---

## 4. Skill 檔案位置

```
C:\Users\User\.copilot\skills\rd-project-manager\
├── make_spec_docx.py    ← 輔助腳本
├── SKILL.md             ← Skill 定義與規則
```

---

## 5. 常見問題

**Q：如何安裝這個 Skill？**
A：將 `SKILL.md` 放到 `C:\Users\User\.copilot\skills\rd-project-manager\` 即可。下次啟動 Agent session 時會自動載入。

**Q：如何更新 Skill？**
A：直接編輯 `SKILL.md`，下次 Agent session 啟動時生效。

---

*GitHub Copilot CLI Skill · rd-project-manager · v1.0*
