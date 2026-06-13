# 📝 auto-skill-docs — User Guide (English)

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

**auto-skill-docs** is a GitHub Copilot CLI skill installed in this environment.

Automatically generates bilingual (EN + ZH) UserGuide markdown files for all installed Copilot CLI skills whenever a skill is created or updated. Saves output to F:\GitHub_Copilot\SkillsDocs\ and updates the README index.

---

## 2. Trigger Keywords

| Phrase | Action |
|--------|--------|
| `new skill created` | Activates this skill |
| `skill updated` | Activates this skill |
| `skill modified` | Activates this skill |
| `sync skill docs` | Activates this skill |
| `sync all skill docs` | Activates this skill |
| `update skill docs` | Activates this skill |
| `/skill-doc` | Activates this skill |
| `generate skill guide <name>` | Activates this skill |

---

## 3. How to Use

Simply type one of the trigger phrases listed above into the chat, and the agent
will automatically execute the corresponding workflow.

All output files are saved to the configured output directory. No special setup
is needed beyond having the skill installed.

---

## 4. Skill Files

```
C:\Users\User\.copilot\skills\auto-skill-docs\
├── generate_skill_docs.py ← Helper script
├── SKILL.md             ← Skill definition and rules
```

---

## 5. FAQ

**Q: How do I install this skill?**
A: The skill is installed by placing the `SKILL.md` file in
`C:\Users\User\.copilot\skills\auto-skill-docs\`. It loads automatically on next session.

**Q: How do I update the skill?**
A: Edit `SKILL.md` directly. Changes take effect on the next agent session.

---

*GitHub Copilot CLI Skill · auto-skill-docs · v1.0*
