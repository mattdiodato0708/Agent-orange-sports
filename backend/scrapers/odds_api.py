import os
import httpx

# The Odds API – sign up at https://the-odds-api.com for a free key
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4/sports"

SPORT_KEYS = {
    "nfl": "americanfootball_nfl",
    "nba": "basketball_nba",
    "mlb": "baseball_mlb",
}

# Request timeout in seconds
REQUEST_TIMEOUT = 15


async def fetch_odds_api(sport: str) -> list:
    """Fetch odds from The Odds API as a fallback data source.

    Returns a list of dicts: ``[{"event", "outcome", "odds", "book", "sport"}, ...]``
    """
    sport_key = SPORT_KEYS.get(sport)
    if not sport_key or not ODDS_API_KEY:
        return []

    url = f"{ODDS_API_BASE}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "american",
    }

    results: list[dict] = []

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        for game in data:
            home = game.get("home_team", "")
            away = game.get("away_team", "")
            event_name = f"{away} vs {home}"

            for bookmaker in game.get("bookmakers", []):
                book_title = bookmaker.get("title", "API")
                for market in bookmaker.get("markets", []):
                    if market.get("key") != "h2h":
                        continue
                    for outcome in market.get("outcomes", []):
                        results.append(
                            {
                                "event": event_name,
                                "outcome": outcome.get("name", ""),
                                "odds": outcome.get("price", 0),
                                "book": book_title,
                                "sport": sport,
                            }
                        )
    except Exception as exc:
        print(f"[OddsAPI] Fetch error ({sport}): {exc}")

    return results
