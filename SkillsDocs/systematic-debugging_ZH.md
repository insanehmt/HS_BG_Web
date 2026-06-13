# ⚙️ systematic-debugging — 使用者指南（繁體中文）

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

**systematic-debugging** 是安裝在此環境中的 GitHub Copilot CLI skill。

Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes

---

## 2. 觸發關鍵詞

| 觸發詞 | 動作 |
|--------|------|
| *(請參考 SKILL.md)* | 啟動此 Skill |

---

## 3. 如何使用

在對話中輸入上方任一觸發詞，Agent 就會自動執行對應的工作流程。

所有輸出檔案會儲存到設定的輸出目錄，不需要特別的安裝設定。

---

## 4. Skill 檔案位置

```
C:\Users\User\.copilot\skills\systematic-debugging\
├── condition-based-waiting-example.ts ← 輔助腳本
├── condition-based-waiting.md ← 輔助腳本
├── CREATION-LOG.md      ← 輔助腳本
├── defense-in-depth.md  ← 輔助腳本
├── find-polluter.sh     ← 輔助腳本
├── root-cause-tracing.md ← 輔助腳本
├── SKILL.md             ← Skill 定義與規則
├── test-academic.md     ← 輔助腳本
├── test-pressure-1.md   ← 輔助腳本
├── test-pressure-2.md   ← 輔助腳本
├── test-pressure-3.md   ← 輔助腳本
```

---

## 5. 常見問題

**Q：如何安裝這個 Skill？**
A：將 `SKILL.md` 放到 `C:\Users\User\.copilot\skills\systematic-debugging\` 即可。下次啟動 Agent session 時會自動載入。

**Q：如何更新 Skill？**
A：直接編輯 `SKILL.md`，下次 Agent session 啟動時生效。

---

*GitHub Copilot CLI Skill · systematic-debugging · v1.0*
