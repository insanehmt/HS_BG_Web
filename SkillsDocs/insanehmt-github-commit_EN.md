# 🚀 insanehmt-github-commit — User Guide (English)

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

**insanehmt-github-commit** is a GitHub Copilot CLI skill installed in this environment.

Push code to GitHub account insanehmt via API token. Triggered when user says 'push to github', 'git push', 'commit and push', 'push code', or 'upload to github'.

---

## 2. Trigger Keywords

| Phrase | Action |
|--------|--------|
| `push to github` | Activates this skill |
| `git push` | Activates this skill |
| `commit and push` | Activates this skill |
| `push code` | Activates this skill |
| `upload to github` | Activates this skill |
| `create repo` | Activates this skill |
| `new github repo` | Activates this skill |
| `set token` | Activates this skill |
| `update token` | Activates this skill |
| `configure token` | Activates this skill |

---

## 3. How to Use

Simply type one of the trigger phrases listed above into the chat, and the agent
will automatically execute the corresponding workflow.

All output files are saved to the configured output directory. No special setup
is needed beyond having the skill installed.

---

## 4. Skill Files

```
C:\Users\User\.copilot\skills\insanehmt-github-commit\
├── config.json          ← Helper script
├── github_commit.py     ← Helper script
├── SKILL.md             ← Skill definition and rules
```

---

## 5. FAQ

**Q: How do I install this skill?**
A: The skill is installed by placing the `SKILL.md` file in
`C:\Users\User\.copilot\skills\insanehmt-github-commit\`. It loads automatically on next session.

**Q: How do I update the skill?**
A: Edit `SKILL.md` directly. Changes take effect on the next agent session.

---

*GitHub Copilot CLI Skill · insanehmt-github-commit · v1.0*
