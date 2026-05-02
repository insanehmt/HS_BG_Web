# HS_BattleGrounds Project Documentation

> **Hearthstone Battlegrounds** personal match tracker + encyclopedia website  
> Local full-featured version + Cloud public version (Render.com)

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Quick Start](#quick-start)
3. [Match Tracker](#match-tracker)
4. [Web Server](#web-server)
5. [Web Pages](#web-pages)
6. [API Endpoints](#api-endpoints)
7. [Scrapers](#scrapers)
8. [Maintenance Scripts](#maintenance-scripts)
9. [Standard Mode Advisor](#standard-mode-advisor)
10. [Cloud Deployment](#cloud-deployment)
11. [Data Files](#data-files)
12. [Environment Setup](#environment-setup)

---

## Project Structure

```
HS_BattleGrounds/
├── main.py                  # Main program: monitors Power.log, tracks BG matches
├── log_parser.py            # Power.log parser
├── log_config.py            # Hearthstone path configuration
├── db.py                    # SQLite database operations
├── card_db.py               # Card database
├── excel_writer.py          # Excel export
├── strategy_viewer.py       # Strategy viewer (command line)
├── update_boards.py         # Board state update tool
├── run_advisor.py           # Advisor launcher
├── regen_excel.py           # Regenerate Excel reports
│
├── web/
│   ├── app.py               # Flask backend (all APIs + pages)
│   ├── templates/           # Jinja2 HTML templates
│   └── uploads/             # Uploaded Excel file staging
│
├── scripts/                 # Maintenance / scraper scripts
├── hs_advisor/              # Standard mode play advisor module
├── data/                    # All data files (JSON + SQLite)
│
├── Dockerfile               # Cloud deployment image
├── docker-compose.yml       # Local public mode testing
├── render.yaml              # Render.com deployment config
├── .push_config             # Local push config (private, not in Git)
│
├── start_web.bat            # Launch local full version
├── start_public.bat         # Launch local public mode (Docker)
└── 打牌顧問.bat              # Launch standard mode advisor
```

---

## Quick Start

| Task | Command / Method |
|------|-----------------|
| Start local website | Double-click `start_web.bat` or `python web/app.py` |
| Start match tracker | `python main.py` |
| Start play advisor | Double-click `打牌顧問.bat` or `python run_advisor.py` |
| Push data to cloud | `python scripts/push_to_web.py` |
| Permanently update cloud | `python scripts/push_to_web.py --commit` |

---

## Match Tracker

### `main.py` — BG Match Monitor

**Purpose:** Runs in the background continuously monitoring Hearthstone's `Power.log`, automatically parsing and saving every Battlegrounds match.

**Tracked data:**
- Hero used + Hero Power
- Two trinkets selected
- Final board state (minion names, attack/health/armor, golden tags)
- Final placement, turn count, max gold, match duration
- All opponent heroes
- Game mode (Solo / Duo)

**Launch:**
```bash
python main.py
```

**Output:**
- Saved to `data/records.db` (SQLite)
- Exported to `output/hs_bg_records.xlsx` (Excel)

---

### `log_parser.py` — Power.log Parser

Parses raw Hearthstone logs, reconstructs game entity states, extracts complete match data.

**Parsed game events:**
- `CREATE_GAME` / `FULL_ENTITY` / `SHOW_ENTITY`: entity creation
- `TAG_CHANGE`: tracks health, attack, placement, game state
- `PlayerID`: identifies heroes and players
- Trinkets (`BATTLEGROUND_TRINKET`): tracks selection events

---

### `log_config.py` — Hearthstone Path Config

Auto-detects Hearthstone installation path:
- `D:\BZGame\Hearthstone` (BZGame version)
- `C:\Program Files (x86)\Hearthstone` (Battle.net version)
- `%LOCALAPPDATA%\Blizzard\Hearthstone`

---

### `db.py` — SQLite Database

**Table:** `games`  
**Fields:** hero, placement, turns, gold, mode, board, trinkets, opponents, timestamp...

**Key functions:**
- `init_db()` — create tables
- `save_game(record)` — save a match
- `get_stats()` — overall statistics
- `start_time_exists(ts)` — prevent duplicate records

---

### `excel_writer.py` — Excel Report Export

Exports SQLite data to structured `.xlsx` tables. One row per match, including hero, board composition, placement, and more.

---

## Web Server

### `web/app.py` — Flask Backend

**Tech stack:** Flask + SQLite + Alpine.js + Tailwind CSS

**Modes:**
- **Local full version** (`PUBLIC_MODE=0`, default): upload, records, scrapers — all features
- **Cloud public version** (`PUBLIC_MODE=1`): shows only 5 encyclopedia pages, hides private data

---

## Web Pages

### 🏠 Records Overview `/` (local only)
Personal BG match statistics:
- Win rate, average placement, top-4 rate
- Hero usage distribution
- Match list (filterable by mode/placement)
- Upload Excel to import records

### 📊 Current Meta `/tier-list`
- 40+ compositions (Tier S/A/B/C)
- Core cards + add-on card icons
- Difficulty, strategy notes
- Editable (add/modify compositions)
- Scraper buttons: auto-fetch Firestone + HSReplay data

### 🐾 Minion Encyclopedia `/minions`
- All BG minions, filterable by tribe/cost/stats
- Ability descriptions, golden version effects
- Search functionality

### ✨ Spell Encyclopedia `/spells`
- All BG spells
- Cost, effect, tribe tag filters

### 💎 Trinket Encyclopedia `/trinkets`
- All BG trinkets
- Quality (Common/Rare/Epic) filters

### 🦸 Hero Guide `/hero-guide`
- Hero power descriptions
- Recommended tribes/archetypes

### 📈 Hero Rankings `/heroes` (local only)
- Personal hero win rate stats (from local records.db)
- Sort by average placement / win rate / games played

---

## API Endpoints

### Match Records
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/games` | GET | Get match list with filtering/pagination |
| `/api/games/stats` | GET | Overall statistics (games/win rate/avg placement) |
| `/api/upload` | POST | Upload Excel to import match records |

### Encyclopedia Data
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/minions` | GET | Get all BG minions |
| `/api/spells` | GET | Get all BG spells |
| `/api/trinkets` | GET | Get all BG trinkets |
| `/api/heroes` | GET | Get hero ranking statistics |
| `/api/hero-guide` | GET | Get hero guide data |
| `/api/cards` | GET | Search cards (keyword/type filter) |

### Composition Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tier-list` | GET | Get all compositions (with rotation flag) |
| `/api/tier-list` | POST | Add a new composition |
| `/api/tier-list/<id>` | PUT | Edit a composition |
| `/api/tier-list/<id>` | DELETE | Delete a composition |

### Scrapers
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scrape-comps` | POST | Playwright scrape Firestone composition data |
| `/api/scrape-hsreplay` | POST | Playwright scrape HSReplay tier ratings |

### Cloud Sync
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/push-data` | POST | Receive local data push (requires SYNC_TOKEN auth) |

---

## Scrapers

### Firestone Scraper (`/api/scrape-comps`)

**Source:** https://www.firestoneapp.com/battlegrounds/comps

**Tech:** Playwright (headless Chromium) + network response interception

**Scraped data:**
- compId, powerLevel (S/A/B/C), difficulty
- Core cards (CORE), add-on choices (ADDON/CYCLE)
- Average placement, data points, patch number
- English strategy tips

**Merge rules (never delete existing compositions):**
1. Direct ID match → update in-place (preserves user's custom name/strategy)
2. Alias match (old↔new ID mapping) → update old ID's record in-place
3. New ID not seen before → add new entry
4. Core cards: **merge** (keep existing + append new), never replace

**Standalone script:** `scripts/scrape_firestone_comps.py`

---

### HSReplay Scraper (`/api/scrape-hsreplay`)

**Source:** https://hsreplay.net/battlegrounds/comps/

**Tech:** Playwright + DOM extraction + scroll to trigger lazy loading

**Scraped data:**
- Composition name, tier rating (S/A/B), difficulty
- Core cards (Card IDs extracted from img src URLs)

**Rules:**
- Does NOT override Firestone's tier (Firestone takes priority)
- Cards are merged, not replaced
- Matches to existing compositions via `HSREPLAY_NAME_TO_ID` name mapping table

**Test script:** `scripts/test_hsreplay_final.py`

---

### `scripts/push_to_web.py` — Data Push Tool

Pushes local JSON data files to the cloud website.

```bash
# Push common data (compositions, hero meta)
python scripts/push_to_web.py

# Push all data (including minion/spell/trinket caches)
python scripts/push_to_web.py --all

# Push + git commit (permanent, triggers Render redeploy)
python scripts/push_to_web.py --commit
```

**Configuration:** Create `.push_config`:
```
WEB_URL=https://hs-bg-web.onrender.com
SYNC_TOKEN=your_secret
```

---

### `scripts/update_and_push.py` — One-Click Update Script

Scrape + push in one command (requires local Flask to be running):

```bash
python scripts/update_and_push.py             # scrape + push
python scripts/update_and_push.py --push-only # push only
python scripts/update_and_push.py --all       # push all data
```

---

## Maintenance Scripts

| Script | Purpose |
|--------|---------|
| `scripts/cleanup_comps.py` | Clean duplicate compositions (merge old→new IDs) |
| `scripts/check_comps.py` | Quick list of all composition IDs and Tiers |
| `scripts/add_comps.py` | Batch add composition data |
| `scripts/merge_old_comps.py` | Merge legacy composition data |
| `scripts/rebuild_comps_firestone.py` | Rebuild compositions from Firestone format |
| `scripts/fetch_bg_spells.py` | Fetch BG spell data |
| `scripts/search_cards.py` | Search card IDs |
| `regen_excel.py` | Regenerate Excel report from SQLite |
| `update_boards.py` | Update board state data |

---

## Standard Mode Advisor

> ⚠️ This module is for **Standard mode** matches, not Battlegrounds

### Launch
- Double-click `打牌顧問.bat`
- Or `python run_advisor.py`

### `hs_advisor/hs_advisor.py` — Main Display Module
Reads live game state from Power.log and displays:
- Likely opponent deck archetypes (class + this week's meta)
- Board state (friendly/enemy minions, attack/health/taunt/divine shield)
- Hand contents (cost, name, card text)
- Turn priority suggestions (clear board / lethal analysis)

### `hs_advisor/hs_game_state.py` — Game State Parser
Real-time Power.log parsing, tracking:
- Board minions (PLAY zone)
- Hand cards (HAND zone)
- Secrets (SECRET zone)

### `hs_advisor/mulligan.py` — Mulligan Advisor
Based on opening hand cost distribution, opponent class, and meta style, gives "keep" or "mulligan" decisions:
- Always keep: taunt, battlecry, card draw engines
- Always mulligan: combo pieces, high-cost cards (when going first)

### `hs_advisor/hsreplay_meta.py` — HSReplay Meta Integration
Fetches this week's strongest archetypes per class from HSReplay API to predict opponent strategies.

### `hs_advisor/strategy_manager.py` — Archetype Strategy Manager
- Reads JSON strategy files from `data/strategies/`
- Auto-detects archetype style (aggro/control/midrange/spell)
- Auto-creates strategy templates on first run

---

## Cloud Deployment

### Architecture

```
Local (you)                  ←→              Cloud (friends)
─────────────────────               ─────────────────────
Full features:                       Public encyclopedia:
• Match tracking                     • Current Meta
• Upload records                     • Minion Encyclopedia
• Run scrapers                       • Spell Encyclopedia
• Hero rankings                      • Trinket Encyclopedia
                                     • Hero Guide
         ↓
python scripts/push_to_web.py
```

### Deployment Files

| File | Description |
|------|-------------|
| `Dockerfile` | Lightweight image (Python + Flask + gunicorn, no Playwright) |
| `docker-compose.yml` | Local public mode testing (port 5001) |
| `render.yaml` | Render.com free tier config |
| `requirements_web.txt` | Cloud minimal dependencies (flask/gunicorn/requests/openpyxl) |
| `.push_config` | Local push settings (URL + token, excluded from Git) |
| `.push_config.example` | Config template |
| `DEPLOY.md` | Full step-by-step deployment guide |

### Environment Variables (Render settings)

| Variable | Description |
|----------|-------------|
| `PUBLIC_MODE=1` | Enable public mode, hide private pages |
| `SYNC_TOKEN=xxx` | Data push authentication token |

### Daily Update Workflow
```bash
# After running scrapers locally:

# Quick push (session-only, resets on Render restart)
python scripts/push_to_web.py

# Permanent update (git commit + push → Render auto-redeploys)
python scripts/push_to_web.py --commit
```

---

## Data Files

| File | Size | Description |
|------|------|-------------|
| `data/bg_comps.json` | 58 KB | BG compositions (40+ comps, Tier/strategy/cards) |
| `data/bg_minions_cache.json` | 666 KB | All BG minions (ID/name/cost/stats/text) |
| `data/bg_spells_cache.json` | 76 KB | All BG spells |
| `data/bg_trinkets_cache.json` | 68 KB | All BG trinkets |
| `data/bg_heroes_cache.json` | — | Hero guide data |
| `data/hero_meta.json` | 4 KB | Hero meta stats (win rate/placement/popularity) |
| `data/hsreplay_meta_cache.json` | 42 KB | HSReplay meta cache |
| `data/bg_config.json` | 1 KB | Version config (current season/patch) |
| `data/records.db` | private | Personal match records SQLite (not synced to cloud) |
| `data/hs_cards_full.json` | 5.3 MB | Full card database (hero power search) |
| `data/cards_cache.json` | 1.1 MB | Card cache |
| `data/strategies/` | — | Archetype strategy JSONs (one file per meta archetype) |

---

## Environment Setup

### Local Installation
```bash
pip install -r requirements.txt
playwright install chromium   # for scrapers
```

### requirements.txt (local full version)
```
flask>=3.0.0
openpyxl>=3.1.0
watchdog>=4.0.0
requests>=2.31.0
playwright>=1.44.0
```

### requirements_web.txt (cloud minimal version)
```
flask>=3.0.0
gunicorn>=21.0.0
requests>=2.31.0
openpyxl>=3.1.0
```

### Git Operations
```bash
# Commit data updates and trigger Render redeploy
git add data/bg_comps.json
git commit -m "data: update composition data"
git push
```

### Cloud Website
🌐 **https://hs-bg-web.onrender.com**
