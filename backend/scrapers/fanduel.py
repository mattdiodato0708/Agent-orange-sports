import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from backend.scrapers.common import USER_AGENTS, MIN_DELAY, MAX_DELAY

FANDUEL_URLS = {
    "nfl": "https://sportsbook.fanduel.com/navigation/nfl",
    "nba": "https://sportsbook.fanduel.com/navigation/nba",
    "mlb": "https://sportsbook.fanduel.com/navigation/mlb",
}


async def scrape_fanduel(sport: str) -> list:
    """Scrape moneyline odds from FanDuel for *sport*.

    Returns a list of dicts: ``[{"event", "outcome", "odds", "book"}, ...]``
    """
    url = FANDUEL_URLS.get(sport)
    if not url:
        return []

    results: list[dict] = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )

            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # FanDuel renders event rows with data attributes;
            # selectors may need updating when FanDuel changes layout.
            event_rows = soup.select("[class*='event-card'], [class*='EventCard']")

            for row in event_rows:
                teams = row.select("[class*='participant'], [class*='team-name']")
                odds_els = row.select("[class*='price'], [class*='odds']")

                if len(teams) >= 2 and len(odds_els) >= 2:
                    event_name = f"{teams[0].get_text(strip=True)} vs {teams[1].get_text(strip=True)}"
                    for team, odds_el in zip(teams, odds_els):
                        odds_text = odds_el.get_text(strip=True).replace("+", "")
                        try:
                            odds_val = float(odds_text)
                        except ValueError:
                            continue
                        results.append(
                            {
                                "event": event_name,
                                "outcome": team.get_text(strip=True),
                                "odds": odds_val,
                                "book": "FanDuel",
                                "sport": sport,
                            }
                        )

            await browser.close()
    except Exception as exc:
        print(f"[FanDuel] Scrape error ({sport}): {exc}")

    return results
