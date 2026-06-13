# ➡️ always-ask-next — User Guide (English)

> **Skill version:** 1.0  |  **Last updated:** 2026-06-04

---

## Table of Contents

1. [What Is This Skill?](#1-what-is-this-skill)
2. [Trigger Keywords](#2-trigger-keywords)
3. [How to Use](#3-how-to-use)
4. [Skill Files](#4-skill-files)
5. [FAQ](#5-faq)

---

## 1. What Is This Skill?

**always-ask-next** is a GitHub Copilot CLI skill installed in this environment.

Always ask the user what to do next before finishing all tasks. Use AskUserQuestion with 3 dynamically generated relevant suggestions". ⚠️ This is a MANDATORY rule — must always be followed without exception.

---

## 2. Trigger Keywords

| Phrase | Action |
|--------|--------|
| *(see SKILL.md)* | Activates this skill |

---

## 3. How to Use

Simply type one of the trigger phrases listed above into the chat, and the agent
will automatically execute the corresponding workflow.

All output files are saved to the configured output directory. No special setup
is needed beyond having the skill installed.

---

## 4. Skill Files

```
C:\Users\User\.copilot\skills\always-ask-next\
├── SKILL.md             ← Skill definition and rules
```

---

## 5. FAQ

**Q: How do I install this skill?**
A: The skill is installed by placing the `SKILL.md` file in
`C:\Users\User\.copilot\skills\always-ask-next\`. It loads automatically on next session.

**Q: How do I update the skill?**
A: Edit `SKILL.md` directly. Changes take effect on the next agent session.

---

*GitHub Copilot CLI Skill · always-ask-next · v1.0*
