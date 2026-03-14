import httpx
import os

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4/sports"

SPORT_MAP = {
    "nfl": "americanfootball_nfl",
    "nba": "basketball_nba",
    "mlb": "baseball_mlb",
}

async def fetch_odds_api(sport: str = "nfl") -> list[dict]:
    if not ODDS_API_KEY:
        return []

    sport_key = SPORT_MAP.get(sport, "americanfootball_nfl")
    url = f"{BASE_URL}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "american",
        "bookmakers": "fanduel,draftkings,betmgm,caesars,pointsbet",
    }

    results = []
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, params=params, timeout=10)
            r.raise_for_status()
            games = r.json()
            for game in games:
                for book in game.get("bookmakers", []):
                    for market in book.get("markets", []):
                        if market["key"] == "h2h":
                            outcomes = market["outcomes"]
                            if len(outcomes) >= 2:
                                results.append({
                                    "book": book["title"],
                                    "sport": sport,
                                    "home": outcomes[0]["name"],
                                    "away": outcomes[1]["name"],
                                    "home_odds": str(outcomes[0]["price"]),
                                    "away_odds": str(outcomes[1]["price"]),
                                })
        except Exception as e:
            print(f"[OddsAPI] Error: {e}")

    return results
