# 🟠 Agent Orange Sports — Arb Finder

A full-stack sports arbitrage analytics system. Scrapes odds from FanDuel, DraftKings, and BetMGM using Playwright (no API required), matches events across books, calculates arbitrage opportunities, and displays them in a live dashboard.

## Stack
- **Backend:** Python + FastAPI
- **Scraping:** Playwright (headless Chromium) — no API key needed
- **API Fallback:** The Odds API (optional, set `ODDS_API_KEY` in Replit Secrets)
- **Arb Engine:** Fuzzy event matching + decimal odds math
- **DB:** SQLite (aiosqlite)
- **Frontend:** Vanilla HTML/JS dashboard

## How to Run on Replit
1. Import this repo into Replit
2. (Optional) Add `ODDS_API_KEY` to Replit Secrets
3. Click **Run** — `start.sh` handles everything

## How It Works
1. Playwright scrapes FanDuel, DraftKings, BetMGM every 60 seconds
2. Events are fuzzy-matched across books
3. Arb calculator checks if `sum(1/odds) < 1.0`
4. Opportunities are saved to SQLite and shown in the dashboard
5. If scraping fails, falls back to The Odds API automatically

## Arbitrage Math
- Convert American odds to decimal: `+150 → 2.5`, `-110 → 1.909`
- Implied probability: `1 / decimal_odds`
- Arb exists when: `(1/oddsA) + (1/oddsB) < 1.0`
- Profit %: `(1 - inv_sum) * 100`

## Project Structure
```
Agent-orange-sports/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── scheduler.py      # Polling loop
│   ├── scrapers/
│   │   ├── fanduel.py    # Playwright scraper
│   │   ├── draftkings.py # Playwright scraper
│   │   ├── betmgm.py     # Playwright scraper
│   │   └── odds_api.py   # API fallback
│   ├── engine/
│   │   ├── normalizer.py     # Odds conversion + fuzzy matching
│   │   └── arb_calculator.py # Core arb logic
│   └── db/
│       └── database.py   # SQLite (aiosqlite)
├── frontend/
│   └── index.html        # Live dashboard
├── requirements.txt
├── .replit
├── start.sh
└── README.md
```

> ⚠️ For educational and analytical use. Always check sportsbook Terms of Service.
