import asyncio
from fuzzywuzzy import fuzz

from backend.scrapers.fanduel import scrape_fanduel
from backend.scrapers.draftkings import scrape_draftkings
from backend.scrapers.betmgm import scrape_betmgm
from backend.scrapers.odds_api import fetch_odds_api
from backend.engine.arb_calculator import find_arbs_from_events, find_all_arbs
from backend.engine.normalizer import MATCH_THRESHOLD
from backend.db.database import save_arbs

SPORTS = ["nfl", "nba", "mlb"]
POLL_INTERVAL = 30  # seconds — fresh data matters for arbs


def _merge_scraped_into_events(events: list[dict], scraped_flat: list[dict]) -> list[dict]:
    """
    Fold flat scraper records {book, home, away, home_odds, away_odds} into the
    per-event grouped structure that find_arbs_from_events() expects.
    New events (not already in the API list) are appended.
    """
    def _norm(name: str) -> str:
        return name.lower().strip()

    for flat in scraped_flat:
        book = flat.get("book", "")
        s_home = _norm(flat.get("home", ""))
        s_away = _norm(flat.get("away", ""))
        merged = False

        for event in events:
            # Use token_set_ratio so "Kansas City Chiefs" matches "Chiefs" reliably
            score = (
                fuzz.token_set_ratio(s_home, _norm(event["home"])) +
                fuzz.token_set_ratio(s_away, _norm(event["away"]))
            ) / 2
            if score >= MATCH_THRESHOLD and book not in event["books"]:
                event["books"][book] = {
                    "home_odds": flat.get("home_odds", ""),
                    "away_odds": flat.get("away_odds", ""),
                }
                merged = True
                break

        if not merged:
            # Brand-new event from scraper — add it
            events.append({
                "event_id": f"scraped_{s_home}_{s_away}",
                "sport": flat.get("sport", ""),
                "home": flat.get("home", ""),
                "away": flat.get("away", ""),
                "books": {
                    book: {
                        "home_odds": flat.get("home_odds", ""),
                        "away_odds": flat.get("away_odds", ""),
                    }
                },
            })

    return events


async def run_cycle():
    print("[Scheduler] Running arb scan...")
    total_arbs = 0

    for sport in SPORTS:
        # ── Primary: Odds API (all bookmakers per game, already grouped) ──
        api_events = await fetch_odds_api(sport)

        # ── Supplemental: Playwright scrapers (parallel) ──
        fd_data, dk_data, mgm_data = await asyncio.gather(
            scrape_fanduel(sport),
            scrape_draftkings(sport),
            scrape_betmgm(sport),
            return_exceptions=True,
        )
        scraped_flat = [
            item
            for source in [fd_data, dk_data, mgm_data]
            if isinstance(source, list)
            for item in source
        ]
        if scraped_flat:
            print(f"  [Scrapers] {sport}: +{len(scraped_flat)} supplemental lines")

        if api_events:
            # Merge any scraper data in, then run the best-odds-across-all-books finder
            events = _merge_scraped_into_events(api_events, scraped_flat)
            arbs = find_arbs_from_events(events, min_profit=0.5)
        else:
            # No API key or API failed — fall back to pairwise scraper comparison
            all_data: dict[str, list[dict]] = {}
            for item in scraped_flat:
                all_data.setdefault(item.get("book", "Unknown"), []).append(item)
            arbs = find_all_arbs(all_data, min_profit=0.5) if len(all_data) >= 2 else []

        total_arbs += len(arbs)
        if arbs:
            print(f"  ✅ {sport}: {len(arbs)} arb(s)")
            await save_arbs(arbs)
        else:
            print(f"  — {sport}: no arbs")

    print(f"[Scheduler] Done — {total_arbs} total arb(s) this cycle\n")


async def start_scheduler():
    while True:
        try:
            await run_cycle()
        except Exception as e:
            print(f"[Scheduler] Error: {e}")
        await asyncio.sleep(POLL_INTERVAL)
