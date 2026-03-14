import asyncio
from backend.scrapers.fanduel import scrape_fanduel
from backend.scrapers.draftkings import scrape_draftkings
from backend.scrapers.betmgm import scrape_betmgm
from backend.scrapers.odds_api import fetch_odds_api
from backend.engine.arb_calculator import find_all_arbs
from backend.db.database import save_arbs

SPORTS = ["nfl", "nba", "mlb"]
POLL_INTERVAL = 60  # seconds between scan cycles
MIN_REQUIRED_SCRAPES = 3  # fall back to API when fewer results arrive


async def run_cycle():
    """Run one full arbitrage scan across all sports and sportsbooks."""
    print("[Scheduler] Running arb scan...")

    for sport in SPORTS:
        print(f"  → Scraping {sport}...")

        fd_data, dk_data, mgm_data = await asyncio.gather(
            scrape_fanduel(sport),
            scrape_draftkings(sport),
            scrape_betmgm(sport),
            return_exceptions=True,
        )

        total_scraped = (
            (len(fd_data) if isinstance(fd_data, list) else 0)
            + (len(dk_data) if isinstance(dk_data, list) else 0)
            + (len(mgm_data) if isinstance(mgm_data, list) else 0)
        )

        api_data: list = []
        if total_scraped < MIN_REQUIRED_SCRAPES:
            print(f"  → Falling back to Odds API for {sport}")
            api_data = await fetch_odds_api(sport)

        all_data: dict[str, list] = {
            "FanDuel": fd_data if isinstance(fd_data, list) else [],
            "DraftKings": dk_data if isinstance(dk_data, list) else [],
            "BetMGM": mgm_data if isinstance(mgm_data, list) else [],
        }

        for item in api_data:
            book = item.get("book", "API")
            if book not in all_data:
                all_data[book] = []
            all_data[book].append(item)

        arbs = find_all_arbs(all_data, min_profit=0.5)

        if arbs:
            # Tag each arb with its sport
            for arb in arbs:
                arb["sport"] = sport
            print(f"  ✅ Found {len(arbs)} arb(s) for {sport}!")
            await save_arbs(arbs)
        else:
            print(f"  — No arbs found for {sport}")


async def start_scheduler():
    """Continuously run arbitrage scans on a fixed interval."""
    while True:
        try:
            await run_cycle()
        except Exception as e:
            print(f"[Scheduler] Error: {e}")
        await asyncio.sleep(POLL_INTERVAL)
