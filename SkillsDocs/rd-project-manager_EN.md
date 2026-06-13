# 📋 rd-project-manager — User Guide (English)

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

**rd-project-manager** is a GitHub Copilot CLI skill installed in this environment.

R&D project management skill. Manages SPEC, IssueList, ReleaseNote, and bilingual UserGuides for a software project. Triggered when user says 'fix issue', 'update spec', 'add feature', 'new release', 'update docs', or uses /rdpm command. Automatically updates all related documents after every code or spec change.

---

## 2. Trigger Keywords

| Phrase | Action |
|--------|--------|
| `fix issue ISS-XXX` | Activates this skill |
| `fix it` | Activates this skill |
| `update spec` | Activates this skill |
| `add feature F-XX` | Activates this skill |
| `new release` | Activates this skill |
| `release v1.2.3` | Activates this skill |
| `update docs` | Activates this skill |
| `sync docs` | Activates this skill |
| `export spec` | Activates this skill |
| `generate word` | Activates this skill |
| `/rdpm export-spec` | Activates this skill |
| `/rdpm status` | Activates this skill |
| `/rdpm init <path> <ProjectName>` | Activates this skill |

---

## 3. How to Use

Simply type one of the trigger phrases listed above into the chat, and the agent
will automatically execute the corresponding workflow.

All output files are saved to the configured output directory. No special setup
is needed beyond having the skill installed.

---

## 4. Skill Files

```
C:\Users\User\.copilot\skills\rd-project-manager\
├── make_spec_docx.py    ← Helper script
├── SKILL.md             ← Skill definition and rules
```

---

## 5. FAQ

**Q: How do I install this skill?**
A: The skill is installed by placing the `SKILL.md` file in
`C:\Users\User\.copilot\skills\rd-project-manager\`. It loads automatically on next session.

**Q: How do I update the skill?**
A: Edit `SKILL.md` directly. Changes take effect on the next agent session.

---

*GitHub Copilot CLI Skill · rd-project-manager · v1.0*
