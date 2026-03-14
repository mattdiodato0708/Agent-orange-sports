import httpx
import os

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4/sports"

# Extended sport coverage
SPORT_KEYS = {
    "nfl":   "americanfootball_nfl",
    "nba":   "basketball_nba",
    "mlb":   "baseball_mlb",
    "nhl":   "icehockey_nhl",
    "ncaaf": "americanfootball_ncaaf",
    "ncaab": "basketball_ncaab",
}

async def fetch_odds_api(sport: str = "nfl") -> list[dict]:
    """
    Return one entry per game with ALL available bookmakers grouped under it.
    Format: [{"sport": ..., "home": ..., "away": ..., "books": {"FanDuel": {...}, ...}}]
    This lets the arb calculator compare every book's odds for the same game at once.
    """
    if not ODDS_API_KEY:
        return []

    sport_key = SPORT_KEYS.get(sport, "americanfootball_nfl")
    url = f"{BASE_URL}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us,us2",
        "markets": "h2h",
        "oddsFormat": "american",
    }

    events: list[dict] = []
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, params=params, timeout=15)
            r.raise_for_status()
            games = r.json()

            for game in games:
                home_team = game.get("home_team", "")
                away_team = game.get("away_team", "")
                books: dict[str, dict] = {}

                for book in game.get("bookmakers", []):
                    for market in book.get("markets", []):
                        if market["key"] != "h2h":
                            continue
                        outcome_map = {o["name"]: o["price"] for o in market["outcomes"]}
                        h_price = outcome_map.get(home_team)
                        a_price = outcome_map.get(away_team)
                        if h_price is not None and a_price is not None:
                            books[book["title"]] = {
                                "home_odds": str(h_price),
                                "away_odds": str(a_price),
                            }

                if books:
                    events.append({
                        "event_id": game.get("id", ""),
                        "sport": sport,
                        "home": home_team,
                        "away": away_team,
                        "commence_time": game.get("commence_time", ""),
                        "books": books,
                    })

            remaining = r.headers.get("x-requests-remaining", "?")
            total_lines = sum(len(e["books"]) for e in events)
            print(f"  [OddsAPI] {sport}: {len(events)} games, {total_lines} book lines"
                  f" | requests left: {remaining}")
        except Exception as e:
            print(f"  [OddsAPI] Error fetching {sport}: {e}")

    return events
