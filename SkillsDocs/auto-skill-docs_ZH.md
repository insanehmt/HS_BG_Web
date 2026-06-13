# 📝 auto-skill-docs — 使用者指南（繁體中文）

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

**auto-skill-docs** 是安裝在此環境中的 GitHub Copilot CLI skill。

Automatically generates bilingual (EN + ZH) UserGuide markdown files for all installed Copilot CLI skills whenever a skill is created or updated. Saves output to F:\GitHub_Copilot\SkillsDocs\ and updates the README index.

---

## 2. 觸發關鍵詞

| 觸發詞 | 動作 |
|--------|------|
| `new skill created` | 啟動此 Skill |
| `skill updated` | 啟動此 Skill |
| `skill modified` | 啟動此 Skill |
| `sync skill docs` | 啟動此 Skill |
| `sync all skill docs` | 啟動此 Skill |
| `update skill docs` | 啟動此 Skill |
| `/skill-doc` | 啟動此 Skill |
| `generate skill guide <name>` | 啟動此 Skill |

---

## 3. 如何使用

在對話中輸入上方任一觸發詞，Agent 就會自動執行對應的工作流程。

所有輸出檔案會儲存到設定的輸出目錄，不需要特別的安裝設定。

---

## 4. Skill 檔案位置

```
C:\Users\User\.copilot\skills\auto-skill-docs\
├── generate_skill_docs.py ← 輔助腳本
├── SKILL.md             ← Skill 定義與規則
```

---

## 5. 常見問題

**Q：如何安裝這個 Skill？**
A：將 `SKILL.md` 放到 `C:\Users\User\.copilot\skills\auto-skill-docs\` 即可。下次啟動 Agent session 時會自動載入。

**Q：如何更新 Skill？**
A：直接編輯 `SKILL.md`，下次 Agent session 啟動時生效。

---

*GitHub Copilot CLI Skill · auto-skill-docs · v1.0*
