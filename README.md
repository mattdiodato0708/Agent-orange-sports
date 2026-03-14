# Agent Orange Sports — Arbitrage Finder

A full-stack sports arbitrage analytics system that scrapes odds from multiple
sportsbooks, matches events across books, calculates arbitrage opportunities,
and displays them in a live dark-themed dashboard.

## Features

- **Playwright scrapers** for FanDuel, DraftKings, and BetMGM (headless, stealth)
- **The Odds API** fallback when scrapers return insufficient data
- **Fuzzy event matching** across sportsbooks (FuzzyWuzzy)
- **Arbitrage calculator** with optimal stake sizing
- **Live dashboard** (auto-refreshing, dark theme, mobile-friendly)
- **SQLite storage** via aiosqlite for historical arb tracking
- **FastAPI** backend with REST endpoints

## Project Structure

```
Agent-orange-sports/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── scheduler.py          # Async polling loop
│   ├── scrapers/
│   │   ├── fanduel.py        # FanDuel Playwright scraper
│   │   ├── draftkings.py     # DraftKings Playwright scraper
│   │   ├── betmgm.py         # BetMGM Playwright scraper
│   │   └── odds_api.py       # The Odds API fallback
│   ├── engine/
│   │   ├── normalizer.py     # Odds conversion & fuzzy matching
│   │   └── arb_calculator.py # Core arbitrage logic
│   └── db/
│       └── database.py       # aiosqlite database layer
├── frontend/
│   └── index.html            # Live arb dashboard
├── requirements.txt
├── .replit
├── start.sh
└── README.md
```

## Quick Start

### On Replit

Click **Run** — the `.replit` config will install dependencies, set up Playwright,
and start the server on port 8080.

### Locally

```bash
pip install -r requirements.txt
python -m playwright install chromium
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```

Open <http://localhost:8080> to view the dashboard.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `ODDS_API_KEY` | API key for [The Odds API](https://the-odds-api.com) | *(empty — API fallback disabled)* |
| `DB_PATH` | Path to the SQLite database file | `arb_data.db` |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/arbs?min_profit=0.5` | Recent arbitrage opportunities |
| `GET` | `/api/status` | Health-check / version |
| `GET` | `/` | Live dashboard (HTML) |
